from app.orchestrator.guardrails import (
    BudgetSnapshot,
    GuardrailCeiling,
    check_cycle,
    check_role_visit,
    check_tool_calls,
    preflight,
)

CEILING = GuardrailCeiling(max_tool_calls=5, max_role_visits=2, cycle_threshold=3)


def test_tool_call_budget_allows_under_cap():
    verdict = check_tool_calls(BudgetSnapshot(tool_calls_used=4), CEILING)
    assert verdict.ok is True
    assert verdict.code is None


def test_tool_call_budget_vetoes_at_cap():
    verdict = check_tool_calls(BudgetSnapshot(tool_calls_used=5), CEILING)
    assert verdict.ok is False
    assert verdict.code == "TOOL_CALL_BUDGET_EXCEEDED"


def test_role_visit_cap_vetoes():
    snap = BudgetSnapshot(role_visits={"matcher": 2})
    verdict = check_role_visit("matcher", snap, CEILING)
    assert verdict.ok is False
    assert verdict.code == "ROLE_VISIT_CAP_EXCEEDED"


def test_cycle_detected_on_repeated_pair():
    snap = BudgetSnapshot(recent_handoffs=[("sup", "matcher")] * 3)
    assert check_cycle(snap, CEILING).code == "CYCLE_DETECTED"


def test_cycle_not_detected_on_varied_handoffs():
    snap = BudgetSnapshot(recent_handoffs=[("sup", "matcher"), ("sup", "variance"), ("sup", "matcher")])
    assert check_cycle(snap, CEILING).ok is True


def test_preflight_first_veto_wins():
    snap = BudgetSnapshot(tool_calls_used=5, role_visits={"matcher": 2})
    assert preflight("matcher", snap, CEILING).code == "TOOL_CALL_BUDGET_EXCEEDED"
