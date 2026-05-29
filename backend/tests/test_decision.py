"""Decision-matrix tests — the authoritative pass/hold/escalate verdict."""
from datetime import date
from decimal import Decimal

from app.orchestrator.decision import evaluate_outcome
from app.schemas.enums import (
    BlockingReason,
    Decision,
    LineCharge,
    LineStatus,
    MatchStatus,
    Severity,
)
from app.schemas.invoice import InvoiceLineItem, VendorInvoice
from app.schemas.match import LineMatch, ThreeWayMatchReport
from app.schemas.policy import PolicyBundle
from app.schemas.variance import LineVariance, VarianceReport

from .conftest import balanced_posting, unbalanced_posting


def _matched_report(invoice_number: str) -> ThreeWayMatchReport:
    return ThreeWayMatchReport(
        invoice_number=invoice_number, po_number="PO-5000", grn_number="GRN-7000",
        match_status=MatchStatus.MATCHED,
        lines=[LineMatch(invoice_line_no=1, status=LineStatus.MATCHED)],
    )


def _clean_variance(invoice_number: str) -> VarianceReport:
    return VarianceReport(invoice_number=invoice_number, lines=[], overall_severity=Severity.NONE)


def test_clean_invoice_passes(clean_invoice, policy):
    outcome = evaluate_outcome(
        invoice=clean_invoice, match=_matched_report("INV-1043"),
        variance=_clean_variance("INV-1043"), posting=balanced_posting("INV-1043"), policy=policy,
    )
    assert outcome.decision is Decision.PASS


def test_medium_variance_out_of_tolerance_holds(clean_invoice, policy):
    variance = VarianceReport(
        invoice_number="INV-1042",
        lines=[LineVariance(
            invoice_line_no=1, financial_impact=Decimal("60.00"),
            severity=Severity.MEDIUM, within_tolerance=False,
        )],
        overall_severity=Severity.MEDIUM, financial_impact_total=Decimal("60.00"),
    )
    outcome = evaluate_outcome(
        invoice=clean_invoice, match=_matched_report("INV-1042"),
        variance=variance, posting=balanced_posting("INV-1042"), policy=policy,
    )
    assert outcome.decision is Decision.HOLD
    assert BlockingReason.VARIANCE_OUTSIDE_TOLERANCE in outcome.blocking_reasons


def test_high_variance_escalates(clean_invoice, policy):
    variance = VarianceReport(
        invoice_number="INV-1042",
        lines=[LineVariance(
            invoice_line_no=1, financial_impact=Decimal("900.00"),
            severity=Severity.HIGH, within_tolerance=False,
        )],
        overall_severity=Severity.HIGH, financial_impact_total=Decimal("900.00"),
    )
    outcome = evaluate_outcome(
        invoice=clean_invoice, match=_matched_report("INV-1042"),
        variance=variance, posting=balanced_posting("INV-1042"), policy=policy,
    )
    assert outcome.decision is Decision.ESCALATE


def test_unbalanced_posting_escalates(clean_invoice, policy):
    outcome = evaluate_outcome(
        invoice=clean_invoice, match=_matched_report("INV-1043"),
        variance=_clean_variance("INV-1043"), posting=unbalanced_posting("INV-1043"), policy=policy,
    )
    assert BlockingReason.POSTING_DRAFT_UNBALANCED in outcome.blocking_reasons
    assert outcome.decision is Decision.ESCALATE


def test_missing_po_holds(clean_invoice, policy):
    report = ThreeWayMatchReport(
        invoice_number="INV-1043", match_status=MatchStatus.MISSING_PO, lines=[],
    )
    outcome = evaluate_outcome(
        invoice=clean_invoice, match=report, variance=_clean_variance("INV-1043"),
        posting=balanced_posting("INV-1043"), policy=policy,
    )
    assert outcome.decision is Decision.HOLD
    assert BlockingReason.THREE_WAY_MATCH_INCOMPLETE in outcome.blocking_reasons


def test_vendor_on_hold_holds(policy):
    invoice = VendorInvoice(
        vendor_name="Contoso", invoice_number="INV-9", invoice_date=date(2026, 5, 20),
        currency="USD", subtotal=Decimal("10.00"), tax_total=Decimal("0"), total=Decimal("10.00"),
        line_items=[InvoiceLineItem(
            line_no=1, description="x", quantity=Decimal("1"),
            unit_price=Decimal("10.00"), line_total=Decimal("10.00"),
        )],
    )
    outcome = evaluate_outcome(
        invoice=invoice, match=_matched_report("INV-9"), variance=_clean_variance("INV-9"),
        posting=balanced_posting("INV-9"), policy=policy,
    )
    assert BlockingReason.VENDOR_ON_HOLD_LIST in outcome.blocking_reasons


def test_over_billed_holds(clean_invoice, policy):
    report = ThreeWayMatchReport(
        invoice_number="INV-1043", match_status=MatchStatus.PARTIAL,
        lines=[LineMatch(invoice_line_no=1, status=LineStatus.QUANTITY_VARIANCE, over_billed=True)],
    )
    outcome = evaluate_outcome(
        invoice=clean_invoice, match=report, variance=_clean_variance("INV-1043"),
        posting=balanced_posting("INV-1043"), policy=policy,
    )
    assert outcome.decision is Decision.HOLD
    assert BlockingReason.OVER_BILLED_VS_RECEIPT in outcome.blocking_reasons


