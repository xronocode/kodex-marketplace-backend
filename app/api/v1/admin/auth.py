# FILE: app/api/v1/admin/auth.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Expose the admin login endpoint that validates credentials and returns a Bearer JWT.
# SCOPE: POST /v1/admin/auth/login — credential validation and token issuance.
# DEPENDS: M-AUTH (app.core.auth), M-SCHEMAS-AUTH (app.schemas.auth)
# LINKS: M-API-ADMIN-AUTH, V-M-API-ADMIN-AUTH
# --- GRACE MODULE_MAP ---
# router - APIRouter with prefix="/v1/admin/auth", tags=["admin-auth"]
# handle_login - POST /login — validate admin credentials and return JWT
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 admin auth API endpoint.

from __future__ import annotations

from typing import Optional
import logging

from fastapi import APIRouter, HTTPException

from app.core.auth import login_admin
from app.schemas.auth import LoginRequest, TokenResponse

logger = logging.getLogger(__name__)
LOG_PREFIX = "[AdminAuthApi]"

router = APIRouter(prefix="/v1/admin/auth", tags=["admin-auth"])


# --- START_BLOCK_HANDLE_LOGIN ---


@router.post("/login", response_model=TokenResponse)
async def handle_login(data: LoginRequest) -> TokenResponse:
    """
    START_CONTRACT: handle_login
        PURPOSE: POST /v1/admin/auth/login endpoint.
        INPUTS: { data: LoginRequest }
        OUTPUTS: { TokenResponse }
        ERRORS: HTTPException 401 — Invalid credentials
        SIDE_EFFECTS: delegates to login_admin (reads settings, issues JWT)
        LINKS: BLOCK_HANDLE_LOGIN, BLOCK_LOGIN_ADMIN
    END_CONTRACT: handle_login
    """
    token = await _authenticate(data.username, data.password)
    if token is None:
        logger.warning(
            "%s[BLOCK_HANDLE_LOGIN] Login failed user=%s",
            LOG_PREFIX,
            data.username,
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    logger.info(
        "%s[BLOCK_HANDLE_LOGIN] Login success user=%s",
        LOG_PREFIX,
        data.username,
    )
    return TokenResponse(access_token=token, token_type="bearer")


# --- END_BLOCK_HANDLE_LOGIN ---


# --- START_BLOCK_AUTHENTICATE ---


async def _authenticate(username: str, password: str) -> Optional[str]:
    """
    START_CONTRACT: _authenticate
        PURPOSE: Async wrapper around login_admin for credential validation.
        INPUTS: { username: str, password: str }
        OUTPUTS: { str - JWT token, or None if credentials invalid }
        SIDE_EFFECTS: delegates to login_admin
        LINKS: BLOCK_AUTHENTICATE, BLOCK_LOGIN_ADMIN
    END_CONTRACT: _authenticate
    """
    return login_admin(username, password)


# --- END_BLOCK_AUTHENTICATE ---
