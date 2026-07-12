"""Cleaning: raw → clean (typing, dedupe, ordering, null policy, drop accounting).

Plain pandas functions (no Prefect, no cloud) so each documented impurity —
null telemetry values, duplicate/out-of-order timestamps, null in/out-lap
durations, missing drivers, schema drift — is covered by a fixture test.

Implemented in Phase 2 (see docs/IMPLEMENTATION_PLAN.md).
"""
