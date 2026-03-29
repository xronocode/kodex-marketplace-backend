# FILE: app/api/v1/agent.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Expose llms.txt, capability context, and natural-language search endpoints for external LLM agents.
# SCOPE: Agent discovery (llms.txt), capability manifest (context), natural-language product search.
# DEPENDS: M-SVC-AGENT (app.services.agent_service), M-DB (app.core.database), M-SCHEMAS-AGENT (app.schemas.agent), M-SCHEMAS-PRODUCT (app.schemas.product)
# LINKS: M-API-AGENT, V-M-API-AGENT
# --- GRACE MODULE_MAP ---
# router - APIRouter with prefix=/v1/agent, tags=["agent"]
# get_context - GET /context — return agent capability manifest JSON
# search - POST /search — natural-language product search with X-Query-Interpreted header
# get_llms_txt - GET /llms-txt — plain text llms.txt manifest for LLM agent discovery
# _LLMS_TXT_CONTENT - Static llms.txt string constant (imported by app/main.py)
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 agent API routes.

from __future__ import annotations

import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.agent import AgentContextResponse, AgentSearchRequest
from app.schemas.product import ProductListItem
from app.services import agent_service

logger = logging.getLogger(__name__)
LOG_PREFIX = "[AgentApi]"

router = APIRouter(prefix="/v1/agent", tags=["agent"])

_LLMS_TXT_CONTENT = """\
# Kodex Marketplace API

> Multi-merchant marketplace with Agentic Commerce support

## Endpoints

### GET /v1/public/products
Browse the public product catalog with cursor pagination.
Query params: cursor (optional), limit (1-100, default 20)

### GET /v1/public/products/{id}
Get detailed product information with attributes and offers.

### POST /v1/agent/search
Search products using natural language queries.
Supports: product name, max price (e.g., "до 5000"), stock availability ("в наличии").
Returns filtered product list with X-Query-Interpreted header.

### GET /v1/agent/context
Get machine-readable capability manifest for agent integration.

### POST /v1/admin/auth/login
Admin authentication endpoint. Returns Bearer JWT token.

### POST /v1/admin/products/{id}/image
Upload product image (requires admin JWT). Returns presigned URLs.
"""


# --- START_BLOCK_GET_CONTEXT ---


# START_CONTRACT: get_context
#   PURPOSE: GET /v1/agent/context — return agent capability manifest JSON.
#   INPUTS: { none }
#   OUTPUTS: { AgentContextResponse }
#   ERRORS: AGENT_HTTP_FAILURE — unexpected service failure.
#   SIDE_EFFECTS: none
#   LINKS: BLOCK_GET_CONTEXT, M-SVC-AGENT
# END_CONTRACT: get_context
@router.get("/context", response_model=AgentContextResponse)
async def get_context() -> AgentContextResponse:
    return agent_service.get_agent_context()


# --- END_BLOCK_GET_CONTEXT ---


# --- START_BLOCK_HANDLE_AGENT_SEARCH ---


# START_CONTRACT: search
#   PURPOSE: POST /v1/agent/search with X-Query-Interpreted response header.
#   INPUTS: { data: AgentSearchRequest }
#   OUTPUTS: { list[ProductListItem] }
#   ERRORS: AGENT_HTTP_FAILURE — propagated from agent_service.search_products.
#   SIDE_EFFECTS: writes AgentRequest audit record via agent_service.search_products.
#   LINKS: BLOCK_HANDLE_AGENT_SEARCH, M-SVC-AGENT
# END_CONTRACT: search
@router.post("/search", response_model=list[ProductListItem])
async def search(
    data: AgentSearchRequest,
    session: AsyncSession = Depends(get_session),
    response: Response = None,
) -> list[ProductListItem]:
    results, intent, _elapsed_ms = await agent_service.search_products(
        session, data.query
    )
    # Encode intent as URL-safe ASCII string for header
    header_value = f"name={intent.name} max_price={intent.max_price} min_stock={intent.min_stock}"
    response.headers["X-Query-Interpreted"] = quote(header_value) if header_value else ""
    logger.info(
        "%s[BLOCK_HANDLE_AGENT_SEARCH] query=%r results=%d",
        LOG_PREFIX,
        data.query,
        len(results),
    )
    return results


# --- END_BLOCK_HANDLE_AGENT_SEARCH ---


# --- START_BLOCK_GET_LLMS_TXT ---


# START_CONTRACT: get_llms_txt
#   PURPOSE: Expose llms.txt manifest at agent discovery endpoint.
#   INPUTS: { none }
#   OUTPUTS: { str - plain text llms.txt content }
#   ERRORS: none
#   SIDE_EFFECTS: none
#   LINKS: BLOCK_GET_LLMS_TXT, M-API-AGENT
# END_CONTRACT: get_llms_txt
@router.get("/llms-txt", response_class=Response)
async def get_llms_txt() -> Response:
    return Response(content=_LLMS_TXT_CONTENT, media_type="text/plain")


# --- END_BLOCK_GET_LLMS_TXT ---
