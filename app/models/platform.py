# FILE: app/models/platform.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Define SQLAlchemy models for merchants and agent request audit records required for Phase 2 preparation.
# SCOPE: Merchant and AgentRequest ORM models with full column definitions.
# DEPENDS: M-DB (app.models.Base)
# LINKS: M-MODELS-PLATFORM, V-M-MODELS-PLATFORM
# --- GRACE MODULE_MAP ---
# Merchant - ORM model for the "merchants" table
# AgentRequest - ORM model for the "agent_requests" table
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Merchant and AgentRequest models for Phase 1/2.

from __future__ import annotations

from typing import Optional
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


# --- START_BLOCK_DECLARE_PLATFORM_SCHEMA ---


# --- START_BLOCK_MERCHANT_MODEL ---
# CONTRACT:
#   PURPOSE: ORM model for merchants — represents a tenant/store in the marketplace.
#     Phase 1 creates one demo merchant "Kodex Demo Store". Phase 2 adds merchant RBAC and self-service.
#   INPUTS: { Base: DeclarativeBase }
#   OUTPUTS: { Merchant: OrmModel }
#   LINKS: M-MODELS-PLATFORM, BLOCK_DECLARE_PLATFORM_SCHEMA


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    def __repr__(self) -> str:
        return f"<Merchant id={self.id!s} slug={self.slug!r}>"


# --- END_BLOCK_MERCHANT_MODEL ---


# --- START_BLOCK_AGENT_REQUEST_MODEL ---
# CONTRACT:
#   PURPOSE: ORM model for agent interaction audit trail. Persists endpoint, query, interpreted intent,
#     result count, response time, and timestamp for every agent API call.
#   INPUTS: { Base: DeclarativeBase }
#   OUTPUTS: { AgentRequest: OrmModel }
#   LINKS: M-MODELS-PLATFORM, BLOCK_DECLARE_PLATFORM_SCHEMA


class AgentRequest(Base):
    __tablename__ = "agent_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    endpoint: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    interpreted_intent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    result_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    response_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<AgentRequest id={self.id!s} endpoint={self.endpoint!r}>"


# --- END_BLOCK_AGENT_REQUEST_MODEL ---


# --- START_BLOCK_PRODUCT_AUDIT_MODEL ---
# CONTRACT:
#   PURPOSE: ORM model for product audit log — tracks admin changes to products.
#   INPUTS: { Base: DeclarativeBase }
#   OUTPUTS: { ProductAudit: OrmModel }
#   LINKS: M-MODELS-PLATFORM, BLOCK_DECLARE_PLATFORM_SCHEMA


class ProductAudit(Base):
    __tablename__ = "product_audit"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    admin_username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    changes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<ProductAudit id={self.id!s} product_id={self.product_id!s} action={self.action!r}>"


# --- END_BLOCK_PRODUCT_AUDIT_MODEL ---


# --- END_BLOCK_DECLARE_PLATFORM_SCHEMA ---
