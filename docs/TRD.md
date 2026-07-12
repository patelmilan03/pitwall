# PitWall — Technical Requirements Document

> Stack, architecture, repo layout, and every design decision with its rationale. The schema itself lives in `BACKEND_SCHEMA.md`; the build order in `IMPLEMENTATION_PLAN.md`.

## 1. Stack

| Concern | Choice | Why (interview answer) |
|---|---|---|
| Language | Python 3.12 | DE lingua franca; matches Milan's Python/FastAPI background |
| Extraction | `httpx` + custom throttled client | OpenF1 is a clean REST API — no Selenium needed. Checking for an API before reaching for browser automation is itself the talking point |
| Transformation | `pandas` | The core skill being showcased; volumes fit in memory per-session |
| Validation | `pandera` | Declarative schema contracts; lighter than Great Expectations, right-sized for one developer |
| File format | Parquet (`pyarrow`), partitioned | Columnar + compressed for millions of telemetry rows; partition pruning story |
| Lake storage | Backblaze B2 (10 GB free, **no card**) via `boto3` S3-compatible API | AWS free tier requires a card + auto-closes after 6 months — fails the no-membership constraint. B2 speaks the S3 API, so all code is boto3 and the resume line stays "S3-compatible object storage (boto3)". Swapping to real AWS S3 later = change endpoint + creds only. Buckets stay **private** (B2 public buckets require a card) |
| Warehouse | Supabase Postgres (free) | SQL surface for the dashboard + interview SQL story; Milan already knows Supabase |
| Orchestration | Prefect 3 (OSS) | Tasks, retries, structured logging, flow-run visibility — a real orchestrator without a server. Optional free Prefect Cloud workspace for the UI |
| Scheduling/compute | GitHub Actions (cron + `workflow_dispatch`) | Free, zero-maintenance, and the run history is **publicly visible proof** the pipeline works |
| Dashboard | Streamlit Community Cloud | Free public hosting, Python-native, reads Postgres directly |
| Exports | `openpyxl` xlsx to S3 | The "deliver to business users" artifact carried over from Portway |
| Testing | `pytest` + `respx` (httpx mocking) | Unit tests for cleaning logic on fixture data; no live API in tests |
| Lint/format | `ruff` | One tool, fast, standard |
| Dependencies | `requirements.txt` + `venv` (pinned) | Boring and universally understood; freshers get grilled on basics, not on uv |

## 2. Architecture

```
GitHub Actions (cron daily 06:00 UTC + manual backfill dispatch)
  └── Prefect flow: pitwall_pipeline
        ├── discover_sessions      → OpenF1 /sessions vs processed_sessions manifest
        │     └── (no new work → log + exit 0)
        ├── for each new session:
        │     ├── extract_raw      → raw JSON.gz → s3://…/raw/        (immutable)
        │     ├── validate_clean   → pandas clean + pandera gate
        │     ├── write_clean      → partitioned Parquet → s3://…/clean/
        │     ├── aggregate        → lap/stint/session-level metrics
        │     ├── load_warehouse   → idempotent upserts → Supabase Postgres
        │     └── export_xlsx      → session workbook → s3://…/exports/
        └── mark session processed in manifest (last step — see idempotency)
Failure  → GitHub Actions failure → auto-created GitHub issue + email
Serving  → Streamlit Cloud app ← reads Postgres
```

