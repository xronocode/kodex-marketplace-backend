# FILE: app/services/offer_service.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Apply offer sorting rules and response shaping for product detail and admin views.
# SCOPE: Offer sorting by price or delivery date with dict-to-schema transformation.
# DEPENDS: M-REPO-OFFER (app.repositories.offer_repo), M-SCHEMAS-OFFER (app.schemas.offer), M-SCHEMAS-PRODUCT (app.schemas.product)
# LINKS: M-SVC-OFFER, V-M-SVC-OFFER, M-REPO-OFFER
# --- GRACE MODULE_MAP ---
# sort_offers - Sort offer collections by price or delivery date, return OfferResponse list
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 offer sorting service.

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import offer_repo
from app.schemas.offer import OfferSortEnum
from app.schemas.product import OfferResponse

logger = logging.getLogger(__name__)
LOG_PREFIX = "[OfferService]"


# --- START_BLOCK_SORT_OFFERS ---


# START_CONTRACT: sort_offers
#   PURPOSE: Sort offer collections by price or delivery date.
#   INPUTS: { session: AsyncSession, product_id: UUID, sort_by: OfferSortEnum, sort_order: str }
#   OUTPUTS: { list[OfferResponse] }
#   ERRORS: OFFER_SORT_FAILED — wraps any unexpected failure from the repository layer
#   LINKS: M-SVC-OFFER, BLOCK_SORT_OFFERS, M-REPO-OFFER.list_for_product
# END_CONTRACT: sort_offers
async def sort_offers(
    session: AsyncSession,
    product_id: UUID,
    sort_by: OfferSortEnum = OfferSortEnum.price,
    sort_order: str = "asc",
) -> list[OfferResponse]:
    logger.info(
        "%s[sort_offers][BLOCK_SORT_OFFERS] sorting offers",
        LOG_PREFIX,
        extra={
            "product_id": str(product_id),
            "sort_by": sort_by.value,
            "sort_order": sort_order,
        },
    )

    rows = await offer_repo.list_for_product(
        session=session,
        product_id=product_id,
        sort_by=sort_by.value,
        sort_order=sort_order,
    )

    offers = [OfferResponse(**row) for row in rows]

    logger.info(
        "%s[sort_offers][BLOCK_SORT_OFFERS] sorted %d offers",
        LOG_PREFIX,
        len(offers),
        extra={"product_id": str(product_id)},
    )

    return offers


# --- END_BLOCK_SORT_OFFERS ---
