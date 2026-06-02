# Roadmap — Retail Supplier Deduction Control Agent

A living plan for the **Agents League AISF 2026** entry (Enterprise Agents / Microsoft 365
Copilot track). The build is decomposed into **workstreams** (parallel tracks) and **phases**
(sequential maturity gates) so each phase can be planned in detail on its own. Update this doc
as phases close.

**Product, in one line:** *A deterministic-control agent that prevents retail margin leakage and
supplier deduction disputes before payment.* A Copilot-native, multi-agent, evidence-grounded,
human-in-the-loop agent over a three-way-match core, whose arithmetic, tolerance, allowance, and
posting decisions are made by deterministic code the LLM cannot override. The differentiator is
**promotion-allowance / margin-leakage detection** — catching invoices that pass three-way match
but are missing a commercial allowance — plus short-receipt deduction cases and UOM normalization.

**Status legend:** ✅ done · 🔵 in progress · ⛔ blocked / gated · ⬜ planned

---

## Workstreams

| WS | Name | Scope | Owner-ish |
|----|------|-------|-----------|
| **WS1** | Agent Core | Domain schemas, deterministic matching/validators/guardrails/decision, Magentic supervisor + 6 specialists (incl. `promotion_auditor`), retail deduction control (allowance/leakage, deduction cases, partial hold, UOM normalization), exception depth, scenario corpus | backend |
| **WS2** | API & Realtime | FastAPI endpoints + SSE reasoning-trace stream over the runner | backend |
| **WS3** | Frontend Console | Next.js approver console — inbox, 3-way canvas, variance, GL preview, audit, policy, live reasoning trace | frontend |
| **WS4** | Microsoft Integration | Azure adapters (Document Intelligence, **Foundry IQ**, Azure OpenAI) behind the ports + M365 Copilot/Teams surface (Agents SDK proxy) | backend + cloud |
| **WS5** | Infra & DevOps | Azure provisioning, deployment (App Service / Static Web Apps), optional CI | cloud |
| **WS6** | Security & Compliance | Client-side hardening now; Entra ID / Key Vault later; secret-scan + git-history audit; hackathon disclaimer compliance | cross-cutting |
| **WS7** | Docs / Demo / Submission | README, architecture diagram, scenario script, ≤5-min demo video, registration + submission | cross-cutting |

The **ports & adapters** seam (WS1) is what lets WS3 and WS4 proceed independently: the offline
fixtures and the Azure adapters satisfy the same contracts, so the orchestrator never changes.

---

## Phases

### P0 — Provisioning & Feasibility ⛔ (gated; user action)
Goal: obtain the environments the cloud workstreams need.
- Register for Agents League; collect Microsoft Learn usernames (WS7).
- Microsoft 365 Developer Program (E5 sandbox) for a Teams/Copilot tenant (WS5).
- Azure subscription (Azure for Students / free tier); **request Azure OpenAI access early** (WS5).
- Create Azure AI Foundry project, Document Intelligence, AI Search (for Foundry IQ) (WS5).
- Decide Copilot-license vs Teams-bot fallback (WS4).
- **Exit:** a tenant + Azure subscription + model access we control. **Until then P4/P5 stay blocked.**

### P1 — Offline Agent Core ✅
Goal: the genuinely-agentic backend, fully offline + tested.
- WS1: schemas, deterministic core, ports/envelope, supervisor + specialists, CLI.
- **Exit met:** `python -m app.cli INV-1042/INV-1043` runs end-to-end; tests green.

### P2 — Exception Depth + API ✅
Goal: credible exception handling + a consumable surface.
- WS1: currency/duplicate/tax, line-level over-bill, SKU alias, slot-fill HITL, 11-scenario catalog.
- WS2: FastAPI endpoints + SSE reasoning-trace stream.
- **Exit met:** 86 tests green; API serves scenarios/jobs/stream/decision offline.

### P2.5 — Retail Deduction Control 🔵 (cloud-free; the differentiator)
Goal: the retail margin-protection layer that sets the entry apart from generic AP matching.
- WS1: `promotion_auditor` specialist + `KnowledgePort.get_promotions`; promotion-allowance /
  margin-leakage detection; short-receipt **deduction cases** with supplier-facing explanations
  and a pay-now / hold split; UOM false-mismatch normalization (factor present → PASS, missing →
  escalate); retail scenario corpus + `expected_results.json`; `triage` CLI investigation flow.
- WS7: rebrand to **Retail Supplier Deduction Control Agent** (README, demo script, this roadmap).
- **Exit:** `python -m app.cli triage` splits the batch; INV-1003 holds with a $25,200 leakage
  deduction case + promotion citation; full test suite green.

