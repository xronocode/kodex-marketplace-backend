# FILE: app/schemas/admin.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Admin catalog CRUD request and response schemas.
# SCOPE: Seller, product, and offer create/update schemas plus image upload and admin product response.
# DEPENDS: pydantic
# LINKS: M-SCHEMAS-ADMIN, app.api.v1.admin (consumes), app.services (consumes)
# --- GRACE MODULE_MAP ---
# SellerCreate - Request body to create a new seller
# SellerResponse - Seller representation with id and timestamps
# ProductCreate - Request body to create a new product
# ProductUpdate - Partial update body for a product (all fields optional)
# OfferCreate - Request body to create a new offer
# OfferUpdate - Partial update body for an offer (all fields optional)
# ImageUploadResponse - Response with presigned image and thumbnail URLs
# ProductAttributeResponse - Key-value attribute attached to a product
# ProductAdminResponse - Full admin product view with status and timestamps
# ProductAdminListResponse - Envelope wrapping a list of ProductAdminResponse items
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 admin CRUD schemas.

from __future__ import annotations

from typing import Optional
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# --- START_BLOCK_SELLER_CREATE ---


class SellerCreate(BaseModel):
    name: str


# --- END_BLOCK_SELLER_CREATE ---


# --- START_BLOCK_SELLER_RESPONSE ---


class SellerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime


# --- END_BLOCK_SELLER_RESPONSE ---


# --- START_BLOCK_PRODUCT_CREATE ---


class ProductCreate(BaseModel):
    name: str
    description: str = ""
    price: Decimal
    stock: int = 0


# --- END_BLOCK_PRODUCT_CREATE ---


# --- START_BLOCK_PRODUCT_UPDATE ---


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None


# --- END_BLOCK_PRODUCT_UPDATE ---


# --- START_BLOCK_OFFER_CREATE ---


class OfferCreate(BaseModel):
    product_id: uuid.UUID
    seller_id: uuid.UUID
    price: Decimal
    delivery_date: date
    stock: int = 0


# --- END_BLOCK_OFFER_CREATE ---


# --- START_BLOCK_OFFER_UPDATE ---


class OfferUpdate(BaseModel):
    price: Optional[Decimal] = None
    delivery_date: Optional[date] = None
    stock: Optional[int] = None


# --- END_BLOCK_OFFER_UPDATE ---


# --- START_BLOCK_IMAGE_UPLOAD_RESPONSE ---


class ImageUploadResponse(BaseModel):
    image_url: str
    thumbnail_url: str


# --- END_BLOCK_IMAGE_UPLOAD_RESPONSE ---


# --- START_BLOCK_PRODUCT_ATTRIBUTE_RESPONSE ---


class ProductAttributeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str


# --- END_BLOCK_PRODUCT_ATTRIBUTE_RESPONSE ---


# --- START_BLOCK_PRODUCT_ADMIN_RESPONSE ---


class ProductAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    price: Decimal
    stock: int
    status: str
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    merchant_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    attributes: list[ProductAttributeResponse] = []

    @classmethod
    def model_validate(cls, obj):
        """Override to map image_object_key to image_url."""
        data = {
            'id': obj.id,
            'name': obj.name,
            'description': obj.description,
            'price': obj.price,
            'stock': obj.stock,
            'status': obj.status,
            'image_url': obj.image_object_key,
            'thumbnail_url': obj.thumbnail_object_key,
            'merchant_id': obj.merchant_id,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
            'attributes': obj.attributes if hasattr(obj, 'attributes') else [],
        }
        return cls(**data)


# --- END_BLOCK_PRODUCT_ADMIN_RESPONSE ---


# --- START_BLOCK_PRODUCT_ADMIN_LIST_RESPONSE ---


class ProductAdminListResponse(BaseModel):
    items: list[ProductAdminResponse]


# --- END_BLOCK_PRODUCT_ADMIN_LIST_RESPONSE ---
