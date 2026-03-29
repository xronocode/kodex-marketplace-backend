# FILE: app/core/auth.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Provide admin password verification, JWT issuing, JWT decoding, and admin identity helpers.
# SCOPE: Password hashing, token creation, token validation, admin authentication, admin extraction from token.
# DEPENDS: M-CONFIG
# LINKS: M-AUTH, V-M-AUTH
# --- GRACE MODULE_MAP ---
# verify_password - Verify a plaintext password against its bcrypt hash
# get_password_hash - Hash a plaintext password with bcrypt
# create_access_token - Create a signed JWT access token with expiry
# login_admin - Authenticate platform admin credentials and return JWT
# decode_token - Decode and validate a JWT token, returning payload or None
# get_current_admin - Decode token and enforce platform_admin role, raise 401 on failure
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 admin auth with JWT.

from __future__ import annotations

from typing import Optional
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

logger = logging.getLogger(__name__)
LOG_PREFIX = "[Auth]"

ALGORITHM = "HS256"

# --- START_BLOCK_PASSWORD_CONTEXT ---
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# --- END_BLOCK_PASSWORD_CONTEXT ---


# --- START_BLOCK_VERIFY_PASSWORD ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    CONTRACT:
        PURPOSE: Verify a plaintext password against its bcrypt hash.
        INPUTS: { plain_password: str, hashed_password: str }
        OUTPUTS: { bool - True if password matches }
    """
    return _pwd_context.verify(plain_password, hashed_password)


# --- END_BLOCK_VERIFY_PASSWORD ---


# --- START_BLOCK_GET_PASSWORD_HASH ---
def get_password_hash(password: str) -> str:
    """
    CONTRACT:
        PURPOSE: Hash a plaintext password with bcrypt.
        INPUTS: { password: str }
        OUTPUTS: { str - bcrypt hash }
    """
    return _pwd_context.hash(password)


# --- END_BLOCK_GET_PASSWORD_HASH ---


# --- START_BLOCK_CREATE_ACCESS_TOKEN ---
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    CONTRACT:
        PURPOSE: Create a signed JWT access token with an expiry claim.
        INPUTS: { data: dict - payload claims, expires_delta: Optional[timedelta] - custom expiry }
        OUTPUTS: { str - encoded JWT string }
        SIDE_EFFECTS: reads settings.secret_key, settings.access_token_expire_minutes
        LINKS: BLOCK_CREATE_ACCESS_TOKEN
    """
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    encoded_jwt: str = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    return encoded_jwt


# --- END_BLOCK_CREATE_ACCESS_TOKEN ---


# --- START_BLOCK_LOGIN_ADMIN ---
def login_admin(username: str, password: str) -> Optional[str]:
    """
    CONTRACT:
        PURPOSE: Authenticate platform admin and create Bearer JWT.
        INPUTS: { username: str, password: str }
        OUTPUTS: { str - JWT token, or None if credentials invalid }
        SIDE_EFFECTS: reads settings.admin_username, settings.admin_password
        LINKS: BLOCK_CREATE_ACCESS_TOKEN, BLOCK_LOGIN_ADMIN
    """
    settings = get_settings()
    if username != settings.admin_username or password != settings.admin_password:
        logger.warning(
            "%s[BLOCK_LOGIN_ADMIN] Failed login attempt for user=%s",
            LOG_PREFIX,
            username,
        )
        return None
    access_token = create_access_token(
        data={"sub": username, "role": "platform_admin"},
    )
    logger.info(
        "%s[BLOCK_LOGIN_ADMIN] Admin authenticated user=%s",
        LOG_PREFIX,
        username,
    )
    return access_token


# --- END_BLOCK_LOGIN_ADMIN ---


# --- START_BLOCK_DECODE_TOKEN ---
def decode_token(token: str) -> Optional[dict]:
    """
    CONTRACT:
        PURPOSE: Decode and validate a JWT token.
        INPUTS: { token: str - encoded JWT }
        OUTPUTS: { dict - payload, or None if invalid/expired }
        SIDE_EFFECTS: reads settings.secret_key
    """
    settings = get_settings()
    try:
        payload: dict = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError:
        logger.warning(
            "%s[BLOCK_DECODE_TOKEN] Invalid or expired token",
            LOG_PREFIX,
        )
        return None


# --- END_BLOCK_DECODE_TOKEN ---


# --- START_BLOCK_GET_CURRENT_ADMIN ---
def get_current_admin(token: str) -> dict:
    """
    CONTRACT:
        PURPOSE: Decode token and enforce platform_admin role.
        INPUTS: { token: str - encoded JWT }
        OUTPUTS: { dict - decoded payload with role == platform_admin }
        ERRORS: HTTPException 401 if token invalid or role mismatch
        SIDE_EFFECTS: reads settings.secret_key
        LINKS: BLOCK_DECODE_TOKEN
    """
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("role") != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient permissions",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# --- END_BLOCK_GET_CURRENT_ADMIN ---
