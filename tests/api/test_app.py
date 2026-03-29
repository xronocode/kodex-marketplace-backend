# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test FastAPI app route registration.
# SCOPE: Root llms/health routes and mounted API route paths only.
# DEPENDS: app.main
# LINKS: V-M-APP
# --- GRACE MODULE_MAP ---
# test_app_registers_root_and_api_routes - Verifies app route surface
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for the FastAPI app shell.

from __future__ import annotations

from app.main import app


def test_app_registers_root_and_api_routes() -> None:
    paths = {route.path for route in app.routes}

    assert '/health' in paths
    assert '/llms.txt' in paths
    assert '/v1/public/products' in paths
    assert '/v1/admin/auth/login' in paths
    assert '/v1/agent/search' in paths
