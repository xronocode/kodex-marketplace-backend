# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Alembic migration environment — async online mode + sync offline mode.
# SCOPE: Database migration runner for both offline (SQL generation) and online (live DB) modes.
# DEPENDS: alembic, sqlalchemy[asyncio], asyncpg, asyncio, app.models (Base.metadata).
# LINKS: alembic.ini (config), app.models (target_metadata)
# --- GRACE MODULE_MAP ---
# EXPORTS: run_migrations_offline(), run_migrations_online()
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial env.py — async pattern with AsyncEngine + asyncio.run().

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.models import Base

# --- START_BLOCK_CONFIG ---
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
# --- END_BLOCK_CONFIG ---


# --- START_BLOCK_RUN_OFFLINE ---
# CONTRACT:
#   PURPOSE: Run migrations in offline mode — generates SQL scripts without DB connection.
#   INPUTS: None (reads from alembic context config).
#   OUTPUTS: Writes SQL to output stream; returns None.
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# --- END_BLOCK_RUN_OFFLINE ---


# --- START_BLOCK_RUN_ONLINE ---
# CONTRACT:
#   PURPOSE: Run migrations in online mode — connects to DB via AsyncEngine (asyncpg).
#   INPUTS: None (reads from alembic context config).
#   OUTPUTS: Applies migrations to live database; returns None.
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# --- END_BLOCK_RUN_ONLINE ---


# --- START_BLOCK_ENTRYPOINT ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
# --- END_BLOCK_ENTRYPOINT ---
