# FILE: app/repositories/product_repo.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Query products for public catalog, detail, and agent search use cases without N+1 behavior.
# SCOPE: Cursor-paginated listing, detail projection with eager-loaded relations, filtered search.
# DEPENDS: M-DB, M-MODELS-CATALOG, M-MODELS-PLATFORM
# LINKS: M-REPO-PRODUCT, V-M-REPO-PRODUCT
# --- GRACE MODULE_MAP ---
# list_paginated - Cursor-paginated product listing with nearest delivery date
# get_detail - Load detailed product projection with attributes and offers
# search - Search products by filters for agent search use case
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 product repository.

from __future__ import annotations

from typing import Optional
import base64
import logging
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import and_, or_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.catalog import Offer, Product, ProductAttribute, Seller
from app.models.platform import Merchant

logger = logging.getLogger(__name__)
LOG_PREFIX = "[ProductRepo]"


# --- START_BLOCK_LIST_PAGINATED ---


# START_CONTRACT: list_paginated
#   PURPOSE: Cursor-paginated product listing with nearest delivery date scalar subquery.
#   INPUTS: { session: AsyncSession, cursor: str|None, limit: int }
#   OUTPUTS: { tuple[list[dict], str|None, int] - (product rows with computed fields, next_cursor, total_count) }
#   ERRORS: PRODUCT_QUERY_FAILED — propagated as SQLAlchemy exceptions.
#   SIDE_EFFECTS: reads from products and offers tables.
#   LINKS: BLOCK_LIST_PAGINATED, M-MODELS-CATALOG
# END_CONTRACT: list_paginated
async def list_paginated(
    session: AsyncSession,
    cursor: Optional[str] = None,
    limit: int = 20,
) -> tuple[list[dict], Optional[str], int]:
    nearest_delivery_sq = (
        select(func.min(Offer.delivery_date).label("nearest"))
        .where(Offer.product_id == Product.id)
        .correlate(Product)
        .scalar_subquery()
    )

    count_stmt = (
        select(func.count()).select_from(Product).where(Product.status == "published")
    )
    total_result = await session.execute(count_stmt)
    total_count = total_result.scalar_one()

    stmt = (
        select(Product, nearest_delivery_sq.label("nearest_delivery_date"))
        .where(Product.status == "published")
        .order_by(Product.created_at.desc(), Product.id.desc())
        .limit(limit + 1)
    )

    if cursor is not None:
        cursor_id = uuid.UUID(base64.b64decode(cursor).decode("ascii"))
        stmt = stmt.where(Product.id < cursor_id)

    result = await session.execute(stmt)
    rows = result.all()

    has_next = len(rows) > limit
    if has_next:
        rows = rows[:limit]

    items: list[dict] = []
    for row in rows:
        product: Product = row[0]
        items.append(
            {
                "id": product.id,
                "merchant_id": product.merchant_id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock,
                "status": product.status,
                "image_object_key": product.image_object_key,
                "thumbnail_object_key": product.thumbnail_object_key,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
                "nearest_delivery_date": row.nearest_delivery_date,
            }
        )

    next_cursor: Optional[str] = None
    if has_next and items:
        next_cursor = base64.b64encode(str(items[-1]["id"]).encode("ascii")).decode(
            "ascii"
        )

    logger.debug(
        "%s[BLOCK_LIST_PAGINATED] returned %d items, total=%d, next_cursor=%s",
        LOG_PREFIX,
        len(items),
        total_count,
        next_cursor,
    )

    return items, next_cursor, total_count


# --- END_BLOCK_LIST_PAGINATED ---


# --- START_BLOCK_GET_DETAIL ---


