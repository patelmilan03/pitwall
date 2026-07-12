# PROGRESS.md — PitWall Live Status

> The single live record of where work stands. **Updated immediately after every completed change — no batching.** If a session dies mid-task, this file is how the next session resumes without loss.

## Update protocol (for any agent/session)

1. When Milan sends a request that changes the project (feature, fix, doc change, decision), append it **verbatim** to the **Request log** below: `[YYYY-MM-DD HH:MM] <exact wording>`. Do not paraphrase. (ModuNote convention.)
2. The moment a change is completed (file written, test passing, step verified — whether Milan built it or the agent updated docs), append a line to the **Change log**: `[YYYY-MM-DD HH:MM] <what was completed> — <files touched>`.
3. Keep the **Resume here** block permanently current: overwrite it after each change (logs are append-only history; Resume here is present-tense state).
4. When a phase's exit criterion passes, tick its boxes in `docs/IMPLEMENTATION_PLAN.md` and note the phase completion here.
5. **End of every run/exchange:** finish these doc updates, then STOP and await Milan's next instruction — no unprompted next steps.
6. Never delete or truncate the logs.
7. Milan builds the code himself (CLAUDE.md "Working mode") — this file still tracks HIS progress; he or the agent updates it after each work block.

---

## Resume here (current state)

- **Phase:** 0 — Prep (in progress — repo skeleton done; Milan's accounts + smoke test remain)
- **Last completed:** Repo skeleton built and verified — `from pitwall.config import settings` imports and all files byte-compile (2026-07-11).
- **Exact next action:** **Milan's account-setup half of Phase 0** (still open in IMPLEMENTATION_PLAN): create Backblaze B2 private bucket `pitwall-data` + scoped app key (note S3 endpoint URL); create Supabase `pitwall` project (grab the Supavisor **session-pooler** `DATABASE_URL`); create the **public** GitHub repo `pitwall`; add the five Actions Secrets (`S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET`, `DATABASE_URL`). Then Milan sets up a Python 3.12 venv + `pip install -r requirements-dev.txt`, copies `.env.example` → `.env`, fills real values, and **Milan runs the manual smoke test himself** (OpenF1 GET + one S3 write + Postgres connect — walkthrough in `docs/BUILD_GUIDE.md` Phase 0) to close Phase 0.
- **Open decisions:** none. (Note: local machine has Python **3.13.1** globally, no pytest; project targets **3.12** — Milan should create the 3.12 venv before installing pinned deps. Global-interpreter smoke test of config import passed regardless.)
- **Blockers:** manual smoke test + Phase 1 real-service work need Milan's credentials in `.env`. Pure-logic Phase 1 code (client/key builders) can be written and unit-tested before creds exist.
- **Files in scope next:** `openf1_client.py` + `storage.py` key builders + their tests — **written by Milan** following `docs/BUILD_GUIDE.md` Phase 1 (pure logic, needs no creds). Agent reviews on request only (CLAUDE.md Working mode, adopted 2026-07-11 AFTER the skeleton was agent-built under the old mode).

### Skeleton created this session (2026-07-11)
`src/pitwall/` — `__init__.py`, `config.py` (real: pydantic-settings, env-driven, `require_storage/require_warehouse` guards), plus docstring stubs `openf1_client.py`, `extract.py`, `schemas.py`, `transform.py`, `aggregate.py`, `storage.py`, `warehouse.py`, `export.py`, `flows.py`. `dashboard/app.py` stub. `tests/test_config.py` (4 tests) + `tests/fixtures/.gitkeep`. Root: `requirements.txt`, `requirements-dev.txt`, `.env.example`, `.gitignore`, `pyproject.toml` (ruff + pytest `pythonpath=["src"]` + setuptools src layout).

## Phase status

| Phase | Status |
|---|---|
| 0 — Prep | 🟡 In progress (skeleton done; accounts + smoke test remain) |
| 1 — Extract | 🔴 Not started |
| 2 — Transform/Validate/Load | 🔴 Not started |
| 3 — Orchestrate/Schedule | 🔴 Not started |
| 4 — Serve/Showcase | 🔴 Not started |
| Stretch | ⚪ Locked until v1 green |

## Request log (verbatim, append-only)

```
[2026-07-10 --:--] "1. id like to do this project myself, with minimal help from agents. So update the readmes accordingly and give detailed guides for me to do them myself. 2. If not already added, Add instructions to update the readmes after every run awaiting next user instructions. 3. Take reference from project modunote about how to handle readmes"
```

## Change log (append-only)

```
[2026-07-10 --:--] Project scoped and approved: OpenF1 F1-telemetry pipeline, Prefect on GitHub Actions, S3 + Supabase, Streamlit dashboard. Source APIs verified (OpenF1 free/keyless; rate limits 3 req/s, 30 req/min).
[2026-07-10 --:--] Planning docs created — docs/PRD.md, docs/TRD.md, docs/APP_FLOW_UIUX.md, docs/BACKEND_SCHEMA.md, docs/IMPLEMENTATION_PLAN.md, CLAUDE.md, PROGRESS.md.
[2026-07-10 --:--] Doability + compatibility re-verification (no-card constraint): storage switched AWS S3 → Backblaze B2 (S3-compatible boto3, 10GB free, no card; AWS requires card + 6-month account auto-close); Supabase must be accessed via IPv4 Supavisor session pooler from GitHub Actions/Streamlit; Prefect 3 confirmed serverless via ephemeral mode; noted GH Actions 60-day cron auto-disable + Supabase 7-day pause. Docs updated: TRD (§1 storage row, §3 secrets, new §6 compatibility notes), PRD (constraints, risks), BACKEND_SCHEMA (§1), IMPLEMENTATION_PLAN (Phase 0). Awaiting GO.
[2026-07-10 --:--] Final pre-build decisions locked: B2 confirmed over AWS (6-month free-plan auto-close + paid-plan leaked-key billing risk), repo public day one, Prefect Cloud deferred to Stretch (IMPLEMENTATION_PLAN updated). Still awaiting GO.
[2026-07-11 --:--] GO received. Phase 0 repo skeleton built — src/pitwall/{__init__,config}.py + docstring stubs (openf1_client, extract, schemas, transform, aggregate, storage, warehouse, export, flows), dashboard/app.py, tests/test_config.py + fixtures/.gitkeep, requirements.txt, requirements-dev.txt, .env.example, .gitignore, pyproject.toml (ruff + pytest src layout). Verified: `from pitwall.config import settings` imports OK; all files byte-compile. IMPLEMENTATION_PLAN skeleton box ticked. (pytest not run — not in global interpreter; runs after Milan's venv install.)
[2026-07-11 --:--] WORKING MODE CHANGE (Milan's request): Milan self-builds all code; agent = mentor/reviewer, docs-only writes unless a piece is explicitly handed over. Created docs/BUILD_GUIDE.md (per-phase DIY walkthrough: steps, snippets ≤5 lines, self-checks, pitfalls, when-to-ask-the-agent). CLAUDE.md: new "Working mode" section, docs-after-every-run-then-await-instructions rule, ModuNote-style verbatim Request log adopted here. IMPLEMENTATION_PLAN standing rules + STARTUP_PROMPT.md aligned to mentor mode.
```
