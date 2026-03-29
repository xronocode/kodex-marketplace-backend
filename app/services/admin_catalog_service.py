# FILE: app/services/admin_catalog_service.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Coordinate admin CRUD operations, image uploads, and product media metadata persistence.
# SCOPE: Admin-facing service layer for sellers, products, offers, and product image management.
# DEPENDS: M-REPO-ADMIN, M-S3, M-SCHEMAS-ADMIN (app.schemas.admin)
# LINKS: M-SVC-ADMIN, V-M-SVC-ADMIN
# --- GRACE MODULE_MAP ---
# create_seller - Create a seller via repo, return SellerResponse
# list_sellers - List all sellers via repo, return list of SellerResponse
# list_products - List all products via repo, return ProductAdminListResponse
# create_product - Create a product via repo, return ProductAdminResponse
# update_product - Partial-update product via repo, return ProductAdminResponse
# delete_product - Delete a product via repo, return bool
# create_offer - Create an offer via repo, return dict
# update_offer - Partial-update offer via repo, return dict
# delete_offer - Delete an offer via repo, return bool
# upload_product_image_service - Upload image to S3, persist keys, return ImageUploadResponse
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — admin catalog service layer.

from __future__ import annotations

from typing import Optional
import json
import logging
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import ProductAudit
from app.repositories import admin_catalog_repo
from app.schemas.admin import (
    ImageUploadResponse,
    OfferCreate,
    OfferUpdate,
    ProductAdminListResponse,
    ProductAdminResponse,
    ProductCreate,
    ProductUpdate,
    SellerCreate,
    SellerResponse,
)
from app.services.s3_service import StoredImageRefs, upload_product_image

logger = logging.getLogger(__name__)
LOG_PREFIX = "[AdminService]"


# --- START_BLOCK_CREATE_SELLER ---
# CONTRACT:
#   PURPOSE: Create a new Seller and return a SellerResponse.
#   INPUTS: { session: AsyncSession, data: SellerCreate }
#   OUTPUTS: { SellerResponse }
#   SIDE_EFFECTS: DB write via repo
async def create_seller(session: AsyncSession, data: SellerCreate) -> SellerResponse:
    seller = await admin_catalog_repo.create_seller(session, name=data.name)
    logger.info("%s[BLOCK_CREATE_SELLER] seller_id=%s", LOG_PREFIX, seller.id)
    return SellerResponse.model_validate(seller)


# --- END_BLOCK_CREATE_SELLER ---


# --- START_BLOCK_LIST_SELLERS ---
# CONTRACT:
#   PURPOSE: Return all sellers as SellerResponse list.
#   INPUTS: { session: AsyncSession }
#   OUTPUTS: { list[SellerResponse] }
#   SIDE_EFFECTS: none (read-only)
async def list_sellers(session: AsyncSession) -> list[SellerResponse]:
    sellers = await admin_catalog_repo.list_sellers(session)
    return [SellerResponse.model_validate(s) for s in sellers]


# --- END_BLOCK_LIST_SELLERS ---


# --- START_BLOCK_LIST_PRODUCTS ---
# CONTRACT:
#   PURPOSE: Return all products as ProductAdminListResponse.
#   INPUTS: { session: AsyncSession }
#   OUTPUTS: { ProductAdminListResponse }
#   SIDE_EFFECTS: none (read-only)
async def list_products(session: AsyncSession) -> ProductAdminListResponse:
    products = await admin_catalog_repo.list_products(session)
    return ProductAdminListResponse(
        items=[ProductAdminResponse.model_validate(p) for p in products]
    )


# --- END_BLOCK_LIST_PRODUCTS ---


