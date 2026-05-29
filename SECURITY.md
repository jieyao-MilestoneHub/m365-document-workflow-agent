# Security posture

This is a public, clean-room hackathon repository. Security is staged: a **client-side hardening
baseline is in place today**, and **cloud identity/secret management is deferred until Azure/M365
provisioning lands** (see [`docs/ROADMAP.md`](docs/ROADMAP.md), WS6).

## In place today (cloud-free)

- **No secrets in the tree or git history.** Configuration is via environment variables and
  `.env.example` only. The browser bundle ships **public, non-sensitive config exclusively**
  (`NEXT_PUBLIC_API_BASE_URL`).
- **Synthetic data only.** All of `sample-data/` is synthetic — no real vendors, customers, PII,
  or proprietary references — safe for a public repo and sufficient to prove edge-case behaviour.
- **Content-Security-Policy + security headers** on the Next.js console (`frontend/next.config.ts`):
  a tight CSP (`default-src 'self'`, scoped `connect-src`, `object-src 'none'`), plus
  `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, and a
  restrictive `Permissions-Policy`. `frame-ancestors` is scoped to allow embedding only as a
  Microsoft Teams personal tab.
- **Validated responses (defense in depth).** The frontend routes **every** API response through
  **zod** schemas in a single API boundary (`frontend/src/lib/api.ts`); the UI never renders
  unvalidated data.
- **Authoritative deterministic controls.** The pass/hold/escalate decision and the supervisor
  guardrails (budget, visit cap, cycle detection) are pure code the LLM cannot override — a
  reliability/safety control as much as a correctness one. A variance never silently auto-posts.
- **CORS** on the API is restricted to the configured console origin
  (`API_CORS_ORIGINS`, default `http://localhost:3000`).

## Deferred until provisioning (gated)

- **Entra ID SSO** for authenticating approvers (and the M365 Copilot/Teams surface).
- **Secrets in Azure Key Vault / managed identity** once Azure adapters (Document Intelligence,
  Foundry IQ, Azure OpenAI) are wired behind the existing ports — no credentials live in code.
- **Pre-submission audit:** secret-detection scan, full git-history review, and dependency audit.

## Reporting

This is a hackathon project, not a production service. For any security concern, please open a
GitHub issue (do not include secrets or sensitive data).
