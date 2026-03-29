# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test agent API route registration.
# SCOPE: Context/search/llms routes and async handler surface only.
# DEPENDS: inspect, app.api.v1.agent
# LINKS: V-M-API-AGENT
# --- GRACE MODULE_MAP ---
# test_agent_router_registers_context_search_and_llms_routes - Verifies agent route set
# test_agent_handlers_are_async - Verifies agent handlers remain async
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for agent API.

from __future__ import annotations

import inspect

import app.api.v1.agent as agent_api


def test_agent_router_registers_context_search_and_llms_routes() -> None:
    routes = {route.path: route.methods for route in agent_api.router.routes}
    assert '/v1/agent/context' in routes
    assert '/v1/agent/search' in routes
    assert '/v1/agent/llms-txt' in routes
    assert 'POST' in routes['/v1/agent/search']


def test_agent_handlers_are_async() -> None:
    assert inspect.iscoroutinefunction(agent_api.get_context)
    assert inspect.iscoroutinefunction(agent_api.search)
    assert inspect.iscoroutinefunction(agent_api.get_llms_txt)
