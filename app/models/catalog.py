# FILE: app/models/catalog.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Define SQLAlchemy ORM models for the marketplace catalog — sellers, products, offers, and product attributes.
# SCOPE: Catalog domain tables, relationships, indexes, and Phase 2 multi-merchant preparation columns.
# DEPENDS: M-DB (app.models.Base), sqlalchemy, asyncpg driver
# LINKS: M-MODELS-CATALOG, V-M-MODELS-CATALOG, alembic/env.py, app.repositories
# --- GRACE MODULE_MAP ---
# Seller - Marketplace seller entity
# Product - Product listing with search vector and Phase 2 merchant_id FK
# Offer - Seller-specific offer for a product with price and delivery
# ProductAttribute - Key-value attribute attached to a product
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 catalog schema with Phase 2 multi-merchant prep.

from __future__ import annotations

from typing import Optional
import uuid
from datetime import datetime, date

from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    Date,
    ForeignKey,
    Index,
    DateTime,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models import Base


# --- START_BLOCK_DECLARE_CATALOG_SCHEMA ---


# --- START_BLOCK_SELLER_MODEL ---
# CONTRACT:
#   PURPOSE: ORM model for the 'sellers' table — a merchant or vendor in the marketplace.
#   INPUTS: { Base: DeclarativeBase }
#   OUTPUTS: { Seller: OrmModel }
class Seller(Base):
    __tablename__ = "sellers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    offers: Mapped[list["Offer"]] = relationship(
        back_populates="seller",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Seller id={self.id} name={self.name!r}>"


# --- END_BLOCK_SELLER_MODEL ---


# --- START_BLOCK_PRODUCT_MODEL ---
# CONTRACT:
#   PURPOSE: ORM model for the 'products' table — core product listing with full-text search and Phase 2 merchant FK.
#   INPUTS: { Base: DeclarativeBase }
#   OUTPUTS: { Product: OrmModel }
#   ERRORS: MODEL_SCHEMA_DRIFT — if generated column or index definitions diverge from migration.
class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    # PHASE_2_PREP: nullable FK to merchants table for multi-merchant expansion
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # PHASE_2_PREP: status column for published/draft/archived lifecycle
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="published",
        server_default="published",
    )
    image_object_key: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    thumbnail_object_key: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        nullable=True,
        server_default=text(
            "to_tsvector('russian', coalesce(name, '') || ' ' || coalesce(description, ''))"
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    offers: Mapped[list["Offer"]] = relationship(
        back_populates="product",
        lazy="selectin",
    )
    attributes: Mapped[list["ProductAttribute"]] = relationship(
        back_populates="product",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_products_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_products_merchant_id", "merchant_id"),
        Index("ix_products_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r} status={self.status!r}>"


# --- END_BLOCK_PRODUCT_MODEL ---


# --- START_BLOCK_OFFER_MODEL ---
# CONTRACT:
#   PURPOSE: ORM model for the 'offers' table — a seller-specific listing for a product with price and delivery date.
#   INPUTS: { Base: DeclarativeBase }
#   OUTPUTS: { Offer: OrmModel }
class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False,
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellers.id"),
        nullable=False,
    )
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    product: Mapped["Product"] = relationship(
        back_populates="offers",
        lazy="selectin",
    )
    seller: Mapped["Seller"] = relationship(
        back_populates="offers",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "seller_id",
            name="uq_offers_product_seller",
        ),
    )

    def __repr__(self) -> str:
        return f"<Offer id={self.id} product_id={self.product_id} seller_id={self.seller_id}>"


# --- END_BLOCK_OFFER_MODEL ---


# --- START_BLOCK_PRODUCT_ATTRIBUTE_MODEL ---
# CONTRACT:
#   PURPOSE: ORM model for the 'product_attributes' table — key-value pairs attached to products.
#   INPUTS: { Base: DeclarativeBase }
#   OUTPUTS: { ProductAttribute: OrmModel }
class ProductAttribute(Base):
    __tablename__ = "product_attributes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)

    product: Mapped["Product"] = relationship(
        back_populates="attributes",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "key",
            name="uq_product_attributes_product_key",
        ),
    )

    def __repr__(self) -> str:
        return f"<ProductAttribute id={self.id} key={self.key!r} value={self.value!r}>"


# --- END_BLOCK_PRODUCT_ATTRIBUTE_MODEL ---


# --- END_BLOCK_DECLARE_CATALOG_SCHEMA ---
