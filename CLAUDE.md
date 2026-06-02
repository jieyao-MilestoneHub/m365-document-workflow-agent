# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A hackathon entry for **Microsoft Agents League AISF 2026** (Enterprise Agents / M365
Copilot track). ONE feature, built deep: an agentic **Retail Supplier Deduction Control
Agent** surfaced in Microsoft 365 Copilot, grounded by **Foundry IQ**.

It runs a full three-way match (Invoice ↔ PO ↔ GRN → variance → exception → GL posting draft),
but its differentiating job is the retail margin-protection layer a textbook three-way match
misses: **promotion-allowance / margin-leakage detection** (deep), **short-receipt partial
deductions** and **deduction cases with supplier-facing explanations** (medium), and **UOM
false-mismatch normalization** (light). The money shot: an invoice that *passes* three-way
match but is missing a promotion allowance the retailer is owed → HOLD before payment, routed
to the Category Manager, with a Foundry IQ citation to the promotion agreement. Frame it as
*"standard three-way match would pass this; our retail promotion control catches the missing
allowance before payment"* — never as "the ERP can't do this."

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
  supervisor** dynamically routes to 6 specialists (`invoice_extractor` → `po_grn_matcher` →
  `promotion_auditor` → `variance_assessor` → `posting_preparer` → `exception_reviewer`). Each
  turn the supervisor emits ONE action: delegate / peer-review / escalate / finalize. State flows
  through a shared envelope (append-only handoff history, per-role results, exception ledger,
  budget). `promotion_auditor` reconciles each invoice against its trade-promotion agreements
  (from the `KnowledgePort`) and emits an `AllowanceAudit` (expected vs applied allowance →
  margin leakage); like every specialist it produces a payload, never a verdict.
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
  Both qty and price are normalized to the PO base UOM first (qty `× uom_factor`, price
  `÷ uom_factor`), so a pack-size difference with a conversion factor matches cleanly; a UOM
  difference with **no** factor is a `uom_mismatch` → escalate.
- Promotion allowance: `expected = Σ(billed qty for the promo SKU) × allowance_per_unit`;
  `applied = Σ invoice.allowances for that promo`; `leakage = max(0, expected − applied)`. Leakage
  above `policy.allowance_tolerance` → `PROMOTION_ALLOWANCE_MISSING` (HOLD, route category manager).
- Posting: AP credit (acct 2100) = invoice total; per-line expense debits (gl_map → fallback
  5000); tax debit (1360). Invariant: Σdebit == Σcredit.
- Deductions: disputable findings (promotion leakage, over-billed/short-receipt) become a
  `DeductionCase` (amount, `evidence_refs`, supplier-facing explanation, route). The outcome
  carries a **pay-now / hold split**: `held = Σ deduction amounts`, `payable = total − held`.
- Decision: missing upstream/quality-fail → escalate; high severity → escalate; missing PO/GRN
  → hold; medium out-of-tolerance → hold; promotion leakage → hold; unbalanced → escalate;
  else pass.

## Microsoft stack

Foundry IQ (`azure-ai-projects`) for grounded retrieval + citations; Azure AI Document
Intelligence `prebuilt-invoice` for extraction; Azure OpenAI via Azure AI Foundry as the
reasoning LLM. Keep all intelligence on the Microsoft stack (maximizes IQ scoring).

## Verification

The canonical end-to-end checks are the retail scenarios (`sample-data/expected_results.json`,
driven by `tests/test_scenarios.py`). The money shot: **INV-1003** matches its PO/GRN exactly yet
`hold (PROMOTION_ALLOWANCE_MISSING)` with **$25,200** margin leakage, a deduction case routed to
the category manager, and a Foundry IQ citation to the promotion agreement. Also canonical:
**INV-1001** (clean) → `pass`; **INV-1002** (short receipt) → `hold (OVER_BILLED_VS_RECEIPT)` with
a pay-now/hold split; **INV-1004** (UOM normalized) → `pass`; **INV-1005** (UOM, no factor) →
`escalate (UOM_MISMATCH)`. Legacy AP invoices (INV-1042 … INV-1060) are retained as regression
coverage but are not part of the demo. All `sample-data/` must stay synthetic.
