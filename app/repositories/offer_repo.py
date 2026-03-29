# FILE: app/repositories/offer_repo.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Load offer collections for product detail and admin write workflows with stable ordering options.
# SCOPE: Read-only offer queries with seller join and deterministic sorting.
# DEPENDS: M-DB (sqlalchemy[asyncio], asyncpg), M-MODELS-CATALOG (app.models.catalog.Offer, Seller)
# LINKS: M-REPO-OFFER, V-M-REPO-OFFER, M-MODELS-CATALOG
# --- GRACE MODULE_MAP ---
# list_for_product - Return offers for one product sorted by price or delivery date
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — list_for_product with seller join and deterministic ordering.

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Offer, Seller

logger = logging.getLogger(__name__)


# --- START_BLOCK_OFFER_REPO_FUNCTIONS ---


# --- START_BLOCK_LIST_FOR_PRODUCT ---
# START_CONTRACT: list_for_product
#   PURPOSE: Return offers for one product sorted by price or delivery date.
#   INPUTS: { session: AsyncSession, product_id: UUID, sort_by: str, sort_order: str }
#   OUTPUTS: { list[dict] - Offers with seller_name included }
#   ERRORS: OFFER_QUERY_FAILED — propagated from SQLAlchemy if query execution fails
#   LINKS: M-REPO-OFFER, BLOCK_LIST_FOR_PRODUCT
# END_CONTRACT: list_for_product
async def list_for_product(
    session: AsyncSession,
    product_id: UUID,
    sort_by: str = "price",
    sort_order: str = "asc",
) -> list[dict]:
    allowed_sort_columns = {"price": Offer.price, "delivery_date": Offer.delivery_date}
    column = allowed_sort_columns.get(sort_by, Offer.price)

    primary_sort = column.asc() if sort_order == "asc" else column.desc()
    secondary_sort = Offer.id.asc()

    stmt = (
        select(
            Offer.id,
            Seller.name.label("seller_name"),
            Offer.price,
            Offer.delivery_date,
            Offer.stock,
        )
        .join(Seller, Offer.seller_id == Seller.id)
        .where(Offer.product_id == product_id)
        .order_by(primary_sort, secondary_sort)
    )

    logger.info(
        "[OfferRepo][list_for_product][BLOCK_LIST_FOR_PRODUCT] querying offers",
        extra={
            "product_id": str(product_id),
            "sort_by": sort_by,
            "sort_order": sort_order,
        },
    )

    result = await session.execute(stmt)
    rows = result.all()

    return [
        {
            "id": row.id,
            "seller_name": row.seller_name,
            "price": float(row.price),
            "delivery_date": row.delivery_date,
            "stock": row.stock,
        }
        for row in rows
    ]


# --- END_BLOCK_LIST_FOR_PRODUCT ---


# --- END_BLOCK_OFFER_REPO_FUNCTIONS ---
