# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test admin auth API route registration.
# SCOPE: Login route path, methods, and async handler surface only.
# DEPENDS: inspect, app.api.v1.admin.auth
# LINKS: V-M-API-ADMIN-AUTH
# --- GRACE MODULE_MAP ---
# test_admin_auth_router_registers_login_route - Verifies login route path and method
# test_admin_auth_handlers_are_async - Verifies auth handlers remain async
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for admin auth API.

from __future__ import annotations

import inspect

import app.api.v1.admin.auth as admin_auth_api


def test_admin_auth_router_registers_login_route() -> None:
    routes = {route.path: route.methods for route in admin_auth_api.router.routes}
    assert '/v1/admin/auth/login' in routes
    assert 'POST' in routes['/v1/admin/auth/login']


def test_admin_auth_handlers_are_async() -> None:
    assert inspect.iscoroutinefunction(admin_auth_api.handle_login)
    assert inspect.iscoroutinefunction(admin_auth_api._authenticate)
