"""Session discovery + raw-zone landing.

Discovers completed OpenF1 sessions not yet in the ``processed_sessions`` manifest
and lands every dataset to the raw zone as gzipped JSON (keys per BACKEND_SCHEMA §1).

Implemented in Phase 1 (see docs/IMPLEMENTATION_PLAN.md).
"""
