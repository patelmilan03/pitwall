"""Throttled httpx client for the OpenF1 API (the ONLY module that calls OpenF1).

Enforces ≤3 req/s and ≤30 req/min with jittered exponential backoff on 429/5xx,
and pages telemetry endpoints (``car_data``) per driver to keep responses bounded.

Implemented in Phase 1 (see docs/IMPLEMENTATION_PLAN.md).
"""