### Zones (medallion, right-sized)
- **raw/** — exact API responses, gzipped JSON, never mutated. Enables full reprocessing when cleaning logic improves.
- **clean/** — validated, typed, deduplicated Parquet, partitioned `season=/meeting_key=/session_key=/dataset=`.
- **warehouse** — Postgres aggregate tables only (Supabase 500 MB cap; see `BACKEND_SCHEMA.md`).
- **exports/** — per-session xlsx workbooks.

## 3. Key design requirements

1. **Idempotency** — reprocessing any session must be safe: raw writes are keyed by session (overwrite-same-key), warehouse loads are `INSERT … ON CONFLICT DO UPDATE`, and the manifest row is written only after all loads succeed. A crashed run reruns cleanly.
2. **Rate limiting** — client enforces ≤3 req/s and ≤30 req/min with jittered exponential backoff on 429/5xx; Prefect task retries (3×) on top. Telemetry endpoints are paged per-driver to keep responses bounded.
3. **Validation gates** — pandera schemas in `src/pitwall/schemas.py` are the contract between extract and load. A failed check raises, fails the flow, and surfaces the exact failing column/row in logs. Known impurities handled in cleaning (each becomes a test case): null telemetry channel values, duplicate timestamps, out-of-order samples, null lap durations (in/out laps), missing drivers, cross-season schema drift.
4. **Secrets** — GitHub Actions Secrets (`S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET`, `DATABASE_URL`, optional `PREFECT_API_KEY`). Provider-neutral names because storage is any S3-compatible endpoint (B2 today, AWS later). Locally via `.env` (gitignored) + `.env.example` committed. **No secret ever in code or committed config.**
5. **Config** — single `src/pitwall/config.py` reading env vars with sane defaults; no magic constants scattered in modules.
6. **Backfill** — `workflow_dispatch` inputs: `season`, optional `meeting_key`. Same flow, same idempotency; backfilling 2023–2025 is how demo data exists on day one.
7. **Alerting** — on job failure, a workflow step opens/updates a GitHub issue labelled `pipeline-failure` (and GitHub emails the owner). Recovery = next green run auto-closes it (stretch).

## 4. Repository layout

```
pitwall/
├── CLAUDE.md                    # AI/session context system (read first)
├── PROGRESS.md                  # live status — updated after every completed change
├── README.md                    # public face: diagram, badges, screenshots (built last)
├── docs/
│   ├── PRD.md  TRD.md  APP_FLOW_UIUX.md  BACKEND_SCHEMA.md  IMPLEMENTATION_PLAN.md
├── src/pitwall/
│   ├── __init__.py
│   ├── config.py                # env-driven settings
│   ├── openf1_client.py         # throttled httpx client + pagination
│   ├── extract.py               # session discovery + raw-zone landing
│   ├── schemas.py               # pandera contracts (one per dataset)
│   ├── transform.py             # cleaning: dedupe, ordering, typing, null policy
│   ├── aggregate.py             # windowed lap/stint/session metrics
│   ├── storage.py               # S3 (boto3) read/write helpers, key builders
│   ├── warehouse.py             # Postgres DDL bootstrap + idempotent upserts
│   ├── export.py                # xlsx workbook per session
│   └── flows.py                 # Prefect flow + task definitions (thin — logic lives above)
├── dashboard/
│   └── app.py                   # Streamlit (deployed from this repo path)
├── tests/
│   ├── fixtures/                # small real API response samples (checked in)
│   └── test_transform.py  test_client.py  test_aggregate.py …
├── .github/workflows/
│   └── pipeline.yml             # cron + workflow_dispatch(backfill) + failure alerting
├── requirements.txt  requirements-dev.txt
├── .env.example  .gitignore  pyproject.toml (ruff config)
```

**Layering rule:** `flows.py` may import everything; business modules (`transform`, `aggregate`, …) never import Prefect — they are plain, unit-testable functions. `storage`/`warehouse` are the only modules touching cloud services.

## 5. Environments

| Env | Compute | Storage | Notes |
|---|---|---|---|
| Local dev | venv, `python -m pitwall.flows` | localstack-free: real S3 dev prefix `dev/` + local Supabase or same DB with `dev_` schema | fast iteration |
| Production | GitHub Actions runner | S3 `prod/` prefix, Supabase `public` schema | cron + dispatch only |

## 6. Verified compatibility notes (checked 2026-07-10 — do not rediscover these)

1. **Prefect 3 needs no server in CI** — with no `PREFECT_API_URL` configured it starts an ephemeral in-memory API, so flows (with retries/logging) run fine inside a GitHub Actions job. Prefect Cloud (free tier, no card) is optional and only adds the hosted dashboard.
2. **Supabase from GitHub Actions/Streamlit Cloud MUST use the Supavisor session pooler** connection string. The direct `db.<ref>.supabase.co` host is IPv6-only since 2024 and GitHub Actions runners have no IPv6 — direct connections will hang/fail. `DATABASE_URL` = the pooler (session mode) string.
3. **GitHub Actions scheduled workflows are auto-disabled after 60 days without repo activity** (public repos). Mitigation: ongoing commits count, and the failure-alerting issue activity helps; if the repo goes dormant, re-enable with one click or add a keepalive step.
4. **Supabase free projects pause after ~1 week of inactivity** — the daily pipeline's DB writes count as activity, so a green cron also keeps the warehouse awake. If the pipeline is ever off for a week, unpause from the Supabase dashboard.
5. **AWS free tier requires a payment card (₹2/$1 verification) and new free-plan accounts auto-close after 6 months** — why B2 was chosen. Backblaze B2 needs no card for private buckets; public buckets would require one (we don't use public buckets).
6. All Python deps (`pandas`, `pandera`, `pyarrow`, `httpx`, `boto3`, `prefect`, `streamlit`, `plotly`, `openpyxl`, `sqlalchemy`/`psycopg2-binary`) are plain pip installs, compatible on Python 3.12; no compiled/native headaches on GitHub's ubuntu runners.

## 7. Out of scope (recorded so nobody re-litigates)

Streaming/Kafka (batch-after-session is correct for this source), dbt (aggregation layer is small; noted as stretch), Docker (Actions runner has Python; noted as stretch talking point), Airflow (Prefect chosen — lighter, no server).
