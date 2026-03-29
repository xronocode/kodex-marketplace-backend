# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test admin catalog repository mutation surface.
# SCOPE: Async mutation exports and product image key persistence helper only.
# DEPENDS: inspect, app.repositories.admin_catalog_repo
# LINKS: V-M-REPO-ADMIN
# --- GRACE MODULE_MAP ---
# test_admin_catalog_repo_exports_async_mutations - Verifies async mutation helpers
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for admin catalog repository.

from __future__ import annotations

import inspect

import app.repositories.admin_catalog_repo as admin_catalog_repo


def test_admin_catalog_repo_exports_async_mutations() -> None:
    exported = [
        admin_catalog_repo.create_seller,
        admin_catalog_repo.list_sellers,
        admin_catalog_repo.create_product,
        admin_catalog_repo.update_product,
        admin_catalog_repo.delete_product,
        admin_catalog_repo.create_offer,
        admin_catalog_repo.update_offer,
        admin_catalog_repo.delete_offer,
        admin_catalog_repo.save_product_image_keys,
        admin_catalog_repo.create_product_attribute,
        admin_catalog_repo.get_product,
    ]

    assert all(inspect.iscoroutinefunction(fn) for fn in exported)
