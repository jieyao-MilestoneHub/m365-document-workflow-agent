"""Deterministic supervisor guardrails: tool-call budget, per-role visit cap, cycle detection.

Run as a pre-flight before every delegation. A veto routes the run to human review — this
prevents runaway loops and bounds cost regardless of what the supervisor LLM decides.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GuardrailCeiling:
    max_tool_calls: int = 25
    max_role_visits: int = 3
    cycle_threshold: int = 3


@dataclass(frozen=True)
class GuardrailVerdict:
    ok: bool
    code: str | None = None
    detail: str = ""

    @classmethod
    def allow(cls) -> "GuardrailVerdict":
        return cls(ok=True)

    @classmethod
    def veto(cls, code: str, detail: str) -> "GuardrailVerdict":
        return cls(ok=False, code=code, detail=detail)


@dataclass(frozen=True)
class BudgetSnapshot:
    """Cumulative counters read at pre-flight time."""

    tool_calls_used: int = 0
    role_visits: dict[str, int] = field(default_factory=dict)
    #: most-recent-last list of (from_role, to_role) handoff pairs
    recent_handoffs: list[tuple[str, str]] = field(default_factory=list)


def check_tool_calls(snapshot: BudgetSnapshot, ceiling: GuardrailCeiling) -> GuardrailVerdict:
    if snapshot.tool_calls_used >= ceiling.max_tool_calls:
        return GuardrailVerdict.veto(
            "TOOL_CALL_BUDGET_EXCEEDED",
            f"{snapshot.tool_calls_used} ≥ {ceiling.max_tool_calls}",
        )
    return GuardrailVerdict.allow()


def check_role_visit(
    role: str, snapshot: BudgetSnapshot, ceiling: GuardrailCeiling
) -> GuardrailVerdict:
    visits = snapshot.role_visits.get(role, 0)
    if visits >= ceiling.max_role_visits:
        return GuardrailVerdict.veto(
            "ROLE_VISIT_CAP_EXCEEDED",
            f"role {role!r} visited {visits} ≥ {ceiling.max_role_visits}",
        )
    return GuardrailVerdict.allow()


def check_cycle(snapshot: BudgetSnapshot, ceiling: GuardrailCeiling) -> GuardrailVerdict:
    """Veto when the last ``cycle_threshold`` handoffs are the identical (from, to) pair."""
    threshold = ceiling.cycle_threshold
    recent = snapshot.recent_handoffs[-threshold:]
    if len(recent) >= threshold and len(set(recent)) == 1:
        return GuardrailVerdict.veto("CYCLE_DETECTED", f"repeated handoff {recent[0]} ×{threshold}")
    return GuardrailVerdict.allow()


def preflight(
    role: str, snapshot: BudgetSnapshot, ceiling: GuardrailCeiling
) -> GuardrailVerdict:
    """Run all pre-flight checks before delegating to ``role``; first veto wins."""
    for check in (
        check_tool_calls(snapshot, ceiling),
        check_role_visit(role, snapshot, ceiling),
        check_cycle(snapshot, ceiling),
    ):
        if not check.ok:
            return check
    return GuardrailVerdict.allow()
