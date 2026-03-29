# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test platform ORM model shape.
# SCOPE: Merchant and agent-request table columns only.
# DEPENDS: app.models.platform
# LINKS: V-M-MODELS-PLATFORM
# --- GRACE MODULE_MAP ---
# test_merchant_model_has_expected_columns - Verifies merchant ownership fields
# test_agent_request_model_has_expected_columns - Verifies audit columns
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for platform models.

from __future__ import annotations

from app.models.platform import AgentRequest, Merchant


def test_merchant_model_has_expected_columns() -> None:
    columns = set(Merchant.__table__.c.keys())
    assert {'id', 'name', 'slug', 'is_active', 'created_at', 'updated_at'} <= columns


def test_agent_request_model_has_expected_columns() -> None:
    columns = set(AgentRequest.__table__.c.keys())
    assert {'endpoint', 'query', 'interpreted_intent', 'result_count', 'response_ms', 'created_at'} <= columns
