# PitWall — Implementation Plan

> The standing build order. Tick boxes here as work completes (PROGRESS.md holds the live "where are we / resume here" state; this file holds the plan). One phase at a time; a phase is done only when its **exit criterion** passes.

## Phase 0 — Prep (one evening, mostly Milan's accounts)

- [ ] Create Backblaze account (no card) → **private** B2 bucket `pitwall-data` + application key scoped to that bucket; note the S3 endpoint URL
- [ ] Create Supabase project `pitwall` → note `DATABASE_URL` = **Supavisor session-pooler string** (direct host is IPv6-only and fails from GitHub Actions — TRD §6)
- [ ] (Optional) Prefect Cloud free workspace → `PREFECT_API_KEY` (not required — ephemeral mode works serverless)
- [ ] Create GitHub repo `pitwall` (public — required for unlimited free Actions minutes + Streamlit Cloud) — Milan handles all git per the no-git-ops rule
- [ ] Add GitHub Actions Secrets: `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET`, `DATABASE_URL` (+ optional Prefect)
- [x] Repo skeleton: folder layout per TRD §4, `requirements*.txt`, `.gitignore`, `.env.example`, `config.py`, ruff config
- [ ] Manual smoke: hit `https://api.openf1.org/v1/sessions?year=2025` from Python, write one test object to S3, connect to Postgres

**Exit criterion:** `python -c "from pitwall.config import settings"` works locally; B2 (via boto3) + Postgres (via pooler) reachable with env creds.

## Phase 1 — Extract (Day 1)

- [ ] `openf1_client.py`: httpx client with 3 req/s + 30 req/min throttle, jittered backoff on 429/5xx, per-driver paging for `car_data`
- [ ] `extract.py`: session discovery (completed sessions vs manifest) + land all datasets to raw zone (gzipped JSON, keys per BACKEND_SCHEMA §1)
- [ ] `storage.py`: S3 helpers + key builders
- [ ] `warehouse.py`: DDL bootstrap + `processed_sessions` / `etl_runs` read/write
- [ ] Tests: client throttling/backoff (respx), key builders; check in small fixture responses
- [ ] Manual run: extract one full 2025 race session end-to-end into `dev/raw/`

**Exit criterion:** one complete race session (incl. all drivers' car_data) in the raw zone; rerunning is a safe no-op/overwrite; tests green.

## Phase 2 — Transform, validate, aggregate, load (Day 2 — the heart)

- [ ] `schemas.py`: pandera contracts per dataset (rules per BACKEND_SCHEMA §3)
- [ ] `transform.py`: raw → clean (typing, dedupe, ordering, null policy for in/out laps, drop-count accounting)
- [ ] Clean-zone Parquet writes
- [ ] `aggregate.py`: lap-level telemetry windowing (top speed, avg throttle, brake %), stint summaries, 5-min weather buckets, 1 Hz best-lap telemetry downsample
- [ ] Warehouse upserts (idempotent) + manifest write as the final step
- [ ] `export.py`: per-session xlsx to exports zone
- [ ] Tests: every documented impurity gets a fixture test (nulls, dupes, out-of-order, schema drift); aggregate math spot-checks
- [ ] Manual run: full local pipeline on the Phase-1 session; verify rows in Postgres + xlsx in S3

**Exit criterion:** `SELECT * FROM fact_laps` shows plausible data for the demo session; rerun produces identical row counts (idempotency proven); tests green.

## Phase 3 — Orchestrate, schedule, alert (Day 3 morning)

- [ ] `flows.py`: Prefect flow + tasks (retries=3, task-level logging, `etl_runs` bookkeeping)
- [ ] `.github/workflows/pipeline.yml`: cron `0 6 * * *` + `workflow_dispatch(season, meeting_key?)` for backfill; Python setup, cached deps, secrets → env
- [ ] Failure alerting: on-failure step opens/updates GitHub issue labelled `pipeline-failure`
- [ ] Backfill 2024–2025 seasons via dispatch (rate-limit-friendly: one meeting per run if needed)
- [ ] Let the cron run overnight untouched

**Exit criterion:** a green **scheduled** (not manual) run visible in the public Actions tab; a forced failure produces an issue.

## Phase 4 — Serve & showcase (Day 3 afternoon)

- [ ] `dashboard/app.py`: three pages per APP_FLOW_UIUX.md (Session Explorer → Comparison → Health)
- [ ] Deploy to Streamlit Community Cloud (read-only Postgres creds via Streamlit secrets)
- [ ] README: pitch, badges (Actions status, dashboard link), mermaid architecture diagram, 2 screenshots, before/after messy-data sample, stack table, setup, decision log pointer
- [ ] Resume bullet drafted from live numbers (sessions, rows, runs)

**Exit criterion:** recruiter path works cold: README → badge → Actions history → dashboard, all public.

## Stretch (only after v1 is fully green)

- [ ] **Prefect Cloud dashboard** (free tier, no card) — decided 2026-07-10: skipped for v1, adopt post-v1. Create workspace, set `PREFECT_API_URL` + `PREFECT_API_KEY` secrets; flows then report to the hosted UI with zero code changes. Any agent picking up post-v1 work should suggest this first.
- [ ] Auto-close `pipeline-failure` issue on next green run
- [ ] Data-quality report artifact per run (pandera summary → Actions artifact)
- [ ] dbt for the aggregate layer (big resume keyword; refactor `aggregate.py` into models)
- [ ] Dockerfile (talking point; Actions doesn't need it)
- [ ] Tyre-degradation analysis page

## Standing rules

- **Milan writes the code; the agent mentors/reviews and maintains docs only** (CLAUDE.md "Working mode", 2026-07-11). Step-by-step how-to for every box: `docs/BUILD_GUIDE.md`. Milan runs all git operations (GitHub Desktop) — mirrored from ModuNote convention.
- After each phase: update PROGRESS.md, tick boxes here, run tests, then Milan commits.
- Scope changes land in PRD.md first, then here. No silent scope creep.
