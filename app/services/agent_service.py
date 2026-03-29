# FILE: app/services/agent_service.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Interpret natural-language product queries, query catalog data, and record audit-ready agent search metadata.
# SCOPE: Query intent parsing, product search orchestration, agent capability manifest.
# DEPENDS: M-REPO-PRODUCT (app.repositories.product_repo), M-MODELS-PLATFORM (app.models.platform), M-SCHEMAS-AGENT (app.schemas.agent), M-SCHEMAS-PRODUCT (app.schemas.product)
# LINKS: M-SVC-AGENT, V-M-SVC-AGENT
# --- GRACE MODULE_MAP ---
# InterpretedIntent - Dataclass holding parsed search filters from a natural-language query
# _parse_query_intent - Parse natural language query into structured search filters
# search_products - Parse intent and return ProductListItem-compatible search results with audit trail
# get_agent_context - Return agent capability manifest for external LLM agents
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 agent service with intent parsing and audit logging.

from __future__ import annotations

from typing import Optional
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import AgentRequest
from app.repositories import product_repo
from app.schemas.agent import AgentCapability, AgentContextResponse
from app.schemas.product import ProductListItem

logger = logging.getLogger(__name__)
LOG_PREFIX = "[AgentService]"

_PRICE_PATTERN = re.compile(
    r"(?:до|under|cheaper?\s+than|below)\s*(\d[\d\s]*)\s*(?:руб\.?|р\.?|rub)?",
    re.IGNORECASE,
)
_STOCK_KEYWORDS = re.compile(r"в\s*наличии|со\s*склада", re.IGNORECASE)


# --- START_BLOCK_INTERPRETED_INTENT ---


@dataclass
class InterpretedIntent:
    name: Optional[str] = None
    max_price: Optional[Decimal] = None
    min_stock: Optional[int] = None
    raw_query: str = ""


# --- END_BLOCK_INTERPRETED_INTENT ---


# --- START_BLOCK_PARSE_QUERY_INTENT ---


# START_CONTRACT: _parse_query_intent
#   PURPOSE: Parse natural language query into structured search filters.
#   INPUTS: { query: str }
#   OUTPUTS: { InterpretedIntent }
#   SIDE_EFFECTS: none
#   LINKS: BLOCK_PARSE_QUERY_INTENT, M-SVC-AGENT
# END_CONTRACT: _parse_query_intent
def _parse_query_intent(query: str) -> InterpretedIntent:
    if not query or not query.strip():
        return InterpretedIntent(raw_query=query)

    max_price: Optional[Decimal] = None
    min_stock: Optional[int] = None

    price_match = _PRICE_PATTERN.search(query)
    if price_match:
        raw_amount = price_match.group(1).replace(" ", "")
        max_price = Decimal(raw_amount)

    if _STOCK_KEYWORDS.search(query):
        min_stock = 1

    name = _PRICE_PATTERN.sub("", query).strip()
    name = _STOCK_KEYWORDS.sub("", name).strip()
    name = re.sub(r"\s+", " ", name).strip()
    if not name:
        name = None

    intent = InterpretedIntent(
        name=name,
        max_price=max_price,
        min_stock=min_stock,
        raw_query=query,
    )

    logger.debug(
        "%s[BLOCK_PARSE_QUERY_INTENT] query=%r → name=%s max_price=%s min_stock=%s",
        LOG_PREFIX,
        query,
        intent.name,
        intent.max_price,
        intent.min_stock,
    )

    return intent


# --- END_BLOCK_PARSE_QUERY_INTENT ---


# --- START_BLOCK_SEARCH_PRODUCTS ---


# START_CONTRACT: search_products
#   PURPOSE: Parse intent and return ProductListItem-compatible search results.
#   INPUTS: { session: AsyncSession, query: str }
#   OUTPUTS: { tuple[list[ProductListItem], InterpretedIntent, int] - (results, intent, response_ms) }
#   ERRORS: AGENT_SEARCH_FAILURE — propagated as SQLAlchemy exceptions on repo or audit write failure.
#   SIDE_EFFECTS: writes AgentRequest audit record to database.
#   LINKS: BLOCK_SEARCH_PRODUCTS, M-REPO-PRODUCT, M-MODELS-PLATFORM
# END_CONTRACT: search_products
async def search_products(
    session: AsyncSession,
    query: str,
) -> tuple[list[ProductListItem], InterpretedIntent, int]:
    start = time.monotonic()

    intent = _parse_query_intent(query)

    raw_rows = await product_repo.search(
        session,
        name=intent.name,
        max_price=intent.max_price,
        min_stock=intent.min_stock,
    )

    results: list[ProductListItem] = []
    for row in raw_rows:
        results.append(
            ProductListItem(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                price=row["price"],
                stock=row["stock"],
                image_url=row.get("image_object_key"),
                thumbnail_url=row.get("thumbnail_object_key"),
                nearest_delivery_date=row.get("nearest_delivery_date"),
                merchant_id=row.get("merchant_id"),
            )
        )

    elapsed_ms = int((time.monotonic() - start) * 1000)

    audit = AgentRequest(
        endpoint="/v1/agent/search",
        query=query,
        interpreted_intent=str(intent),
        result_count=len(results),
        response_ms=elapsed_ms,
    )
    session.add(audit)
    await session.commit()

    logger.info(
        "%s[BLOCK_SEARCH_PRODUCTS] query=%r results=%d response_ms=%d",
        LOG_PREFIX,
        query,
        len(results),
        elapsed_ms,
    )

    return results, intent, elapsed_ms


# --- END_BLOCK_SEARCH_PRODUCTS ---


# --- START_BLOCK_GET_AGENT_CONTEXT ---


# START_CONTRACT: get_agent_context
#   PURPOSE: Return agent capability manifest for external LLM agents.
#   INPUTS: { none }
#   OUTPUTS: { AgentContextResponse }
#   SIDE_EFFECTS: none
#   LINKS: BLOCK_GET_AGENT_CONTEXT, M-SCHEMAS-AGENT
# END_CONTRACT: get_agent_context
def get_agent_context() -> AgentContextResponse:
    return AgentContextResponse(
        api_version="v1",
        capabilities=[
            AgentCapability(
                name="search_products",
                description="Search marketplace products by name, price, stock",
                parameters={
                    "query": "Natural language search query",
                },
            ),
            AgentCapability(
                name="browse_catalog",
                description="Browse paginated product catalog",
                parameters={
                    "cursor": "Pagination cursor",
                    "limit": "Page size",
                },
            ),
        ],
    )


# --- END_BLOCK_GET_AGENT_CONTEXT ---
