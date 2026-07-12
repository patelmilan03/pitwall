# PitWall — Self-Build Guide (Milan's DIY walkthrough)

> **You (Milan) write every line of code.** This guide gives per-phase steps, hints, self-checks, and pitfalls — not finished code. Illustrative snippets are ≤5 lines on purpose. When stuck >30 min on one step, ask the agent to *explain or review*, not to write it (see CLAUDE.md working mode).
> Checklists/exit criteria live in `IMPLEMENTATION_PLAN.md`; schema details in `BACKEND_SCHEMA.md`; gotchas in `TRD.md §6`. This guide tells you **how** to do each box.

---

## Phase 0 — Accounts & skeleton (one evening)

### 0.1 Backblaze B2 (storage)
1. Sign up at backblaze.com (email only, no card). In the left menu: **B2 Cloud Storage → Buckets → Create a Bucket** → name `pitwall-data`, **Private**, encryption off, object lock off.
2. **Application Keys → Add a New Application Key** → restrict to bucket `pitwall-data`, read+write. Copy `keyID` + `applicationKey` NOW (shown once).
3. Note the bucket's **Endpoint** shown on the bucket page (e.g. `s3.us-west-004.backblazeb2.com`). Your `S3_ENDPOINT_URL` = `https://` + that.
4. Self-check with boto3: `boto3.client("s3", endpoint_url=..., aws_access_key_id=keyID, aws_secret_access_key=appKey).list_buckets()` should return your bucket.

### 0.2 Supabase (warehouse)
1. Create project `pitwall` (free tier). Save the DB password you set.
2. Get the connection string: **Connect (top bar) → Session pooler** — it looks like `postgresql://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:5432/postgres`. **Never use the "Direct connection" string** — IPv6-only, dies on GitHub Actions (TRD §6.2).
3. Self-check: `psql` or a 3-line `sqlalchemy` script running `SELECT 1`.

### 0.3 GitHub repo
1. Create **public** repo `pitwall` on github.com. Clone via GitHub Desktop into this folder's parent (or init from the existing folder).
2. **Settings → Secrets and variables → Actions** → add: `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET`, `DATABASE_URL`.

### 0.4 Local environment (Windows)
```powershell
cd "C:\Milan\Code\resume projects\pitwall"
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install httpx boto3 pandas pandera pyarrow prefect sqlalchemy psycopg2-binary openpyxl python-dotenv
pip install pytest respx ruff   # dev deps
pip freeze > requirements.txt   # then split dev deps into requirements-dev.txt by hand
```

### 0.5 Skeleton files you create by hand
- Folder tree per `TRD.md §4` (empty `__init__.py` files included).
- `.gitignore`: `.venv/`, `.env`, `__pycache__/`, `*.pyc`, `.pytest_cache/`.
- `.env.example` listing the 5 secret names with dummy values; copy to `.env` with real values.
- `config.py`: one `Settings` class (plain class or `dataclass`) reading `os.environ` (load `.env` via `python-dotenv`), fields: the 5 secrets + `env_prefix` (`dev`/`prod`, default `dev`) + `openf1_base_url`.
- `pyproject.toml` with a `[tool.ruff]` block (line-length 100 is fine).

**Pitfalls:** pooler string uses username `postgres.<projectref>`, not `postgres` — copy it exactly. B2 keys are shown once. Don't commit `.env` (check GitHub Desktop's staged list before your first commit).

---

## Phase 1 — Extract (Day 1)

### 1.1 Explore the API first (30 min, browser only)
Open these and read the JSON shapes — this is your schema research:
- `https://api.openf1.org/v1/sessions?year=2025`
- `.../v1/laps?session_key=<pick one>&driver_number=1`
- `.../v1/car_data?session_key=...&driver_number=1&speed>=0` (big!)
- also: `meetings`, `drivers`, `stints`, `pit`, `position`, `weather`.
Note which fields are null/missing — write them down; they become Phase 2 cleaning rules and test fixtures.

