# FILE: app/schemas/agent.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Agent search request and response schemas.
# SCOPE: Agent search query input, capability descriptor, and context response for LLM agents.
# DEPENDS: pydantic
# LINKS: M-SCHEMAS-AGENT, app.api.v1 (consumes), app.services (consumes)
# --- GRACE MODULE_MAP ---
# AgentSearchRequest - Search query input from an agent client
# AgentCapability - Single capability descriptor (name, description, parameters)
# AgentContextResponse - API version and capability list for agent discovery
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 agent search and context schemas.

from __future__ import annotations

from pydantic import BaseModel


# --- START_BLOCK_AGENT_SEARCH_REQUEST ---


class AgentSearchRequest(BaseModel):
    query: str


# --- END_BLOCK_AGENT_SEARCH_REQUEST ---


# --- START_BLOCK_AGENT_CAPABILITY ---


class AgentCapability(BaseModel):
    name: str
    description: str
    parameters: dict[str, str]


# --- END_BLOCK_AGENT_CAPABILITY ---


# --- START_BLOCK_AGENT_CONTEXT_RESPONSE ---


class AgentContextResponse(BaseModel):
    api_version: str = "v1"
    capabilities: list[AgentCapability]


# --- END_BLOCK_AGENT_CONTEXT_RESPONSE ---
