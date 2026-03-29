# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test public API route registration.
# SCOPE: Public router paths, methods, and async handler surface only.
# DEPENDS: inspect, app.api.v1.public
# LINKS: V-M-API-PUBLIC
# --- GRACE MODULE_MAP ---
# test_public_router_registers_catalog_routes - Verifies public route paths and methods
# test_public_handlers_are_async - Verifies public handlers remain async
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for public API.

from __future__ import annotations

import inspect

import app.api.v1.public as public_api


def test_public_router_registers_catalog_routes() -> None:
    routes = {route.path: route.methods for route in public_api.router.routes}
    assert '/v1/public/products' in routes
    assert '/v1/public/products/{product_id}' in routes
    assert 'GET' in routes['/v1/public/products']


def test_public_handlers_are_async() -> None:
    assert inspect.iscoroutinefunction(public_api.get_products)
    assert inspect.iscoroutinefunction(public_api.get_product_detail)
