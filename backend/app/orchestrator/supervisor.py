"""Supervisor loop — fixed orchestration infrastructure.

Repeatedly asks the :class:`SupervisorBrain` for the next action, enforces deterministic
guardrails before every delegation, dispatches to the specialist registry, threads the
envelope functionally, and emits a trace event per step (for the SSE reasoning panel).
Terminates on finalize, escalate, guardrail veto, or the iteration safety cap.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.schemas.enums import BlockingReason, Decision, Severity
from app.schemas.outcome import ExceptionTicket, ValidationOutcome

from .actions import Delegate, Escalate, Finalize, PeerReview, RequestInput
from .brain import SupervisorBrain
from .envelope import HandoffRecord, MultiAgentEnvelope, PeerReviewResponse
from .guardrails import GuardrailCeiling, preflight
from .ports import Clock, HumanInputPort, IdGen, ReasoningPort
from .roles import EXCEPTION_REVIEWER, INVOICE_EXTRACTOR, SUPERVISOR
from .specialists.base import Specialist


@dataclass(frozen=True)
class TraceEvent:
    seq: int
    kind: str  # delegate_result | peer_review | finalize | escalate | veto
    role: str
    detail: str
    ts: str


@dataclass(frozen=True)
class SupervisorRun:
    envelope: MultiAgentEnvelope
    outcome: ValidationOutcome
    events: tuple[TraceEvent, ...]


class Supervisor:
    def __init__(
        self,
        *,
        brain: SupervisorBrain,
        registry: dict[str, Specialist],
        clock: Clock,
        idgen: IdGen,
        ceiling: GuardrailCeiling | None = None,
        reasoning: ReasoningPort | None = None,
        human: HumanInputPort | None = None,
        on_event: Callable[[TraceEvent], None] | None = None,
        max_iterations: int = 50,
    ) -> None:
        self._brain = brain
        self._registry = registry
        self._clock = clock
        self._idgen = idgen
        self._ceiling = ceiling or GuardrailCeiling()
        self._reasoning = reasoning
        self._human = human
        self._on_event = on_event
        self._max_iterations = max_iterations

    def run(self, envelope: MultiAgentEnvelope) -> SupervisorRun:
        events: list[TraceEvent] = []

        def emit(kind: str, role: str, detail: str) -> None:
            event = TraceEvent(len(events) + 1, kind, role, detail, self._clock.now_iso())
            events.append(event)
            if self._on_event is not None:
                self._on_event(event)

        for _ in range(self._max_iterations):
            action = self._brain.next_action(envelope)

            if isinstance(action, Finalize):
                outcome = envelope.payload_for(EXCEPTION_REVIEWER) or self._engine_outcome(
                    envelope, BlockingReason.MISSING_THREE_WAY_MATCH_UPSTREAM, "no reviewer outcome"
                )
                envelope = self._handoff(envelope, SUPERVISOR, "FINALIZE", outcome.decision.value, 0)
                emit("finalize", SUPERVISOR, outcome.decision.value)
                return SupervisorRun(envelope, outcome, tuple(events))

            if isinstance(action, Escalate):
                outcome = self._engine_outcome(
                    envelope, BlockingReason.SPECIALIST_FAILED, action.summary
                )
                envelope = self._handoff(envelope, SUPERVISOR, action.reason_code, action.summary, 0)
                emit("escalate", SUPERVISOR, action.summary)
                return SupervisorRun(envelope, outcome, tuple(events))

            if isinstance(action, RequestInput):
                answer = (
                    self._human.answer(
                        field=action.field, prompt=action.prompt, candidates=list(action.candidates)
                    )
                    if self._human is not None
                    else None
                )
                if answer is not None:
                    envelope = envelope.with_field_correction(
                        INVOICE_EXTRACTOR, action.field, answer
                    )
                    detail = f"{action.field} = {answer}"
                else:
                    envelope = envelope.with_requested_input(action.field)
                    detail = f"{action.field} unanswered"
                envelope = self._handoff(envelope, INVOICE_EXTRACTOR, "REQUEST_INPUT", detail, 0)
                emit("request_input", INVOICE_EXTRACTOR, detail)
                continue

            if isinstance(action, PeerReview):
                text = self._peer_review_text(action.subject_role)
                envelope = envelope.with_peer_review(
                    PeerReviewResponse(action.reviewer, action.subject_role, "accept", text)
                )
                envelope = self._handoff(envelope, action.reviewer, "PEER_REVIEW", action.claim, 0)
                emit("peer_review", action.reviewer, text)
                continue

            if isinstance(action, Delegate):
                verdict = preflight(action.role, envelope.budget_snapshot(), self._ceiling)
                if not verdict.ok:
                    outcome = self._engine_outcome(
                        envelope, BlockingReason.SUPERVISOR_GUARDRAIL_VETO, verdict.detail
                    )
                    envelope = self._handoff(
                        envelope, action.role, verdict.code or "VETO", verdict.detail, 0
                    )
                    emit("veto", action.role, f"{verdict.code}: {verdict.detail}")
                    return SupervisorRun(envelope, outcome, tuple(events))

                attempt = envelope.visited(action.role)
                result = self._registry[action.role].run(envelope)
                envelope = envelope.with_result(result)
                envelope = self._handoff(envelope, action.role, "DELEGATE", action.reason, attempt)
                emit("delegate_result", action.role, result.summary or result.error or "ok")
                continue

        outcome = self._engine_outcome(
            envelope, BlockingReason.SUPERVISOR_GUARDRAIL_VETO, "max iterations exceeded"
        )
        return SupervisorRun(envelope, outcome, tuple(events))

    # --- helpers --------------------------------------------------------------
    def _handoff(
        self, envelope: MultiAgentEnvelope, to_role: str, reason_code: str, detail: str, attempt: int
    ) -> MultiAgentEnvelope:
        return envelope.with_handoff(HandoffRecord(
            from_role=SUPERVISOR, to_role=to_role, reason_code=reason_code,
            detail=detail, attempt=attempt, event_id=self._idgen.next_id(), ts=self._clock.now_iso(),
        ))

    def _peer_review_text(self, subject_role: str) -> str:
        if self._reasoning is not None:
            return self._reasoning.narrate(role="peer_review", context={"subject": subject_role})
        return f"Peer review of {subject_role}: accept - grading consistent with the deltas."

    def _engine_outcome(
        self, envelope: MultiAgentEnvelope, reason: BlockingReason, detail: str
    ) -> ValidationOutcome:
        invoice = envelope.payload_for(INVOICE_EXTRACTOR)
        inv_no = invoice.invoice_number if invoice else envelope.invoice_ref
        ticket = ExceptionTicket(
            ticket_id=f"{inv_no}:{reason.value}", exception_type=reason,
            severity=Severity.HIGH, suggested_resolution="Human review required.",
            evidence={"detail": detail},
        )
        return ValidationOutcome(
            invoice_number=inv_no, decision=Decision.ESCALATE, confidence=0.4,
            blocking_reasons=[reason], summary=f"Escalated - {detail}",
            escalation_target="ap_manager", exception_tickets=[ticket],
        )
