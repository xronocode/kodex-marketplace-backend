# FILE: app/services/product_service.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Assemble public catalog and product detail responses from repository data and response schemas.
# SCOPE: Cursor-paginated product listing, product detail with offers and attributes, filtered product search.
# DEPENDS: M-REPO-PRODUCT, M-REPO-OFFER, M-SCHEMAS-PRODUCT, M-CONFIG
# LINKS: M-SVC-PRODUCT, V-M-SVC-PRODUCT
# --- GRACE MODULE_MAP ---
# list_products - Cursor-based product listing with next cursor metadata
# get_product_detail - Full product detail payload with attributes and sorted offers
# search_products - Filtered product search returning matching items
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 public product service.

from __future__ import annotations

from typing import Optional
import logging
import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.repositories.offer_repo import list_for_product
from app.repositories.product_repo import get_detail, list_paginated, search
from app.schemas.product import (
    OfferResponse,
    ProductAttributeResponse,
    ProductDetailResponse,
    ProductListItem,
    ProductListResponse,
)

logger = logging.getLogger(__name__)
LOG_PREFIX = "[ProductService]"


# --- START_BLOCK_URL_BUILDER ---


# START_CONTRACT: _build_image_url
#   PURPOSE: Construct a public URL from a base URL and object key, or return None when key is absent.
#            Handles both MinIO object keys and external absolute URLs (e.g., picsum.photos placeholders).
#   INPUTS: { base_url: str, object_key: str|None }
#   OUTPUTS: { str|None }
# END_CONTRACT: _build_image_url
def _build_image_url(base_url: str, object_key: Optional[str]) -> Optional[str]:
    if object_key is None:
        return None
    # Handle external absolute URLs (e.g., placeholder images from picsum.photos)
    if object_key.startswith("http://") or object_key.startswith("https://"):
        return object_key
    return f"{base_url}/{object_key}"


# --- END_BLOCK_URL_BUILDER ---


# --- START_BLOCK_BUILD_LIST_ITEM ---


# START_CONTRACT: _build_list_item
#   PURPOSE: Transform a raw product dict from the repository into a ProductListItem schema.
#   INPUTS: { row: dict, base_url: str }
#   OUTPUTS: { ProductListItem }
# END_CONTRACT: _build_list_item
def _build_list_item(row: dict, base_url: str) -> ProductListItem:
    return ProductListItem(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        price=row["price"],
        stock=row["stock"],
        image_url=_build_image_url(base_url, row.get("image_object_key")),
        thumbnail_url=_build_image_url(base_url, row.get("thumbnail_object_key")),
        nearest_delivery_date=row.get("nearest_delivery_date"),
        merchant_id=row.get("merchant_id"),
    )


# --- END_BLOCK_BUILD_LIST_ITEM ---


# --- START_BLOCK_LIST_PRODUCTS ---


# START_CONTRACT: list_products
#   PURPOSE: Return cursor-based product listing payload with next cursor metadata.
#   INPUTS: { session: AsyncSession, cursor: str|None, limit: int }
#   OUTPUTS: { ProductListResponse }
#   ERRORS: PUBLIC_PRODUCT_FAILURE — wraps repository or unexpected errors.
#   LINKS: BLOCK_LIST_PRODUCTS, M-REPO-PRODUCT
# END_CONTRACT: list_products
async def list_products(
    session: AsyncSession,
    cursor: Optional[str] = None,
    limit: int = 20,
) -> ProductListResponse:
    base_url = get_settings().minio_public_base_url

    items, next_cursor, _total_count = await list_paginated(
        session, cursor=cursor, limit=limit
    )

    product_items = [_build_list_item(row, base_url) for row in items]

    logger.debug(
        "%s[BLOCK_LIST_PRODUCTS] returned %d items, next_cursor=%s",
        LOG_PREFIX,
        len(product_items),
        next_cursor,
    )

    return ProductListResponse(items=product_items, next_cursor=next_cursor)


# --- END_BLOCK_LIST_PRODUCTS ---


# --- START_BLOCK_GET_PRODUCT_DETAIL ---


# START_CONTRACT: get_product_detail
#   PURPOSE: Build full product detail payload with attributes and sorted offers.
#   INPUTS: { session: AsyncSession, product_id: UUID }
#   OUTPUTS: { ProductDetailResponse }
#   ERRORS: PUBLIC_PRODUCT_FAILURE — HTTPException 404 when product not found.
#   LINKS: BLOCK_GET_PRODUCT_DETAIL, M-REPO-PRODUCT, M-REPO-OFFER
# END_CONTRACT: get_product_detail
async def get_product_detail(
    session: AsyncSession,
    product_id: uuid.UUID,
) -> ProductDetailResponse:
    base_url = get_settings().minio_public_base_url

    detail = await get_detail(session, product_id)

    if detail is None:
        raise HTTPException(status_code=404, detail="Product not found")

    offer_rows = await list_for_product(
        session, product_id, sort_by="price", sort_order="asc"
    )

    attributes = [
        ProductAttributeResponse(key=attr["key"], value=attr["value"])
        for attr in detail.get("attributes", [])
    ]

    offers = [
        OfferResponse(
            id=offer["id"],
            seller_name=offer["seller_name"],
            price=offer["price"],
            delivery_date=offer["delivery_date"],
            stock=offer["stock"],
        )
        for offer in offer_rows
    ]

    response = ProductDetailResponse(
        id=detail["id"],
        name=detail["name"],
        description=detail["description"],
        price=detail["price"],
        stock=detail["stock"],
        image_url=_build_image_url(base_url, detail.get("image_object_key")),
        thumbnail_url=_build_image_url(base_url, detail.get("thumbnail_object_key")),
        merchant_id=detail.get("merchant_id"),
        attributes=attributes,
        offers=offers,
    )

    logger.debug(
        "%s[BLOCK_GET_PRODUCT_DETAIL] id=%s attrs=%d offers=%d",
        LOG_PREFIX,
        product_id,
        len(attributes),
        len(offers),
    )

    return response


# --- END_BLOCK_GET_PRODUCT_DETAIL ---


# --- START_BLOCK_SEARCH_PRODUCTS ---


# START_CONTRACT: search_products
#   PURPOSE: Search products by name, max_price, and/or min_stock filters, returning matching items.
#   INPUTS: { session: AsyncSession, name: str|None, max_price: Decimal|None, min_stock: int|None }
#   OUTPUTS: { list[ProductListItem] }
#   ERRORS: PUBLIC_PRODUCT_FAILURE — propagated from repository layer.
#   LINKS: BLOCK_SEARCH_PRODUCTS, M-REPO-PRODUCT
# END_CONTRACT: search_products
async def search_products(
    session: AsyncSession,
    name: Optional[str] = None,
    max_price: Optional[Decimal] = None,
    min_stock: Optional[int] = None,
) -> list[ProductListItem]:
    base_url = get_settings().minio_public_base_url

    rows = await search(session, name=name, max_price=max_price, min_stock=min_stock)

    items = [_build_list_item(row, base_url) for row in rows]

    logger.debug(
        "%s[BLOCK_SEARCH_PRODUCTS] filters(name=%s, max_price=%s, min_stock=%s) returned %d items",
        LOG_PREFIX,
        name,
        max_price,
        min_stock,
        len(items),
    )

    return items


# --- END_BLOCK_SEARCH_PRODUCTS ---
