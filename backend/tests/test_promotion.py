"""promotion_auditor + allowance-reconciliation tests.

Proves the retail differentiator: an invoice that matches its PO/GRN exactly still surfaces a
margin-leakage finding when a promotion allowance the retailer is owed was never applied.
"""
from __future__ import annotations

from decimal import Decimal

from app.adapters.fixtures import FixtureExtractor, FixtureKnowledge
from app.orchestrator.envelope import MultiAgentEnvelope, SpecialistResult
from app.orchestrator.roles import INVOICE_EXTRACTOR
from app.orchestrator.specialists.promotion_auditor import PromotionAuditor
from app.runner import DEFAULT_DATA_DIR, run


def _audit(invoice_id: str):
    invoice = FixtureExtractor(DEFAULT_DATA_DIR).extract(document_ref=invoice_id)
    env = MultiAgentEnvelope(invoice_ref=invoice_id).with_result(
        SpecialistResult(role=INVOICE_EXTRACTOR, payload=invoice)
    )
    return PromotionAuditor(FixtureKnowledge(DEFAULT_DATA_DIR)).run(env).payload


def test_missing_allowance_is_full_leakage():
    audit = _audit("INV-1003")
    assert audit.margin_leakage_total == Decimal("25200")
    (line,) = audit.lines
    assert line.promo_id == "PROMO-MAY-BEV"
    assert line.billed_quantity == Decimal("8400")
    assert line.expected_allowance == Decimal("25200")
    assert line.applied_allowance == Decimal("0")
    assert line.leakage == Decimal("25200")


def test_applied_allowance_has_no_leakage():
    audit = _audit("INV-1006")
    assert audit.margin_leakage_total == Decimal("0")
    (line,) = audit.lines
    assert line.expected_allowance == Decimal("25200")
    assert line.applied_allowance == Decimal("25200")
    assert line.leakage == Decimal("0")


def test_no_applicable_promotion_yields_empty_audit():
    # Fabrikam Foods has no promotion in effect → nothing to reconcile, no leakage.
    audit = _audit("INV-1004")
    assert audit.lines == []
    assert audit.margin_leakage_total == Decimal("0")


def test_promotion_audit_emits_a_grounded_citation():
    audit = _audit("INV-1003")
    assert any(c.document_id == "PROMO-MAY-BEV" for c in audit.citations)


def test_missing_allowance_holds_with_promotion_citation_end_to_end():
    result = run("INV-1003")
    outcome = result.outcome
    assert outcome.decision.value == "hold"
    assert any(r.value == "PROMOTION_ALLOWANCE_MISSING" for r in outcome.blocking_reasons)
    # the three-way match itself is clean — the hold comes from the promotion reconciliation
    match = result.envelope.payload_for("po_grn_matcher")
    assert all(m.within_tolerance for m in match.lines)