# --- START_BLOCK_CREATE_PRODUCT ---
# CONTRACT:
#   PURPOSE: Create a new product and return ProductAdminResponse.
#   INPUTS: { session: AsyncSession, data: ProductCreate, merchant_id: UUID|None }
#   OUTPUTS: { ProductAdminResponse }
#   SIDE_EFFECTS: DB write via repo, audit log entry
async def create_product(
    session: AsyncSession,
    data: ProductCreate,
    merchant_id: Optional[UUID] = None,
) -> ProductAdminResponse:
    product = await admin_catalog_repo.create_product(
        session,
        name=data.name,
        description=data.description,
        price=float(data.price),
        stock=data.stock,
        merchant_id=merchant_id,
    )
    logger.info("%s[BLOCK_CREATE_PRODUCT] product_id=%s", LOG_PREFIX, product.id)

    # Audit log
    audit = ProductAudit(
        product_id=product.id,
        admin_username="admin",
        action="CREATE",
        changes=json.dumps(
            {"name": data.name, "price": float(data.price), "stock": data.stock}
        ),
    )
    session.add(audit)
    await session.commit()

    return ProductAdminResponse.model_validate(product)


# --- END_BLOCK_CREATE_PRODUCT ---


# --- START_BLOCK_UPDATE_PRODUCT ---
# CONTRACT:
#   PURPOSE: Partial-update product fields and return updated ProductAdminResponse.
#   INPUTS: { session: AsyncSession, product_id: UUID, data: ProductUpdate }
#   OUTPUTS: { ProductAdminResponse }
#   ERRORS: HTTPException 404 if product not found
#   SIDE_EFFECTS: DB write via repo, audit log entry
async def update_product(
    session: AsyncSession,
    product_id: UUID,
    data: ProductUpdate,
) -> ProductAdminResponse:
    updates = data.model_dump(exclude_unset=True)
    if "price" in updates and updates["price"] is not None:
        updates["price"] = float(updates["price"])

    product = await admin_catalog_repo.update_product(session, product_id, **updates)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    logger.info(
        "%s[BLOCK_UPDATE_PRODUCT] product_id=%s fields=%s",
        LOG_PREFIX,
        product_id,
        list(updates.keys()),
    )

    # Audit log
    audit = ProductAudit(
        product_id=product.id,
        admin_username="admin",
        action="UPDATE",
        changes=json.dumps(updates),
    )
    session.add(audit)
    await session.commit()

    return ProductAdminResponse.model_validate(product)


# --- END_BLOCK_UPDATE_PRODUCT ---


