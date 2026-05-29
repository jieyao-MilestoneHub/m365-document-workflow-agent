# Demo script (≤ 5 minutes)

The shooting script for the submission video. The thesis to land in the first 20 seconds and
again at the close:

> **Let AI participate in the finance process, but never let AI break financial controls.**

Everything below runs **today, offline, with zero Azure/M365 credentials** — the CLI, the
FastAPI/SSE backend, and the Next.js console all drive the same orchestrator over the synthetic
`sample-data/` corpus. The M365 Copilot/Teams surface and the Azure adapters (Document
Intelligence, Foundry IQ, Azure OpenAI) are **gated on provisioning** (see
[`ROADMAP.md`](ROADMAP.md), P4) — narrate them as the designed-but-gated end state, don't fake
them.

The numbers, decisions, and citations quoted here are the **actual** runner output (verified via
`python -m app.cli <ID>`), so the on-screen trace will match.

---

## Setup before recording

```bash
# Terminal A — API (optional, if showing the console/SSE)
cd backend
pip install -e ".[dev,api]"
uvicorn "app.api.app:create_app" --factory          # http://localhost:8000

# Terminal B — CLI runs (the reliable, screenshot-friendly path)
cd backend

# Terminal C — console (optional)
cd frontend && npm install && npm run dev            # http://localhost:3000
```

Pre-warm by running `python -m app.cli INV-1043` once so the first take is clean.

---

## The arc (6 beats, ~40s each)

| Beat | Invoice | What you say / show | Verified outcome |
|------|---------|---------------------|------------------|
| 0 | — | "Three-way match: Invoice ↔ PO ↔ Goods Receipt. The LLM reasons and cites; **deterministic code owns every verdict.**" | (thesis slide) |
| 1 | **INV-1043** | The happy path. Clean match, balanced posting draft, ready to post. | **PASS** |
| 2 | **INV-1042** | The money shot: one line at **100.70 vs PO 95.00** (+6%, **$57** impact). Outside tolerance → it will **not** auto-post. | **HOLD** · `VARIANCE_OUTSIDE_TOLERANCE` |
| 3 | **INV-1053** | Line-level depth: 10 received but **8 already invoiced**; vendor bills 10. Only 2 are billable. | **HOLD** · `OVER_BILLED_VS_RECEIPT` |
| 4 | **INV-1054** | The guardrail-over-LLM beat: **150 vs PO 95** (≈ **$550** impact). High severity — the deterministic matrix **escalates regardless of what the model says**. | **ESCALATE** · `VARIANCE_HIGH_SEVERITY` |
| 5 | **INV-1057** | Human-in-the-loop: the PO reference is unreadable. The agent **pauses and asks**; a human supplies **PO-5000**; the run resumes and clears. | **HOLD → PASS** (slot-fill) |
| 6 | **INV-1056** | The control catch: this invoice number is **already in the posted ledger**. Duplicate-payment control fires. | **ESCALATE** · `DUPLICATE_INVOICE` |
| 7 | — | Close on the thesis + "the same backend is surfaced inside **M365 Copilot/Teams** and grounded by **Foundry IQ with clickable citations** once provisioning lands." | (gated end-state slide) |

> Drop a beat if you're over time — keep **1, 2, 4** (pass → hold → guardrail-overrides-LLM):
> they carry the whole story.

---

## Beat 2 — the money shot, verbatim

Run `python -m app.cli INV-1042` on screen. The trace to point at:

```
  [01] delegate_result  invoice_extractor  Extracted invoice INV-1042 from Globex (2 lines, total 1107.00 USD).
  [02] delegate_result  po_grn_matcher     Matched 2 lines against PO PO-5000 / GRN GRN-7000: partial.
  [03] delegate_result  variance_assessor  Variance: 1 line(s) off, overall medium, impact 57.00.
  [04] peer_review      po_grn_matcher     Peer review of variance_assessor: accept ...
  [05] delegate_result  posting_preparer   Drafted posting: 3 lines, debit 1107.00 / credit 1107.00 (balanced).
  [06] delegate_result  exception_reviewer Hold - VARIANCE_OUTSIDE_TOLERANCE.
  [07] finalize         supervisor         hold

== Decision: HOLD  (confidence 0.8)
  reasons: VARIANCE_OUTSIDE_TOLERANCE
  citations:
    - Purchase Order PO-5000: WIDGET-A x10 @ 95.00; WIDGET-B x5 @ 20.00
    - Goods Receipt Note GRN-7000: WIDGET-A received 10; WIDGET-B received 5
```

Talking point: the posting draft **balances to the cent** (1107.00 = 1107.00) yet the invoice
**still holds** — balancing is necessary, not sufficient. The deterministic decision matrix, not
the LLM, made that call.

---

## What to emphasize for the judging pillars

- **Reliability & Safety** — deterministic guardrails (tool-call budget 25, per-role visit cap 3,
  cycle detection) and the `pass/hold/escalate` matrix are pure code the LLM cannot override. A
  variance never silently auto-posts (beats 2, 4).
- **Microsoft IQ (Foundry IQ)** — the citations under each decision are the seam Foundry IQ fills:
  grounded retrieval of POs/GRNs/policy with clickable citations. Today the `KnowledgePort` is a
  fixture; the wire contract is identical when the Foundry IQ adapter drops in (gated).
- **M365 Copilot integration** — the same backend is exposed as a custom-engine agent via the M365
  Agents SDK, with the slot-fill prompt (beat 5) rendered as an Adaptive Card (gated on tenant).
- **Agentic design** — a Magentic-style supervisor emits one action per turn (delegate /
  peer-review / request-input / escalate / finalize) over 5 specialists, with state threading
  through an append-only envelope; visible live in the SSE reasoning trace.

---

## Recording checklist

- [ ] Keep total runtime **≤ 5:00**.
- [ ] Open and close on the thesis line.
- [ ] Clearly label gated features as **planned / gated**, never as live (compliance + honesty).
- [ ] Show at least one live trace (CLI or console SSE), not just slides.
- [ ] No secrets, tenants, or real vendor data on screen — `sample-data/` is synthetic by design.
- [ ] Submit public repo + README + `docs/architecture.md` diagram + this video by the deadline
      (see [`ROADMAP.md`](ROADMAP.md), P6).
