# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test product repository async entrypoints.
# SCOPE: Public repository function availability and nearest-delivery query marker only.
# DEPENDS: inspect, app.repositories.product_repo, tests.helpers
# LINKS: V-M-REPO-PRODUCT
# --- GRACE MODULE_MAP ---
# test_product_repo_exports_async_entrypoints - Verifies repository call surface
# test_product_repo_source_mentions_nearest_delivery_calculation - Verifies nearest-delivery query intent
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for product repository.

from __future__ import annotations

import inspect

import app.repositories.product_repo as product_repo
from tests.helpers import read_repo_text


def test_product_repo_exports_async_entrypoints() -> None:
    assert inspect.iscoroutinefunction(product_repo.list_paginated)
    assert inspect.iscoroutinefunction(product_repo.get_detail)
    assert inspect.iscoroutinefunction(product_repo.search)


def test_product_repo_source_mentions_nearest_delivery_calculation() -> None:
    source = read_repo_text('app/repositories/product_repo.py')
    assert 'nearest_delivery_date' in source
    assert 'min(Offer.delivery_date)' in source or 'func.min' in source