### P3 — Frontend Console 🔵 (in progress; cloud-free)
Goal: the commercial-grade approver console + the visible reasoning trace.
- WS3: scaffold ✅ → inbox → 3-way canvas → variance + GL preview → reasoning trace + citations → audit + policy → Teams-tab wrapper.
- WS6: client-side security baseline (CSP, zod-validated responses, no secrets) — folded into WS3.
- **Exit:** all 7 surfaces wired to the local API; INV-1042 (hold) / INV-1043 (pass) demoable in the browser.

### P4 — Microsoft Integration ⛔ (blocked on P0)
Goal: the scored pillars — **Microsoft IQ + M365 Copilot**.
- WS4: swap fixtures for Azure adapters behind the ports (Doc Intelligence extractor, **Foundry IQ** retrieval + citations, Azure OpenAI reasoning); M365 Agents-SDK proxy + Adaptive Card; Teams tab live sideload.
- WS6: Entra ID SSO; secrets in Key Vault / managed identity.
- **Exit:** "Process invoice INV-1042" works inside Teams/Copilot, grounded by Foundry IQ with clickable citations.

### P5 — Hardening & Compliance ⬜
Goal: submission-ready quality + safety.
- WS6: secret-detection scan, full git-history audit, 2FA, dependency `npm audit`.
- WS7: README, `docs/architecture.md` diagram; confirm all `sample-data/` is synthetic/public-safe.
- **Exit:** clean public repo, no secrets in history, README + diagram complete.

### P6 — Demo & Submission ⬜
Goal: ship it.
- WS7: record ≤5-min demo video (the hard-point arc), submit public repo + README + diagram + video by **June 14, 2026**. Checklist: [`SUBMISSION.md`](SUBMISSION.md).
- **Exit:** submitted; digital badge.

---

## Phase × Workstream matrix

| | WS1 Core | WS2 API | WS3 FE | WS4 MS | WS5 Infra | WS6 Sec | WS7 Docs |
|---|---|---|---|---|---|---|---|
| **P0** Provision | | | | decide fallback | ✅ register/provision | | ⬜ register |
| **P1** Agent Core | ✅ | | | | | | |
| **P2** Depth+API | ✅ | ✅ | | | | | |
| **P3** Console | | | 🔵 | | | 🔵 client | |
| **P4** MS Integ | (ports ready) | | (consumes) | ⛔ | ⛔ deploy | ⛔ authn | |
| **P5** Hardening | | | | | | ⬜ | ⬜ |
| **P6** Submission | | | | | | | ⬜ |

---

## Dependencies & gating

- **P0 gates P4 and P5/P6's cloud bits.** P1→P2→P3 are cloud-free and unblocked.
- WS4 depends on WS1's ports being stable (they are) — adapters drop in with no orchestrator change.
- WS3 depends only on WS2 (done). WS6-client rides along WS3; WS6-cloud rides along P4.
- If P0 stays blocked, the project still reaches a **complete, secure, demoable offline product**
  (P3 done); P4 becomes a documented, ports-isolated add-on.

---

## PR map

- **Done & pushed:** PR1–3 (scaffold/schemas/core) · agentic backend (ports/specialists/supervisor/adapters/CLI/data/tests) · PR-D1–D5 (exception depth) · PR11–12 (API + SSE) · PR15 (frontend scaffold).
- **Planned — P3:** PR16 inbox · PR17 3-way canvas · PR18 variance + GL preview · PR19 reasoning trace + citations · PR20 audit + policy · PR21 Teams-tab wrapper + approve/reject.
- **Planned — P4 (gated):** PR8 Doc Intelligence · PR9 Foundry IQ · PR10 Azure OpenAI · PR13 Agents-SDK proxy · PR14 Adaptive Card.
- **Planned — P5/P6:** PR22 README + architecture diagram · PR23 compliance + sample-data audit · demo video.

---

## Next detailed-planning targets

Plan these per-phase, one at a time:
1. **P3 frontend** (active) — per-surface component/data-hook design against the API contract.
2. **P4 Azure adapters** — once P0 lands: Foundry IQ knowledge-base setup + citation mapping, Doc
   Intelligence field mapping, Agents-SDK proxy wiring; each adapter as its own PR behind a port.
3. **P5 hardening** — security checklist + docs.

Engineering discipline across all phases: **SOLID** (ports & adapters), **clean git** (Conventional
Commits now; PR+Issue once at scale), every change ≤30-min reviewable, `main` green, no secrets or
private references in this public repo.
