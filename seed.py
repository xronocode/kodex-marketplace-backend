# FILE: seed.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Populate a fresh database with demo merchant, products, sellers, attributes, offers, and valid delivery dates.
# SCOPE: Standalone async seed script — creates demo data for UC-005.
# INPUTS: seed-config (SeedParameters)
# OUTPUTS: seed-summary (SeedCounts)
# ERRORS: SEED_FAILURE
# DEPENDS: M-DB, M-MIGRATIONS, M-MODELS-CATALOG, M-MODELS-PLATFORM, M-CONFIG (app.core.config)
# LINKS: M-SEED, V-M-SEED
# PATH: seed.py
# VERIFICATION: V-M-SEED
# --- GRACE MODULE_MAP ---
# SeedParameters - Configuration dataclass for seed generation limits
# SeedCounts - Result dataclass with counts of created entities
# generate_delivery_dates - CRITICAL: produces valid delivery dates relative to today
# run_seed - Main async seed routine
# main - CLI entry point via asyncio.run()
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 demo data seed for UC-005.

from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from random import choice, randint, sample, uniform
from uuid import uuid4

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.catalog import Offer, Product, ProductAttribute, Seller
from app.models.platform import Merchant

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("seed")
LOG_PREFIX = "[Seed]"


# --- START_BLOCK_SEED_PARAMETERS ---
@dataclass(frozen=True)
class SeedParameters:
    """
    CONTRACT:
        PURPOSE: Immutable configuration for seed data generation limits.
        INPUTS: {}
        OUTPUTS: { SeedParameters }
        LINKS: M-SEED
    """

    num_sellers: int = 6
    num_products: int = 120
    min_attributes_per_product: int = 2
    max_attributes_per_product: int = 6
    min_offers_per_product: int = 2
    max_offers_per_product: int = 8
    price_min: Decimal = Decimal("100")
    price_max: Decimal = Decimal("50000")
    stock_min: int = 0
    stock_max: int = 100
    offer_stock_max: int = 50
    delivery_days_range: int = 6


# --- END_BLOCK_SEED_PARAMETERS ---


# --- START_BLOCK_SEED_COUNTS ---
@dataclass
class SeedCounts:
    """
    CONTRACT:
        PURPOSE: Summary of entities created during seed execution.
        INPUTS: {}
        OUTPUTS: { SeedCounts }
        LINKS: M-SEED
    """

    merchants: int = 0
    sellers: int = 0
    products: int = 0
    attributes: int = 0
    offers: int = 0


# --- END_BLOCK_SEED_COUNTS ---


# --- START_BLOCK_GENERATE_DELIVERY_DATES ---
# CONTRACT:
#   PURPOSE: Generate a list of valid delivery dates relative to today.
#   INPUTS: { count: int, days_range: int }
#   OUTPUTS: { list[date] — each date is date.today() + timedelta(days=randint(0, days_range)) }
#   CRITICAL: delivery_date ALWAYS = date.today() + timedelta(days=randint(0,6)). Never hardcoded.
#   LINKS: BLOCK_GENERATE_DELIVERY_DATES, V-M-SEED
def generate_delivery_dates(count: int, days_range: int = 6) -> list[date]:
    """
    Generate *count* delivery dates, each offset from today by a random
    number of days in [0, days_range].

    IRON RULE: no hardcoded date strings anywhere.
    """
    today = date.today()
    return [today + timedelta(days=randint(0, days_range)) for _ in range(count)]


# --- END_BLOCK_GENERATE_DELIVERY_DATES ---


# --- START_BLOCK_ATTRIBUTE_KEY_POOL ---
ATTRIBUTE_KEYS: list[str] = [
    "Цвет",
    "Вес",
    "Размер",
    "Материал",
    "Бренд",
    "Страна производства",
    "Гарантия",
    "Мощность",
    "Объём",
    "Тип упаковки",
]
# --- END_BLOCK_ATTRIBUTE_KEY_POOL ---


