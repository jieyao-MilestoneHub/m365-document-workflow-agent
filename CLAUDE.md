# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A hackathon entry for **Microsoft Agents League AISF 2026** (Enterprise Agents / M365
Copilot track). ONE feature, built deep: an **agentic AP Invoice Three-Way Match** agent
(Invoice ↔ PO ↔ GRN → variance → exception → GL posting draft) surfaced in Microsoft 365
Copilot, grounded by **Foundry IQ**.

The full design, build sequence, and rationale live in the approved plan:
`~/.claude/plans/rule-workflow-agent-convilyn-enterprise-bubbly-taco.md`. Read it first.

## Hard constraints (read before writing code)

- **Clean-room.** Logic is reimplemented from the private `../convilyn` project by *shape
  only*. NEVER copy convilyn source, and never reference convilyn internals (cluster names,
  spec internals, incident IDs) in code, comments, commits, or history.
- **Public repo.** `origin` is a public GitHub repo. Nothing secret/PII/proprietary may enter
  the working tree OR git history — env vars + `.env.example` only. Audit full history before push.
- **Compliance** is codified in `.claude/rules/hackathon.md` (submission gate, IQ requirement,
  confidentiality). `.claude/rules/{security,coding-style}.md` cover secrets and style.
- NOTE: `.claude/rules/git-workflow.md` and the `verify-fix` skill are inherited from convilyn
  and do NOT apply here — ignore their convilyn-specific procedures.

## Commands

Backend lives in `backend/` (Python ≥3.11, packaged via `pyproject.toml`).

```bash
cd backend
pip install -e ".[dev]"            # deterministic core + test deps (no cloud needed)
pip install -e ".[dev,azure,agent,api]"   # full runtime (Azure SDKs, Agent Framework, FastAPI)

pytest                             # run all tests
pytest tests/test_validators.py    # one file
pytest tests/test_validators.py::test_posting_balance   # one test
ruff check .                       # lint (line-length 100, py311)
```

The **deterministic core** (`app/schemas`, `app/orchestrator/validators.py`,
`app/orchestrator/guardrails.py`) and its tests run with NO Azure/M365 credentials — keep it
that way so logic is testable offline. Cloud calls are isolated behind `app/iq/` and `app/azure/`.

## Architecture (big picture)

Two deployables + an M365 agent package (monorepo):

- **`backend/`** — FastAPI + **Microsoft Agent Framework** (`agent-framework`). A **Magentic
  supervisor** dynamically routes to 5 specialists (`invoice_extractor` → `po_grn_matcher` →
  `variance_assessor` → `posting_preparer` → `exception_reviewer`). Each turn the supervisor
  emits ONE action: delegate / peer-review / escalate / finalize. State flows through a shared
  envelope (append-only handoff history, per-role results, exception ledger, budget).
- **`m365-agent/`** — M365 Agents SDK custom-engine-agent proxy that exposes the backend as a
  real Copilot/Teams agent (the hard "M365 Copilot integration" requirement).
- **`frontend/`** — Next.js console (approver inbox, three-way canvas, variance evidence, GL
  preview, audit trail, vendor/policy config, and a live SSE **agent reasoning trace** with
  clickable Foundry IQ citations).

### The load-bearing design principle

**Deterministic guardrails are authoritative over the LLM.** Pydantic invariants (invoice
arithmetic, posting balance to the cent, tolerance bounds) and the supervisor guardrails
(budget / cycle / per-role visit caps) are pure code the LLM can never override. This is both
the correctness backbone and the hackathon's "Reliability & Safety" story — a variance never
auto-posts; it holds/escalates to a human.

### Schema conventions (`app/schemas/`)

- **Money is `Decimal`, never `float`** — use `money.py` (`to_money`, `money_close`). Floats
  break the balance/arithmetic invariants.
- **Closed enums** (`enums.py`: `LineStatus`, `MatchStatus`, `Severity`, `Decision`,
  `BlockingReason`) are validation guardrails — specialists must emit exact values; Pydantic
  rejects anything else. `BlockingReason` values double as exception-ticket types;
  `ESCALATE_REASONS` distinguishes escalate-vs-hold.

### Core workflow rules (encoded in the matcher/reviewer)

- Tolerance: `within = abs(qty_delta) ≤ 0.5 AND abs(price_delta) ≤ max(0.5, po_unit_price×0.02)`.
- Posting: AP credit (acct 2100) = invoice total; per-line expense debits (gl_map → fallback
  5000); tax debit (1360). Invariant: Σdebit == Σcredit.
- Decision: missing upstream/quality-fail → escalate; high severity → escalate; missing PO/GRN
  → hold; medium out-of-tolerance → hold; unbalanced → escalate; else pass.

## Microsoft stack

Foundry IQ (`azure-ai-projects`) for grounded retrieval + citations; Azure AI Document
Intelligence `prebuilt-invoice` for extraction; Azure OpenAI via Azure AI Foundry as the
reasoning LLM. Keep all intelligence on the Microsoft stack (maximizes IQ scoring).

## Verification

Two synthetic invoices are the canonical end-to-end check: **INV-1043** (clean) → `pass` with a
balanced posting; **INV-1042** (one line +6% over PO price) → `hold (VARIANCE_OUTSIDE_TOLERANCE)`
with the offending line and a Foundry IQ citation. All `sample-data/` must stay synthetic.
