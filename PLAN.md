# Worktree plan — WS1 Agent-Core stretch exceptions (`feat/agent-core-stretch`)

**Branch:** `feat/agent-core-stretch`  ·  **Worktree:** `C:/Users/USER/Desktop/Develop/m365-core`
**GitHub issues:** `gh issue list --label ws1-agent-core` (freight/misc-charge; UOM mismatch)

This worktree adds two **stretch** exception types to the Python backend, **strictly additively**.
The 86 existing tests MUST stay green and no Pydantic invariant may be loosened. Read
`docs/ROADMAP.md`, `CLAUDE.md`, and the existing patterns before coding.

## Start-of-session setup

```bash
cd C:/Users/USER/Desktop/Develop/m365-core/backend
python -m venv .venv                      # if `python` missing use /c/Users/USER/bin/python3
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest -q     # confirm green baseline (86)
```

## Patterns to follow (DO NOT deviate)

- `BlockingReason` (`app/schemas/enums.py`) is **append-only**; `ESCALATE_REASONS` is the
  escalate-vs-hold set; `_RESOLUTIONS` (`app/orchestrator/decision.py`) has one line per reason.
- All numbers live in pure functions (`app/orchestrator/matching.py`); the LLM never decides.
- `evaluate_outcome` (`decision.py`) is the authoritative matrix — every new exception surfaces
  there as a `BlockingReason`.
- Scenarios are JSON fixtures under `sample-data/` + parametrized in `tests/test_scenarios.py`.
- New schema fields are **optional with defaults** so existing fixtures/tests are unaffected.

## Task 1 — Freight / misc-charge exception (primary)

1. `app/schemas/enums.py`: add `LineCharge` enum (`good|freight|misc|discount`); add
   `BlockingReason.UNPLANNED_CHARGE` (HOLD — add to `_RESOLUTIONS`, NOT to `ESCALATE_REASONS`).
2. `app/schemas/invoice.py`: add `charge_type: LineCharge = LineCharge.GOOD` to `InvoiceLineItem`.
   The `line_total == quantity*unit_price` invariant still holds for charge lines — keep it.
3. `app/schemas/policy.py`: add `freight_tolerance: Decimal` + `freight_gl_account: str` to the
   GL/policy bundle (defaults).
4. `app/orchestrator/specialists/po_grn_matcher.py`: charge lines (`charge_type != good`) **skip**
   three-way matching — emit a `LineMatch` with a neutral status (`within_tolerance=True`,
   `over_billed=False`) and a note; do not attempt PO/GRN lookup for them.
5. `app/orchestrator/decision.py`: if total freight charges exceed `policy.freight_tolerance`
   → append `UNPLANNED_CHARGE` ticket (HOLD).
6. `app/orchestrator/specialists/posting_preparer.py`: post freight to `freight_gl_account`
   (keep Σdebit==Σcredit).
7. Fixtures + tests: add `sample-data/invoices/INV-1059.json` (a freight line over tolerance) and
   a `tests/test_scenarios.py` row asserting `HOLD / UNPLANNED_CHARGE`; update `sample-data/README.md`.

## Task 2 — UOM mismatch (if time)

1. `InvoiceLineItem`/`POLine`: optional `unit_of_measure: str | None`, `uom_factor: Decimal = 1`.
2. Matcher: normalize invoice qty by `uom_factor` before computing `quantity_delta`; on a UOM that
   can't be reconciled, set `LineStatus.UNIT_VARIANCE` (currently unused) and flag it.
3. `BlockingReason.UOM_MISMATCH` (ESCALATE — silent unit errors are high-$). Add to
   `ESCALATE_REASONS` + `_RESOLUTIONS`. Fixture `INV-1060` + scenario test.

## Definition of done & delivery

DoD: `pytest -q` green (now ~90+ tests); freight scenario holds with `UNPLANNED_CHARGE`; existing
11 scenarios unchanged. Commit each exception as `feat(exceptions): …` then `test: …`, ending
every message with `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
`git push -u origin feat/agent-core-stretch`; `gh pr create --draft --base main --head
feat/agent-core-stretch` referencing the WS1 issues. Do NOT merge.

**Risk note:** Task 1 touches the invoice-line schema — verify the existing arithmetic invariant
still passes for non-charge lines (it must, since `charge_type` defaults to `good`). If any of the
86 baseline tests break, you've loosened something — revert and re-approach.
