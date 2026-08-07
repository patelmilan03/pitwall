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

- **Phase:** 0 — Prep (offline half DONE + verified green; live half blocked on Milan's cloud accounts)
- **Last completed:** Phase-0 **offline verification PASSED** on Python 3.13.1 (2026-07-11): `.venv` created, full pinned dev stack installed clean (all cp313 wheels, exit 0), `from pitwall.config import settings` imports, **pytest 4/4 pass**, **ruff clean**.
- **PYTHON DECISION (agent call, evidence-based):** machine has **no 3.12, only 3.13.1**; the entire pinned stack (pandas 2.2.3, pyarrow 18.1, prefect 3.1.15, boto3, streamlit, psycopg2-binary 2.9.10) resolved and ran on 3.13. **Standardized on 3.13** — local venv + CI both 3.13. `requires-python` floor stays `>=3.12`. Docs updated (requirements.txt comment, BUILD_GUIDE Phase 0 `py -3.13` + Phase 3 setup-python 3.13). Overrides Milan's earlier "use 3.12" suggestion because 3.12 isn't installed and buys nothing here.
- **Exact next action:** **Milan's cloud-account half of Phase 0** (the ONLY thing left in Phase 0): Backblaze B2 private bucket `pitwall-data` + scoped app key (note S3 endpoint URL); Supabase `pitwall` project (grab the Supavisor **session-pooler** `DATABASE_URL`); public GitHub repo `pitwall` (repo now, secrets can wait for Phase 3); then copy `.env.example` → `.env` and fill real values. Then Milan runs the live smoke test himself (BUILD_GUIDE Phase 0: OpenF1 GET + one B2 write + Postgres connect).
- **Open decisions:** whether to fold two profile-gap options into docs as formal decisions (asked 2026-07-11, awaiting Milan): (a) use MongoDB Atlas for the raw JSON zone to back the unbacked résumé MongoDB claim; (b) elevate the tyre-degradation stretch to a small scikit-learn model to back the unbacked sklearn claim. Both optional, neither a shoehorn.
- **Blockers:** live smoke test + Phase 1 *live run/exit criterion* need creds in `.env` (B2 for raw landing, Supabase for the `processed_sessions` manifest read in discovery). GitHub secrets are Phase 3, not blocking now. All Phase 1 *code* (client, key builders, extract logic) is offline/mock-testable and can be written now with only the venv.
- **Files in scope next:** `openf1_client.py` + `storage.py` key builders + their `respx`/unit tests — **written by Milan** per `docs/BUILD_GUIDE.md` Phase 1. Agent reviews on request only (CLAUDE.md Working mode).

### Skeleton created this session (2026-07-11)
`src/pitwall/` — `__init__.py`, `config.py` (real: pydantic-settings, env-driven, `require_storage/require_warehouse` guards), plus docstring stubs `openf1_client.py`, `extract.py`, `schemas.py`, `transform.py`, `aggregate.py`, `storage.py`, `warehouse.py`, `export.py`, `flows.py`. `dashboard/app.py` stub. `tests/test_config.py` (4 tests) + `tests/fixtures/.gitkeep`. Root: `requirements.txt`, `requirements-dev.txt`, `.env.example`, `.gitignore`, `pyproject.toml` (ruff + pytest `pythonpath=["src"]` + setuptools src layout).

## Phase status

| Phase | Status |
|---|---|
| 0 — Prep | 🟡 Offline half done + verified green (3.13); cloud accounts + live smoke test remain (Milan) |
| 1 — Extract | 🔴 Not started |
| 2 — Transform/Validate/Load | 🔴 Not started |
| 3 — Orchestrate/Schedule | 🔴 Not started |
| 4 — Serve/Showcase | 🔴 Not started |
| Stretch | ⚪ Locked until v1 green |

## Request log (verbatim, append-only)

```
[2026-07-10 --:--] "1. id like to do this project myself, with minimal help from agents. So update the readmes accordingly and give detailed guides for me to do them myself. 2. If not already added, Add instructions to update the readmes after every run awaiting next user instructions. 3. Take reference from project modunote about how to handle readmes"
[2026-07-11 --:--] "1. ive finished phase 0, verify and smoke test it 2. Give steps for the next phase - manual vs agent-assisted for optimal studying/retention of the tech stack. 3. Flag: global Python is 3.13, project targets 3.12 — make the venv with 3.12. 4. Not yet done (flag if blocker for next phase): B2 bucket+key; Supabase pooler URL; public repo + 5 secrets; 3.12 venv + install + .env. 5. pytest not run (no venv). 6. Any stack suggestions vs my interview-prep/skills/profile plan — free to read those files."
```

## Change log (append-only)

```
[2026-07-10 --:--] Project scoped and approved: OpenF1 F1-telemetry pipeline, Prefect on GitHub Actions, S3 + Supabase, Streamlit dashboard. Source APIs verified (OpenF1 free/keyless; rate limits 3 req/s, 30 req/min).
[2026-07-10 --:--] Planning docs created — docs/PRD.md, docs/TRD.md, docs/APP_FLOW_UIUX.md, docs/BACKEND_SCHEMA.md, docs/IMPLEMENTATION_PLAN.md, CLAUDE.md, PROGRESS.md.
[2026-07-10 --:--] Doability + compatibility re-verification (no-card constraint): storage switched AWS S3 → Backblaze B2 (S3-compatible boto3, 10GB free, no card; AWS requires card + 6-month account auto-close); Supabase must be accessed via IPv4 Supavisor session pooler from GitHub Actions/Streamlit; Prefect 3 confirmed serverless via ephemeral mode; noted GH Actions 60-day cron auto-disable + Supabase 7-day pause. Docs updated: TRD (§1 storage row, §3 secrets, new §6 compatibility notes), PRD (constraints, risks), BACKEND_SCHEMA (§1), IMPLEMENTATION_PLAN (Phase 0). Awaiting GO.
[2026-07-10 --:--] Final pre-build decisions locked: B2 confirmed over AWS (6-month free-plan auto-close + paid-plan leaked-key billing risk), repo public day one, Prefect Cloud deferred to Stretch (IMPLEMENTATION_PLAN updated). Still awaiting GO.
[2026-07-11 --:--] GO received. Phase 0 repo skeleton built — src/pitwall/{__init__,config}.py + docstring stubs (openf1_client, extract, schemas, transform, aggregate, storage, warehouse, export, flows), dashboard/app.py, tests/test_config.py + fixtures/.gitkeep, requirements.txt, requirements-dev.txt, .env.example, .gitignore, pyproject.toml (ruff + pytest src layout). Verified: `from pitwall.config import settings` imports OK; all files byte-compile. IMPLEMENTATION_PLAN skeleton box ticked. (pytest not run — not in global interpreter; runs after Milan's venv install.)
[2026-07-11 --:--] WORKING MODE CHANGE (Milan's request): Milan self-builds all code; agent = mentor/reviewer, docs-only writes unless a piece is explicitly handed over. Created docs/BUILD_GUIDE.md (per-phase DIY walkthrough: steps, snippets ≤5 lines, self-checks, pitfalls, when-to-ask-the-agent). CLAUDE.md: new "Working mode" section, docs-after-every-run-then-await-instructions rule, ModuNote-style verbatim Request log adopted here. IMPLEMENTATION_PLAN standing rules + STARTUP_PROMPT.md aligned to mentor mode.
[2026-07-11 --:--] Phase-0 offline verification (agent-run, allowed as verification not code-authoring): created .venv on Python 3.13.1, installed requirements-dev.txt (full pinned stack resolved clean, cp313 wheels, exit 0), config import OK, pytest 4/4 pass, ruff clean. Decision: standardize on Python 3.13 (no 3.12 on machine; stack verified on 3.13). Docs updated: requirements.txt comment, BUILD_GUIDE Phase 0 venv cmd → py -3.13 + Phase 3 setup-python → 3.13. Live smoke test (B2 write + Postgres connect) still pending Milan's cloud accounts. Also surfaced (response, not yet in docs): Phase-1 blocker analysis (code writable now, live run needs B2+Supabase, GH secrets are Phase 3); manual-vs-agent split for Phase 1 retention; profile-gap stack options (MongoDB raw zone, sklearn stretch); re-raised the weekly data-engineering mock-interview kickoff per user-career-plan memory.
```
