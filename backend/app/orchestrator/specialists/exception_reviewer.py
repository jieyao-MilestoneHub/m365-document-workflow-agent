"""exception_reviewer — produce the authoritative pass/hold/escalate verdict.

The verdict and blocking reasons come from :func:`evaluate_outcome` (deterministic). An
optional :class:`ReasoningPort` only rewrites the human-readable ``summary`` — it can never
change the decision. This is the guardrail-over-LLM principle made concrete.
"""
from __future__ import annotations

from ..decision import evaluate_outcome
from ..envelope import MultiAgentEnvelope, SpecialistResult
from ..ports import ReasoningPort
from ..roles import (
    EXCEPTION_REVIEWER,
    INVOICE_EXTRACTOR,
    PO_GRN_MATCHER,
    POSTING_PREPARER,
    VARIANCE_ASSESSOR,
)


class ExceptionReviewer:
    role = EXCEPTION_REVIEWER

    def __init__(self, reasoning: ReasoningPort | None = None) -> None:
        self._reasoning = reasoning

    def run(self, envelope: MultiAgentEnvelope) -> SpecialistResult:
        outcome = evaluate_outcome(
            invoice=envelope.payload_for(INVOICE_EXTRACTOR),
            match=envelope.payload_for(PO_GRN_MATCHER),
            variance=envelope.payload_for(VARIANCE_ASSESSOR),
            posting=envelope.payload_for(POSTING_PREPARER),
            policy=envelope.policy,
        )
        if self._reasoning is not None:
            narrated = self._reasoning.narrate(
                role=self.role,
                context={
                    "decision": outcome.decision.value,
                    "blocking_reasons": [r.value for r in outcome.blocking_reasons],
                },
            )
            outcome = outcome.model_copy(update={"summary": narrated})
        return SpecialistResult(role=self.role, payload=outcome, summary=outcome.summary)
