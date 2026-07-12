"""S3 (boto3) read/write helpers + key builders — one of two cloud-touching modules.

Wraps the S3-compatible endpoint (Backblaze B2 today) and builds every lake key
from the env prefix (``dev/`` | ``prod/``) per BACKEND_SCHEMA §1. Calls
``settings.require_storage()`` before any network I/O.

Implemented in Phase 1 (see docs/IMPLEMENTATION_PLAN.md).
"""
