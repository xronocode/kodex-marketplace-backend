# FILE: app/api/v1/admin/catalog.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Expose admin CRUD endpoints for products, sellers, offers, and product image uploads.
# SCOPE: Admin-facing REST API routes for catalog management behind JWT auth.
# DEPENDS: M-AUTH (app.core.auth), M-SVC-ADMIN (app.services.admin_catalog_service), M-DB (app.core.database), M-SCHEMAS-ADMIN (app.schemas.admin)
# LINKS: M-API-ADMIN-CATALOG, V-M-API-ADMIN-CATALOG
# --- GRACE MODULE_MAP ---
# router - APIRouter with prefix="/v1/admin", tags=["admin-catalog"]
# require_admin - Dependency that extracts and validates Bearer JWT for platform_admin role
# handle_create_seller - POST /sellers
# handle_list_sellers - GET /sellers
# handle_create_product - POST /products
# handle_list_products - GET /products
# handle_update_product - PUT /products/{product_id}
# handle_delete_product - DELETE /products/{product_id}
# handle_create_offer - POST /offers
# handle_update_offer - PUT /offers/{offer_id}
# handle_delete_offer - DELETE /offers/{offer_id}
# handle_upload_image - POST /products/{product_id}/image
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — admin catalog API routes.

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_admin
from app.core.database import get_session
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
from app.services import admin_catalog_service

logger = logging.getLogger(__name__)
LOG_PREFIX = "[AdminCatalogApi]"


# --- START_BLOCK_REQUIRE_ADMIN ---
# CONTRACT:
#   PURPOSE: FastAPI dependency that extracts the Bearer token and validates admin identity.
#   INPUTS: { authorization: str - from Header("Authorization") }
#   OUTPUTS: { dict - decoded JWT payload with role == platform_admin }
#   ERRORS: HTTPException 401 if header missing, malformed, or token invalid
#   LINKS: M-AUTH, BLOCK_GET_CURRENT_ADMIN
async def require_admin(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ")
    return get_current_admin(token)


# --- END_BLOCK_REQUIRE_ADMIN ---


router = APIRouter(prefix="/v1/admin", tags=["admin-catalog"])


# --- START_BLOCK_HANDLE_CREATE_SELLER ---
# CONTRACT:
#   PURPOSE: POST /v1/admin/sellers — create a new seller.
#   INPUTS: { data: SellerCreate }
#   OUTPUTS: { SellerResponse }
#   ERRORS: ADMIN_HTTP_FAILURE — propagated from service layer
#   SIDE_EFFECTS: DB write via admin_catalog_service
#   LINKS: BLOCK_CREATE_SELLER
@router.post("/sellers", response_model=SellerResponse)
async def handle_create_seller(
    data: SellerCreate,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin),
) -> SellerResponse:
    logger.info("%s[BLOCK_HANDLE_CREATE_SELLER] admin=%s", LOG_PREFIX, admin.get("sub"))
    return await admin_catalog_service.create_seller(session, data)


# --- END_BLOCK_HANDLE_CREATE_SELLER ---


# --- START_BLOCK_HANDLE_LIST_SELLERS ---
# CONTRACT:
#   PURPOSE: GET /v1/admin/sellers — list all sellers.
#   INPUTS: {}
#   OUTPUTS: { list[SellerResponse] }
#   ERRORS: ADMIN_HTTP_FAILURE — propagated from service layer
#   LINKS: BLOCK_LIST_SELLERS
@router.get("/sellers", response_model=list[SellerResponse])
async def handle_list_sellers(
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin),
) -> list[SellerResponse]:
    logger.info("%s[BLOCK_HANDLE_LIST_SELLERS] admin=%s", LOG_PREFIX, admin.get("sub"))
    return await admin_catalog_service.list_sellers(session)


# --- END_BLOCK_HANDLE_LIST_SELLERS ---


