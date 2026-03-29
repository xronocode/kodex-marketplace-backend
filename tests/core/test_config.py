# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test backend settings loading and CORS parsing.
# SCOPE: Default settings values and env-driven CORS parsing only.
# DEPENDS: pytest, app.core.config
# LINKS: V-M-CONFIG
# --- GRACE MODULE_MAP ---
# test_default_settings_match_phase1_contract - Validates core default config values
# test_backend_cors_origins_parses_json_env - Validates JSON CORS env parsing
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for backend settings.

from __future__ import annotations

from app.core.config import BackendSettings, get_settings


def test_default_settings_match_phase1_contract() -> None:
    settings = get_settings()

    assert settings.database_url.startswith('postgresql+asyncpg://')
    assert settings.minio_bucket == 'kodex-products'
    assert 'http://localhost:5173' in settings.backend_cors_origins


def test_backend_cors_origins_parses_json_env(monkeypatch) -> None:
    monkeypatch.setenv('BACKEND_CORS_ORIGINS', '["http://localhost:5173","http://localhost:4173"]')

    settings = BackendSettings(_env_file=None)

    assert settings.backend_cors_origins == [
        'http://localhost:5173',
        'http://localhost:4173',
    ]
