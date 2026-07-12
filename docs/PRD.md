# PitWall — Product Requirements Document

> Owner: Milan Patel · Status: Approved (2026-07-10) · Changes to scope go here first.

## 1. What is PitWall?

PitWall is an automated data-engineering pipeline that ingests Formula 1 telemetry and timing data from the free [OpenF1 API](https://openf1.org), cleans and validates it, stores it in a layered cloud data lake + warehouse, and serves aggregated race insights through a public dashboard. It runs unattended on a schedule and processes new race sessions as they appear.

## 2. Why does it exist? (Purpose & audience)

**Primary purpose:** a portfolio project demonstrating junior data-engineer competency, built as a direct upgrade of Milan's Portway experience (Selenium/govt-data extraction → ETL → AWS S3).

**Audiences, in priority order:**
1. **Recruiters / interviewers** — must be able to verify the pipeline works (public GitHub Actions run history), understand the architecture in <2 minutes (README diagram), and see the data (dashboard).
2. **Milan** — must learn: orchestration (Prefect), data validation (pandera), lake/warehouse layering, idempotent scheduled pipelines.
3. **F1-curious visitors** — the dashboard should be genuinely interesting to browse.

## 3. Product goals & success metrics

| Goal | Metric |
|---|---|
| Pipeline runs unattended | ≥30 consecutive scheduled runs without manual intervention |
| Real data volume story | ≥1 full race weekend of telemetry processed (millions of raw rows) |
| Verifiable to recruiters | Public repo, green Actions badge, live dashboard URL |
| Interview-ready narrative | Every layer (extract/validate/transform/load/orchestrate) has a documented design decision |
| Resume line | "Automated ETL pipeline: OpenF1 → pandas/pandera → S3 + Postgres, orchestrated with Prefect on GitHub Actions" |

## 4. Core features (v1 scope)

1. **Extract** — pull completed F1 sessions (laps, car telemetry, positions, pit stops, stints, weather, session/meeting/driver metadata) from OpenF1 via a rate-limit-respecting HTTP client (3 req/s cap). Raw responses land untouched in the S3 **raw zone**, partitioned by season/meeting/session.
2. **Clean & validate** — pandas transformations fixing real impurities (nulls in telemetry channels, duplicate/out-of-order timestamps, null lap durations on in/out laps, schema drift between seasons). Every cleaned dataset must pass a declarative **pandera** schema before it may proceed; failures abort the run loudly.
3. **Transform & aggregate** — lap-level and stint-level metrics (sector times, top speed, throttle/brake percentages, tyre stint summaries) computed from high-frequency telemetry via windowed aggregation; written as partitioned Parquet to the **clean zone** and as tables to Postgres.
4. **Load** — idempotent upserts into Supabase Postgres (warehouse). A `processed_sessions` manifest guarantees a session is never double-processed. A spreadsheet (xlsx) per-session export lands in S3 for the "deliver to business users" story.
5. **Orchestrate & schedule** — a Prefect flow (tasks with retries + logging) executed by a GitHub Actions cron: a light daily check discovers newly completed sessions and triggers full processing only when there is work. Manual `workflow_dispatch` supports historical backfill (2023 →) with parameters.
6. **Observe** — run failure opens a GitHub issue / sends email; PROGRESS.md and the Actions tab show pipeline health.
7. **Serve** — Streamlit dashboard (free Community Cloud) reading Postgres: session explorer, driver telemetry comparison, pipeline health page. See `APP_FLOW_UIUX.md`.

## 5. Non-goals (v1)

- No live/streaming ingestion during races (OpenF1 live tier is paid; batch-after-session is the design).
- No ML/predictions.
- No user accounts, no write access from the dashboard.
- No Airflow/Kafka/Spark — deliberately right-sized; the TRD records why.

## 6. Constraints

- **₹0 budget, no payment card anywhere** — every service free without a card on file (OpenF1, GitHub Actions on a public repo, Backblaze B2 private bucket via S3 API, Supabase free Postgres, Streamlit Community Cloud, Prefect OSS ephemeral mode). Verified 2026-07-10; details in TRD §6.
- **3-day weekend core build** + one prep evening; stretch items only after v1 is green end-to-end.
- OpenF1 rate limits: 3 req/s, 30 req/min — client must throttle and back off.
- Supabase free tier ~500 MB — warehouse holds **aggregates only**; raw/high-frequency data lives in S3 as Parquet.

## 7. Risks

| Risk | Mitigation |
|---|---|
| OpenF1 schema drift / downtime | pandera catches drift; raw zone preserves originals for reprocessing; retries + alerting |
| Storage provider change ever needed | storage code uses the boto3 S3 API → swap endpoint/creds (B2 ↔ AWS ↔ R2), no code change |
| F1 calendar gaps (no new sessions some weeks) | daily check is cheap/no-op; backfill guarantees demo data always exists |
