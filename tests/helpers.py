# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Provide shared helpers for backend smoke tests.
# SCOPE: Repository-root path resolution and source-text loading only.
# DEPENDS: pathlib
# LINKS: V-M-CONFIG, V-M-APP, V-M-SEED
# --- GRACE MODULE_MAP ---
# ROOT - Repository root path for smoke tests
# read_repo_text - Read a repository file as UTF-8 text
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added shared smoke-test helpers for backend verification.

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_repo_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding='utf-8')
