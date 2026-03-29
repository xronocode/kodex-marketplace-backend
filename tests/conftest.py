# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Stabilize backend smoke-test environment defaults.
# SCOPE: Environment variable defaults and config cache reset between tests.
# DEPENDS: pytest, app.core.config
# LINKS: V-M-CONFIG, V-M-APP
# --- GRACE MODULE_MAP ---
# backend_env_defaults - Canonical env defaults for smoke tests
# reset_backend_settings_cache - Autouse fixture clearing cached settings
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added backend smoke-test env bootstrap.

from __future__ import annotations

import pytest

pytest_plugins = ("anyio",)

backend_env_defaults = {
    'DATABASE_URL': 'postgresql+asyncpg://kodex:changeme@db:5432/kodex_db',
    'MINIO_ENDPOINT': 'http://s3:9000',
    'MINIO_ROOT_USER': 'kodex_minio',
    'MINIO_ROOT_PASSWORD': 'changeme_strong_password',
    'MINIO_BUCKET': 'kodex-products',
    'MINIO_PUBLIC_BASE_URL': 'http://localhost:9000/kodex-products',
    'ADMIN_USERNAME': 'admin',
    'ADMIN_PASSWORD': 'changeme_strong_password',
    'SECRET_KEY': 'change-this-to-a-random-64-character-string-before-any-deployment',
    'ACCESS_TOKEN_EXPIRE_MINUTES': '60',
    'BACKEND_CORS_ORIGINS': '["http://localhost:5173","http://localhost:3000"]',
}


@pytest.fixture(autouse=True)
def reset_backend_settings_cache(monkeypatch: pytest.MonkeyPatch):
    for key, value in backend_env_defaults.items():
        monkeypatch.setenv(key, value)

    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
