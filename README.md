# AP Invoice Three-Way Match Agent

> **Let AI participate in the finance process, but never let AI break financial controls.**

A Copilot-native, multi-agent, evidence-grounded, human-in-the-loop agent for **Accounts
Payable invoice three-way matching** (Invoice ↔ Purchase Order ↔ Goods Receipt → variance →
exception → GL posting draft). The agent *reasons, retrieves, and recommends*; **deterministic
code makes every arithmetic, tolerance, and posting decision the LLM can never override.**

Built for the **Agents League AISF 2026** hackathon (Enterprise Agents / Microsoft 365 Copilot
track). All sample data is synthetic; this is a public, clean-room repository with no secrets.

---

## The load-bearing idea

In AP, a wrong number is a wrong payment. So the intelligence and the authority are deliberately
separated:

- **The LLM / multi-agent layer** narrates, routes, and surfaces evidence with citations.
- **Deterministic guardrails** — Pydantic invariants (money is `Decimal`, posting must balance to
  the cent, tolerance bounds) plus supervisor guardrails (tool-call budget, per-role visit cap,
  cycle detection) — own the verdict.

A variance never silently auto-posts. It **holds** or **escalates** to a human. This is both the
correctness backbone and the hackathon's *Reliability & Safety* story.

---

## What is built today (offline, fully tested — no cloud required)

The entire agentic pipeline runs and is tested with **zero Azure/M365 credentials**, against a
synthetic data fixture set.

- **Magentic-style supervisor + 5 specialists.** A supervisor loop repeatedly chooses ONE action
  per turn from a closed set — `delegate` / `peer-review` / `request-input` / `escalate` /
  `finalize` — and routes over a specialist registry:
  `invoice_extractor → po_grn_matcher → variance_assessor → posting_preparer → exception_reviewer`.
  State flows through an append-only **envelope** (handoff history, per-role results, exception
  ledger, budget).
- **Deterministic guardrails & decision matrix.** A pre-flight runs before every delegation
  (tool-call budget = 25, per-role visit cap = 3, repeated-handoff cycle detection); a veto routes
  the run to a human. The authoritative `pass / hold / escalate` matrix lives in pure code, not in
  the model.
- **Exception depth.** Line-level over-billing vs. receipt, currency mismatch, duplicate-invoice
  control, tax discrepancy, vendor-SKU → internal-SKU alias resolution, vendor hold-list, and
  high-severity escalation.
- **Human-in-the-loop slot-fill.** When a required field (e.g. an unreadable PO reference) is
  missing, the agent pauses and asks; a supplied answer corrects the envelope and the run resumes.
- **11-scenario synthetic catalog** that is simultaneously the demo script and the test suite
  (see [`sample-data/README.md`](sample-data/README.md)).
- **FastAPI + SSE API** exposing scenarios, jobs, a per-step **reasoning-trace SSE stream**, and a
  human-decision endpoint over the offline runner (`backend/app/api/`).
- **Next.js console scaffold** with a typed, zod-validated API client and a hardened security
  baseline (CSP, security headers) (`frontend/`).
- **86 tests** covering money/schemas, matcher, validators, guardrails, decision matrix, slot-fill,
  the supervisor end-to-end, the scenario catalog (exact decision + reason per invoice), and the API.

### Ports & adapters seam

Specialists and the supervisor depend only on narrow **port protocols**
(`backend/app/orchestrator/ports.py`): `ExtractorPort`, `KnowledgePort`, `LedgerPort`,
`ReasoningPort`, `HumanInputPort`, plus injected `Clock`/`IdGen`. Today these are satisfied by
**offline fixture adapters** (`backend/app/adapters/fixtures.py`) backed by synthetic JSON. The
same contracts will be satisfied by Azure adapters with **no change to the orchestrator**.

---

## What is gated on Azure / M365 provisioning (planned, ports-ready)

These are designed and ports-isolated, but not yet wired — they require a tenant, an Azure
subscription, and model access we control. They are clearly marked *planned* throughout the code
and the [roadmap](docs/ROADMAP.md).

- **Azure adapters behind the existing ports:**
  - **Azure AI Document Intelligence** (`prebuilt-invoice`) as the `ExtractorPort`.
  - **Foundry IQ** (Azure AI Foundry / `azure-ai-projects`) as the `KnowledgePort` — grounded
    retrieval of POs, GRNs, and policy **with clickable citations**.
  - **Azure OpenAI** (via Azure AI Foundry) as the `ReasoningPort` — advisory narration only; it
    never decides outcomes.
