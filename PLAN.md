# Worktree plan — WS3 Frontend Console (`feat/frontend-console`)

**Branch:** `feat/frontend-console`  ·  **Worktree:** `C:/Users/USER/Desktop/Develop/m365-frontend`
**GitHub issues:** `gh issue list --label ws3-frontend` (#1 Inbox, #2 Canvas, #3 Variance+GL,
#4 Reasoning Trace, #5 Audit+Policy, #6 Teams tab)

This worktree builds the Next.js approver console (WS3, Phase P3). It is **cloud-free** — it
consumes the local FastAPI only. Read `docs/ROADMAP.md` and `CLAUDE.md` first.

## Start-of-session setup

```bash
cd C:/Users/USER/Desktop/Develop/m365-frontend
# 1) backend (separate terminal) — provides the API the console reads:
cd backend && pip install -e ".[dev,api]" && uvicorn "app.api.app:create_app" --factory --port 8000
# 2) frontend:
cd frontend && npm install && npm run dev      # http://localhost:3000
```

The scaffold already exists: `frontend/src/lib/api.ts` (single fetch/EventSource boundary),
`frontend/src/lib/types.ts` (zod), `next.config.ts` (security headers), a connectivity landing page.

## API contract (from `backend/app/api/`)

- `GET /api/scenarios` → `[{id, vendor, total, currency}]`
- `POST /api/jobs {invoice_ref}` → `JobDetail`
- `GET /api/jobs/{id}` → `JobDetail`
- `GET /api/jobs/{id}/stream` → SSE: repeated `event: trace` (`data` = `{seq,kind,role,detail,ts}`) then one `event: completed` (`data` = `{job_id,decision,summary,blocking_reasons}`)
- `POST /api/jobs/{id}/decision {action: approve|reject, reviewer, note}` → `JobDetail`

`JobDetail` = `{job_id, invoice_ref, status, decision, outcome{decision,confidence,blocking_reasons[],summary,exception_tickets[]}, invoice, match{po_number,grn_number,currency_mismatch,lines[{invoice_line_no,status,quantity_delta,price_delta,within_tolerance,po_unit_price,received_quantity,remaining_billable_quantity,over_billed,resolved_sku}],citations[{document_id,document_title,cited_text}]}, variance{lines[{invoice_line_no,financial_impact,severity,within_tolerance,rationale}],overall_severity,financial_impact_total}, posting{lines[{gl_account,direction,amount,memo}],balanced}, handoff_history[{from_role,to_role,reason_code,detail,attempt,event_id,ts}], events[], human_decision}`.
**Money fields are JSON strings** (pydantic json mode) — parse with `Number()` only for display math.
Cross-check exact shapes in `backend/app/api/service.py` + `backend/app/schemas/*.py`.

## Build order (one Conventional Commit per step; keep `npm run build` + `npx vitest run` green)

1. **Types + hooks.** Extend `src/lib/types.ts` zod schemas to fully type invoice/match/variance/
   posting (replace the `z.unknown()` placeholders). Add `src/hooks/`: `useScenarios`, `useJob`,
   `useReasoningStream` (EventSource → array of trace events + completed). The hooks call `api`
   only; never fetch in components.
2. **OCP registries** `src/lib/registry.ts`: `BLOCKING_REASON_META[code] → {label, severity, help}`
   and `DECISION_BADGE[decision] → {label, tone}`. New reasons render without touching components.
3. **Inbox** (`src/app/page.tsx` or `src/app/inbox`): table of scenarios (id, vendor, total),
   "Process" runs `createJob`, row shows resulting decision badge, link → `/review/{jobId}`.
4. **Review page** `src/app/review/[id]/page.tsx` — **client component**, read id via
   `useParams()` from `next/navigation` (Next 16 server `params` are async — avoid). Compose:
   - **ThreeWayMatchCanvas** — PO ↔ GRN ↔ Invoice columns, per-line diff, variance % badge.
   - **VarianceEvidenceTable** — per-line impact, tolerance, severity, rationale.
   - **GLJournalPreview** — debit/credit lines, totals, balance check.
   - **AgentReasoningTrace** — live SSE timeline (kind/role/detail) + **CitedText** popover
     (shows `cited_text` + document_title). Plain text only.
   - **Approve/Reject** buttons → `api.decide`; reflect `human_decision`.
5. **Audit Trail** (`handoff_history`) + read-only **Vendor/Policy** view (from a policy endpoint
   if added, else from the job's data). (#5)
6. **Teams tab wrapper** (#6): `@microsoft/teams-js` init in a tab route; standalone-safe (init
   no-ops outside Teams). Live Teams sideload is gated on a tenant — build + document only.

## SOLID + Security (both are hard requirements from the user)

- DIP: `src/lib/api.ts` is the ONLY module calling `fetch`/`EventSource`.
- SRP/ISP: small, prop-driven components; data via hooks; no fetching in leaf components.
- OCP: the registries above.
- Security: zod-parse EVERY response (already the api.ts pattern); **no `dangerouslySetInnerHTML`**;
  render agent text/citations as plain text; no secrets in the bundle; keep the CSP in
  `next.config.ts` (connect-src must include the API origin).

## Tests

Vitest + Testing Library + MSW. Mock the API boundary; a few component tests per surface
(inbox renders scenarios; canvas shows a variance row; reasoning trace renders streamed events;
decision button posts). `npm run build` and `npx vitest run` must pass before each commit.

## Definition of done & delivery

DoD: inbox → run INV-1042 → review shows hold + the +6% canvas + variance + balanced posting +
streamed reasoning trace with a clickable PO citation; INV-1043 → pass. Build + tests green.
Delivery: commit per step (end every message with
`Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`), `git push -u origin
feat/frontend-console`, then `gh pr create --draft --base main --head feat/frontend-console`
referencing the WS3 issues. Do NOT merge.
