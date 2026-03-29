# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test admin catalog API route registration.
# SCOPE: CRUD/image paths and async handler surface only.
# DEPENDS: inspect, app.api.v1.admin.catalog
# LINKS: V-M-API-ADMIN-CATALOG
# --- GRACE MODULE_MAP ---
# test_admin_catalog_router_registers_image_and_product_routes - Verifies critical admin routes
# test_admin_catalog_handlers_are_async - Verifies admin catalog handlers remain async
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for admin catalog API.

from __future__ import annotations

import inspect

import app.api.v1.admin.catalog as admin_catalog_api


def test_admin_catalog_router_registers_image_and_product_routes() -> None:
    routes = {route.path: route.methods for route in admin_catalog_api.router.routes}
    assert '/v1/admin/products' in routes
    assert '/v1/admin/products/{product_id}/image' in routes
    assert 'POST' in routes['/v1/admin/products/{product_id}/image']


def test_admin_catalog_handlers_are_async() -> None:
    assert inspect.iscoroutinefunction(admin_catalog_api.handle_create_product)
    assert inspect.iscoroutinefunction(admin_catalog_api.handle_upload_image)
    assert inspect.iscoroutinefunction(admin_catalog_api.require_admin)
