# Demo script (≤ 5 minutes)

The shooting script for the submission video. The thesis to land in the first 20 seconds and
again at the close:

> **Standard three-way match would pass this invoice. Our retail promotion control catches the
> missing allowance before payment** — and never lets the LLM override a financial control.

This is **not** a parade of static scenarios. It's **one interactive investigation**: the agent
triages a batch of retail supplier invoices, surfaces what would overpay or leak margin, and
answers the reviewer's follow-up questions with evidence.

Everything below runs **today, offline, with zero Azure/M365 credentials** — the CLI, the
FastAPI/SSE backend, and the Next.js console all drive the same orchestrator over the synthetic
`sample-data/` corpus. The M365 Copilot/Teams surface and the Azure adapters (Document
Intelligence, Foundry IQ, Azure OpenAI) are **gated on provisioning** (see
[`ROADMAP.md`](ROADMAP.md), P4) — narrate them as the designed-but-gated end state, don't fake
them. The numbers, decisions, and citations quoted here are the **actual** runner output.

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

Pre-warm by running `python -m app.cli triage` once so the first take is clean.

---

## The arc (investigation, ~60s per beat)

### Beat 0 — thesis (slide)
"Retail AP loses margin in the gap between the invoice and the *commercial agreement*. Three-way
match checks PO ↔ GRN ↔ invoice — it can't see a promotion allowance the supplier forgot to
deduct. This agent reaches into the agreement and reconciles it, and **deterministic code owns
every verdict.**"

### Beat 1 — triage the batch
Run on screen:

```bash
python -m app.cli triage
```

The agent reviews the May retail invoices and splits them (actual output):

```
>> Triage: reviewing 6 retail supplier invoices

Payment-ready:
  - INV-1001  clean — payable $2,400.00
  - INV-1004  clean — payable $1,800.00          (apparent UOM mismatch cleared by normalization)
  - INV-1006  clean — payable $151,200.00        (promotion allowance correctly applied)

Needs action:
  - INV-1002  $480.00 short receipt -> dc_receiving_supervisor
  - INV-1003  $25,200.00 promotion allowance missing -> category_manager
  - INV-1005  uom mismatch -> ap_manager
```

Talking point: nothing in "needs action" is a raw OCR/matching error — INV-1003 is a *commercial*
exception (a missing allowance) and INV-1004 was *spared* a false hold by pack-size
normalization. (Parenthetical notes above are narration, not CLI text.)

### Beat 2 — the money shot: drill into INV-1003
"INV-1003 passed three-way match. Why are you holding it?"

```bash
python -m app.cli INV-1003
```

The trace and decision the reviewer sees (actual output):

```
  [02] delegate_result  po_grn_matcher     Matched 1 lines against PO PO-6003 / GRN GRN-8003: matched.
  [03] delegate_result  promotion_auditor  Allowance audit: 1 promotion(s) in effect, margin leakage 25200.00.
  [05] delegate_result  posting_preparer   Drafted posting: 2 lines, debit 151200.00 / credit 151200.00 (balanced).
  [06] delegate_result  exception_reviewer Hold - PROMOTION_ALLOWANCE_MISSING.

== Decision: HOLD  (confidence 0.8)
  reasons: PROMOTION_ALLOWANCE_MISSING
  summary: Hold - PROMOTION_ALLOWANCE_MISSING.
  Pay now: $126,000.00   Hold: $25,200.00
```

Talking point: the matcher reports **matched** (every number agrees — a textbook three-way match
passes), the posting **balances to the cent**, yet the invoice **holds**. The hold comes from the
`promotion_auditor` reconciling the *promotion agreement*, which lives outside the PO/GRN/invoice
triad. The deterministic control layer, not the LLM, computed the leakage.

### Beat 3 — show the evidence
"Show me the evidence." The same `INV-1003` run prints the deduction case (actual output):

```
  Deduction case DED-INV-1003-1  (PROMOTION_ALLOWANCE_MISSING, $25,200.00, OPEN) -> category_manager
    evidence: PO-6003#line-1, GRN-8003#line-1, INV-1003#line-1, PROMO-MAY-BEV
    explanation: Invoice INV-1003 billed 8400 case of OJ-1L-CASE at full price with no allowance
      line. Promotion PROMO-MAY-BEV grants a 3.00 allowance per case (valid 2026-05-01..2026-05-15),
      so an allowance of 25200.00 was expected. Margin leakage: 25200.00.

  citations:
    - Purchase Order PO-6003: OJ-1L-CASE x8400 @ 18.00
    - Goods Receipt Note GRN-8003: OJ-1L-CASE received 8400
    - Promotion Agreement PROMO-MAY-BEV: 3.00 allowance per case on OJ-1L-CASE, valid 2026-05-01 to 2026-05-15
```

The `PROMO-MAY-BEV` citation is the **Foundry IQ** seam: today the `KnowledgePort` serves it from
a fixture; the Foundry IQ adapter drops in behind the same contract, with the citation clickable
through to the agreement.

### Beat 4 — partial deduction (INV-1002), optional
"Short receipts shouldn't block the whole payment." Run `python -m app.cli INV-1002`: billed 500
cases, GRN accepted 420 → the agent recommends **pay $2,520 now, hold $480** for the 80-case
shortfall, with a deduction case and supplier explanation — not a blanket block.

### Beat 5 — close (slide)
"Same backend, surfaced inside **M365 Copilot/Teams** and grounded by **Foundry IQ with clickable
citations** once provisioning lands. The control is deterministic; the AI explains and routes."

---

## What to emphasize for the judging pillars

- **Reliability & Safety** — the `pass/hold/escalate` matrix, the allowance reconciliation, and
  the pay-now/hold split are pure code the LLM cannot override; guardrails (tool-call budget 25,
  per-role visit cap 3, cycle detection) bound the agent. A leakage never silently auto-posts.
- **Microsoft IQ (Foundry IQ)** — the citations under each decision (PO, GRN, **promotion
  agreement**) are the seam Foundry IQ fills: grounded retrieval with clickable citations. Today
  the `KnowledgePort` is a fixture; the wire contract is identical when the adapter drops in.
- **M365 Copilot integration** — the same backend is exposed as a custom-engine agent via the
  M365 Agents SDK; the triage + follow-up investigation is the Copilot conversation (gated).
- **Agentic design** — a Magentic-style supervisor emits one action per turn (delegate /
  peer-review / request-input / escalate / finalize) over 6 specialists incl. `promotion_auditor`,
  with state threading through an append-only envelope; visible live in the SSE reasoning trace.

---

## Recording checklist

- [ ] Keep total runtime **≤ 5:00**.
- [ ] Open and close on the thesis line; say "would pass three-way match" out loud on INV-1003.
- [ ] Clearly label gated features as **planned / gated**, never as live (compliance + honesty).
- [ ] Show at least one live trace (CLI `triage` + `INV-1003`), not just slides.
- [ ] No secrets, tenants, or real vendor data on screen — `sample-data/` is synthetic by design.
- [ ] Submit public repo + README + `docs/architecture.md` diagram + this video by the deadline
      (see [`ROADMAP.md`](ROADMAP.md), P6).
</content>
