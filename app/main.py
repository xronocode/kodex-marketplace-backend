# FILE: app/main.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Wire FastAPI application startup, middleware, routers, CORS, and root discovery endpoints.
# SCOPE: Application factory — CORS middleware registration, router inclusion, health endpoint.
# INPUTS: router-modules (ApiRouters)
# OUTPUTS: fastapi-app (FastAPIApplication)
# ERRORS: APP_BOOT_FAILURE
# DEPENDS: M-API-PUBLIC, M-API-ADMIN-AUTH, M-API-ADMIN-CATALOG, M-API-AGENT, M-CONFIG
# PATH: app/main.py
# VERIFICATION: V-M-APP
# LINKS: M-APP, V-M-APP, M-API-PUBLIC, M-API-ADMIN-AUTH, M-API-ADMIN-CATALOG, M-API-AGENT, M-CONFIG
# --- GRACE MODULE_MAP ---
# app - FastAPI application instance with CORS middleware and all routers mounted
# health - GET /health — lightweight liveness probe returning {"status": "ok"}
# llms_txt - GET /llms.txt — plain text manifest for LLM agent discovery (root mount)
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 application wiring.
# 2026-03-28: v1.0.1 — Added /llms.txt at app root for agent discovery.

from __future__ import annotations

import logging

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.admin.auth import router as admin_auth_router
from app.api.v1.admin.catalog import router as admin_catalog_router
from app.api.v1.agent import router as agent_router, _LLMS_TXT_CONTENT
from app.api.v1.public import router as public_router
from app.core.config import get_settings

logger = logging.getLogger(__name__)
LOG_PREFIX = "[App]"

settings = get_settings()

app = FastAPI(title="Kodex Marketplace API", version="1.0.0")


# --- START_BLOCK_LLMS_TXT_ENDPOINT ---
# CONTRACT:
#   PURPOSE: Expose llms.txt manifest at app root for LLM agent discovery per llmstxt.org.
#   INPUTS: { none }
#   OUTPUTS: { str - plain text llms.txt content }
#   ERRORS: none
#   SIDE_EFFECTS: none
#   LINKS: BLOCK_LLMS_TXT_ENDPOINT, M-API-AGENT
@app.get("/llms.txt", include_in_schema=False)
async def llms_txt() -> Response:
    return Response(content=_LLMS_TXT_CONTENT, media_type="text/plain")


# --- END_BLOCK_LLMS_TXT_ENDPOINT ---


# --- START_BLOCK_REGISTER_CORS ---
# CONTRACT:
#   PURPOSE: Attach CORS middleware with origins from centralised settings.
#   INPUTS: { settings.backend_cors_origins: list[str] }
#   OUTPUTS: { middleware registered on app }
#   ERRORS: APP_BOOT_FAILURE — if settings are malformed (caught by Pydantic at load).
#   LINKS: BLOCK_REGISTER_CORS, M-CONFIG
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- END_BLOCK_REGISTER_CORS ---


# --- START_BLOCK_REGISTER_ROUTERS ---
# CONTRACT:
#   PURPOSE: Mount all API v1 route modules onto the application.
#   INPUTS: { public_router, admin_auth_router, admin_catalog_router, agent_router: APIRouter }
#   OUTPUTS: { routers registered on app }
#   ERRORS: APP_BOOT_FAILURE — if any router module is missing or malformed.
#   LINKS: BLOCK_REGISTER_ROUTERS, M-API-PUBLIC, M-API-ADMIN-AUTH, M-API-ADMIN-CATALOG, M-API-AGENT
app.include_router(public_router)
app.include_router(admin_auth_router)
app.include_router(admin_catalog_router)
app.include_router(agent_router)

logger.info(
    "%s[BLOCK_REGISTER_ROUTERS] Routers mounted: public, admin-auth, admin-catalog, agent",
    LOG_PREFIX,
)
# --- END_BLOCK_REGISTER_ROUTERS ---


# --- START_BLOCK_HEALTH_ENDPOINT ---
# CONTRACT:
#   PURPOSE: Lightweight liveness probe for container orchestrators and load balancers.
#   INPUTS: { none }
#   OUTPUTS: { dict - {"status": "ok"} }
#   ERRORS: none
#   SIDE_EFFECTS: none
#   LINKS: BLOCK_HEALTH_ENDPOINT, V-M-APP
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# --- END_BLOCK_HEALTH_ENDPOINT ---
