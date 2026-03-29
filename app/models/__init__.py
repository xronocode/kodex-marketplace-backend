# --- GRACE MODULE_CONTRACT ---
# PURPOSE: SQLAlchemy ORM models and declarative Base for all database tables.
# SCOPE: Domain models, Base declarative class, metadata for Alembic migrations.
# DEPENDS: sqlalchemy, app.models.catalog, app.models.platform.
# LINKS: alembic/env.py (consumes Base.metadata), app.repositories (consumes models)
# --- GRACE MODULE_MAP ---
# EXPORTS: Base
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial package init — exports Base declarative class.
# 2026-03-28: Import catalog and platform submodules so Alembic autogenerate sees all tables.

# --- START_BLOCK_BASE_DECLARATION ---
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# --- END_BLOCK_BASE_DECLARATION ---


# --- START_BLOCK_MODEL_REGISTRATION ---
import app.models.catalog  # noqa: F401  — registers Seller, Product, Offer, ProductAttribute
import app.models.platform  # noqa: F401  — registers Merchant, AgentRequest
# --- END_BLOCK_MODEL_REGISTRATION ---
