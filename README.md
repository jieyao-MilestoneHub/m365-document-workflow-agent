# AP Invoice Three-Way Match Agent

> **Let AI participate in the finance process, but never let AI break financial controls.**

A Copilot-native, multi-agent, human-in-the-loop agent for **Accounts Payable three-way matching**
(Invoice ↔ Purchase Order ↔ Goods Receipt → variance → exception → GL posting draft). The agent
*reasons, retrieves, and recommends*; **deterministic code makes every arithmetic, tolerance, and
posting decision the LLM can never override.**

Built for the **Agents League AISF 2026** hackathon (Enterprise Agents / Microsoft 365 Copilot
track). Public, clean-room repo; all sample data is synthetic; no secrets.

## The load-bearing idea

In AP, a wrong number is a wrong payment — so intelligence and authority are separated:

- **The LLM / multi-agent layer** narrates, routes, and surfaces cited evidence.
- **Deterministic guardrails** own the verdict: Pydantic invariants (money is `Decimal`, posting
  balances to the cent, tolerance bounds) plus supervisor limits (tool-call budget, per-role visit
  cap, cycle detection).

A variance never silently auto-posts; it **holds** or **escalates** to a human. This is both the
correctness backbone and the *Reliability & Safety* story.

## What runs today (offline, fully tested — no cloud)

The whole pipeline runs and is tested with **zero Azure/M365 credentials** against a synthetic
fixture set.

- **Magentic-style supervisor + 5 specialists.** Each turn the supervisor picks ONE action —
  `delegate` / `peer-review` / `request-input` / `escalate` / `finalize` — over the chain
  `invoice_extractor → po_grn_matcher → variance_assessor → posting_preparer → exception_reviewer`.
  State threads through an append-only **envelope** (handoff history, per-role results, ledger,
  budget).
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
- **86 passing tests** across money/schemas, matcher, validators, guardrails, the decision matrix,
  slot-fill, the supervisor end-to-end, the scenario catalog, and the API.

### Ports & adapters seam

Specialists and the supervisor depend only on narrow **port protocols**
(`backend/app/orchestrator/ports.py`): `ExtractorPort`, `KnowledgePort`, `LedgerPort`,
`ReasoningPort`, `HumanInputPort`, plus injected `Clock`/`IdGen`. Today these are satisfied by
**offline fixture adapters** (`backend/app/adapters/fixtures.py`) over synthetic JSON. Azure
adapters will satisfy the same contracts with **no orchestrator change**.

## What is gated on Azure / M365 provisioning (planned, ports-ready)

Designed and ports-isolated, but not yet wired — they need a tenant, an Azure subscription, and
model access. Marked *planned* throughout the code and the [roadmap](docs/ROADMAP.md).

- **Azure adapters behind the ports:** Document Intelligence (`prebuilt-invoice`) as `ExtractorPort`;
  **Foundry IQ** (`azure-ai-projects`) as `KnowledgePort` — grounded retrieval **with clickable
  citations**; Azure OpenAI as `ReasoningPort` — advisory narration only, never deciding outcomes.
- **M365 Copilot / Teams surface:** an **M365 Agents-SDK** custom-engine-agent proxy exposing the
  backend as a real Copilot/Teams agent, with Adaptive Cards for the slot-fill `HumanInputPort`.
- **Cloud security:** Entra ID SSO; secrets in Key Vault / managed identity.

The intelligence stays on the Microsoft stack to maximize the **Microsoft IQ (Foundry IQ)** pillar.
End-state demo: *"Process invoice INV-1042"* answered inside Teams/Copilot, grounded by Foundry IQ
with clickable citations.

## How to run

### Backend (offline core + API)

```bash
cd backend
pip install -e ".[dev,api]"                  # deterministic core + tests + FastAPI/SSE
uvicorn "app.api.app:create_app" --factory   # serves http://localhost:8000
pytest                                        # 86 tests, no cloud needed
```

Run one scenario end-to-end and print the reasoning trace:

```bash
python -m app.cli INV-1042   # the +6% over-tolerance "money shot" → HOLD
python -m app.cli INV-1043   # clean three-way match → PASS
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

The catalog *proves* behaviour on the exceptions that matter (full table in
[`sample-data/README.md`](sample-data/README.md); shooting script in
[`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)). The headline arc:

| Step | Invoice | What it shows | Outcome |
|------|---------|---------------|---------|
| 1 | **INV-1043** | clean three-way match, balanced posting | **PASS** |
| 2 | **INV-1042** | one line +6% over PO price ($57 impact) — the money shot | **HOLD** · `VARIANCE_OUTSIDE_TOLERANCE` |
| 3 | **INV-1053** | 10 received, 8 already invoiced, bills 10 (line-level depth) | **HOLD** · `OVER_BILLED_VS_RECEIPT` |
| 4 | **INV-1054** | 150 vs PO 95 ($550 impact) — guardrail overrides the LLM | **ESCALATE** · `VARIANCE_HIGH_SEVERITY` |
| 5 | **INV-1057** | unreadable PO ref → agent asks → human supplies PO-5000 | **HOLD → PASS** (slot-fill) |
| 6 | **INV-1056** | invoice already in the posted ledger (duplicate control) | **ESCALATE** · `DUPLICATE_INVOICE` |

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the Mermaid diagram (renders on GitHub) and a
walk-through, and [`docs/ROADMAP.md`](docs/ROADMAP.md) for the workstream × phase plan.

```text
M365 Copilot / Teams  →  M365 Agents-SDK proxy  →  FastAPI (+ SSE)  →  Magentic supervisor
                                                                          ├─ 5 specialists
                                                                          └─ deterministic guardrails
        Foundry IQ · Azure Document Intelligence · Azure OpenAI  (behind ports — gated)
        Next.js console  ←  consumes the SSE reasoning stream
```

## Compliance & safety

- **Synthetic data only** — no real vendors, customers, PII, or secrets.
- **Public, clean-room repo** — no proprietary or internal references in code, comments, or history.
- **No secrets in tree or history** — config via environment variables and `.env.example` only.
- **Controls are authoritative** — the decision matrix and guardrails, not the LLM, decide every
  posting; a variance always holds or escalates. See [`SECURITY.md`](SECURITY.md).
