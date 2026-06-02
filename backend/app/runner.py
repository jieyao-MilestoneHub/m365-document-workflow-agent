"""Wire the offline pipeline together and run one invoice.

Shared by the CLI and the tests (DRY). Swapping the fixture adapters for Azure adapters here
is the only change needed to go from offline to cloud — the orchestrator stays identical.
"""
from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from app.adapters.fixtures import (
    FixedClock,
    FixtureExtractor,
    FixtureHumanInput,
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
    PROMOTION_AUDITOR,
    VARIANCE_ASSESSOR,
)
from app.orchestrator.specialists.exception_reviewer import ExceptionReviewer
from app.orchestrator.specialists.invoice_extractor import InvoiceExtractor
from app.orchestrator.specialists.po_grn_matcher import PoGrnMatcher
from app.orchestrator.specialists.posting_preparer import PostingPreparer
from app.orchestrator.specialists.promotion_auditor import PromotionAuditor
from app.orchestrator.specialists.variance_assessor import VarianceAssessor
from app.orchestrator.supervisor import Supervisor, SupervisorRun, TraceEvent

#: Name of the synthetic-data directory shipped alongside the code.
_SAMPLE_DATA_DIRNAME = "sample-data"


def _resolve_sample_data_dir() -> Path:
    """Locate ``sample-data/`` without assuming a fixed folder depth.

    Resolution order, so the package can be relocated within (or vendored out of)
    the repo without breaking data lookup:

    1. the ``AP_SAMPLE_DATA_DIR`` environment variable, if set;
    2. the nearest ``sample-data/`` directory found by walking up from this file;
    3. the historical ``repo-root/sample-data`` layout, as a last-resort fallback.
    """
    override = os.environ.get("AP_SAMPLE_DATA_DIR")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / _SAMPLE_DATA_DIRNAME
        if candidate.is_dir():
            return candidate
    return here.parents[2] / _SAMPLE_DATA_DIRNAME


#: Default synthetic-data directory (resolved robustly; see _resolve_sample_data_dir).
DEFAULT_DATA_DIR = _resolve_sample_data_dir()


def default_registry(base_dir: str | Path) -> tuple[dict, FixtureKnowledge]:
    knowledge = FixtureKnowledge(base_dir)
    extractor = FixtureExtractor(base_dir)
    ledger = FixtureLedger(base_dir)
    reasoning = ScriptedReasoner()
    registry = {
        INVOICE_EXTRACTOR: InvoiceExtractor(extractor),
        PO_GRN_MATCHER: PoGrnMatcher(knowledge),
        PROMOTION_AUDITOR: PromotionAuditor(knowledge),
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
        human=FixtureHumanInput(base_dir),
        on_event=on_event,
        ceiling=ceiling,
    )
    envelope = MultiAgentEnvelope(invoice_ref=invoice_ref, policy=knowledge.get_policy())
    return supervisor.run(envelope)
