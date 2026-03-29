# FILE: app/core/database.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Create async SQLAlchemy engine and session factories for FastAPI dependencies and seed workflows.
# SCOPE: Async engine creation, async sessionmaker, FastAPI Depends() session generator.
# DEPENDS: M-CONFIG (app.core.config), M-MODELS-CATALOG (app.models.catalog), M-MODELS-PLATFORM (app.models.platform), asyncpg driver, sqlalchemy[asyncio].
# LINKS: M-DB, V-M-DB
# --- GRACE MODULE_MAP ---
# engine - AsyncEngine singleton for the application lifecycle
# AsyncSessionFactory - async_sessionmaker bound to engine
# get_session - Async generator yielding AsyncSession, usable as FastAPI Depends()
# Base - Re-exported DeclarativeBase from app.models
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 async database layer.
# 2026-03-28: v1.0.1 — Added connection pool config (pool_size=10, max_overflow=20, pool_recycle=3600).

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models import Base  # noqa: F401 — re-export for convenience

logger = logging.getLogger(__name__)
LOG_PREFIX = "[Database]"


# --- START_BLOCK_ASYNC_ENGINE ---
# CONTRACT:
#   PURPOSE: Build the async SQLAlchemy engine from settings.database_url (asyncpg driver).
#   INPUTS: { settings: BackendSettings via get_settings() }
#   OUTPUTS: { engine: AsyncEngine }
#   SIDE_EFFECTS: logs engine creation with redacted DSN.
#   LINKS: M-CONFIG, BLOCK_DATABASE_SETTINGS
_settings = get_settings()
engine = create_async_engine(
    _settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)
logger.info(
    "%s[BLOCK_ASYNC_ENGINE] Async engine created — dsn=%s, pool_size=10, max_overflow=20",
    LOG_PREFIX,
    _settings.database_url.split("@")[-1],
)
# --- END_BLOCK_ASYNC_ENGINE ---


# --- START_BLOCK_SESSION_FACTORY ---
# CONTRACT:
#   PURPOSE: Produce async_sessionmaker bound to the engine for AsyncSession instances.
#   INPUTS: { engine: AsyncEngine }
#   OUTPUTS: { AsyncSessionFactory: async_sessionmaker[AsyncSession] }
#   LINKS: BLOCK_ASYNC_ENGINE
AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
logger.info("%s[BLOCK_SESSION_FACTORY] AsyncSessionFactory configured", LOG_PREFIX)
# --- END_BLOCK_SESSION_FACTORY ---


# --- START_BLOCK_CREATE_SESSION ---
# CONTRACT:
#   PURPOSE: FastAPI Depends() async generator — yields an AsyncSession and guarantees cleanup.
#   INPUTS: {}
#   OUTPUTS: { AsyncSession - yielded, auto-closed on scope exit }
#   ERRORS: DB_CONNECTION_FAILURE — propagated as SQLAlchemy exceptions if the connection is broken.
#   SIDE_EFFECTS: opens and closes a DB session per request.
#   LINKS: BLOCK_SESSION_FACTORY, V-M-DB
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.

    Usage::

        @app.get("/items")
        async def list_items(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# --- END_BLOCK_CREATE_SESSION ---
