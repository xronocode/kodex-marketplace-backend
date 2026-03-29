# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test seed helper behavior for delivery dates.
# SCOPE: Delivery-date generation range and demo-merchant marker text only.
# DEPENDS: datetime, seed, tests.helpers
# LINKS: V-M-SEED
# --- GRACE MODULE_MAP ---
# test_generate_delivery_dates_stay_within_current_week_window - Verifies delivery-date rule
# test_seed_source_mentions_demo_store - Verifies demo merchant marker in seed source
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for seed helpers.

from __future__ import annotations

from datetime import date, timedelta

from seed import generate_delivery_dates
from tests.helpers import read_repo_text


def test_generate_delivery_dates_stay_within_current_week_window() -> None:
    today = date.today()
    dates = generate_delivery_dates(100)

    assert min(dates) >= today
    assert max(dates) <= today + timedelta(days=6)


def test_seed_source_mentions_demo_store() -> None:
    source = read_repo_text('seed.py')
    assert 'Kodex Demo Store' in source
