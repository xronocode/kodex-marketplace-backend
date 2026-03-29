# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test admin auth token creation and decoding.
# SCOPE: Default admin login, JWT creation, and role decoding only.
# DEPENDS: app.core.auth
# LINKS: V-M-AUTH
# --- GRACE MODULE_MAP ---
# test_login_admin_returns_platform_admin_token - Verifies default admin login
# test_create_access_token_round_trips_role_claim - Verifies JWT encode/decode path
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for auth helpers.

from __future__ import annotations

from app.core.auth import create_access_token, decode_token, login_admin


def test_login_admin_returns_platform_admin_token() -> None:
    token = login_admin('admin', 'changeme_strong_password')

    assert token is not None
    payload = decode_token(token)
    assert payload is not None
    assert payload['role'] == 'platform_admin'
    assert payload['sub'] == 'admin'


def test_create_access_token_round_trips_role_claim() -> None:
    token = create_access_token({'role': 'platform_admin', 'sub': 'reviewer'})
    payload = decode_token(token)

    assert payload is not None
    assert payload['role'] == 'platform_admin'
    assert payload['sub'] == 'reviewer'