- **M365 Copilot / Teams surface:** an **M365 Agents-SDK** custom-engine-agent proxy that exposes
  the backend as a real Copilot/Teams agent, with Adaptive Cards for the slot-fill `HumanInputPort`.
- **Cloud security:** Entra ID SSO and secrets in Key Vault / managed identity.

### Microsoft IQ + M365 Copilot integration intent

The intelligence stays on the Microsoft stack to maximize the **Microsoft IQ (Foundry IQ)** scoring
pillar: Foundry IQ provides grounded, cited retrieval of the reference data the matcher and
reviewer rely on, while the agent is surfaced natively inside **M365 Copilot / Teams** via the
Agents SDK. The end-state demo — *"Process invoice INV-1042"* answered inside Teams/Copilot,
grounded by Foundry IQ with clickable citations — is the target of the gated integration phase.

---

## How to run

### Backend (offline core + API)

```bash
cd backend
pip install -e ".[dev,api]"          # deterministic core + test deps + FastAPI/SSE
uvicorn app.api.app:create_app --factory   # serves http://localhost:8000
pytest                                # 86 tests, no cloud needed
```

Run a single scenario end-to-end and print the reasoning trace:

```bash
python -m app.cli INV-1042            # the +6% over-tolerance "money shot"
python -m app.cli INV-1043            # clean three-way match → pass
```

> The full cloud runtime extras (`azure`, `agent`) exist in `pyproject.toml` but are **not** needed
> for the offline core or its tests. Install them only once provisioning lands:
> `pip install -e ".[dev,azure,agent,api]"`.

### Frontend (console)

```bash
cd frontend
npm install
npm run dev                           # http://localhost:3000, talks to the API at :8000
```

Configure the API endpoint via `NEXT_PUBLIC_API_BASE_URL` (see `frontend/.env.example`). Only
public, non-sensitive config ships to the browser.

---

## The demo / scenario arc

The catalog is curated to *prove* behaviour on the exceptions that matter (full table in
[`sample-data/README.md`](sample-data/README.md); shooting script in
[`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)). The headline arc:

| Step | Invoice | What it shows | Outcome |
|------|---------|---------------|---------|
| 1 | **INV-1043** | clean three-way match, balanced posting | **PASS** |
| 2 | **INV-1042** | one line +6% over PO price (≈ $57 impact) — the money shot | **HOLD** · `VARIANCE_OUTSIDE_TOLERANCE` |
| 3 | **INV-1053** | 10 received but 8 already invoiced; bills 10 (line-level depth) | **HOLD** · `OVER_BILLED_VS_RECEIPT` |
| 4 | **INV-1054** | unit price 150 vs PO 95 (≥ $500 impact) — guardrail overrides the LLM | **ESCALATE** · `VARIANCE_HIGH_SEVERITY` |
| 5 | **INV-1057** | unreadable PO ref → agent asks → human supplies PO-5000 (slot-fill) | **HOLD → PASS** |
| 6 | **INV-1056** | invoice number already in the posted ledger (duplicate control) | **ESCALATE** · `DUPLICATE_INVOICE` |

---

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full diagram (Mermaid, renders on
GitHub) and a prose walk-through, and [`docs/ROADMAP.md`](docs/ROADMAP.md) for the
workstream × phase plan and gating.

```text
M365 Copilot / Teams  →  M365 Agents-SDK proxy  →  FastAPI (+ SSE)  →  Magentic supervisor
                                                                          ├─ 5 specialists
                                                                          └─ deterministic guardrails
        Foundry IQ · Azure Document Intelligence · Azure OpenAI  (behind ports — gated)
        Next.js console  ←  consumes the SSE reasoning stream
```

---

## Compliance & safety note

- **All sample data is synthetic.** No real vendors, customers, PII, or secrets — synthetic-by-design
  is the correct posture for confidential AP data and lets us deterministically prove edge-case
  behaviour.
- **Public, clean-room repository.** No proprietary or internal references in code, comments, or git
  history.
- **No secrets in the tree or history.** Configuration is via environment variables and
  `.env.example` only. The browser bundle carries public config exclusively.
- **Controls are authoritative.** The deterministic guardrails and decision matrix — not the LLM —
  decide every posting; a variance always holds or escalates to a human.
