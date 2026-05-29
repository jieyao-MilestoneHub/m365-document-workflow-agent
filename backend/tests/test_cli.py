"""Offline CLI entrypoint tests (no cloud).

The CLI is the human-facing offline runner; these assert it exits cleanly and surfaces the
authoritative decision, blocking reasons, and Foundry IQ citations to stdout.
"""
from __future__ import annotations

from app.cli import main


def test_cli_clean_invoice_reports_pass(sample_data_dir, capsys):
    exit_code = main(["INV-1043", "--data", str(sample_data_dir)])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Decision: PASS" in out


def test_cli_variance_invoice_reports_hold_with_reason_and_citation(sample_data_dir, capsys):
    exit_code = main(["INV-1042", "--data", str(sample_data_dir)])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Decision: HOLD" in out
    assert "VARIANCE_OUTSIDE_TOLERANCE" in out
    # the matcher attaches PO/GRN citations, which the CLI prints under "citations:"
    assert "citations:" in out
