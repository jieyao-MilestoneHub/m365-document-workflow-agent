"""Shared multi-agent state envelope.

Clean-room of convilyn's ``MultiAgentEnvelope``: an append-only handoff ledger (the audit
trail), the latest result per specialist role, peer-review responses, and budget counters.
Updates are functional — every ``with_*`` method returns a NEW envelope, never mutating —
so state transitions are easy to reason about and test.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from app.schemas.policy import PolicyBundle

from .guardrails import BudgetSnapshot


@dataclass(frozen=True)
class HandoffRecord:
    """One state transition in the audit trail."""

    from_role: str
    to_role: str
    reason_code: str
    detail: str
    attempt: int
    event_id: str
    ts: str


@dataclass(frozen=True)
class SpecialistResult:
    """A specialist's typed output (or an error). ``payload`` is a schema model instance."""

    role: str
    payload: Any | None = None
    citations: tuple = ()
    error: str | None = None
    summary: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.payload is not None


@dataclass(frozen=True)
class PeerReviewResponse:
    reviewer: str
    subject_role: str
    verdict: str  # "accept" | "reject"
    reasoning: str


@dataclass(frozen=True)
class MultiAgentEnvelope:
    """Immutable run state threaded through the supervisor loop."""

    invoice_ref: str
    policy: PolicyBundle = field(default_factory=PolicyBundle)
    handoff_history: tuple[HandoffRecord, ...] = ()
    results: dict[str, SpecialistResult] = field(default_factory=dict)
    peer_reviews: tuple[PeerReviewResponse, ...] = ()
    tool_calls_used: int = 0
    role_visits: dict[str, int] = field(default_factory=dict)

    # --- reads ----------------------------------------------------------------
    def result_for(self, role: str) -> SpecialistResult | None:
        return self.results.get(role)

    def payload_for(self, role: str) -> Any | None:
        res = self.results.get(role)
        return res.payload if res and res.ok else None

    def visited(self, role: str) -> int:
        return self.role_visits.get(role, 0)

    def budget_snapshot(self) -> BudgetSnapshot:
        recent = [(h.from_role, h.to_role) for h in self.handoff_history]
        return BudgetSnapshot(
            tool_calls_used=self.tool_calls_used,
            role_visits=dict(self.role_visits),
            recent_handoffs=recent,
        )

    # --- functional updates (return new envelopes) ----------------------------
    def with_handoff(self, record: HandoffRecord) -> "MultiAgentEnvelope":
        return replace(self, handoff_history=self.handoff_history + (record,))

    def with_result(self, result: SpecialistResult) -> "MultiAgentEnvelope":
        results = {**self.results, result.role: result}
        visits = {**self.role_visits, result.role: self.visited(result.role) + 1}
        return replace(
            self, results=results, role_visits=visits, tool_calls_used=self.tool_calls_used + 1
        )

    def with_peer_review(self, response: PeerReviewResponse) -> "MultiAgentEnvelope":
        return replace(self, peer_reviews=self.peer_reviews + (response,))
