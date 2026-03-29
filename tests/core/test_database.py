# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test async database session wiring.
# SCOPE: Engine driver selection and async session dependency shape only.
# DEPENDS: inspect, app.core.database
# LINKS: V-M-DB
# --- GRACE MODULE_MAP ---
# test_database_engine_uses_asyncpg_driver - Verifies asyncpg runtime driver
# test_get_session_is_async_generator - Verifies FastAPI session dependency shape
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for database engine/session wiring.

from __future__ import annotations

import inspect

import app.core.database as database


def test_database_engine_uses_asyncpg_driver() -> None:
    assert database.engine.url.drivername == 'postgresql+asyncpg'


def test_get_session_is_async_generator() -> None:
    assert inspect.isasyncgenfunction(database.get_session)
