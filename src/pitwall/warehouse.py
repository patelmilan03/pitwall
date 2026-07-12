"""Postgres warehouse access — the other cloud-touching module.

Bootstraps DDL (``CREATE TABLE IF NOT EXISTS``, schema per BACKEND_SCHEMA §2),
performs idempotent ``INSERT … ON CONFLICT DO UPDATE`` loads, and reads/writes the
``processed_sessions`` manifest + ``etl_runs`` bookkeeping. Connects via the
Supavisor session pooler (TRD §6.2). Calls ``settings.require_warehouse()`` first.

Implemented in Phases 1–2 (see docs/IMPLEMENTATION_PLAN.md).
"""