# --- START_BLOCK_DELETE_PRODUCT ---
# CONTRACT:
#   PURPOSE: Delete a product by id.
#   INPUTS: { session: AsyncSession, product_id: UUID }
#   OUTPUTS: { bool - True if deleted }
#   ERRORS: HTTPException 404 if product not found
#   SIDE_EFFECTS: DB delete via repo, audit log entry
async def delete_product(session: AsyncSession, product_id: UUID) -> bool:
    # Get product info before deletion for audit
    product = await admin_catalog_repo.get_product(session, product_id)

    deleted = await admin_catalog_repo.delete_product(session, product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")

    logger.info("%s[BLOCK_DELETE_PRODUCT] product_id=%s", LOG_PREFIX, product_id)

    # Audit log
    audit = ProductAudit(
        product_id=product_id,
        admin_username="admin",
        action="DELETE",
        changes=json.dumps({"name": product.name if product else "unknown"}),
    )
    session.add(audit)
    await session.commit()

    return True


# --- END_BLOCK_DELETE_PRODUCT ---


# --- START_BLOCK_CREATE_OFFER ---
# CONTRACT:
#   PURPOSE: Create a new offer and return dict representation.
#   INPUTS: { session: AsyncSession, data: OfferCreate }
#   OUTPUTS: { dict - offer fields }
#   SIDE_EFFECTS: DB write via repo
async def create_offer(session: AsyncSession, data: OfferCreate) -> dict:
    offer = await admin_catalog_repo.create_offer(
        session,
        product_id=data.product_id,
        seller_id=data.seller_id,
        price=float(data.price),
        delivery_date=data.delivery_date,
        stock=data.stock,
    )
    logger.info("%s[BLOCK_CREATE_OFFER] offer_id=%s", LOG_PREFIX, offer.id)
    return {
        "id": str(offer.id),
        "product_id": str(offer.product_id),
        "seller_id": str(offer.seller_id),
        "price": float(offer.price),
        "delivery_date": offer.delivery_date.isoformat(),
        "stock": offer.stock,
    }


# --- END_BLOCK_CREATE_OFFER ---


# --- START_BLOCK_UPDATE_OFFER ---
# CONTRACT:
#   PURPOSE: Partial-update offer fields and return dict representation.
#   INPUTS: { session: AsyncSession, offer_id: UUID, data: OfferUpdate }
#   OUTPUTS: { dict - updated offer fields }
#   ERRORS: HTTPException 404 if offer not found
#   SIDE_EFFECTS: DB write via repo
async def update_offer(
    session: AsyncSession,
    offer_id: UUID,
    data: OfferUpdate,
) -> dict:
    updates = data.model_dump(exclude_unset=True)
    if "price" in updates and updates["price"] is not None:
        updates["price"] = float(updates["price"])

    offer = await admin_catalog_repo.update_offer(session, offer_id, **updates)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    logger.info(
        "%s[BLOCK_UPDATE_OFFER] offer_id=%s fields=%s",
        LOG_PREFIX,
        offer_id,
        list(updates.keys()),
    )
    return {
        "id": str(offer.id),
        "product_id": str(offer.product_id),
        "seller_id": str(offer.seller_id),
        "price": float(offer.price),
        "delivery_date": offer.delivery_date.isoformat(),
        "stock": offer.stock,
    }


# --- END_BLOCK_UPDATE_OFFER ---


# --- START_BLOCK_DELETE_OFFER ---
# CONTRACT:
#   PURPOSE: Delete an offer by id.
#   INPUTS: { session: AsyncSession, offer_id: UUID }
#   OUTPUTS: { bool - True if deleted }
#   ERRORS: HTTPException 404 if offer not found
#   SIDE_EFFECTS: DB delete via repo
async def delete_offer(session: AsyncSession, offer_id: UUID) -> bool:
    deleted = await admin_catalog_repo.delete_offer(session, offer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Offer not found")

    logger.info("%s[BLOCK_DELETE_OFFER] offer_id=%s", LOG_PREFIX, offer_id)
    return True


# --- END_BLOCK_DELETE_OFFER ---


# --- START_BLOCK_UPLOAD_AND_PERSIST_IMAGE ---
# CONTRACT:
#   PURPOSE: Persist original and thumbnail object keys after MinIO upload.
#   INPUTS: { session: AsyncSession, product_id: UUID, file: UploadFile }
#   OUTPUTS: { ImageUploadResponse - presigned URLs for original and thumbnail }
#   SIDE_EFFECTS: Writes to MinIO S3 storage and updates product DB row
async def upload_product_image_service(
    session: AsyncSession,
    product_id: UUID,
    file: UploadFile,
) -> ImageUploadResponse:
    product = await admin_catalog_repo.get_product(session, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    refs: StoredImageRefs = await upload_product_image(file)

    await admin_catalog_repo.save_product_image_keys(
        session,
        product_id,
        image_key=refs.image_object_key,
        thumbnail_key=refs.thumbnail_object_key,
    )

    logger.info(
        "%s[BLOCK_UPLOAD_AND_PERSIST_IMAGE] product_id=%s image_key=%s thumb_key=%s",
        LOG_PREFIX,
        product_id,
        refs.image_object_key,
        refs.thumbnail_object_key,
    )
    return ImageUploadResponse(
        image_url=refs.image_url,
        thumbnail_url=refs.thumbnail_url,
    )


# --- END_BLOCK_UPLOAD_AND_PERSIST_IMAGE ---
