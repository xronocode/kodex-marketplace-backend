# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test offer service sorting entrypoint.
# SCOPE: Async export presence and sorting block marker only.
# DEPENDS: inspect, app.services.offer_service, tests.helpers
# LINKS: V-M-SVC-OFFER
# --- GRACE MODULE_MAP ---
# test_offer_service_exports_sort_offers - Verifies async offer sorting surface
# test_offer_service_contains_sort_marker - Verifies sorting block marker
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for offer service.

from __future__ import annotations

import inspect

import app.services.offer_service as offer_service
from tests.helpers import read_repo_text


def test_offer_service_exports_sort_offers() -> None:
    assert inspect.iscoroutinefunction(offer_service.sort_offers)


def test_offer_service_contains_sort_marker() -> None:
    source = read_repo_text('app/services/offer_service.py')
    assert 'BLOCK_SORT_OFFERS' in source