# --- START_BLOCK_HANDLE_CREATE_PRODUCT ---
# CONTRACT:
#   PURPOSE: POST /v1/admin/products — create a new product.
#   INPUTS: { data: ProductCreate }
#   OUTPUTS: { ProductAdminResponse }
#   ERRORS: ADMIN_HTTP_FAILURE — propagated from service layer
#   SIDE_EFFECTS: DB write via admin_catalog_service
#   LINKS: BLOCK_CREATE_PRODUCT
@router.post("/products", response_model=ProductAdminResponse)
async def handle_create_product(
    data: ProductCreate,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin),
) -> ProductAdminResponse:
    logger.info(
        "%s[BLOCK_HANDLE_CREATE_PRODUCT] admin=%s", LOG_PREFIX, admin.get("sub")
    )
    return await admin_catalog_service.create_product(session, data)


# --- END_BLOCK_HANDLE_CREATE_PRODUCT ---


# --- START_BLOCK_HANDLE_LIST_PRODUCTS ---
# CONTRACT:
#   PURPOSE: GET /v1/admin/products — list all products.
#   INPUTS: {}
#   OUTPUTS: { ProductAdminListResponse }
#   ERRORS: ADMIN_HTTP_FAILURE — propagated from service layer
#   LINKS: BLOCK_LIST_PRODUCTS
@router.get("/products", response_model=ProductAdminListResponse)
async def handle_list_products(
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin),
) -> ProductAdminListResponse:
    logger.info("%s[BLOCK_HANDLE_LIST_PRODUCTS] admin=%s", LOG_PREFIX, admin.get("sub"))
    return await admin_catalog_service.list_products(session)


# --- END_BLOCK_HANDLE_LIST_PRODUCTS ---


# --- START_BLOCK_HANDLE_UPDATE_PRODUCT ---
# CONTRACT:
#   PURPOSE: PUT /v1/admin/products/{product_id} — partial-update a product.
#   INPUTS: { product_id: UUID, data: ProductUpdate }
#   OUTPUTS: { ProductAdminResponse }
#   ERRORS: HTTPException 404 if product not found; ADMIN_HTTP_FAILURE otherwise
#   SIDE_EFFECTS: DB write via admin_catalog_service
#   LINKS: BLOCK_UPDATE_PRODUCT
@router.put("/products/{product_id}", response_model=ProductAdminResponse)
async def handle_update_product(
    product_id: UUID,
    data: ProductUpdate,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin),
) -> ProductAdminResponse:
    logger.info(
        "%s[BLOCK_HANDLE_UPDATE_PRODUCT] product_id=%s admin=%s",
        LOG_PREFIX,
        product_id,
        admin.get("sub"),
    )
    return await admin_catalog_service.update_product(session, product_id, data)


# --- END_BLOCK_HANDLE_UPDATE_PRODUCT ---


# --- START_BLOCK_HANDLE_DELETE_PRODUCT ---
# CONTRACT:
#   PURPOSE: DELETE /v1/admin/products/{product_id} — delete a product.
#   INPUTS: { product_id: UUID }
#   OUTPUTS: { dict - {"deleted": True} }
#   ERRORS: HTTPException 404 if product not found; ADMIN_HTTP_FAILURE otherwise
#   SIDE_EFFECTS: DB delete via admin_catalog_service
#   LINKS: BLOCK_DELETE_PRODUCT
@router.delete("/products/{product_id}")
async def handle_delete_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin),
) -> dict:
    logger.info(
        "%s[BLOCK_HANDLE_DELETE_PRODUCT] product_id=%s admin=%s",
        LOG_PREFIX,
        product_id,
        admin.get("sub"),
    )
    await admin_catalog_service.delete_product(session, product_id)
    return {"deleted": True}


# --- END_BLOCK_HANDLE_DELETE_PRODUCT ---


