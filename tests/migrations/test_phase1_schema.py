# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test the Phase 1 Alembic schema definition.
# SCOPE: Static migration text for the required tables, columns, and search index only.
# DEPENDS: tests.helpers
# LINKS: V-M-MIGRATIONS
# --- GRACE MODULE_MAP ---
# test_phase1_migration_contains_required_phase1_artifacts - Verifies key schema strings in the migration
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for the Phase 1 migration file.

from __future__ import annotations

from tests.helpers import read_repo_text


def test_phase1_migration_contains_required_phase1_artifacts() -> None:
    migration = read_repo_text('alembic/versions/001_initial_phase1_schema.py')

    assert 'merchants' in migration
    assert 'agent_requests' in migration
    assert 'merchant_id' in migration
    assert 'search_vector' in migration
    assert 'ix_products_search_vector' in migration
