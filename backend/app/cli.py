"""Offline CLI: run the three-way-match agent over a sample invoice and print the trace.

    python -m app.cli INV-1042
    python -m app.cli INV-1043 --data ../sample-data
"""
from __future__ import annotations

import argparse
import sys

from app.orchestrator.supervisor import TraceEvent
from app.runner import DEFAULT_DATA_DIR, run


def _print_event(event: TraceEvent) -> None:
    print(f"  [{event.seq:02d}] {event.kind:<16} {event.role:<18} {event.detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AP three-way-match agent (offline runner)")
    parser.add_argument("invoice_ref", help="invoice id, e.g. INV-1042")
    parser.add_argument("--data", default=str(DEFAULT_DATA_DIR), help="sample-data directory")
    args = parser.parse_args(argv)

    print(f"\n>> Processing {args.invoice_ref}\n")
    result = run(args.invoice_ref, base_dir=args.data, on_event=_print_event)
    outcome = result.outcome

    print(f"\n== Decision: {outcome.decision.value.upper()}  (confidence {outcome.confidence})")
    if outcome.blocking_reasons:
        print(f"  reasons: {', '.join(r.value for r in outcome.blocking_reasons)}")
    print(f"  summary: {outcome.summary}")

    match = result.envelope.payload_for("po_grn_matcher")
    if match and match.citations:
        print("  citations:")
        for c in match.citations:
            print(f"    - {c.document_title}: {c.cited_text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
