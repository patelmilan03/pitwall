"""Skeleton-level tests: config imports and credential guards behave.

Verifies the Phase 0 exit criterion programmatically (`from pitwall.config ...`).
Passing `_env_file=None` + explicit kwargs makes these independent of any local
`.env` or ambient environment.
"""

import pytest

from pitwall.config import Settings, settings


def test_settings_importable_with_defaults():
    # The module-level singleton must import in a fresh checkout (no .env needed).
    assert settings.s3_bucket == "pitwall-data"
    assert settings.pitwall_env == "dev"
    assert settings.s3_prefix == "dev/"
    assert settings.openf1_base_url.startswith("https://")


def test_s3_prefix_follows_env():
    assert Settings(_env_file=None, pitwall_env="prod").s3_prefix == "prod/"
    assert Settings(_env_file=None, pitwall_env="prod").is_prod is True


def test_require_storage_raises_when_unset():
    s = Settings(
        _env_file=None,
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
    )
    with pytest.raises(RuntimeError, match="storage env vars"):
        s.require_storage()


def test_require_warehouse_raises_when_unset():
    s = Settings(_env_file=None, database_url=None)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        s.require_warehouse()
