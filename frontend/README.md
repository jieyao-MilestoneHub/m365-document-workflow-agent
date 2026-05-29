# AP Three-Way Match — Agent Console (WS3)

Next.js approver console for the agentic AP Invoice Three-Way Match agent. It is **cloud-free**:
it consumes the local FastAPI backend only (no Azure/M365 credentials needed to run the UI).

## Getting started

```bash
# 1) backend (separate terminal) — provides the API the console reads:
cd ../backend && pip install -e ".[dev,api]" && uvicorn "app.api.app:create_app" --factory --port 8000

# 2) frontend:
npm install
npm run dev        # http://localhost:3000
```

Point the console at a non-default API with `NEXT_PUBLIC_API_BASE_URL` (see `.env.example`).
The CSP `connect-src` in `next.config.ts` must include that origin.

## Routes

- `/` — approver **inbox**: list sample invoices, **Process** runs the agent, the row shows the
  decision badge and links to the review.
- `/review/[id]` — **review** of one job: outcome banner, vendor/policy panel, three-way match
  canvas (PO ↔ GRN ↔ Invoice with variance % and Foundry IQ citations), variance evidence, GL
  journal preview with balance check, **live SSE reasoning trace**, audit trail, approve/reject.
- `/teams` — the same inbox wrapped as a **Microsoft Teams personal tab** (see below).

## Architecture (SOLID + security)

- **DIP:** `src/lib/api.ts` is the only module that calls `fetch`/`EventSource`. Every response
  is **zod-parsed** (`src/lib/types.ts`) before it reaches the UI — unvalidated data never renders.
- **SRP/ISP:** components are prop-driven and presentational; data comes from hooks
  (`src/hooks/*`) which call the api boundary. Leaf components never fetch.
- **OCP:** `src/lib/registry.ts` maps backend codes (decision / severity / line status /
  blocking reason) to display metadata via lookups with safe fallbacks — a new backend code
  renders without touching components.
- **Security:** no `dangerouslySetInnerHTML`; agent text and IQ citation snippets render as plain
  text; no secrets in the bundle (`NEXT_PUBLIC_*` config only); security headers + CSP in
  `next.config.ts`.

## Microsoft Teams personal tab

`/teams` initializes `@microsoft/teams-js` (dynamically, so it never runs during SSR) and is
**standalone-safe**: outside a Teams host `app.initialize()` rejects and the page falls back to a
normal browser view. The CSP `frame-ancestors` already allowlists `*.teams.microsoft.com`.

Live sideloading into a tenant is gated on a Teams app package + admin consent and a hosted
HTTPS URL, so it is **built and documented here, not sideloaded**. To sideload later: create a
Teams app manifest with a personal tab `contentUrl` pointing at `<host>/teams`, zip it with the
icons, and upload via *Teams → Apps → Manage your apps → Upload a custom app*.

## Console vs Teams/Copilot — division of labor

Both surfaces drive the **same** agent/orchestrator through the ports & adapters seam, so neither
duplicates business logic — they differ only in what they're good at:

- **Teams / M365 Copilot — the conversational surface** (and the hard "M365 Copilot integration"
  submission gate). Best for *triggering* the agent ("run the three-way match for INV-1042"),
  *answering* questions with a short summary + a citation, and *notifying* ("INV-1042 is on hold —
  needs your review").
- **This console — the review workbench**, for the dense, tabular, side-by-side actions a chat
  bubble handles poorly: the **approver inbox** (triage exceptions), the **three-way canvas + GL
  preview** (line-by-line Invoice ↔ PO ↔ GRN diff and Σdebit == Σcredit checked to the cent), and
  the **live SSE reasoning trace** with clickable Foundry IQ citations.

In short: Teams/Copilot is the *entry point + notifications + Q&A*; the console is where the
human actually makes the approval decision. See `docs/ROADMAP.md` for how this maps to WS3
(this console) vs WS4 (the Copilot/Teams proxy).

## Commands

```bash
npm run dev          # dev server
npm run build        # production build (gate)
npm test             # vitest run (gate)
npm run lint         # eslint
```

Tests use **Vitest + Testing Library + MSW**; the API boundary is mocked, so the suite is
deterministic and cloud-free.
