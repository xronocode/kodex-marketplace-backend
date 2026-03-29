# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test catalog ORM model shape.
# SCOPE: Table names, critical Phase 2 prep columns, and search indexes only.
# DEPENDS: app.models.catalog
# LINKS: V-M-MODELS-CATALOG
# --- GRACE MODULE_MAP ---
# test_product_model_has_phase2_prep_columns - Verifies merchant/status/search fields
# test_offer_and_attribute_models_expose_expected_tables - Verifies related table names
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for catalog models.

from __future__ import annotations

from app.models.catalog import Offer, Product, ProductAttribute, Seller


def test_product_model_has_phase2_prep_columns() -> None:
    columns = set(Product.__table__.c.keys())
    index_names = {index.name for index in Product.__table__.indexes}

    assert {'merchant_id', 'status', 'search_vector'} <= columns
    assert {'ix_products_merchant_id', 'ix_products_status', 'ix_products_search_vector'} <= index_names


def test_offer_and_attribute_models_expose_expected_tables() -> None:
    assert Seller.__tablename__ == 'sellers'
    assert Offer.__tablename__ == 'offers'
    assert ProductAttribute.__tablename__ == 'product_attributes'
    assert 'delivery_date' in Offer.__table__.c.keys()
