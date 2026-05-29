# Worktree plan — WS7 Docs (`docs/readme-architecture`)

**Branch:** `docs/readme-architecture`  ·  **Worktree:** `C:/Users/USER/Desktop/Develop/m365-docs`
**GitHub issues:** `gh issue list --label ws7-docs` (README; architecture diagram; demo video + submission)

## Status — a first draft is already committed & pushed

Commit `3dcb76e` on this branch (pushed to `origin/docs/readme-architecture`) added:
- `README.md` (172 lines) — product description, run steps, demo arc, compliance note.
- `docs/architecture.md` (138 lines) — Mermaid architecture diagram + walk-through.
- `SECURITY.md` (38 lines) — security posture.

⚠️ **This draft was machine-generated and is UNREVIEWED.** The new session's first job is to
**verify every claim against the actual code** and fix drift, NOT to assume it's correct.

## New-session tasks (in order)

1. **Accuracy review** — read `docs/ROADMAP.md`, `CLAUDE.md`, `backend/app/` (orchestrator,
   schemas, api), `sample-data/README.md`, and `git log`. Correct the README/architecture/SECURITY
   so they describe ONLY what exists; clearly mark gated items (Foundry IQ / Document Intelligence /
   Azure OpenAI adapters, M365 Copilot/Teams surface — all gated on Day-0 provisioning).
2. **Run-steps check** — confirm the commands actually work: backend `pip install -e ".[dev,api]"`
   + `uvicorn "app.api.app:create_app" --factory` + `pytest`; frontend `npm install` + `npm run dev`.
3. **Diagram** — ensure the Mermaid diagram in `docs/architecture.md` renders on GitHub and shows:
   M365 Copilot/Teams → Agents-SDK proxy → FastAPI → Magentic supervisor + 5 specialists +
   deterministic guardrails, with Foundry IQ / Doc Intelligence / Azure OpenAI behind ports
   (marked gated), and the Next.js console consuming the SSE reasoning stream. This is the
   hackathon's hard "architecture diagram" submission requirement.
4. **README must convey the thesis:** *"Let AI participate in the finance process, but never let
   AI break financial controls."* + the Microsoft IQ (Foundry IQ) + M365 Copilot integration story.
5. **Demo video (#21)** — out of scope for code; leave a `docs/DEMO_SCRIPT.md` outlining the ≤5-min
   arc (INV-1043 pass → INV-1042 +6% hold → INV-1053 over-bill → INV-1054 guardrail-over-LLM →
   INV-1057 slot-fill → INV-1056 duplicate) for the eventual recording.

## Constraints

No secrets; **no references to any private/internal project** (clean-room, public repo); be precise
about implemented-vs-gated.

## Delivery

Commit as `docs: …` (end every message with `Co-Authored-By: Claude Opus 4.8 (1M context)
<noreply@anthropic.com>`). Push `docs/readme-architecture`; open a **draft** PR
(`gh pr create --draft --base main --head docs/readme-architecture`) referencing the WS7 issues.
Do NOT merge.
