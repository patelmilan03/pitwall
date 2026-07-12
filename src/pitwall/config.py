"""Central, env-driven configuration for PitWall.

Every tunable and every secret is read here exactly once so no other module
reaches into ``os.environ`` (CLAUDE.md convention: config only via this file,
no scattered constants).

Secrets default to ``None`` so importing :data:`settings` always succeeds — even
in a fresh checkout with no ``.env`` — which keeps the skeleton and unit tests
import-safe. Modules that actually talk to the cloud call
:meth:`Settings.require_storage` / :meth:`Settings.require_warehouse` at point of
use, so a missing credential fails loudly with a clear message instead of a
cryptic boto3/psycopg error.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings. Field ``foo_bar`` reads env var ``FOO_BAR``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Environment -------------------------------------------------------
    # "dev" writes under the dev/ S3 prefix; "prod" under prod/. Never set this
    # to "prod" on a local machine (TRD §5 + hard rule: no prod writes locally).
    pitwall_env: str = "dev"

    # Bumped to force reprocessing when cleaning/aggregation logic changes;
    # stored on each processed_sessions row (BACKEND_SCHEMA §2).
    pipeline_version: str = "0.1.0"

    # --- Object storage (S3-compatible endpoint; Backblaze B2 today) -------
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_bucket: str = "pitwall-data"

    # --- Warehouse (Supabase Postgres via the Supavisor session pooler) ----
    # Must be the pooler string, NOT db.<ref>.supabase.co — the direct host is
    # IPv6-only and hangs from GitHub Actions/Streamlit (TRD §6.2).
    database_url: str | None = None

    # --- OpenF1 API + rate limits (TRD §1; hard rule 6: all HTTP is throttled)
    openf1_base_url: str = "https://api.openf1.org/v1"
    openf1_max_requests_per_second: int = 3
    openf1_max_requests_per_minute: int = 30

    # --- Prefect (optional; ephemeral mode needs neither) ------------------
    prefect_api_url: str | None = None
    prefect_api_key: str | None = None

    @property
    def is_prod(self) -> bool:
        return self.pitwall_env.lower() == "prod"

    @property
    def s3_prefix(self) -> str:
        """Leading key segment for every lake object: ``dev/`` or ``prod/``."""
        return f"{self.pitwall_env.lower()}/"

    def require_storage(self) -> None:
        """Raise if any S3 credential is missing. Called by ``storage.py``."""
        missing = [
            name
            for name, value in {
                "S3_ENDPOINT_URL": self.s3_endpoint_url,
                "S3_ACCESS_KEY_ID": self.s3_access_key_id,
                "S3_SECRET_ACCESS_KEY": self.s3_secret_access_key,
                "S3_BUCKET": self.s3_bucket,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing storage env vars: "
                + ", ".join(missing)
                + ". Set them in .env (local) or GitHub Actions Secrets (CI)."
            )

    def require_warehouse(self) -> None:
        """Raise if the warehouse connection string is missing. Called by ``warehouse.py``."""
        if not self.database_url:
            raise RuntimeError(
                "Missing DATABASE_URL (Supabase Supavisor session-pooler string). "
                "Set it in .env (local) or GitHub Actions Secrets (CI)."
            )


# Import once; share everywhere.
settings = Settings()
