# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test admin catalog service mutation entrypoints.
# SCOPE: Async CRUD/image helpers and upload persistence marker only.
# DEPENDS: inspect, app.services.admin_catalog_service, tests.helpers
# LINKS: V-M-SVC-ADMIN
# --- GRACE MODULE_MAP ---
# test_admin_catalog_service_exports_async_entrypoints - Verifies admin service call surface
# test_admin_catalog_service_contains_upload_marker - Verifies image upload orchestration marker
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for admin catalog service.

from __future__ import annotations

import inspect

import app.services.admin_catalog_service as admin_catalog_service
from tests.helpers import read_repo_text


def test_admin_catalog_service_exports_async_entrypoints() -> None:
    exported = [
        admin_catalog_service.create_seller,
        admin_catalog_service.list_sellers,
        admin_catalog_service.create_product,
        admin_catalog_service.update_product,
        admin_catalog_service.delete_product,
        admin_catalog_service.create_offer,
        admin_catalog_service.update_offer,
        admin_catalog_service.delete_offer,
        admin_catalog_service.upload_product_image_service,
    ]

    assert all(inspect.iscoroutinefunction(fn) for fn in exported)


def test_admin_catalog_service_contains_upload_marker() -> None:
    source = read_repo_text('app/services/admin_catalog_service.py')
    assert 'BLOCK_UPLOAD_AND_PERSIST_IMAGE' in source
