"""Wire the offline pipeline together and run one invoice.

Shared by the CLI and the tests (DRY). Swapping the fixture adapters for Azure adapters here
is the only change needed to go from offline to cloud — the orchestrator stays identical.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.adapters.fixtures import (
    FixedClock,
    FixtureExtractor,
    FixtureKnowledge,
    FixtureLedger,
    ScriptedReasoner,
    SeqIdGen,
)
from app.orchestrator.brain import ScriptedSupervisor
from app.orchestrator.envelope import MultiAgentEnvelope
from app.orchestrator.guardrails import GuardrailCeiling
from app.orchestrator.roles import (
    EXCEPTION_REVIEWER,
    INVOICE_EXTRACTOR,
    PO_GRN_MATCHER,
    POSTING_PREPARER,
    VARIANCE_ASSESSOR,
)
from app.orchestrator.specialists.exception_reviewer import ExceptionReviewer
from app.orchestrator.specialists.invoice_extractor import InvoiceExtractor
from app.orchestrator.specialists.po_grn_matcher import PoGrnMatcher
from app.orchestrator.specialists.posting_preparer import PostingPreparer
from app.orchestrator.specialists.variance_assessor import VarianceAssessor
from app.orchestrator.supervisor import Supervisor, SupervisorRun, TraceEvent

#: repo-root/sample-data
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "sample-data"


def default_registry(base_dir: str | Path) -> tuple[dict, FixtureKnowledge]:
    knowledge = FixtureKnowledge(base_dir)
    extractor = FixtureExtractor(base_dir)
    ledger = FixtureLedger(base_dir)
    reasoning = ScriptedReasoner()
    registry = {
        INVOICE_EXTRACTOR: InvoiceExtractor(extractor),
        PO_GRN_MATCHER: PoGrnMatcher(knowledge),
        VARIANCE_ASSESSOR: VarianceAssessor(),
        POSTING_PREPARER: PostingPreparer(),
        EXCEPTION_REVIEWER: ExceptionReviewer(reasoning, ledger),
    }
    return registry, knowledge


def run(
    invoice_ref: str,
    *,
    base_dir: str | Path = DEFAULT_DATA_DIR,
    on_event: Callable[[TraceEvent], None] | None = None,
    ceiling: GuardrailCeiling | None = None,
    registry: dict | None = None,
    knowledge: FixtureKnowledge | None = None,
) -> SupervisorRun:
    if registry is None or knowledge is None:
        registry, knowledge = default_registry(base_dir)
    supervisor = Supervisor(
        brain=ScriptedSupervisor(),
        registry=registry,
        clock=FixedClock(),
        idgen=SeqIdGen(),
        reasoning=ScriptedReasoner(),
        on_event=on_event,
        ceiling=ceiling,
    )
    envelope = MultiAgentEnvelope(invoice_ref=invoice_ref, policy=knowledge.get_policy())
    return supervisor.run(envelope)
