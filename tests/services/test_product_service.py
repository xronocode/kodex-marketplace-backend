# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test product service async entrypoints.
# SCOPE: Public list/detail/search exports and response-building block markers only.
# DEPENDS: inspect, app.services.product_service, tests.helpers
# LINKS: V-M-SVC-PRODUCT
# --- GRACE MODULE_MAP ---
# test_product_service_exports_async_entrypoints - Verifies product service call surface
# test_product_service_contains_public_response_markers - Verifies product response assembly markers
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for product service.

from __future__ import annotations

import inspect

import app.services.product_service as product_service
from tests.helpers import read_repo_text


def test_product_service_exports_async_entrypoints() -> None:
    assert inspect.iscoroutinefunction(product_service.list_products)
    assert inspect.iscoroutinefunction(product_service.get_product_detail)
    assert inspect.iscoroutinefunction(product_service.search_products)


def test_product_service_contains_public_response_markers() -> None:
    source = read_repo_text('app/services/product_service.py')
    assert 'BLOCK_LIST_PRODUCTS' in source
    assert 'BLOCK_GET_PRODUCT_DETAIL' in source
