# FILE: alembic/versions/001_initial_phase1_schema.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Initial Phase 1 schema migration — creates all Kodex marketplace tables.
# SCOPE: merchants, sellers, products (with GIN search_vector), offers, product_attributes,
#         agent_requests tables and their indexes/constraints.
# DEPENDS: alembic, sqlalchemy, postgresql (gen_random_uuid, tsvector, GIN)
# LINKS: M-MIGRATIONS, app/models/catalog.py, app/models/platform.py
# --- GRACE MODULE_MAP ---
# upgrade()  - creates all Phase 1 tables, indexes, and computed columns
# downgrade() - drops all Phase 1 tables in dependency-safe order
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial migration — Phase 1 marketplace schema.

"""Initial Phase 1 schema

Revision ID: 001_phase1
Revises: None
Create Date: 2026-03-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_phase1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- START_BLOCK_UPGRADE_MERCHANTS ---
# CONTRACT:
#   PURPOSE: Create 'merchants' table — marketplace tenant/store entity.
#   INPUTS: { op: Alembic operations context }
#   OUTPUTS: DDL applied to database; returns None.
def _create_merchants() -> None:
    op.create_table(
        "merchants",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


# --- END_BLOCK_UPGRADE_MERCHANTS ---


# --- START_BLOCK_UPGRADE_SELLERS ---
# CONTRACT:
#   PURPOSE: Create 'sellers' table — marketplace seller entity.
#   INPUTS: { op: Alembic operations context }
#   OUTPUTS: DDL applied to database; returns None.
def _create_sellers() -> None:
    op.create_table(
        "sellers",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


# --- END_BLOCK_UPGRADE_SELLERS ---


# --- START_BLOCK_UPGRADE_PRODUCTS ---
# CONTRACT:
#   PURPOSE: Create 'products' table without search_vector, then add the computed
#            tsvector column via raw DDL. Creates status and merchant_id indexes.
#   INPUTS: { op: Alembic operations context }
#   OUTPUTS: DDL applied to database; returns None.
def _create_products() -> None:
    op.create_table(
        "products",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "merchant_id", sa.Uuid(), sa.ForeignKey("merchants.id"), nullable=True
        ),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="published",
        ),
        sa.Column("image_object_key", sa.String(500), nullable=True),
        sa.Column("thumbnail_object_key", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_products_merchant_id", "products", ["merchant_id"])
    op.create_index("ix_products_status", "products", ["status"])

    op.execute(
        """
        ALTER TABLE products
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('russian', coalesce(name, '') || ' ' || coalesce(description, ''))
        ) STORED
        """
    )
    op.create_index(
        "ix_products_search_vector",
        "products",
        [sa.text("search_vector")],
        postgresql_using="gin",
    )


# --- END_BLOCK_UPGRADE_PRODUCTS ---


# --- START_BLOCK_UPGRADE_OFFERS ---
# CONTRACT:
#   PURPOSE: Create 'offers' table — seller-specific listing for a product with unique
#            constraint on (product_id, seller_id).
#   INPUTS: { op: Alembic operations context }
#   OUTPUTS: DDL applied to database; returns None.
def _create_offers() -> None:
    op.create_table(
        "offers",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "product_id",
            sa.Uuid(),
            sa.ForeignKey("products.id"),
            nullable=False,
        ),
        sa.Column(
            "seller_id",
            sa.Uuid(),
            sa.ForeignKey("sellers.id"),
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("delivery_date", sa.Date(), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("product_id", "seller_id", name="uq_offers_product_seller"),
    )


# --- END_BLOCK_UPGRADE_OFFERS ---


# --- START_BLOCK_UPGRADE_PRODUCT_ATTRIBUTES ---
# CONTRACT:
#   PURPOSE: Create 'product_attributes' table — key-value pairs attached to products
#            with unique constraint on (product_id, key).
#   INPUTS: { op: Alembic operations context }
#   OUTPUTS: DDL applied to database; returns None.
def _create_product_attributes() -> None:
    op.create_table(
        "product_attributes",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "product_id",
            sa.Uuid(),
            sa.ForeignKey("products.id"),
            nullable=False,
        ),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
        sa.UniqueConstraint(
            "product_id", "key", name="uq_product_attributes_product_key"
        ),
    )


# --- END_BLOCK_UPGRADE_PRODUCT_ATTRIBUTES ---


# --- START_BLOCK_UPGRADE_AGENT_REQUESTS ---
# CONTRACT:
#   PURPOSE: Create 'agent_requests' table — audit trail for agent API interactions.
#   INPUTS: { op: Alembic operations context }
#   OUTPUTS: DDL applied to database; returns None.
def _create_agent_requests() -> None:
    op.create_table(
        "agent_requests",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("interpreted_intent", sa.Text(), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=True),
        sa.Column("response_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


# --- END_BLOCK_UPGRADE_AGENT_REQUESTS ---


# --- START_BLOCK_UPGRADE_ENTRY ---
# CONTRACT:
#   PURPOSE: Top-level upgrade — creates all Phase 1 tables in dependency order.
#   INPUTS: None
#   OUTPUTS: All tables, indexes, and constraints applied; returns None.
def upgrade() -> None:
    _create_merchants()
    _create_sellers()
    _create_products()
    _create_offers()
    _create_product_attributes()
    _create_agent_requests()


# --- END_BLOCK_UPGRADE_ENTRY ---


# --- START_BLOCK_DOWNGRADE_ENTRY ---
# CONTRACT:
#   PURPOSE: Reverse all Phase 1 schema changes — drops tables in reverse dependency order.
#   INPUTS: None
#   OUTPUTS: All Phase 1 tables removed; returns None.
def downgrade() -> None:
    op.drop_table("agent_requests")
    op.drop_table("product_attributes")
    op.drop_table("offers")
    op.drop_table("products")
    op.drop_table("sellers")
    op.drop_table("merchants")


# --- END_BLOCK_DOWNGRADE_ENTRY ---
