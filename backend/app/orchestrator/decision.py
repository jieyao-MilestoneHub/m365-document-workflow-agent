"""Authoritative pass / hold / escalate decision matrix.

The exception_reviewer specialist writes the human-readable summary, but the *verdict* comes
from here — deterministic, testable, and impossible for the LLM to override. This is what
guarantees a variance never silently auto-posts.
"""
from __future__ import annotations

from decimal import Decimal

from app.schemas.enums import (
    ESCALATE_REASONS,
    BlockingReason,
    Decision,
    LineCharge,
    MatchStatus,
    Severity,
)
from app.schemas.invoice import VendorInvoice
from app.schemas.match import ThreeWayMatchReport
from app.schemas.outcome import ExceptionTicket, ValidationOutcome
from app.schemas.policy import PolicyBundle
from app.schemas.posting import PostingDraft
from app.schemas.variance import VarianceReport

from .validators import (
    check_gl_accounts,
    check_posting_balance,
    check_posting_period,
    check_tax_consistency,
)

# Suggested resolutions keyed by reason, surfaced to the human reviewer.
_RESOLUTIONS: dict[BlockingReason, str] = {
    BlockingReason.MISSING_INVOICE_UPSTREAM: "Re-run extraction or request a clearer invoice.",
    BlockingReason.MISSING_THREE_WAY_MATCH_UPSTREAM: "Re-run the matcher.",
    BlockingReason.INVOICE_QUALITY_FAIL: "Request the vendor to resubmit a legible invoice.",
    BlockingReason.THREE_WAY_MATCH_INCOMPLETE: "Locate the missing PO or GRN reference.",
    BlockingReason.VARIANCE_HIGH_SEVERITY: "AP manager to review the high-impact variance.",
    BlockingReason.VARIANCE_OUTSIDE_TOLERANCE: "Confirm the price/quantity change with procurement.",
    BlockingReason.POSTING_DRAFT_UNBALANCED: "Re-derive the posting; debits must equal credits.",
    BlockingReason.GL_ACCOUNT_INVALID: "Map the line to a valid GL account.",
    BlockingReason.POSTING_PERIOD_CLOSED: "Defer posting to the next open period.",
    BlockingReason.VENDOR_ON_HOLD_LIST: "Vendor is on hold; clear the hold before posting.",
    BlockingReason.VENDOR_GRAY_ZONE: "Vendor requires extra scrutiny; manual approval needed.",
    BlockingReason.INVOICE_MISSING_FIELDS: "Fill the missing invoice fields and re-run.",
    BlockingReason.CURRENCY_MISMATCH: "Invoice and PO currencies differ; resolve FX before matching.",
    BlockingReason.DUPLICATE_INVOICE: "Invoice already posted; reject as a duplicate payment.",
    BlockingReason.TAX_DISCREPANCY: "Reconcile the invoice tax against the line tax rates.",
    BlockingReason.OVER_BILLED_VS_RECEIPT: "Billed quantity exceeds received; confirm receipt before posting.",
    BlockingReason.UNPLANNED_CHARGE: "Unplanned freight/misc charge above tolerance; confirm with procurement.",
    BlockingReason.UOM_MISMATCH: "Invoice unit of measure differs from the PO; confirm the conversion factor.",
    BlockingReason.SKU_ALIAS_UNRESOLVED: "Confirm the vendor-SKU to internal-SKU mapping.",
}


def _ticket(
    invoice_number: str,
    reason: BlockingReason,
    severity: Severity,
    affected_lines: list[int] | None = None,
    evidence: dict | None = None,
) -> ExceptionTicket:
    return ExceptionTicket(
        ticket_id=f"{invoice_number}:{reason.value}",
        exception_type=reason,
        severity=severity,
        affected_lines=affected_lines or [],
        suggested_resolution=_RESOLUTIONS.get(reason),
        evidence=evidence or {},
    )


