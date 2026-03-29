# FILE: app/schemas/offer.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Offer sorting and response shaping schemas.
# SCOPE: Offer sort enum and offer list response envelope.
# DEPENDS: pydantic, app.schemas.product (OfferResponse)
# LINKS: M-SCHEMAS-OFFER, app.api.v1 (consumes), app.schemas.product
# --- GRACE MODULE_MAP ---
# OfferSortEnum - Sort options for offer listings (price, delivery_date)
# OfferListResponse - Envelope for a list of offers with shared OfferResponse model
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 offer sorting and list schemas.

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from app.schemas.product import OfferResponse


# --- START_BLOCK_OFFER_SORT_ENUM ---


class OfferSortEnum(str, Enum):
    price = "price"
    delivery_date = "delivery_date"


# --- END_BLOCK_OFFER_SORT_ENUM ---


# --- START_BLOCK_OFFER_LIST_RESPONSE ---


class OfferListResponse(BaseModel):
    offers: list[OfferResponse]


# --- END_BLOCK_OFFER_LIST_RESPONSE ---
