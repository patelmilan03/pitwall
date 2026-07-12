"""Prefect flow + task definitions — the ONLY module that imports Prefect.

Thin orchestration over the business modules: discover → extract → validate →
clean → aggregate → load → export, with retries (3×), task-level logging, and
``etl_runs`` bookkeeping. Runs serverless via Prefect's ephemeral mode in CI
(TRD §6.1). Business logic lives in the imported modules, never here.

Run locally: ``python -m pitwall.flows`` (uses ``.env``).

Implemented in Phase 3 (see docs/IMPLEMENTATION_PLAN.md).
"""
