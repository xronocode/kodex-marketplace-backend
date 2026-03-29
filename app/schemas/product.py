# FILE: app/schemas/product.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Pydantic schemas for public product listing and detail responses.
# SCOPE: Product attribute, product list (cursor-paginated), offer, and product detail response models.
# DEPENDS: pydantic
# LINKS: M-SCHEMAS-PRODUCT, app.api.v1 (consumes), app.services (consumes), app.schemas.offer
# --- GRACE MODULE_MAP ---
# ProductAttributeResponse - Key-value attribute on a product
# ProductListItem - Single product row in a cursor-paginated list
# ProductListResponse - Cursor-paginated product list envelope
# OfferResponse - Seller offer with price and delivery date (shared with offer schema)
# ProductDetailResponse - Full product detail with attributes and offers
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 public product schemas.

from __future__ import annotations

from typing import Optional
import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# --- START_BLOCK_PRODUCT_ATTRIBUTE_RESPONSE ---


class ProductAttributeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str


# --- END_BLOCK_PRODUCT_ATTRIBUTE_RESPONSE ---


# --- START_BLOCK_PRODUCT_LIST_ITEM ---


class ProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    price: Decimal
    stock: int
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    nearest_delivery_date: Optional[date] = None
    merchant_id: Optional[uuid.UUID] = None


# --- END_BLOCK_PRODUCT_LIST_ITEM ---


# --- START_BLOCK_PRODUCT_LIST_RESPONSE ---


class ProductListResponse(BaseModel):
    items: list[ProductListItem]
    next_cursor: Optional[str] = None


# --- END_BLOCK_PRODUCT_LIST_RESPONSE ---


# --- START_BLOCK_OFFER_RESPONSE ---


class OfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_name: str
    price: Decimal
    delivery_date: date
    stock: int


# --- END_BLOCK_OFFER_RESPONSE ---


# --- START_BLOCK_PRODUCT_DETAIL_RESPONSE ---


class ProductDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    price: Decimal
    stock: int
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    merchant_id: Optional[uuid.UUID] = None
    attributes: list[ProductAttributeResponse]
    offers: list[OfferResponse]


# --- END_BLOCK_PRODUCT_DETAIL_RESPONSE ---