### 1.2 `openf1_client.py`
- One class wrapping `httpx.Client`, single public method `get(endpoint, **params) -> list[dict]`.
- Throttle: record request timestamps in a `collections.deque`; before each request, sleep until you're under 3/sec AND 30/min. Simple and testable — no library needed.
- Backoff: on 429/5xx, retry up to 5× with `sleep(2**attempt + random.random())`.
- `car_data` responses can be huge → always request per driver, and if a response errors/times out, split the time range in half and recurse (or filter with `date>` / `date<` params).
- Test with `respx`: assert 3 rapid calls take ≥~0.66s (throttle works) and that a mocked 429 then 200 succeeds.

### 1.3 `storage.py`
- `boto3.client("s3", endpoint_url=settings.s3_endpoint_url, ...)`.
- Key-builder functions implementing `BACKEND_SCHEMA §1` exactly (write tests for them — cheap and catches typos forever).
- `put_json_gz(key, obj)` (gzip via `gzip.compress(json.dumps(...).encode())`), `put_bytes`, `get_json_gz`.

### 1.4 `warehouse.py` (bootstrap part only)
- `ensure_schema()`: run the `CREATE TABLE IF NOT EXISTS` DDL from `BACKEND_SCHEMA §2` (paste it as a constant; executing it repeatedly is safe).
- `get_processed_session_keys() -> set[int]`, plus insert helpers you'll finish in Phase 2.

### 1.5 `extract.py`
- `discover_new_sessions()`: fetch `/sessions?year=<current>`, keep sessions whose `date_end` < now (completed), subtract manifest keys.
- `extract_session(session_key)`: for each dataset, fetch → `put_json_gz` to `raw/`. car_data loops over the session's drivers.
- A `__main__` block (or small CLI arg) to run it for one hardcoded session_key.

**Self-check (exit):** pick one 2025 race, run extract, then list the bucket — you should see all datasets under `dev/raw/season=2025/...`, car_data split per driver. Re-run: no errors, keys overwritten. `pytest` green.
**Pitfalls:** OpenF1 uses `session_key`/`meeting_key` as ints — keep them ints end-to-end. Timestamps are ISO strings with timezone — parse with `datetime.fromisoformat`. Don't fetch all drivers' car_data in parallel — you'll blow the rate limit; sequential is fine.

---

## Phase 2 — Transform, validate, aggregate, load (Day 2 — the heart)

### 2.1 `schemas.py` (pandera) — write these BEFORE transform
One `pandera.DataFrameSchema` per dataset using the rules in `BACKEND_SCHEMA §3`. Start strict, loosen only when a real session fails a rule you decide is legitimate (document each loosening as a comment — interview material).

### 2.2 `transform.py`
Per dataset: `raw json → pd.DataFrame → clean → schema.validate(df) → parquet`.
Cleaning policies (each = one small function + one fixture test):
- **dedupe**: `drop_duplicates` on the natural key (laps: driver+lap_number; car_data: driver+date).
- **ordering**: sort car_data by `date`; count and drop rows that go backwards in time.
- **typing**: explicit `astype` map; ISO strings → `pd.to_datetime(utc=True)`.
- **null policy**: in/out laps legitimately have null `lap_duration` — keep row, flag `is_pit_out_lap`; drop rows with null in *key* columns only. Track `rows_dropped` per dataset and return it (goes to the manifest).

