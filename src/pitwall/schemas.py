"""pandera contracts — one DataFrameSchema per clean dataset.

The validation gate between extract and load: a failed check raises, fails the
flow, and surfaces the exact offending column/row. Rules per BACKEND_SCHEMA §3.

Implemented in Phase 2 (see docs/IMPLEMENTATION_PLAN.md).
"""
