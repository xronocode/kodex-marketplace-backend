# FILE: app/schemas/auth.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Admin authentication request and response schemas.
# SCOPE: Login request body and JWT token response.
# DEPENDS: pydantic
# LINKS: M-SCHEMAS-AUTH, app.api.v1.admin (consumes), app.core.auth (consumes)
# --- GRACE MODULE_MAP ---
# LoginRequest - Admin login credentials (username + password)
# TokenResponse - JWT access token response
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 admin auth schemas.

from __future__ import annotations

from pydantic import BaseModel


# --- START_BLOCK_LOGIN_REQUEST ---


class LoginRequest(BaseModel):
    username: str
    password: str


# --- END_BLOCK_LOGIN_REQUEST ---


# --- START_BLOCK_TOKEN_RESPONSE ---


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- END_BLOCK_TOKEN_RESPONSE ---
