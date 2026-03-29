# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test offer repository async surface.
# SCOPE: Async export presence and delivery-date sorting signal only.
# DEPENDS: inspect, app.repositories.offer_repo, tests.helpers
# LINKS: V-M-REPO-OFFER
# --- GRACE MODULE_MAP ---
# test_offer_repo_exports_async_entrypoint - Verifies async list surface
# test_offer_repo_source_mentions_delivery_sorting - Verifies delivery-date sorting support
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for offer repository.

from __future__ import annotations

import inspect

import app.repositories.offer_repo as offer_repo
from tests.helpers import read_repo_text


def test_offer_repo_exports_async_entrypoint() -> None:
    assert inspect.iscoroutinefunction(offer_repo.list_for_product)


def test_offer_repo_source_mentions_delivery_sorting() -> None:
    source = read_repo_text('app/repositories/offer_repo.py')
    assert 'delivery_date' in source
    assert 'price' in source
