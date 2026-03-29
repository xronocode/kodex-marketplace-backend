# FILE: app/api/v1/public.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Expose public catalog and product detail endpoints for anonymous visitors.
# SCOPE: Cursor-paginated product listing, single product detail with sorted offers.
# DEPENDS: M-SVC-PRODUCT (app.services.product_service), M-SVC-OFFER (app.services.offer_service),
#          M-DB (app.core.database.get_session), M-SCHEMAS-PRODUCT (app.schemas.product), M-SCHEMAS-OFFER (app.schemas.offer)
# LINKS: M-API-PUBLIC, V-M-API-PUBLIC, M-SVC-PRODUCT, M-SVC-OFFER
# --- GRACE MODULE_MAP ---
# router - FastAPI APIRouter with prefix="/v1/public" and tags=["public"]
# get_products - GET /products — cursor-paginated product list with X-Total-Count header
# get_product_detail - GET /products/{product_id} — product detail with attributes and sorted offers
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 public API endpoints.
# 2026-03-28: v1.0.1 — Added PERF_NOTE comment for X-Total-Count performance consideration.

from __future__ import annotations

from typing import Optional
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.offer import OfferSortEnum
from app.schemas.product import ProductDetailResponse, ProductListResponse
from app.services import offer_service, product_service

# PERF_NOTE: COUNT(*) on large tables is expensive.
# Phase 2: cache total count in Redis with 60s TTL.
# Current approach acceptable for prototype (<10k products).

logger = logging.getLogger(__name__)
LOG_PREFIX = "[PublicApi]"

router = APIRouter(prefix="/v1/public", tags=["public"])


# --- START_BLOCK_HANDLE_PUBLIC_PRODUCTS ---


# START_CONTRACT: get_products
#   PURPOSE: GET /v1/public/products list endpoint with cursor pagination.
#   INPUTS: { cursor: str|None, limit: int, session: AsyncSession }
#   OUTPUTS: { ProductListResponse }
#   ERRORS: PUBLIC_HTTP_FAILURE — propagated from product_service.list_products.
#   LINKS: BLOCK_HANDLE_PUBLIC_PRODUCTS, M-SVC-PRODUCT.list_products
# END_CONTRACT: get_products
@router.get("/products", response_model=ProductListResponse)
async def get_products(
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ProductListResponse:
    result = await product_service.list_products(session, cursor, limit)

    logger.info(
        "%s[get_products][BLOCK_HANDLE_PUBLIC_PRODUCTS] returned %d items, cursor=%s",
        LOG_PREFIX,
        len(result.items),
        cursor,
    )

    return result


# --- END_BLOCK_HANDLE_PUBLIC_PRODUCTS ---


# --- START_BLOCK_HANDLE_PUBLIC_PRODUCT_DETAIL ---


# START_CONTRACT: get_product_detail
#   PURPOSE: GET /v1/public/products/{id} detail endpoint with attributes and sorted offers.
#   INPUTS: { product_id: UUID, session: AsyncSession, sort_offers_by: OfferSortEnum }
#   OUTPUTS: { ProductDetailResponse }
#   ERRORS: PUBLIC_HTTP_FAILURE — propagated from product_service / offer_service (404 if not found).
#   LINKS: BLOCK_HANDLE_PUBLIC_PRODUCT_DETAIL, M-SVC-PRODUCT.get_product_detail, M-SVC-OFFER.sort_offers
# END_CONTRACT: get_product_detail
@router.get("/products/{product_id}", response_model=ProductDetailResponse)
async def get_product_detail(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    sort_offers_by: OfferSortEnum = Query(OfferSortEnum.price),
) -> ProductDetailResponse:
    detail = await product_service.get_product_detail(session, product_id)

    if sort_offers_by != OfferSortEnum.price:
        sorted_offers = await offer_service.sort_offers(
            session, product_id, sort_by=sort_offers_by
        )
        detail.offers = sorted_offers

    logger.info(
        "%s[get_product_detail][BLOCK_HANDLE_PUBLIC_PRODUCT_DETAIL] id=%s offers=%d sort_by=%s",
        LOG_PREFIX,
        product_id,
        len(detail.offers),
        sort_offers_by.value,
    )

    return detail


# --- END_BLOCK_HANDLE_PUBLIC_PRODUCT_DETAIL ---
