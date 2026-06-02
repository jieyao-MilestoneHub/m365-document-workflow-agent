# Retail Supplier Deduction Control Agent

> **A deterministic-control agent that prevents retail margin leakage and supplier deduction
> disputes before payment.**

A Copilot-native, multi-agent, human-in-the-loop agent for **retail accounts payable**. It does a
full three-way match (Invoice ↔ Purchase Order ↔ Goods Receipt), but its real job is the part a
textbook three-way match misses: **promotion allowances that were never deducted (margin
leakage), short-receipt deductions, and unit-of-measure false mismatches** — surfaced as
*auditable, disputable, supplier-facing deduction cases* before money leaves.

The agent *reasons, retrieves, and recommends*; **deterministic code makes every arithmetic,
tolerance, allowance, and posting decision the LLM can never override.**

Built for the **Agents League AISF 2026** hackathon (Enterprise Agents / Microsoft 365 Copilot
track). Public, clean-room repo; all sample data is synthetic; no secrets.

## The money shot

> **Standard three-way match would pass this invoice. Our retail promotion control catches the
> missing allowance before payment.**

`INV-1003` matches its PO and GRN exactly on quantity and price — every traditional AP system
passes it. But promotion **PROMO-MAY-BEV** grants a **$3 / case** allowance on 8,400 cases of
orange juice, and the invoice carries **no allowance line**. The deterministic control layer
computes:

```
8,400 cases × $3.00 allowance = $25,200.00 expected
applied on invoice              =      $0.00
margin leakage                  = $25,200.00   → HOLD, route: Category Manager / Commercial Finance
```

This is not "the ERP can't do this" — three-way match is *working as designed*. It's that the
commercial condition (the promotion agreement) lives outside the PO/GRN/invoice triad, so the
control needs to *reach into the agreement* and reconcile it. That's the gap this agent closes.

## The load-bearing idea

In AP, a wrong number is a wrong payment — so intelligence and authority are separated:

- **The LLM / multi-agent layer** narrates, routes, and surfaces cited evidence.
- **Deterministic guardrails** own the verdict: Pydantic invariants (money is `Decimal`, posting
  balances to the cent, tolerance bounds, **allowance reconciliation**) plus supervisor limits
  (tool-call budget, per-role visit cap, cycle detection).

A leakage or deduction never silently auto-posts; it **holds** or **escalates** to the right
human, with a **deduction case** (disputed amount, evidence refs, a supplier-facing explanation,
and a pay-now / hold split). This is both the correctness backbone and the *Reliability & Safety*
story.

## What runs today (offline, fully tested — no cloud)

The whole pipeline runs and is tested with **zero Azure/M365 credentials** against a synthetic
fixture set.

- **Magentic-style supervisor + 6 specialists.** Each turn the supervisor picks ONE action —
  `delegate` / `peer-review` / `request-input` / `escalate` / `finalize` — over the chain
  `invoice_extractor → po_grn_matcher → promotion_auditor → variance_assessor → posting_preparer →
  exception_reviewer`. State threads through an append-only **envelope** (handoff history,
  per-role results, ledger, budget).
- **Retail deduction control (the differentiator).**
  - **Promotion allowance / margin leakage** — reconciles each invoice against its trade-promotion
    agreements; expected-minus-applied allowance becomes a margin-leakage deduction case.
  - **Short-receipt partial deduction** — bills only what the GRN accepted; splits the invoice
    into a **pay-now** amount and a **held / disputed** amount instead of blocking the whole thing.
  - **UOM false-mismatch normalization** — a present pack-size conversion factor resolves cleanly
    to PASS (no false hold); a *missing* factor escalates to master data.
  - **Deduction cases** — disputable findings become a `DeductionCase` with `evidence_refs`, a
    generated **supplier-facing explanation**, and a routing target.
- **Authoritative guardrails.** A pre-flight runs before every delegation (tool-call budget 25,
  per-role visit cap 3, cycle detection); a veto routes to a human. The `pass / hold / escalate`
  matrix is pure code, not the model.
- **Exception depth.** Line-level over-billing, currency mismatch, duplicate-invoice control, tax
  discrepancy, vendor-SKU → internal-SKU aliasing, vendor hold-list, high-severity escalation.
- **Human-in-the-loop slot-fill.** On a missing required field (e.g. an unreadable PO reference)
  the agent pauses, asks, applies the answer, and resumes.
- **FastAPI + SSE.** Scenarios, jobs, a per-step **reasoning-trace** stream, and a human-decision
  endpoint over the offline runner (`backend/app/api/`).
- **Next.js console scaffold** with a zod-validated API client and a hardened security baseline
  (CSP + security headers) (`frontend/`).
- **Full test suite** across money/schemas, matcher, validators, guardrails, the decision matrix,
  promotion/leakage math, deduction-case assembly, slot-fill, the supervisor end-to-end, the
  scenario catalog, and the API.

### Ports & adapters seam

