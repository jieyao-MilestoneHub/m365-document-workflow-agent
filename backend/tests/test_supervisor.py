"""End-to-end supervisor tests over the synthetic sample data (offline, no cloud)."""
from __future__ import annotations

from app.orchestrator.envelope import SpecialistResult
from app.orchestrator.guardrails import GuardrailCeiling
from app.orchestrator.roles import INVOICE_EXTRACTOR, PO_GRN_MATCHER
from app.runner import default_registry, run
from app.schemas.enums import BlockingReason, Decision


def test_clean_invoice_passes():
    result = run("INV-1043")
    assert result.outcome.decision is Decision.PASS


def test_clean_invoice_posting_is_balanced():
    result = run("INV-1043")
    posting = result.envelope.payload_for("posting_preparer")
    assert posting.debit_total() == posting.credit_total()


def test_variance_invoice_holds():
    result = run("INV-1042")
    assert result.outcome.decision is Decision.HOLD
    assert BlockingReason.VARIANCE_OUTSIDE_TOLERANCE in result.outcome.blocking_reasons


def test_variance_invoice_triggers_peer_review():
    result = run("INV-1042")
    assert any(e.kind == "peer_review" for e in result.events)


def test_match_report_carries_citations():
    result = run("INV-1042")
    match = result.envelope.payload_for(PO_GRN_MATCHER)
    assert len(match.citations) >= 1


def test_run_emits_finalize_event():
    result = run("INV-1043")
    assert result.events[-1].kind == "finalize"


def test_audit_trail_is_populated():
    result = run("INV-1043")
    assert len(result.envelope.handoff_history) >= 5


class _FailingExtractor:
    role = INVOICE_EXTRACTOR

    def run(self, envelope):
        return SpecialistResult(role=self.role, error="boom")


def test_failed_specialist_is_retried_then_escalated(sample_data_dir):
    registry, knowledge = default_registry(sample_data_dir)
    registry[INVOICE_EXTRACTOR] = _FailingExtractor()
    result = run("INV-1043", registry=registry, knowledge=knowledge)
    assert result.outcome.decision is Decision.ESCALATE
    assert BlockingReason.SPECIALIST_FAILED in result.outcome.blocking_reasons
    # initial attempt + one retry (MAX_ATTEMPTS) before giving up
    assert result.envelope.visited(INVOICE_EXTRACTOR) == 2


def test_guardrail_veto_escalates():
    result = run("INV-1043", ceiling=GuardrailCeiling(max_tool_calls=0))
    assert result.outcome.decision is Decision.ESCALATE
    assert BlockingReason.SUPERVISOR_GUARDRAIL_VETO in result.outcome.blocking_reasons
