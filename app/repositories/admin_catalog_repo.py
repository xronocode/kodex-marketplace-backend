# FILE: app/repositories/admin_catalog_repo.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Persist admin CRUD changes for products, sellers, offers, and media object keys.
# SCOPE: Admin-facing mutation and query functions for catalog entities.
# DEPENDS: M-DB, M-MODELS-CATALOG
# LINKS: M-REPO-ADMIN, V-M-REPO-ADMIN
# --- GRACE MODULE_MAP ---
# create_seller - Create a new Seller record
# list_sellers - Return all Seller records
# list_products - Return all Products with attributes, ordered by created_at desc
# create_product - Create a new Product record with status='published'
# update_product - Partial-update Product fields
# delete_product - Delete a Product by id
# create_offer - Create a new Offer record
# update_offer - Partial-update Offer fields
# delete_offer - Delete an Offer by id
# save_product_image_keys - Persist image and thumbnail object keys on a Product
# create_product_attribute - Create a new ProductAttribute record
# get_product - Fetch a single Product by id (no status filter)
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — admin catalog CRUD repository.

from __future__ import annotations

from typing import Optional
import logging
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Offer, Product, ProductAttribute, Seller

logger = logging.getLogger(__name__)


# --- START_BLOCK_PERSIST_CATALOG_MUTATION ---


# --- START_BLOCK_CREATE_SELLER ---
# CONTRACT:
#   PURPOSE: Create and persist a new Seller record.
#   INPUTS: { session: AsyncSession, name: str }
#   OUTPUTS: { Seller }
async def create_seller(session: AsyncSession, name: str) -> Seller:
    seller = Seller(name=name)
    session.add(seller)
    await session.flush()
    logger.info(
        "[AdminRepo][create_seller][BLOCK_CREATE_SELLER] seller_id=%s", seller.id
    )
    return seller


# --- END_BLOCK_CREATE_SELLER ---


# --- START_BLOCK_LIST_SELLERS ---
# CONTRACT:
#   PURPOSE: Return all Seller records ordered by created_at.
#   INPUTS: { session: AsyncSession }
#   OUTPUTS: { list[Seller] }
async def list_sellers(session: AsyncSession) -> list[Seller]:
    stmt = select(Seller).order_by(Seller.created_at)
    result = await session.execute(stmt)
    return list(result.scalars().all())


# --- END_BLOCK_LIST_SELLERS ---


