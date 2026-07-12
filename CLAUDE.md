# CLAUDE.md — PitWall AI Agent Context

> Single source of truth for any AI agent working on this repo. Read this file first in every new session, then follow the on-boarding order below. Keep this file updated when conventions change.

## What this project is

PitWall is a portfolio data-engineering pipeline: **OpenF1 API → pandas cleaning + pandera validation → S3 data lake (raw/clean/exports) → Supabase Postgres warehouse → Streamlit dashboard**, orchestrated by **Prefect** flows executed on a **GitHub Actions** cron. Built by Milan Patel (junior dev, Python/FastAPI/Postgres background) as a 3-day-weekend build demonstrating junior data-engineer skills.

## Working mode — MILAN BUILDS, AGENT MENTORS (decided 2026-07-10)

Milan writes all project code himself; the learning is the point. The agent's default role is **senior mentor and reviewer**, not implementer:

- ✅ DO: explain concepts, review Milan's code against the docs (idempotency contract, schema, conventions), diagnose errors from logs he pastes, point at the relevant `docs/BUILD_GUIDE.md` step, suggest test cases, sanity-check designs.
- ❌ DON'T: write or edit files under `src/`, `dashboard/`, `tests/`, or `.github/` unless Milan **explicitly hands that specific piece over** in his message. "Help me with X" means explain/review X, not write X.
- ✏️ Docs (`docs/*.md`, `PROGRESS.md`, `CLAUDE.md`, `README.md`) remain agent-editable — keeping them current IS the agent's job.
- Milan's step-by-step manual is `docs/BUILD_GUIDE.md`; the agent keeps it accurate as reality diverges from plan.

## Doc map — where every fact lives (no duplication)

| Question | Doc |
|---|---|
| What are we building, for whom, what's in/out of scope | `docs/PRD.md` |
| Stack, architecture, repo layout, design decisions + rationale | `docs/TRD.md` |
| Dashboard pages, navigation, README structure, visual style | `docs/APP_FLOW_UIUX.md` |
| S3 key layout, Postgres DDL, pandera rules, idempotency contract | `docs/BACKEND_SCHEMA.md` |
| Build order, phase checklists, exit criteria, stretch items | `docs/IMPLEMENTATION_PLAN.md` |
| HOW Milan does each step himself (DIY walkthrough, pitfalls, self-checks) | `docs/BUILD_GUIDE.md` |
| Where work stands RIGHT NOW / how to resume | `PROGRESS.md` |

**Rule:** each fact lives in exactly one doc; other docs point to it. Don't restate schema in the TRD or scope in the plan.

## On-boarding order (new session / new agent)

1. Read this file.
2. Read `PROGRESS.md` — current phase, last completed step, exact next action, open blockers. **The "Resume here" section overrides any stale assumption.**
3. Read the active phase's checklist in `docs/IMPLEMENTATION_PLAN.md` — ticked boxes are authoritative; never redo ticked work.
4. Read other docs only as the task requires (map above).
5. Confirm understanding of the next step with Milan before writing code.

## Hard rules

1. **No git operations.** Never run `git commit/push/pull/reset` or anything mutating repo state or GitHub. Milan handles all git via GitHub Desktop. Creating/editing files is unrestricted.
2. **Update the docs after EVERY run/exchange, then await Milan's next instruction.** Concretely, before ending any turn where something changed: (a) log Milan's request verbatim + timestamp in PROGRESS.md's Request log, (b) append what was completed to the Change log and refresh "Resume here", (c) once Milan confirms/accepts a piece of work, fold any new durable knowledge into the correct permanent doc (decision → TRD; scope → PRD; schema → BACKEND_SCHEMA; how-to correction → BUILD_GUIDE; convention → this file) — write only what's new, never duplicate. Then stop and wait; do not start the next piece of work unprompted. (Convention inherited from ModuNote's CLAUDE.md/session_context system.)
3. **No secrets in code or committed files.** Credentials via env vars (`.env` locally — gitignored; GitHub Actions Secrets in CI). `.env.example` documents required vars without values.
4. **Idempotency is sacred.** Any pipeline step must be safely rerunnable. Manifest row (`processed_sessions`) is written only after all loads for a session succeed.
5. **Business logic stays Prefect-free.** Only `src/pitwall/flows.py` imports Prefect; `transform`/`aggregate`/etc. are plain testable functions. Only `storage.py`/`warehouse.py` touch cloud services.
6. **Respect OpenF1 limits** (3 req/s, 30 req/min) — all HTTP goes through `openf1_client.py`; never call `httpx` directly elsewhere.
7. **Every documented data impurity gets a fixture test** in `tests/` when its handling is implemented.
8. **Scope changes go to `docs/PRD.md` first.** Roadmap/stretch ideas live only in IMPLEMENTATION_PLAN.md "Stretch" (pre-README) / README Roadmap (once it exists).

## Conventions

- Python 3.12, `requirements.txt` pinned, `ruff` for lint+format (config in `pyproject.toml`).
- Config only via `src/pitwall/config.py` (env-driven) — no scattered constants.
- Tests with `pytest`; HTTP mocked with `respx`; small real API fixtures checked into `tests/fixtures/`.
- `dev/` vs `prod/` S3 prefixes; never write to `prod/` from a local machine.
- Run pipeline locally: `python -m pitwall.flows` (uses `.env`).

## Context-window / thread-switch protocol

- Treat **~15% context remaining** as the hard trigger (or the moment Milan says context is low): stop new work, update `PROGRESS.md` "Resume here" (last completed step, exact next action, open decisions, files in scope), tick IMPLEMENTATION_PLAN boxes, then tell Milan.
- On resume: PROGRESS.md → active phase checklist → confirm with Milan. Never repeat ticked work.