# --- START_BLOCK_HANDLE_CREATE_OFFER ---
# CONTRACT:
#   PURPOSE: POST /v1/admin/offers — create a new offer.
#   INPUTS: { data: OfferCreate }
#   OUTPUTS: { dict - offer fields }
#   ERRORS: ADMIN_HTTP_FAILURE — propagated from service layer
#   SIDE_EFFECTS: DB write via admin_catalog_service
#   LINKS: BLOCK_CREATE_OFFER
@router.post("/offers")
async def handle_create_offer(
    data: OfferCreate,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin),
) -> dict:
    logger.info("%s[BLOCK_HANDLE_CREATE_OFFER] admin=%s", LOG_PREFIX, admin.get("sub"))
    return await admin_catalog_service.create_offer(session, data)


# --- END_BLOCK_HANDLE_CREATE_OFFER ---


# --- START_BLOCK_HANDLE_UPDATE_OFFER ---
# CONTRACT:
#   PURPOSE: PUT /v1/admin/offers/{offer_id} — partial-update an offer.
#   INPUTS: { offer_id: UUID, data: OfferUpdate }
#   OUTPUTS: { dict - updated offer fields }
#   ERRORS: HTTPException 404 if offer not found; ADMIN_HTTP_FAILURE otherwise
#   SIDE_EFFECTS: DB write via admin_catalog_service
#   LINKS: BLOCK_UPDATE_OFFER
@router.put("/offers/{offer_id}")
async def handle_update_offer(
    offer_id: UUID,
    data: OfferUpdate,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin),
) -> dict:
    logger.info(
        "%s[BLOCK_HANDLE_UPDATE_OFFER] offer_id=%s admin=%s",
        LOG_PREFIX,
        offer_id,
        admin.get("sub"),
    )
    return await admin_catalog_service.update_offer(session, offer_id, data)


# --- END_BLOCK_HANDLE_UPDATE_OFFER ---


# --- START_BLOCK_HANDLE_DELETE_OFFER ---
# CONTRACT:
#   PURPOSE: DELETE /v1/admin/offers/{offer_id} — delete an offer.
#   INPUTS: { offer_id: UUID }
#   OUTPUTS: { dict - {"deleted": True} }
#   ERRORS: HTTPException 404 if offer not found; ADMIN_HTTP_FAILURE otherwise
#   SIDE_EFFECTS: DB delete via admin_catalog_service
#   LINKS: BLOCK_DELETE_OFFER
@router.delete("/offers/{offer_id}")
async def handle_delete_offer(
    offer_id: UUID,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin),
) -> dict:
    logger.info(
        "%s[BLOCK_HANDLE_DELETE_OFFER] offer_id=%s admin=%s",
        LOG_PREFIX,
        offer_id,
        admin.get("sub"),
    )
    await admin_catalog_service.delete_offer(session, offer_id)
    return {"deleted": True}


# --- END_BLOCK_HANDLE_DELETE_OFFER ---


# --- START_BLOCK_HANDLE_IMAGE_UPLOAD ---
# CONTRACT:
#   PURPOSE: POST /v1/admin/products/{product_id}/image — upload a product image.
#   INPUTS: { product_id: UUID, file: UploadFile }
#   OUTPUTS: { ImageUploadResponse }
#   ERRORS: HTTPException 404 if product not found; ADMIN_HTTP_FAILURE otherwise
#   SIDE_EFFECTS: S3 upload + DB write via admin_catalog_service
#   LINKS: BLOCK_UPLOAD_AND_PERSIST_IMAGE
@router.post("/products/{product_id}/image", response_model=ImageUploadResponse)
async def handle_upload_image(
    product_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin),
) -> ImageUploadResponse:
    logger.info(
        "%s[BLOCK_HANDLE_IMAGE_UPLOAD] product_id=%s filename=%s admin=%s",
        LOG_PREFIX,
        product_id,
        file.filename,
        admin.get("sub"),
    )
    return await admin_catalog_service.upload_product_image_service(
        session, product_id, file
    )


# --- END_BLOCK_HANDLE_IMAGE_UPLOAD ---
