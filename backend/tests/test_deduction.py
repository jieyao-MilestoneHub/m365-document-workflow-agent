"""Deduction-case assembly + pay-now/hold split tests."""
from __future__ import annotations

from decimal import Decimal

from app.runner import run


def test_promotion_deduction_case_is_disputable_and_evidenced():
    outcome = run("INV-1003").outcome
    (case,) = outcome.deduction_cases
    assert case.deduction_type.value == "PROMOTION_ALLOWANCE_MISSING"
    assert case.amount == Decimal("25200.00")
    assert case.status == "OPEN"
    assert case.supplier_dispute_allowed is True
    assert case.route_to == "category_manager"
    # evidence ties the PO, GRN, invoice line, and the promotion agreement together
    assert "PROMO-MAY-BEV" in case.evidence_refs
    assert any(ref.startswith("PO-6003#") for ref in case.evidence_refs)
    assert any(ref.startswith("GRN-8003#") for ref in case.evidence_refs)
    assert "25,200.00" in case.supplier_explanation or "25200.00" in case.supplier_explanation


def test_short_receipt_partial_hold_splits_payable_and_held():
    outcome = run("INV-1002").outcome
    (case,) = outcome.deduction_cases
    assert case.deduction_type.value == "SHORT_RECEIPT"
    assert case.amount == Decimal("480.00")           # (500 - 420) cases × $6.00
    assert case.route_to == "dc_receiving_supervisor"
    assert outcome.held_amount == Decimal("480.00")
    assert outcome.payable_amount == Decimal("2520.00")


def test_clean_invoice_has_no_deductions_and_full_payable():
    outcome = run("INV-1001").outcome
    assert outcome.deduction_cases == []
    assert outcome.held_amount == Decimal("0")
    assert outcome.payable_amount == Decimal("2400.00")


def test_payable_plus_held_equals_total_for_deduction_scenarios():
    for invoice_id, total in [("INV-1002", "3000.00"), ("INV-1003", "151200.00")]:
        outcome = run(invoice_id).outcome
        assert outcome.payable_amount + outcome.held_amount == Decimal(total)