### 2.3 `aggregate.py` — the windowed-aggregation story
The trick: laps give you time windows, car_data gives you 3.7 Hz samples. Assign each telemetry sample to its lap, then groupby:
1. From laps build per-driver interval frames (`date_start` of lap N to lap N+1).
2. Use `pd.merge_asof(car_data.sort_values("date"), lap_starts, by="driver_number", direction="backward")` to tag each sample with its lap_number.
3. `groupby(["driver_number","lap_number"]).agg(top_speed=("speed","max"), avg_throttle=("throttle","mean"), brake_pct=("brake","mean"), avg_gear=("n_gear","mean"))`.
Also: stint summaries (join stints to laps, mean lap time per stint), weather → `df.resample("5min", on="date")`, and the 1 Hz best-lap downsample (`df.iloc[::4]` after filtering to each driver's best lap — good enough, say why in a comment).

### 2.4 `warehouse.py` (loads)
- Upserts: build `INSERT INTO … VALUES … ON CONFLICT (pk cols) DO UPDATE SET …` with `sqlalchemy.text` + `executemany`-style parameter lists. Chunk rows (500/batch).
- Order: dims → facts → **manifest last** (idempotency contract, BACKEND_SCHEMA §2).

### 2.5 `export.py`
One xlsx per session via `pd.ExcelWriter(engine="openpyxl")`: sheets = Results (fact_laps summary), Stints, Weather. Upload bytes to `exports/`.

**Self-check (exit):** full local run on your Phase-1 session; in Supabase Table Editor, `fact_laps` shows ~50-70 laps/driver for a race with plausible durations (90–110 s); run twice → identical counts. Every documented impurity has a passing fixture test.
**Pitfalls:** OpenF1 throttle can exceed 100 (up to 104) — clamp or widen the check, don't drop. `merge_asof` requires sorted keys — sort both frames or it raises. Parquet timestamps: keep everything UTC-aware.

---

## Phase 3 — Orchestrate & schedule (Day 3 morning)

### 3.1 `flows.py`
- `@task(retries=3, retry_delay_seconds=30)` on extract/transform/load steps; one `@flow` composing them: discover → loop sessions → per-session tasks → manifest.
- Write `etl_runs` row at start (status `running`) and finish (success/failed) — use `prefect.runtime.flow_run.id` as `run_id`.
- No `PREFECT_API_URL` set anywhere → ephemeral mode just works (TRD §6.1).

### 3.2 `.github/workflows/pipeline.yml`
Structure (write it yourself; every block is a learning point):
- `on:` → `schedule: [cron: "0 6 * * *"]` + `workflow_dispatch:` with inputs `season` (string, optional) and `meeting_key` (optional).
- One job: checkout → `actions/setup-python` (3.12, `cache: pip`) → `pip install -r requirements.txt` → `python -m pitwall.flows` with `env:` mapping the 5 secrets (`${{ secrets.NAME }}`) + `ENV_PREFIX: prod` + dispatch inputs as env vars.
- Failure alert step: `if: failure()` → `uses: actions/github-script` (or `gh issue create` with `GH_TOKEN: ${{ github.token }}`) opening an issue labelled `pipeline-failure`.

### 3.3 Backfill & burn-in
- Extend discovery: if `SEASON` env is set, list that season's sessions instead of "new ones". Backfill 2024–2025 one meeting per dispatch run (rate-limit friendly).
- Force a failure once (temporarily bad secret) to see the issue appear; fix; then leave the cron alone overnight.

**Self-check (exit):** a green **scheduled** run in the public Actions tab that you didn't touch.
**Pitfalls:** cron is UTC and can fire minutes late — normal. `workflow_dispatch` inputs arrive as strings. A job that fails on secrets prints nothing useful — echo non-secret config early (never echo secrets).

---

## Phase 4 — Dashboard & README (Day 3 afternoon)

### 4.1 `dashboard/app.py`
- `pip install streamlit plotly` (add to requirements). Multipage: `st.Page`/`st.navigation` or a sidebar radio — either is fine.
- DB: `st.connection("postgresql", type="sql")` with the pooler URL in `.streamlit/secrets.toml` locally (gitignore it!) and in Streamlit Cloud's Secrets UI when deploying.
- Cache queries with `@st.cache_data(ttl=3600)`.
- Build pages per `APP_FLOW_UIUX.md`; charts with `plotly.express` (`line` for lap evolution, `timeline`-style bar for stints, overlaid `line` for telemetry compare).
- Run locally: `streamlit run dashboard/app.py`.

### 4.2 Deploy
share.streamlit.io → New app → repo `pitwall`, file `dashboard/app.py` → paste secrets → deploy. First build takes minutes.

### 4.3 README (the real landing page — structure in APP_FLOW_UIUX §4)
Badges: Actions status badge (from the workflow page → "Create status badge") + a dashboard link badge (shields.io static). Mermaid diagram of TRD §2. Two dashboard screenshots. The before/after messy-data table (5 raw rows vs cleaned — pull real ones from your data).

**Self-check (exit):** cold recruiter path works in an incognito browser: README → badge → Actions history → live dashboard.

---

## When to ask the agent (and for what)

✅ "Explain why merge_asof needs sorting" · "Review my transform.py for the idempotency contract" · "My Actions run fails at X, here's the log — what direction should I look?"
❌ "Write transform.py" — only if you explicitly decide to hand a piece over; the default is you build it.