# --- START_BLOCK_RUN_SEED ---
# CONTRACT:
#   PURPOSE: Main async seed routine — creates all demo entities and commits in one transaction.
#   INPUTS: { params: SeedParameters }
#   OUTPUTS: { SeedCounts }
#   ERRORS: SEED_FAILURE — raised on any DB or data generation error; transaction is rolled back.
#   SIDE_EFFECTS: writes to merchants, sellers, products, product_attributes, offers tables.
#   LINKS: M-SEED, V-M-SEED, BLOCK_GENERATE_DELIVERY_DATES
async def run_seed(params: SeedParameters | None = None) -> SeedCounts:
    params = params or SeedParameters()
    counts = SeedCounts()
    fake = Faker("ru_RU")

    settings = get_settings()
    logger.info(
        "%s[BLOCK_RUN_SEED] Creating async engine — dsn=%s",
        LOG_PREFIX,
        settings.database_url.split("@")[-1],
    )

    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with session_factory() as session:
            async with session.begin():
                # --- START_BLOCK_CREATE_MERCHANT ---
                # CONTRACT:
                #   PURPOSE: Create the single demo merchant.
                #   INPUTS: { session: AsyncSession }
                #   OUTPUTS: { Merchant }
                merchant = Merchant(
                    name="Kodex Demo Store",
                    slug="kodex-demo-store",
                    is_active=True,
                )
                session.add(merchant)
                await session.flush()
                counts.merchants = 1
                logger.info(
                    "%s[BLOCK_CREATE_MERCHANT] merchant_id=%s",
                    LOG_PREFIX,
                    merchant.id,
                )
                # --- END_BLOCK_CREATE_MERCHANT ---

                # --- START_BLOCK_CREATE_SELLERS ---
                # CONTRACT:
                #   PURPOSE: Create random sellers with Russian names.
                #   INPUTS: { session: AsyncSession, params.num_sellers: int }
                #   OUTPUTS: { list[Seller] }
                sellers: list[Seller] = []
                for _ in range(params.num_sellers):
                    seller = Seller(name=fake.company())
                    session.add(seller)
                    sellers.append(seller)
                await session.flush()
                counts.sellers = len(sellers)
                logger.info(
                    "%s[BLOCK_CREATE_SELLERS] created=%d",
                    LOG_PREFIX,
                    counts.sellers,
                )
                # --- END_BLOCK_CREATE_SELLERS ---

                # --- START_BLOCK_CREATE_PRODUCTS ---
                # CONTRACT:
                #   PURPOSE: Create products with attributes and offers.
                #   INPUTS: { session: AsyncSession, merchant: Merchant, sellers: list[Seller], params: SeedParameters }
                #   OUTPUTS: { counts: SeedCounts }
                all_products: list[Product] = []
                for i in range(params.num_products):
                    price_raw = float(
                        uniform(float(params.price_min), float(params.price_max))
                    )
                    # Generate placeholder image URL using picsum.photos
                    image_id = i % 100  # Use different image IDs for variety
                    product = Product(
                        merchant_id=merchant.id,
                        name=fake.catch_phrase(),
                        description=fake.text(max_nb_chars=300),
                        price=Decimal(f"{price_raw:.2f}"),
                        stock=randint(params.stock_min, params.stock_max),
                        status="published",
                        image_object_key=f"https://picsum.photos/seed/{image_id}/800/600.jpg",
                        thumbnail_object_key=f"https://picsum.photos/seed/{image_id}/300/300.jpg",
                    )
                    session.add(product)
                    all_products.append(product)

                await session.flush()
                counts.products = len(all_products)
                logger.info(
                    "%s[BLOCK_CREATE_PRODUCTS] created=%d",
                    LOG_PREFIX,
                    counts.products,
                )
                # --- END_BLOCK_CREATE_PRODUCTS ---

                # --- START_BLOCK_CREATE_ATTRIBUTES ---
                # CONTRACT:
                #   PURPOSE: Attach 2-6 random key-value attributes to each product.
                #   INPUTS: { session: AsyncSession, products: list[Product], params: SeedParameters }
                #   OUTPUTS: { counts.attributes updated }
                attr_count = 0
                for product in all_products:
                    num_attrs = randint(
                        params.min_attributes_per_product,
                        params.max_attributes_per_product,
                    )
                    selected_keys = sample(
                        ATTRIBUTE_KEYS, min(num_attrs, len(ATTRIBUTE_KEYS))
                    )
                    for attr_key in selected_keys:
                        attr_value = fake.word()
                        pa = ProductAttribute(
                            product_id=product.id,
                            key=attr_key,
                            value=attr_value,
                        )
                        session.add(pa)
                        attr_count += 1

                await session.flush()
                counts.attributes = attr_count
                logger.info(
                    "%s[BLOCK_CREATE_ATTRIBUTES] created=%d",
                    LOG_PREFIX,
                    counts.attributes,
                )
                # --- END_BLOCK_CREATE_ATTRIBUTES ---

                # --- START_BLOCK_CREATE_OFFERS ---
                # CONTRACT:
                #   PURPOSE: Create 2-8 offers per product from distinct sellers with dynamic delivery dates.
                #   INPUTS: { session: AsyncSession, products: list[Product], sellers: list[Seller], params: SeedParameters }
                #   OUTPUTS: { counts.offers updated }
                #   CRITICAL: delivery_date = date.today() + timedelta(days=randint(0, params.delivery_days_range))
                offer_count = 0
                for product in all_products:
                    num_offers = randint(
                        params.min_offers_per_product,
                        min(params.max_offers_per_product, len(sellers)),
                    )
                    selected_sellers = sample(sellers, num_offers)
                    product_price_float = float(product.price)

                    for seller in selected_sellers:
                        offer_price = Decimal(
                            f"{product_price_float * uniform(0.8, 1.2):.2f}"
                        )
                        offer = Offer(
                            product_id=product.id,
                            seller_id=seller.id,
                            price=offer_price,
                            stock=randint(0, params.offer_stock_max),
                            delivery_date=date.today()
                            + timedelta(days=randint(0, params.delivery_days_range)),
                        )
                        session.add(offer)
                        offer_count += 1

                await session.flush()
                counts.offers = offer_count
                logger.info(
                    "%s[BLOCK_CREATE_OFFERS] created=%d",
                    LOG_PREFIX,
                    counts.offers,
                )
                # --- END_BLOCK_CREATE_OFFERS ---

            logger.info(
                "%s[BLOCK_RUN_SEED] Transaction committed successfully",
                LOG_PREFIX,
            )

    except Exception:
        logger.exception("%s[BLOCK_RUN_SEED] SEED_FAILURE", LOG_PREFIX)
        raise
    finally:
        await engine.dispose()

    return counts


# --- END_BLOCK_RUN_SEED ---


# --- START_BLOCK_MAIN_ENTRY ---
# CONTRACT:
#   PURPOSE: CLI entry point — runs seed and prints summary.
#   INPUTS: { argv: sys.argv (unused) }
#   OUTPUTS: { stdout summary }
#   ERRORS: exits with code 1 on SEED_FAILURE.
#   LINKS: BLOCK_RUN_SEED
def main() -> None:
    logger.info("%s[BLOCK_MAIN_ENTRY] Starting seed script", LOG_PREFIX)
    counts = asyncio.run(run_seed())
    print("\n=== Seed Summary ===")
    print(f"  Merchants : {counts.merchants}")
    print(f"  Sellers   : {counts.sellers}")
    print(f"  Products  : {counts.products}")
    print(f"  Attributes: {counts.attributes}")
    print(f"  Offers    : {counts.offers}")
    print("====================\n")


if __name__ == "__main__":
    main()


# --- END_BLOCK_MAIN_ENTRY ---