Specialists and the supervisor depend only on narrow **port protocols**
(`backend/app/orchestrator/ports.py`): `ExtractorPort`, `KnowledgePort` (POs, GRNs, **promotion
agreements**), `LedgerPort`, `ReasoningPort`, `HumanInputPort`, plus injected `Clock`/`IdGen`.
Today these are satisfied by **offline fixture adapters** (`backend/app/adapters/fixtures.py`)
over synthetic JSON. Azure adapters will satisfy the same contracts with **no orchestrator
change**.

## What is gated on Azure / M365 provisioning (planned, ports-ready)

Designed and ports-isolated, but not yet wired — they need a tenant, an Azure subscription, and
model access. Marked *planned* throughout the code and the [roadmap](docs/ROADMAP.md).

- **Azure adapters behind the ports:** Document Intelligence (`prebuilt-invoice`) as `ExtractorPort`;
  **Foundry IQ** (`azure-ai-projects`) as `KnowledgePort` — grounded retrieval of POs, GRNs, **and
  promotion agreements with clickable citations**; Azure OpenAI as `ReasoningPort` — advisory
  narration and supplier-facing explanations, never deciding outcomes.
- **M365 Copilot / Teams surface:** an **M365 Agents-SDK** custom-engine-agent proxy exposing the
  backend as a real Copilot/Teams agent, with Adaptive Cards for the slot-fill `HumanInputPort`.
- **Cloud security:** Entra ID SSO; secrets in Key Vault / managed identity.

The intelligence stays on the Microsoft stack to maximize the **Microsoft IQ (Foundry IQ)** pillar.
End-state demo: *"Review the May retail supplier invoices"* answered inside Teams/Copilot,
grounded by Foundry IQ with clickable citations to the promotion agreement.

## How to run

### Backend (offline core + API)

```bash
cd backend
pip install -e ".[dev,api]"                  # deterministic core + tests + FastAPI/SSE
uvicorn "app.api.app:create_app" --factory   # serves http://localhost:8000
pytest                                        # full suite, no cloud needed
```

Run the interactive investigation demo, or a single scenario:

```bash
python -m app.cli triage          # triage the retail batch → payment-ready vs needs-action
python -m app.cli INV-1003        # the margin-leakage money shot → HOLD, $25,200 deduction case
python -m app.cli INV-1001        # clean three-way match → PASS
```

> Cloud extras (`azure`, `agent`) exist in `pyproject.toml` but aren't needed offline. Install once
> provisioning lands: `pip install -e ".[dev,azure,agent,api]"`.

### Frontend (console)

```bash
cd frontend
npm install
npm run dev                  # http://localhost:3000, talks to the API at :8000
```

Set the API endpoint via `NEXT_PUBLIC_API_BASE_URL` (see `frontend/.env.example`). Only public,
non-sensitive config ships to the browser.

## The demo / scenario arc

The demo is one **interactive investigation workflow**, not a parade of static scenarios: the
agent triages a batch of retail invoices, surfaces the ones that would overpay or leak margin,
and answers the reviewer's follow-up "why?" / "show me the evidence." Full catalog in
[`sample-data/README.md`](sample-data/README.md); shooting script in
[`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md). The headline set:

| Invoice | What it shows | Outcome |
|---------|---------------|---------|
| **INV-1001** | clean beverage three-way match, balanced posting | **PASS** |
| **INV-1003** | three-way match is clean, but a **$3/case promotion allowance is missing** — the money shot | **HOLD** · `PROMOTION_ALLOWANCE_MISSING` · **$25,200** leakage |
| **INV-1002** | short receipt: billed 500 cases, GRN accepted 420 — pay-now / hold split | **HOLD** · `OVER_BILLED_VS_RECEIPT` · **$480** held |
| **INV-1004** | apparent UOM mismatch (cases vs each) cleared by pack-size normalization | **PASS** (false hold avoided) |
| **INV-1005** | UOM mismatch with **no** conversion factor → defer to master data | **ESCALATE** · `UOM_MISMATCH` |
| **INV-1006** | promotion allowance **correctly applied** — proves no false positive | **PASS** |

## Architecture

![Retail Supplier Deduction Control Agent — architecture](docs/architecture.svg)

See [`docs/architecture.md`](docs/architecture.md) for the diagram walk-through,
[`docs/ROADMAP.md`](docs/ROADMAP.md) for the workstream × phase plan, and
[`docs/SUBMISSION.md`](docs/SUBMISSION.md) for the hackathon submission checklist.

## Compliance & safety

- **Synthetic data only** — no real vendors, customers, PII, or secrets.
- **Public, clean-room repo** — no proprietary or internal references in code, comments, or history.
- **No secrets in tree or history** — config via environment variables and `.env.example` only.
- **Controls are authoritative** — the decision matrix and guardrails, not the LLM, decide every
  posting, allowance, and deduction; a leakage or deduction always holds or escalates. See
  [`SECURITY.md`](SECURITY.md).
</content>
