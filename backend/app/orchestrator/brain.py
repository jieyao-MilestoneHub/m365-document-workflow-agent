"""Supervisor brains — the swappable decision policy behind the supervisor loop.

The loop (``supervisor.py``) is fixed infrastructure; the *decision* of what to do next is a
:class:`SupervisorBrain`. Offline/tests use :class:`ScriptedSupervisor` (deterministic but
state-reactive: it retries on failure and triggers peer review). In prod, an Agent-Framework
Magentic manager implements the same protocol — same loop, LLM-driven routing.
"""
from __future__ import annotations

from typing import Protocol

from app.schemas.enums import Severity

from .actions import Delegate, Escalate, Finalize, PeerReview, RequestInput, SupervisorAction
from .envelope import MultiAgentEnvelope
from .roles import (
    INVOICE_EXTRACTOR,
    PIPELINE_ORDER,
    PO_GRN_MATCHER,
    POSTING_PREPARER,
    VARIANCE_ASSESSOR,
)

MAX_ATTEMPTS = 2  # initial try + one self-correction retry

#: invoice fields a human can fill in to unblock a run (vs a hard quality failure)
SLOT_FILLABLE = frozenset({"po_ref", "grn_ref"})


class SupervisorBrain(Protocol):
    def next_action(self, envelope: MultiAgentEnvelope) -> SupervisorAction: ...


class ScriptedSupervisor:
    """Routes along the dependency order, reacting to failures and variance severity."""

    def next_action(self, envelope: MultiAgentEnvelope) -> SupervisorAction:
        for role in PIPELINE_ORDER:
            result = envelope.result_for(role)

            if result is None:
                if role is PO_GRN_MATCHER:
                    ask = self._slot_fill(envelope)
                    if ask is not None:
                        return ask
                if role is POSTING_PREPARER and self._needs_peer_review(envelope):
                    return PeerReview(
                        reviewer=PO_GRN_MATCHER, subject_role=VARIANCE_ASSESSOR,
                        claim="variance severity grading", question="Is the grading sound?",
                    )
                return Delegate(role=role, reason="next in pipeline")

            if not result.ok:
                if envelope.visited(role) < MAX_ATTEMPTS:
                    return Delegate(role=role, reason=f"retry after error: {result.error}")
                return Escalate(reason_code="SPECIALIST_FAILED", summary=f"{role}: {result.error}")

        return Finalize()

    @staticmethod
    def _slot_fill(envelope: MultiAgentEnvelope) -> RequestInput | None:
        """Ask the human for the first slot-fillable missing field not yet requested."""
        invoice = envelope.payload_for(INVOICE_EXTRACTOR)
        if invoice is None:
            return None
        pending = [
            f for f in invoice.missing_fields
            if f in SLOT_FILLABLE and f not in envelope.requested_inputs
        ]
        if not pending:
            return None
        return RequestInput(
            field=pending[0],
            prompt=f"The invoice is missing '{pending[0]}'. Which value applies?",
        )

    @staticmethod
    def _needs_peer_review(envelope: MultiAgentEnvelope) -> bool:
        variance = envelope.payload_for(VARIANCE_ASSESSOR)
        if variance is None or envelope.peer_reviews:
            return False
        return variance.overall_severity in (Severity.MEDIUM, Severity.HIGH)