def test_currency_mismatch_escalates(clean_invoice, policy):
    report = ThreeWayMatchReport(
        invoice_number="INV-1043", match_status=MatchStatus.PARTIAL,
        currency_mismatch=True, po_currency="EUR", lines=[],
    )
    outcome = evaluate_outcome(
        invoice=clean_invoice, match=report, variance=_clean_variance("INV-1043"),
        posting=balanced_posting("INV-1043"), policy=policy,
    )
    assert outcome.decision is Decision.ESCALATE
    assert BlockingReason.CURRENCY_MISMATCH in outcome.blocking_reasons


def test_duplicate_invoice_escalates(clean_invoice, policy):
    outcome = evaluate_outcome(
        invoice=clean_invoice, match=_matched_report("INV-1043"),
        variance=_clean_variance("INV-1043"), posting=balanced_posting("INV-1043"),
        policy=policy, is_duplicate=True,
    )
    assert outcome.decision is Decision.ESCALATE
    assert BlockingReason.DUPLICATE_INVOICE in outcome.blocking_reasons


def test_tax_discrepancy_holds(policy):
    line = InvoiceLineItem(
        line_no=1, description="x", quantity=Decimal("1"), unit_price=Decimal("100.00"),
        line_total=Decimal("100.00"), tax_rate=Decimal("0.10"),
    )
    invoice = VendorInvoice(
        vendor_name="Globex", invoice_number="INV-T", invoice_date=date(2026, 5, 20),
        currency="USD", subtotal=Decimal("100.00"), tax_total=Decimal("5.00"),
        total=Decimal("105.00"), line_items=[line],
    )
    outcome = evaluate_outcome(
        invoice=invoice, match=_matched_report("INV-T"), variance=_clean_variance("INV-T"),
        posting=balanced_posting("INV-T"), policy=policy,
    )
    assert outcome.decision is Decision.HOLD
    assert BlockingReason.TAX_DISCREPANCY in outcome.blocking_reasons


def _invoice_with_freight(freight_total: str) -> VendorInvoice:
    freight = Decimal(freight_total)
    return VendorInvoice(
        vendor_name="Globex", invoice_number="INV-F", invoice_date=date(2026, 5, 20),
        currency="USD", subtotal=Decimal("100.00") + freight, tax_total=Decimal("0"),
        total=Decimal("100.00") + freight,
        line_items=[
            InvoiceLineItem(
                line_no=1, description="Widget", quantity=Decimal("1"),
                unit_price=Decimal("100.00"), line_total=Decimal("100.00"),
            ),
            InvoiceLineItem(
                line_no=2, description="Freight", quantity=Decimal("1"),
                unit_price=freight, line_total=freight, charge_type=LineCharge.FREIGHT,
            ),
        ],
    )


def test_freight_over_tolerance_holds(policy):
    invoice = _invoice_with_freight("75.00")  # default freight_tolerance is 25.00
    outcome = evaluate_outcome(
        invoice=invoice, match=_matched_report("INV-F"), variance=_clean_variance("INV-F"),
        posting=balanced_posting("INV-F"), policy=policy,
    )
    assert outcome.decision is Decision.HOLD
    assert BlockingReason.UNPLANNED_CHARGE in outcome.blocking_reasons


def test_freight_within_tolerance_passes(policy):
    invoice = _invoice_with_freight("10.00")  # below the 25.00 freight_tolerance
    outcome = evaluate_outcome(
        invoice=invoice, match=_matched_report("INV-F"), variance=_clean_variance("INV-F"),
        posting=balanced_posting("INV-F"), policy=policy,
    )
    assert outcome.decision is Decision.PASS
    assert BlockingReason.UNPLANNED_CHARGE not in outcome.blocking_reasons


def test_uom_mismatch_escalates(clean_invoice, policy):
    report = ThreeWayMatchReport(
        invoice_number="INV-1043", match_status=MatchStatus.PARTIAL,
        lines=[LineMatch(
            invoice_line_no=1, status=LineStatus.UNIT_VARIANCE,
            within_tolerance=False, uom_mismatch=True,
        )],
    )
    outcome = evaluate_outcome(
        invoice=clean_invoice, match=report, variance=_clean_variance("INV-1043"),
        posting=balanced_posting("INV-1043"), policy=policy,
    )
    assert outcome.decision is Decision.ESCALATE
    assert BlockingReason.UOM_MISMATCH in outcome.blocking_reasons


def test_empty_line_items_escalates_quality_fail(policy):
    invoice = VendorInvoice(
        vendor_name="Globex", invoice_number="INV-Q", invoice_date=date(2026, 5, 20),
        currency="USD", subtotal=Decimal("0"), tax_total=Decimal("0"), total=Decimal("0"),
        line_items=[],
    )
    outcome = evaluate_outcome(
        invoice=invoice, match=_matched_report("INV-Q"), variance=_clean_variance("INV-Q"),
        posting=balanced_posting("INV-Q"), policy=policy,
    )
    assert BlockingReason.INVOICE_QUALITY_FAIL in outcome.blocking_reasons
    assert outcome.decision is Decision.ESCALATE
