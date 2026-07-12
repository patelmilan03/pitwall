"""Windowed lap/stint/session metrics computed from clean data.

Per-lap car_data windows (top speed, avg throttle, brake %, avg gear), stint
summaries, 5-minute weather buckets, and the 1 Hz best-lap telemetry downsample
that powers the comparison page. Pure functions — unit-tested with spot-checks.

Implemented in Phase 2 (see docs/IMPLEMENTATION_PLAN.md).
"""
