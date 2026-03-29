# FILE: app/core/config.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Load and validate backend runtime settings from environment variables via Pydantic Settings.
# SCOPE: Database, MinIO/S3, auth, CORS, and feature-flag configuration for Phase 1.
# DEPENDS: M-INFRA-ENV, pydantic-settings
# LINKS: M-CONFIG, V-M-CONFIG
# --- GRACE MODULE_MAP ---
# BackendSettings - Pydantic Settings model with all backend configuration fields
# get_settings - Cached singleton accessor for BackendSettings
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 scaffolding.

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)
LOG_PREFIX = "[Config]"


# --- START_BLOCK_BACKEND_SETTINGS ---
class BackendSettings(BaseSettings):
    """
    Central configuration model.

    CONTRACT:
        PURPOSE: Bind every runtime knob to an environment variable with sensible Phase 1 defaults.
        INPUTS: { env: os.environ + optional .env file }
        OUTPUTS: { BackendSettings - validated settings instance }
        SIDE_EFFECTS: none
        LINKS: M-INFRA-ENV
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- START_BLOCK_DATABASE_SETTINGS ---
    # CONTRACT:
    #   PURPOSE: PostgreSQL async connection string.
    #   INPUTS: { DATABASE_URL: str - from env }
    #   OUTPUTS: { database_url: str }
    database_url: str = "postgresql+asyncpg://kodex:changeme@db:5432/kodex_db"
    # --- END_BLOCK_DATABASE_SETTINGS ---

    # --- START_BLOCK_MINIO_SETTINGS ---
    # CONTRACT:
    #   PURPOSE: MinIO / S3 object storage connection and bucket configuration.
    #   INPUTS: { MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, MINIO_BUCKET, MINIO_PUBLIC_BASE_URL: str - from env }
    #   OUTPUTS: { minio_endpoint, minio_root_user, minio_root_password, minio_bucket, minio_public_base_url: str }
    minio_endpoint: str = "http://s3:9000"
    minio_root_user: str = "kodex_minio"
    minio_root_password: str = "changeme_strong_password"
    minio_bucket: str = "kodex-products"
    minio_public_base_url: str = "http://localhost:9000/kodex-products"
    # --- END_BLOCK_MINIO_SETTINGS ---

    # --- START_BLOCK_AUTH_SETTINGS ---
    # CONTRACT:
    #   PURPOSE: Prototype admin authentication and JWT signing configuration.
    #   INPUTS: { ADMIN_USERNAME, ADMIN_PASSWORD, SECRET_KEY: str, ACCESS_TOKEN_EXPIRE_MINUTES: int - from env }
    #   OUTPUTS: { admin_username, admin_password, secret_key: str, access_token_expire_minutes: int }
    admin_username: str = "admin"
    admin_password: str = "changeme_strong_password"
    secret_key: str = (
        "change-this-to-a-random-64-character-string-before-any-deployment"
    )
    access_token_expire_minutes: int = 60
    # --- END_BLOCK_AUTH_SETTINGS ---

    # --- START_BLOCK_CORS_SETTINGS ---
    # CONTRACT:
    #   PURPOSE: Allowed origins for CORS middleware.
    #   INPUTS: { BACKEND_CORS_ORIGINS: str | list[str] - JSON string or list from env }
    #   OUTPUTS: { backend_cors_origins: list[str] }
    backend_cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """
        CONTRACT:
            PURPOSE: Parse CORS origins from a JSON string when loaded from env.
            INPUTS: { v: Any - raw value, may be str (JSON) or list[str] }
            OUTPUTS: { list[str] - validated list of origin URLs }
        """
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                logger.warning(
                    "%s[BLOCK_CORS_SETTINGS] Failed to parse BACKEND_CORS_ORIGINS JSON, using default",
                    LOG_PREFIX,
                )
                raise
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid CORS origins value: {v!r}")

    # --- END_BLOCK_CORS_SETTINGS ---

    # --- START_BLOCK_FEATURE_FLAG_SETTINGS ---
    # CONTRACT:
    #   PURPOSE: Phase 1 feature toggles for optional integrations (Recombee).
    #   INPUTS: { ENABLE_RECOMBEE: bool, RECOMBEE_API_KEY, RECOMBEE_DB_ID: str - from env }
    #   OUTPUTS: { enable_recombee: bool, recombee_api_key, recombee_db_id: str }
    enable_recombee: bool = False
    recombee_api_key: str = ""
    recombee_db_id: str = ""
    # --- END_BLOCK_FEATURE_FLAG_SETTINGS ---


# --- END_BLOCK_BACKEND_SETTINGS ---


# --- START_BLOCK_LOAD_SETTINGS ---
@lru_cache()
def get_settings() -> BackendSettings:
    """
    CONTRACT:
        PURPOSE: Return a cached singleton of BackendSettings.
        INPUTS: { env: os.environ + .env file via Pydantic Settings }
        OUTPUTS: { BackendSettings - validated, immutable settings instance }
        SIDE_EFFECTS: reads env / .env on first call; logs load event.
        LINKS: BLOCK_LOAD_SETTINGS, M-CONFIG
    """
    settings = BackendSettings()
    logger.info(
        "%s[BLOCK_LOAD_SETTINGS] Settings loaded — db=%s minio=%s",
        LOG_PREFIX,
        settings.database_url.split("@")[-1],
        settings.minio_endpoint,
    )
    return settings


# --- END_BLOCK_LOAD_SETTINGS ---