# --- START_BLOCK_LIST_PRODUCTS ---
# CONTRACT:
#   PURPOSE: Return all Product records with eagerly loaded attributes, ordered by created_at desc.
#   INPUTS: { session: AsyncSession }
#   OUTPUTS: { list[Product] }
async def list_products(session: AsyncSession) -> list[Product]:
    stmt = (
        select(Product)
        .options(selectinload(Product.attributes))
        .order_by(Product.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


# --- END_BLOCK_LIST_PRODUCTS ---


# --- START_BLOCK_CREATE_PRODUCT ---
# CONTRACT:
#   PURPOSE: Create and persist a new Product with status='published'.
#   INPUTS: { session: AsyncSession, name: str, description: str, price: Decimal, stock: int, merchant_id: UUID|None }
#   OUTPUTS: { Product }
async def create_product(
    session: AsyncSession,
    name: str,
    description: str,
    price: float,
    stock: int,
    merchant_id: Optional[UUID] = None,
) -> Product:
    product = Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        merchant_id=merchant_id,
        status="published",
    )
    session.add(product)
    await session.flush()
    logger.info(
        "[AdminRepo][create_product][BLOCK_CREATE_PRODUCT] product_id=%s", product.id
    )
    return product


# --- END_BLOCK_CREATE_PRODUCT ---


# --- START_BLOCK_UPDATE_PRODUCT ---
# CONTRACT:
#   PURPOSE: Partial-update Product fields from kwargs.
#   INPUTS: { session: AsyncSession, product_id: UUID, **kwargs: name|description|price|stock }
#   OUTPUTS: { Product|None }
async def update_product(
    session: AsyncSession,
    product_id: UUID,
    **kwargs,
) -> Optional[Product]:
    allowed = {"name", "description", "price", "stock"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return await get_product(session, product_id)

    product = await get_product(session, product_id)
    if product is None:
        return None

    for field, value in updates.items():
        setattr(product, field, value)

    await session.flush()
    logger.info(
        "[AdminRepo][update_product][BLOCK_UPDATE_PRODUCT] product_id=%s fields=%s",
        product_id,
        list(updates.keys()),
    )
    return product


# --- END_BLOCK_UPDATE_PRODUCT ---


# --- START_BLOCK_DELETE_PRODUCT ---
# CONTRACT:
#   PURPOSE: Delete a Product by id.
#   INPUTS: { session: AsyncSession, product_id: UUID }
#   OUTPUTS: { bool - True if deleted, False if not found }
async def delete_product(session: AsyncSession, product_id: UUID) -> bool:
    product = await get_product(session, product_id)
    if product is None:
        return False

    await session.delete(product)
    await session.flush()
    logger.info(
        "[AdminRepo][delete_product][BLOCK_DELETE_PRODUCT] product_id=%s", product_id
    )
    return True


# --- END_BLOCK_DELETE_PRODUCT ---


# --- START_BLOCK_CREATE_OFFER ---
# CONTRACT:
#   PURPOSE: Create and persist a new Offer record.
#   INPUTS: { session: AsyncSession, product_id: UUID, seller_id: UUID, price: Decimal, delivery_date: date, stock: int }
#   OUTPUTS: { Offer }
async def create_offer(
    session: AsyncSession,
    product_id: UUID,
    seller_id: UUID,
    price: float,
    delivery_date: date,
    stock: int,
) -> Offer:
    offer = Offer(
        product_id=product_id,
        seller_id=seller_id,
        price=price,
        delivery_date=delivery_date,
        stock=stock,
    )
    session.add(offer)
    await session.flush()
    logger.info("[AdminRepo][create_offer][BLOCK_CREATE_OFFER] offer_id=%s", offer.id)
    return offer


# --- END_BLOCK_CREATE_OFFER ---


# --- START_BLOCK_UPDATE_OFFER ---
# CONTRACT:
#   PURPOSE: Partial-update Offer fields from kwargs.
#   INPUTS: { session: AsyncSession, offer_id: UUID, **kwargs: price|delivery_date|stock }
#   OUTPUTS: { Offer|None }
async def update_offer(
    session: AsyncSession,
    offer_id: UUID,
    **kwargs,
) -> Optional[Offer]:
    allowed = {"price", "delivery_date", "stock"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        stmt = select(Offer).where(Offer.id == offer_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    stmt = select(Offer).where(Offer.id == offer_id)
    result = await session.execute(stmt)
    offer = result.scalar_one_or_none()
    if offer is None:
        return None

    for field, value in updates.items():
        setattr(offer, field, value)

    await session.flush()
    logger.info(
        "[AdminRepo][update_offer][BLOCK_UPDATE_OFFER] offer_id=%s fields=%s",
        offer_id,
        list(updates.keys()),
    )
    return offer


# --- END_BLOCK_UPDATE_OFFER ---


# --- START_BLOCK_DELETE_OFFER ---
# CONTRACT:
#   PURPOSE: Delete an Offer by id.
#   INPUTS: { session: AsyncSession, offer_id: UUID }
#   OUTPUTS: { bool - True if deleted, False if not found }
async def delete_offer(session: AsyncSession, offer_id: UUID) -> bool:
    stmt = select(Offer).where(Offer.id == offer_id)
    result = await session.execute(stmt)
    offer = result.scalar_one_or_none()
    if offer is None:
        return False

    await session.delete(offer)
    await session.flush()
    logger.info("[AdminRepo][delete_offer][BLOCK_DELETE_OFFER] offer_id=%s", offer_id)
    return True


# --- END_BLOCK_DELETE_OFFER ---


# --- START_BLOCK_SAVE_PRODUCT_IMAGE_KEYS ---
# CONTRACT:
#   PURPOSE: Persist original and thumbnail object key references on products.
#   INPUTS: { session: AsyncSession, product_id: UUID, image_key: str, thumbnail_key: str }
#   OUTPUTS: { Product|None - Updated product or None if not found }
async def save_product_image_keys(
    session: AsyncSession,
    product_id: UUID,
    image_key: str,
    thumbnail_key: str,
) -> Optional[Product]:
    product = await get_product(session, product_id)
    if product is None:
        return None

    product.image_object_key = image_key
    product.thumbnail_object_key = thumbnail_key
    await session.flush()
    logger.info(
        "[AdminRepo][save_product_image_keys][BLOCK_SAVE_PRODUCT_IMAGE_KEYS] product_id=%s",
        product_id,
    )
    return product


# --- END_BLOCK_SAVE_PRODUCT_IMAGE_KEYS ---


# --- START_BLOCK_CREATE_PRODUCT_ATTRIBUTE ---
# CONTRACT:
#   PURPOSE: Create and persist a new ProductAttribute record.
#   INPUTS: { session: AsyncSession, product_id: UUID, key: str, value: str }
#   OUTPUTS: { ProductAttribute }
async def create_product_attribute(
    session: AsyncSession,
    product_id: UUID,
    key: str,
    value: str,
) -> ProductAttribute:
    attr = ProductAttribute(product_id=product_id, key=key, value=value)
    session.add(attr)
    await session.flush()
    logger.info(
        "[AdminRepo][create_product_attribute][BLOCK_CREATE_PRODUCT_ATTRIBUTE] attr_id=%s",
        attr.id,
    )
    return attr


# --- END_BLOCK_CREATE_PRODUCT_ATTRIBUTE ---


# --- START_BLOCK_GET_PRODUCT ---
# CONTRACT:
#   PURPOSE: Fetch a single Product by id with no status filter (admin context).
#   INPUTS: { session: AsyncSession, product_id: UUID }
#   OUTPUTS: { Product|None }
async def get_product(session: AsyncSession, product_id: UUID) -> Optional[Product]:
    stmt = select(Product).where(Product.id == product_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# --- END_BLOCK_GET_PRODUCT ---


# --- END_BLOCK_PERSIST_CATALOG_MUTATION ---
