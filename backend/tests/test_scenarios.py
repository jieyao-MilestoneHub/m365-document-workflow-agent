"""Scenario catalog — the synthetic corpus that is also the demo script.

Each row runs the full agent over a sample-data invoice and asserts the exact decision and,
for non-pass cases, that the headline blocking reason is present. This is the contract the
Azure adapters must later reproduce.
"""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from app.runner import DEFAULT_DATA_DIR, run
from app.schemas.enums import BlockingReason, Decision

PASS, HOLD, ESCALATE = Decision.PASS, Decision.HOLD, Decision.ESCALATE

SCENARIOS = [
    ("INV-1043", PASS, None),                                       # clean
    ("INV-1050", PASS, None),                                       # partial receipt in tolerance
    ("INV-1051", PASS, None),                                       # vendor-SKU alias resolves
    ("INV-1042", HOLD, BlockingReason.VARIANCE_OUTSIDE_TOLERANCE),  # price +6%
    ("INV-1052", HOLD, BlockingReason.TAX_DISCREPANCY),            # tax off
    ("INV-1053", HOLD, BlockingReason.OVER_BILLED_VS_RECEIPT),     # over-billed vs remaining
    ("INV-1054", ESCALATE, BlockingReason.VARIANCE_HIGH_SEVERITY), # high-severity variance
    ("INV-1055", ESCALATE, BlockingReason.CURRENCY_MISMATCH),      # EUR vs USD
    ("INV-1056", ESCALATE, BlockingReason.DUPLICATE_INVOICE),      # already posted
    ("INV-1057", PASS, None),                                       # slot-fill clears it
    ("INV-1058", HOLD, BlockingReason.VENDOR_ON_HOLD_LIST),        # vendor on hold
    ("INV-1059", HOLD, BlockingReason.UNPLANNED_CHARGE),           # freight charge over tolerance
    ("INV-1060", ESCALATE, BlockingReason.UOM_MISMATCH),           # billed in case vs PO ea, no factor
]


#: just the clean scenarios, flattened out of SCENARIOS so each is its own test case
PASS_SCENARIOS = [inv for inv, decision, _ in SCENARIOS if decision is PASS]


@pytest.mark.parametrize("invoice_id, decision, reason", SCENARIOS)
def test_scenario(invoice_id, decision, reason):
    outcome = run(invoice_id).outcome
    assert outcome.decision is decision
    if reason is not None:
        assert reason in outcome.blocking_reasons


@pytest.mark.parametrize("invoice_id", PASS_SCENARIOS)
def test_pass_scenario_has_no_blocking_reasons(invoice_id):
    # a clean invoice must carry an empty ledger — not merely a PASS verdict
    assert run(invoice_id).outcome.blocking_reasons == []


# --- Retail deduction-control scenarios, driven by the expected_results contract -------------
def _retail_expected() -> dict:
    path = Path(DEFAULT_DATA_DIR) / "expected_results.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


RETAIL_EXPECTED = _retail_expected()


@pytest.mark.parametrize("invoice_id", list(RETAIL_EXPECTED))
def test_retail_scenario(invoice_id):
    exp = RETAIL_EXPECTED[invoice_id]
    outcome = run(invoice_id).outcome

    assert outcome.decision.value == exp["decision"]
    actual_reasons = {r.value for r in outcome.blocking_reasons}
    for reason in exp["blocking_reasons"]:
        assert reason in actual_reasons, f"{invoice_id}: expected blocking reason {reason}"

    assert outcome.payable_amount == Decimal(exp["payable_amount"])
    assert outcome.held_amount == Decimal(exp["held_amount"])

    types = sorted(c.deduction_type.value for c in outcome.deduction_cases)
    assert types == sorted(exp["deduction_case_types"])

    leakage = sum(
        (c.amount for c in outcome.deduction_cases
         if c.deduction_type.value == "PROMOTION_ALLOWANCE_MISSING"),
        Decimal("0"),
    )
    assert leakage == Decimal(exp["margin_leakage"])
