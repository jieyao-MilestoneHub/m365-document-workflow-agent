"""Authoritative pass / hold / escalate decision matrix.

The exception_reviewer specialist writes the human-readable summary, but the *verdict* comes
from here — deterministic, testable, and impossible for the LLM to override. This is what
guarantees a variance never silently auto-posts.
"""
from __future__ import annotations

from decimal import Decimal

from app.schemas.deduction import AllowanceAudit, DeductionCase, DeductionType
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
from app.schemas.money import to_money
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
    BlockingReason.PROMOTION_ALLOWANCE_MISSING: "Promotion allowance not applied; deduct the margin leakage and route to the category manager.",
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
    allowance_audit: AllowanceAudit | None = None,
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

    # --- Promotion allowance / margin leakage → hold --------------------------
    # A clean three-way match can still leak margin if a promotion allowance the retailer is
    # owed was never applied. Leakage above tolerance holds and routes to the category manager.
    if allowance_audit is not None and allowance_audit.margin_leakage_total > policy.allowance_tolerance:
        leaking = [ln for ln in allowance_audit.lines if ln.leakage > 0]
        affected = sorted({n for ln in leaking for n in ln.affected_lines})
        tickets.append(
            _ticket(
                inv_no, BlockingReason.PROMOTION_ALLOWANCE_MISSING, Severity.MEDIUM, affected,
                evidence={
                    "margin_leakage": str(to_money(allowance_audit.margin_leakage_total)),
                    "promotions": [ln.promo_id for ln in leaking],
                    "expected": str(to_money(sum((ln.expected_allowance for ln in leaking), Decimal("0")))),
                    "applied": str(to_money(sum((ln.applied_allowance for ln in leaking), Decimal("0")))),
                },
            )
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

    deduction_cases = build_deduction_cases(invoice, match, allowance_audit, tickets)
    held = sum((c.amount for c in deduction_cases), Decimal("0"))
    payable: Decimal | None = None
    held_out: Decimal | None = None
    if invoice is not None:
        held_out = to_money(held)
        payable = to_money(invoice.total - held)
    return _assemble(inv_no, tickets, deduction_cases, payable, held_out)


#: routing target per deduction type (where the disputable case should go)
_DEDUCTION_ROUTE: dict[DeductionType, str] = {
    DeductionType.PROMOTION_ALLOWANCE_MISSING: "category_manager",
    DeductionType.SHORT_RECEIPT: "dc_receiving_supervisor",
}


def build_deduction_cases(
    invoice: VendorInvoice | None,
    match: ThreeWayMatchReport | None,
    allowance_audit: AllowanceAudit | None,
    tickets: list[ExceptionTicket],
) -> list[DeductionCase]:
    """Turn disputable findings into auditable, supplier-facing deduction packets.

    Covers promotion-allowance leakage and short-receipt / over-billing. Each case carries the
    disputed amount, evidence references, a generated supplier-facing explanation, and a route.
    """
    if invoice is None:
        return []
    reasons = {t.exception_type for t in tickets}
    cases: list[DeductionCase] = []
    po_ref = (match.po_number if match else None) or invoice.po_ref or "PO"
    grn_ref = (match.grn_number if match else None) or invoice.grn_ref or "GRN"
    inv_no = invoice.invoice_number

    def _next_id() -> str:
        return f"DED-{inv_no}-{len(cases) + 1}"

    # Promotion allowance missing → one case per leaking promotion.
    if BlockingReason.PROMOTION_ALLOWANCE_MISSING in reasons and allowance_audit is not None:
        promos = {p.promo_id: p for p in allowance_audit.applicable_promotions}
        for ln in allowance_audit.lines:
            if ln.leakage <= 0:
                continue
            promo = promos.get(ln.promo_id)
            unit = (promo.unit_of_measure if promo else None) or "unit"
            window = f"{promo.effective_from}..{promo.effective_to}" if promo else "the agreement"
            per_unit = promo.allowance_per_unit if promo else Decimal("0")
            evidence = [f"{po_ref}#line-{n}" for n in ln.affected_lines]
            evidence += [f"{grn_ref}#line-{n}" for n in ln.affected_lines]
            evidence += [f"{inv_no}#line-{n}" for n in ln.affected_lines]
            evidence.append(ln.promo_id)
            explanation = (
                f"Invoice {inv_no} billed {ln.billed_quantity} {unit} of {ln.sku or 'goods'} at "
                f"full price with no allowance line. Promotion {ln.promo_id} grants a {per_unit} "
                f"allowance per {unit} (valid {window}), so an allowance of "
                f"{to_money(ln.expected_allowance)} was expected. Margin leakage: "
                f"{to_money(ln.leakage)}."
            )
            cases.append(DeductionCase(
                deduction_case_id=_next_id(), invoice_number=inv_no,
                vendor_name=invoice.vendor_name,
                deduction_type=DeductionType.PROMOTION_ALLOWANCE_MISSING,
                amount=to_money(ln.leakage),
                affected_lines=list(ln.affected_lines), evidence_refs=evidence,
                supplier_explanation=explanation,
                route_to=(promo.route_to if promo else _DEDUCTION_ROUTE[DeductionType.PROMOTION_ALLOWANCE_MISSING]),
            ))

    # Short receipt / over-billing → one case per over-billed line.
    if BlockingReason.OVER_BILLED_VS_RECEIPT in reasons and match is not None:
        by_line = {li.line_no: li for li in invoice.line_items}
        for m in match.lines:
            if not m.over_billed:
                continue
            li = by_line.get(m.invoice_line_no)
            if li is None:
                continue
            billable = m.remaining_billable_quantity or Decimal("0")
            short = li.quantity - billable
            if short <= 0:
                continue
            amount = to_money(short * li.unit_price)
            received = m.received_quantity if m.received_quantity is not None else billable
            unit = li.unit_of_measure or "unit"
            explanation = (
                f"Invoice {inv_no} billed {li.quantity} {unit} of {li.sku or 'goods'}, but GRN "
                f"{grn_ref} accepted only {received}. Disputed quantity: {short} {unit} at "
                f"{to_money(li.unit_price)} = {amount}."
            )
            cases.append(DeductionCase(
                deduction_case_id=_next_id(), invoice_number=inv_no,
                vendor_name=invoice.vendor_name,
                deduction_type=DeductionType.SHORT_RECEIPT, amount=amount,
                affected_lines=[m.invoice_line_no],
                evidence_refs=[
                    f"{po_ref}#line-{m.invoice_line_no}", f"{grn_ref}#line-{m.invoice_line_no}",
                    f"{inv_no}#line-{m.invoice_line_no}",
                ],
                supplier_explanation=explanation,
                route_to=_DEDUCTION_ROUTE[DeductionType.SHORT_RECEIPT],
            ))

    return cases


def _assemble(
    invoice_number: str,
    tickets: list[ExceptionTicket],
    deduction_cases: list[DeductionCase] | None = None,
    payable_amount: Decimal | None = None,
    held_amount: Decimal | None = None,
) -> ValidationOutcome:
    deduction_cases = deduction_cases or []
    reasons = [t.exception_type for t in tickets]
    if not reasons:
        return ValidationOutcome(
            invoice_number=invoice_number,
            decision=Decision.PASS,
            confidence=0.97,
            summary="All checks passed; invoice is a clean three-way match and ready to post.",
            payable_amount=payable_amount,
            held_amount=held_amount,
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
        deduction_cases=deduction_cases,
        payable_amount=payable_amount,
        held_amount=held_amount,
    )
