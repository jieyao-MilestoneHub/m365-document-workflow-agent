"""Offline CLI for the Retail Supplier Deduction Control Agent.

    python -m app.cli triage          # triage the retail batch → payment-ready vs needs-action
    python -m app.cli INV-1003        # drill into one invoice (decision, deduction cases, evidence)
    python -m app.cli INV-1001 --data ../sample-data
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal

from app.orchestrator.roles import PO_GRN_MATCHER, PROMOTION_AUDITOR
from app.orchestrator.supervisor import TraceEvent
from app.runner import DEFAULT_DATA_DIR, run

#: the retail deduction-control scenarios that make up the demo batch
RETAIL_BATCH = ["INV-1001", "INV-1002", "INV-1003", "INV-1004", "INV-1005", "INV-1006"]


def _money(value: Decimal | None) -> str:
    return f"${value:,.2f}" if value is not None else "—"


def _print_event(event: TraceEvent) -> None:
    print(f"  [{event.seq:02d}] {event.kind:<16} {event.role:<18} {event.detail}")


def _needs_action_label(outcome) -> str:
    if outcome.deduction_cases:
        c = outcome.deduction_cases[0]
        kind = c.deduction_type.value.replace("_", " ").lower()
        return f"{_money(c.amount)} {kind} -> {c.route_to}"
    reason = outcome.blocking_reasons[0].value.replace("_", " ").lower() if outcome.blocking_reasons else "review"
    return f"{reason} -> {outcome.escalation_target or 'review'}"


def _triage(base_dir: str) -> int:
    print(f"\n>> Triage: reviewing {len(RETAIL_BATCH)} retail supplier invoices\n")
    ready: list[tuple[str, str]] = []
    action: list[tuple[str, str]] = []
    for inv in RETAIL_BATCH:
        outcome = run(inv, base_dir=base_dir).outcome
        if outcome.decision.value == "pass":
            ready.append((inv, f"clean — payable {_money(outcome.payable_amount)}"))
        else:
            action.append((inv, _needs_action_label(outcome)))

    print("Payment-ready:")
    for inv, label in ready:
        print(f"  - {inv}  {label}")
    print("\nNeeds action:")
    for inv, label in action:
        print(f"  - {inv}  {label}")
    print()
    return 0


def _drill(invoice_ref: str, base_dir: str) -> int:
    print(f"\n>> Processing {invoice_ref}\n")
    result = run(invoice_ref, base_dir=base_dir, on_event=_print_event)
    outcome = result.outcome

    print(f"\n== Decision: {outcome.decision.value.upper()}  (confidence {outcome.confidence})")
    if outcome.blocking_reasons:
        print(f"  reasons: {', '.join(r.value for r in outcome.blocking_reasons)}")
    print(f"  summary: {outcome.summary}")
    if outcome.held_amount is not None and outcome.held_amount > 0:
        print(f"  Pay now: {_money(outcome.payable_amount)}   Hold: {_money(outcome.held_amount)}")

    for case in outcome.deduction_cases:
        print(
            f"\n  Deduction case {case.deduction_case_id}  "
            f"({case.deduction_type.value}, {_money(case.amount)}, {case.status}) "
            f"-> {case.route_to}"
        )
        print(f"    evidence: {', '.join(case.evidence_refs)}")
        print(f"    explanation: {case.supplier_explanation}")

    citations = list(_payload_citations(result, PO_GRN_MATCHER))
    citations += list(_payload_citations(result, PROMOTION_AUDITOR))
    if citations:
        print("\n  citations:")
        for c in citations:
            print(f"    - {c.document_title}: {c.cited_text}")
    return 0


def _payload_citations(result, role):
    payload = result.envelope.payload_for(role)
    return getattr(payload, "citations", ()) or ()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Retail Supplier Deduction Control Agent (offline runner)"
    )
    parser.add_argument(
        "invoice_ref", help="invoice id (e.g. INV-1003), or 'triage' for the retail batch"
    )
    parser.add_argument("--data", default=str(DEFAULT_DATA_DIR), help="sample-data directory")
    args = parser.parse_args(argv)

    if args.invoice_ref.lower() == "triage":
        return _triage(args.data)
    return _drill(args.invoice_ref, args.data)


if __name__ == "__main__":
    sys.exit(main())
