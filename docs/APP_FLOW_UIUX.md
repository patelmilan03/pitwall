# PitWall — App Flow & UI/UX Design Brief

> Covers the two user-facing surfaces: the **Streamlit dashboard** (recruiters + F1 fans) and the **README** (the real landing page — most recruiters never leave it). The dashboard reads Postgres only; it never triggers pipeline work.

## 1. Design principles

1. **README-first** — the repo README is the primary UX. Architecture diagram, live badges, dashboard link, and a before/after messy-data sample must all be visible without scrolling past one screen of intro.
2. **Two-minute comprehension** — a recruiter should understand what the pipeline does, see proof it runs, and reach the dashboard within two minutes.
3. **Data does the talking** — charts over text; every dashboard page answers one concrete question.
4. **No auth, no state** — dashboard is public and read-only.

## 2. Dashboard navigation

Streamlit multipage app (sidebar navigation), three pages:

```
Sidebar
├── 🏁 Session Explorer      (default landing page)
├── 📊 Driver Comparison
└── 🩺 Pipeline Health
Global sidebar controls: Season → Grand Prix → Session (cascading selects, Postgres-driven)
```

### Page 1 — Session Explorer (landing)
**Question it answers:** "What happened in this session?"
- Header: GP name, session type, date, circuit; weather summary chips (air/track temp, rain).
- Lap-time evolution chart: line per driver, laps on x-axis, lap time on y-axis; pit stops as markers. Default: top 6 finishers pre-selected (all 20 lines is unreadable).
- Stint strategy bar: horizontal stacked bars per driver, coloured by tyre compound.
- Results table: position, driver, best lap, sectors, top speed, stops.
- Empty state (no data yet for selection): "This session hasn't been processed yet — pipeline runs daily" + link to Pipeline Health.

### Page 2 — Driver Comparison
**Question it answers:** "Where is driver A faster than driver B?"
- Controls: two driver selects + lap select (default: each driver's best lap).
- Telemetry traces (from clean-zone aggregates in Postgres, downsampled): speed, throttle %, brake, gear vs. lap distance — two overlaid lines per chart.
- Delta summary cards: lap-time delta, top-speed delta, avg corner-speed delta.
- This page is the wow-factor screenshot for the README.

### Page 3 — Pipeline Health
**Question it answers (for recruiters):** "Does this actually run unattended?"
- KPI cards: total sessions processed, total raw rows ingested, last successful run (UTC), data freshness (latest session date vs. today).
- Run-history table from `etl_runs`: run id, trigger (cron/backfill), sessions processed, rows loaded, duration, status.
- Validation stats: rows dropped by cleaning per session (proves the pandera/cleaning layer is real).
- Link out to the public GitHub Actions history.

## 3. Visual style

- Streamlit defaults + one accent: F1-ish red `#E10600` for primary chart lines/highlights; otherwise neutral. Dark theme via `.streamlit/config.toml` (telemetry reads better on dark).
- Charts: Plotly (interactive hover matters for telemetry traces). Consistent driver colours within a page.
- Every chart gets a one-line caption stating the aggregation ("3.7 Hz telemetry downsampled to 1 Hz for display").

## 4. README flow (the other UI)

Top-to-bottom: title + one-sentence pitch → badges (Actions status, last run, dashboard link) → architecture diagram (mermaid) → 2 dashboard screenshots → "The data problem" section with a real before/after cleaning sample (5 messy raw rows vs. cleaned) → stack table → local setup → design decisions (link to TRD).

## 5. Non-goals

No mobile-specific layout (Streamlit default responsiveness is acceptable), no custom CSS beyond theme config, no user preferences/persistence.
