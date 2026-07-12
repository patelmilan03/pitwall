# PitWall — Backend Schema

> Single source of truth for storage layouts. Three stores: S3 data lake (raw/clean/exports), Supabase Postgres warehouse (aggregates + ops), and the manifest that makes runs idempotent.

## 1. S3 data lake layout

Bucket: `pitwall-data` (name configurable via `S3_BUCKET`) on Backblaze B2, accessed through the S3-compatible API (`S3_ENDPOINT_URL`); bucket is **private**. Env prefix first: `prod/` or `dev/`.

```
{env}/raw/season={year}/meeting_key={mk}/session_key={sk}/{dataset}.json.gz
{env}/clean/season={year}/meeting_key={mk}/session_key={sk}/{dataset}.parquet
{env}/exports/season={year}/{gp_slug}_{session_type}.xlsx
```

`dataset` ∈ `sessions | meetings | drivers | laps | stints | pit | position | weather | car_data`.
`car_data` (3.7 Hz telemetry, the big one) is additionally split per driver in raw: `car_data_driver={driver_number}.json.gz`.

- **raw** = byte-exact API responses, gzipped. Written once per session; overwriting the same key on reprocess is safe.
- **clean** = validated, typed Parquet (snappy). One file per dataset per session — partition-pruning story without over-engineering.

## 2. Postgres warehouse (Supabase)

Aggregates only — full-resolution telemetry stays in the lake (500 MB free-tier cap). All DDL is bootstrapped by `warehouse.py` (`CREATE TABLE IF NOT EXISTS`); loads are `INSERT … ON CONFLICT … DO UPDATE` (idempotent).

### Dimensions

```sql
CREATE TABLE dim_meetings (
    meeting_key      INT PRIMARY KEY,          -- OpenF1 natural key
    season           INT NOT NULL,
    meeting_name     TEXT NOT NULL,            -- "Singapore Grand Prix"
    circuit_name     TEXT,
    country_name     TEXT,
    date_start       TIMESTAMPTZ
);

CREATE TABLE dim_sessions (
    session_key      INT PRIMARY KEY,
    meeting_key      INT NOT NULL REFERENCES dim_meetings(meeting_key),
    session_type     TEXT NOT NULL,            -- Practice / Qualifying / Race / Sprint
    session_name     TEXT NOT NULL,
    date_start       TIMESTAMPTZ,
    date_end         TIMESTAMPTZ
);

CREATE TABLE dim_drivers (
    driver_number    INT NOT NULL,
    session_key      INT NOT NULL REFERENCES dim_sessions(session_key),
    full_name        TEXT,
    name_acronym     TEXT,                     -- VER, HAM …
    team_name        TEXT,
    team_colour      TEXT,                     -- hex, used by dashboard
    PRIMARY KEY (driver_number, session_key)   -- drivers/teams change across sessions
);
```

### Facts

```sql
CREATE TABLE fact_laps (
    session_key      INT NOT NULL REFERENCES dim_sessions(session_key),
    driver_number    INT NOT NULL,
    lap_number       INT NOT NULL,
    lap_duration_s   NUMERIC(8,3),             -- NULL on in/out laps (documented impurity)
    sector1_s        NUMERIC(7,3),
    sector2_s        NUMERIC(7,3),
    sector3_s        NUMERIC(7,3),
    speed_trap_kmh   NUMERIC(6,1),
    is_pit_out_lap   BOOLEAN NOT NULL DEFAULT FALSE,
    -- windowed aggregates computed from 3.7 Hz car_data over the lap:
    top_speed_kmh    NUMERIC(6,1),
    avg_throttle_pct NUMERIC(5,2),
    brake_applied_pct NUMERIC(5,2),            -- % of samples with brake on
    avg_gear         NUMERIC(4,2),
    PRIMARY KEY (session_key, driver_number, lap_number)
);

CREATE TABLE fact_stints (
    session_key      INT NOT NULL REFERENCES dim_sessions(session_key),
    driver_number    INT NOT NULL,
    stint_number     INT NOT NULL,
    compound         TEXT,                     -- SOFT / MEDIUM / HARD / INTER / WET
    lap_start        INT,
    lap_end          INT,
    tyre_age_at_start INT,
    avg_lap_s        NUMERIC(8,3),             -- degradation story
    PRIMARY KEY (session_key, driver_number, stint_number)
);

CREATE TABLE fact_session_weather (
    session_key      INT NOT NULL REFERENCES dim_sessions(session_key),
    bucket_start     TIMESTAMPTZ NOT NULL,     -- weather downsampled to 5-min buckets
    air_temp_c       NUMERIC(4,1),
    track_temp_c     NUMERIC(4,1),
    humidity_pct     NUMERIC(5,2),
    rainfall         BOOLEAN,
    wind_speed_ms    NUMERIC(5,2),
    PRIMARY KEY (session_key, bucket_start)
);

-- Downsampled telemetry for the dashboard's comparison page (1 Hz, best laps only)
CREATE TABLE fact_lap_telemetry_1hz (
    session_key      INT NOT NULL,
    driver_number    INT NOT NULL,
    lap_number       INT NOT NULL,
    sample_index     INT NOT NULL,             -- 0..n within lap
    speed_kmh        NUMERIC(6,1),
    throttle_pct     NUMERIC(5,1),
    brake            BOOLEAN,
    gear             SMALLINT,
    PRIMARY KEY (session_key, driver_number, lap_number, sample_index)
);
```

`fact_lap_telemetry_1hz` is loaded **only for each driver's best lap per session** — keeps Postgres far under the free cap while powering the comparison page. Full-resolution traces remain in clean-zone Parquet.

### Ops / manifest

```sql
CREATE TABLE processed_sessions (
    session_key      INT PRIMARY KEY,
    processed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    pipeline_version TEXT NOT NULL,            -- bump to force reprocess on logic change
    raw_row_count    BIGINT,
    clean_row_count  BIGINT,
    rows_dropped     BIGINT                    -- cleaning visibility for the dashboard
);

CREATE TABLE etl_runs (
    run_id           TEXT PRIMARY KEY,          -- Prefect flow-run id
    triggered_by     TEXT NOT NULL,             -- cron | backfill | manual
    started_at       TIMESTAMPTZ NOT NULL,
    finished_at      TIMESTAMPTZ,
    status           TEXT NOT NULL,             -- running | success | failed
    sessions_processed INT DEFAULT 0,
    rows_loaded      BIGINT DEFAULT 0,
    error_summary    TEXT
);
```

**Idempotency contract:** a session's `processed_sessions` row is inserted only after all its warehouse loads and exports succeed. Discovery = OpenF1 completed sessions minus manifest keys, so crashed runs self-heal on the next execution. Reprocessing after logic changes = bump `pipeline_version`, delete affected manifest rows (or a `--force` flag).

## 3. pandera contracts (source of truth: `src/pitwall/schemas.py`)

One `DataFrameSchema` per clean dataset. Representative rules — `laps`: `lap_duration_s` nullable but `> 30 and < 600` when present; `lap_number ≥ 1`; unique on (driver, lap). `car_data`: `speed 0–400`, `throttle 0–104` (OpenF1 quirk: >100 values exist — documented), `gear -1..8`, timestamps strictly increasing after cleaning, no duplicate (driver, date) pairs. Violations raise → flow fails → alert.