def evaluate_outcome(
    *,
    invoice: VendorInvoice | None,
    match: ThreeWayMatchReport | None,
    variance: VarianceReport | None,
    posting: PostingDraft | None,
    policy: PolicyBundle,
    is_duplicate: bool = False,
) -> ValidationOutcome:
    """Compute the authoritative outcome from the upstream specialist payloads."""
    inv_no = invoice.invoice_number if invoice else (match.invoice_number if match else "UNKNOWN")
    tickets: list[ExceptionTicket] = []

    # --- Duplicate / currency (irreversible controls → escalate) ---------------
    if is_duplicate:
        tickets.append(_ticket(inv_no, BlockingReason.DUPLICATE_INVOICE, Severity.HIGH))
    if match is not None and match.currency_mismatch:
        tickets.append(
            _ticket(inv_no, BlockingReason.CURRENCY_MISMATCH, Severity.HIGH,
                    evidence={"invoice_currency": invoice.currency if invoice else None,
                              "po_currency": match.po_currency})
        )

    # --- Tax consistency -------------------------------------------------------
    if invoice is not None:
        tax = check_tax_consistency(invoice)
        if not tax.ok:
            tickets.append(_ticket(inv_no, BlockingReason.TAX_DISCREPANCY, Severity.MEDIUM,
                                   evidence={"detail": tax.detail}))

    # --- Upstream completeness -------------------------------------------------
    if invoice is None:
        tickets.append(_ticket(inv_no, BlockingReason.MISSING_INVOICE_UPSTREAM, Severity.HIGH))
    elif not invoice.line_items:
        tickets.append(_ticket(inv_no, BlockingReason.INVOICE_QUALITY_FAIL, Severity.HIGH))
    if match is None:
        tickets.append(
            _ticket(inv_no, BlockingReason.MISSING_THREE_WAY_MATCH_UPSTREAM, Severity.HIGH)
        )

    # --- Variance --------------------------------------------------------------
    if variance is not None:
        out_of_tol = [lv.invoice_line_no for lv in variance.lines if not lv.within_tolerance]
        if variance.overall_severity is Severity.HIGH:
            tickets.append(
                _ticket(inv_no, BlockingReason.VARIANCE_HIGH_SEVERITY, Severity.HIGH, out_of_tol)
            )
        elif variance.overall_severity is Severity.MEDIUM and out_of_tol:
            tickets.append(
                _ticket(inv_no, BlockingReason.VARIANCE_OUTSIDE_TOLERANCE, Severity.MEDIUM, out_of_tol)
            )

    # --- Unplanned charges (freight/misc above tolerance) → hold --------------
    if invoice is not None:
        charge_lines = [
            li for li in invoice.line_items
            if li.charge_type in (LineCharge.FREIGHT, LineCharge.MISC)
        ]
        charge_total = sum((li.line_total for li in charge_lines), Decimal("0"))
        if charge_total > policy.freight_tolerance:
            tickets.append(
                _ticket(
                    inv_no, BlockingReason.UNPLANNED_CHARGE, Severity.MEDIUM,
                    [li.line_no for li in charge_lines],
                    evidence={"charge_total": str(charge_total),
                              "freight_tolerance": str(policy.freight_tolerance)},
                )
            )

    # --- Three-way match completeness -----------------------------------------
    if match is not None and match.match_status in (MatchStatus.MISSING_PO, MatchStatus.MISSING_GRN):
        tickets.append(_ticket(inv_no, BlockingReason.THREE_WAY_MATCH_INCOMPLETE, Severity.MEDIUM))

    # --- Over-billed vs receipt (billing goods not yet received) ---------------
    if match is not None:
        over_lines = [m.invoice_line_no for m in match.lines if m.over_billed]
        if over_lines:
            tickets.append(
                _ticket(inv_no, BlockingReason.OVER_BILLED_VS_RECEIPT, Severity.MEDIUM, over_lines)
            )
        alias_lines = [m.invoice_line_no for m in match.lines if m.alias_unresolved]
        if alias_lines:
            tickets.append(
                _ticket(inv_no, BlockingReason.SKU_ALIAS_UNRESOLVED, Severity.LOW, alias_lines)
            )
        uom_lines = [m.invoice_line_no for m in match.lines if m.uom_mismatch]
        if uom_lines:
            tickets.append(
                _ticket(inv_no, BlockingReason.UOM_MISMATCH, Severity.HIGH, uom_lines)
            )

    # --- Posting / GL ----------------------------------------------------------
    if posting is not None:
        balance = check_posting_balance(posting)
        if not balance.ok:
            tickets.append(
                _ticket(inv_no, BlockingReason.POSTING_DRAFT_UNBALANCED, Severity.HIGH,
                        evidence={"detail": balance.detail})
            )
        gl = check_gl_accounts(posting, policy)
        if not gl.ok:
            tickets.append(_ticket(inv_no, BlockingReason.GL_ACCOUNT_INVALID, Severity.HIGH,
                                   evidence={"detail": gl.detail}))
    if invoice is not None:
        period = check_posting_period(invoice, policy)
        if not period.ok:
            tickets.append(_ticket(inv_no, BlockingReason.POSTING_PERIOD_CLOSED, Severity.MEDIUM,
                                   evidence={"detail": period.detail}))

    # --- Vendor policy ---------------------------------------------------------
    if invoice is not None:
        vname = invoice.vendor_name.lower()
        if any(v.lower() == vname for v in policy.vendors.hold_on_vendors):
            tickets.append(_ticket(inv_no, BlockingReason.VENDOR_ON_HOLD_LIST, Severity.MEDIUM))
        elif any(v.lower() == vname for v in policy.vendors.gray_zone_vendors):
            tickets.append(_ticket(inv_no, BlockingReason.VENDOR_GRAY_ZONE, Severity.LOW))
        if invoice.missing_fields:
            tickets.append(
                _ticket(inv_no, BlockingReason.INVOICE_MISSING_FIELDS, Severity.LOW,
                        evidence={"missing_fields": invoice.missing_fields})
            )

    return _assemble(inv_no, tickets)


def _assemble(invoice_number: str, tickets: list[ExceptionTicket]) -> ValidationOutcome:
    reasons = [t.exception_type for t in tickets]
    if not reasons:
        return ValidationOutcome(
            invoice_number=invoice_number,
            decision=Decision.PASS,
            confidence=0.97,
            summary="All checks passed; invoice is a clean three-way match and ready to post.",
        )
    escalate = any(r in ESCALATE_REASONS for r in reasons)
    decision = Decision.ESCALATE if escalate else Decision.HOLD
    reason_list = ", ".join(r.value for r in reasons)
    return ValidationOutcome(
        invoice_number=invoice_number,
        decision=decision,
        confidence=0.5 if escalate else 0.8,
        blocking_reasons=reasons,
        summary=f"{decision.value.title()} - {reason_list}.",
        escalation_target="ap_manager" if escalate else "process_owner",
        exception_tickets=tickets,
    )
