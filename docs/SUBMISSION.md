# Submission checklist

Closes out **WS7** for **Agents League AISF 2026** (Enterprise Agents / M365 Copilot track).
Deadline: **2026-06-14**. The video itself is a human recording step — see
[`DEMO_SCRIPT.md`](DEMO_SCRIPT.md).

## Artifacts to submit

- [ ] **Public repo** — this repository, clean-room, no secrets in tree or history.
- [ ] **README** — description, run steps, IQ usage, demo arc ([`../README.md`](../README.md), #19).
- [ ] **Architecture diagram** — self-contained SVG, renders on GitHub ([`architecture.md`](architecture.md), #20).
- [ ] **Demo video** — ≤ 5 min, the hard-point arc ([`DEMO_SCRIPT.md`](DEMO_SCRIPT.md), #21).

## Registration (user action)

- [ ] Register for Agents League; record Microsoft Learn usernames.
- [ ] Microsoft 365 Developer Program (E5 sandbox) for a Teams/Copilot tenant.
- [ ] Azure subscription + Azure OpenAI access (request early).

These gate the live Foundry IQ / Copilot demo (P4); the offline product ships without them.

## Pre-submission audit (run before the final push)

- [ ] **Secret scan** of the working tree and full git history — none expected (env vars only).
- [ ] **Git-history review** — no proprietary or internal-project references in any commit.
- [ ] **`sample-data/` is synthetic** — no real vendors, customers, or PII.
- [ ] **Dependency audit** — `npm audit` (frontend); review backend extras.
- [ ] **Backend green** — `cd backend && pytest` → full suite passing (retail + legacy regression).

## Judging-pillar map (where each is shown)

| Pillar | Evidence |
|--------|----------|
| Reliability & Safety | Deterministic guardrails + decision matrix + allowance reconciliation + pay-now/hold split; a margin leakage never auto-posts (INV-1003), a short receipt holds only the disputed amount (INV-1002). |
| Microsoft IQ (Foundry IQ) | Cited PO / GRN / **promotion-agreement** retrieval via `KnowledgePort` — fixture today, Foundry IQ adapter gated; the PROMO-MAY-BEV citation under INV-1003 is the seam. |
| M365 Copilot integration | Backend exposed as a custom-engine agent via the M365 Agents SDK; the triage + follow-up investigation is the Copilot conversation; slot-fill as an Adaptive Card (gated). |
| Agentic design | Magentic supervisor, one action per turn over 6 specialists (incl. `promotion_auditor`), live in the SSE trace. |
