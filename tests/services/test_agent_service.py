# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test agent service query parsing and search surface.
# SCOPE: Intent parser, search export, and context export presence only.
# DEPENDS: inspect, app.services.agent_service
# LINKS: V-M-SVC-AGENT
# --- GRACE MODULE_MAP ---
# test_agent_service_exports_search_and_context - Verifies async search and sync context surface
# test_parse_query_intent_extracts_name_and_price - Verifies core intent parsing behavior
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for agent service.

from __future__ import annotations

import inspect

import app.services.agent_service as agent_service


def test_agent_service_exports_search_and_context() -> None:
    assert inspect.iscoroutinefunction(agent_service.search_products)
    assert inspect.isfunction(agent_service.get_agent_context)


def test_parse_query_intent_extracts_name_and_price() -> None:
    intent = agent_service._parse_query_intent('беспроводные наушники до 5000')

    assert intent.max_price == 5000
    assert intent.name is not None