# START_CONTRACT: get_detail
#   PURPOSE: Load detailed product projection with attributes and offers.
#   INPUTS: { session: AsyncSession, product_id: UUID }
#   OUTPUTS: { dict|None - Full product detail with attributes and offers, or None }
#   ERRORS: PRODUCT_QUERY_FAILED — propagated as SQLAlchemy exceptions.
#   SIDE_EFFECTS: reads from products, product_attributes, offers, sellers tables.
#   LINKS: BLOCK_GET_DETAIL, M-MODELS-CATALOG
# END_CONTRACT: get_detail
async def get_detail(
    session: AsyncSession,
    product_id: uuid.UUID,
) -> Optional[dict]:
    stmt = (
        select(Product)
        .where(Product.id == product_id, Product.status == "published")
        .options(
            selectinload(Product.attributes),
            selectinload(Product.offers).joinedload(Offer.seller),
        )
    )

    result = await session.execute(stmt)
    product = result.unique().scalar_one_or_none()

    if product is None:
        logger.debug(
            "%s[BLOCK_GET_DETAIL] product not found id=%s",
            LOG_PREFIX,
            product_id,
        )
        return None

    attributes = [
        {
            "id": attr.id,
            "key": attr.key,
            "value": attr.value,
        }
        for attr in product.attributes
    ]

    offers = [
        {
            "id": offer.id,
            "seller_id": offer.seller_id,
            "seller_name": offer.seller.name if offer.seller else None,
            "price": offer.price,
            "delivery_date": offer.delivery_date,
            "stock": offer.stock,
        }
        for offer in product.offers
    ]

    detail = {
        "id": product.id,
        "merchant_id": product.merchant_id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock": product.stock,
        "status": product.status,
        "image_object_key": product.image_object_key,
        "thumbnail_object_key": product.thumbnail_object_key,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "attributes": attributes,
        "offers": offers,
    }

    logger.debug(
        "%s[BLOCK_GET_DETAIL] loaded product id=%s attrs=%d offers=%d",
        LOG_PREFIX,
        product_id,
        len(attributes),
        len(offers),
    )

    return detail


# --- END_BLOCK_GET_DETAIL ---


# --- START_BLOCK_SEARCH ---


# START_CONTRACT: search
#   PURPOSE: Search products by filters for agent search use case.
#   INPUTS: { session: AsyncSession, name: str|None, max_price: Decimal|None, min_stock: int|None }
#   OUTPUTS: { list[dict] - Matching product rows with nearest_delivery_date }
#   ERRORS: PRODUCT_QUERY_FAILED — propagated as SQLAlchemy exceptions.
#   SIDE_EFFECTS: reads from products and offers tables.
#   LINKS: BLOCK_SEARCH, M-MODELS-CATALOG
# END_CONTRACT: search
async def search(
    session: AsyncSession,
    name: Optional[str] = None,
    max_price: Optional[Decimal] = None,
    min_stock: Optional[int] = None,
) -> list[dict]:
    nearest_delivery_sq = (
        select(func.min(Offer.delivery_date).label("nearest"))
        .where(Offer.product_id == Product.id)
        .correlate(Product)
        .scalar_subquery()
    )

    clauses = [Product.status == "published"]

    if name is not None:
        clauses.append(
            or_(
                Product.name.ilike(f"%{name}%"),
                Product.description.ilike(f"%{name}%")
            )
        )
    if max_price is not None:
        clauses.append(Product.price <= max_price)
    if min_stock is not None:
        clauses.append(Product.stock >= min_stock)

    stmt = (
        select(Product, nearest_delivery_sq.label("nearest_delivery_date"))
        .where(and_(*clauses))
        .order_by(Product.created_at.desc())
    )

    result = await session.execute(stmt)
    rows = result.all()

    items: list[dict] = []
    for row in rows:
        product: Product = row[0]
        items.append(
            {
                "id": product.id,
                "merchant_id": product.merchant_id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock,
                "status": product.status,
                "image_object_key": product.image_object_key,
                "thumbnail_object_key": product.thumbnail_object_key,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
                "nearest_delivery_date": row.nearest_delivery_date,
            }
        )

    logger.debug(
        "%s[BLOCK_SEARCH] filters(name=%s, max_price=%s, min_stock=%s) returned %d items",
        LOG_PREFIX,
        name,
        max_price,
        min_stock,
        len(items),
    )

    return items


# --- END_BLOCK_SEARCH ---
