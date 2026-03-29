# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Smoke-test async S3 service surface and aioboto3 usage.
# SCOPE: Export presence, thumbnail helper, and presigned URL implementation markers only.
# DEPENDS: inspect, app.services.s3_service, tests.helpers
# LINKS: V-M-S3
# --- GRACE MODULE_MAP ---
# test_s3_service_exports_async_entrypoints - Verifies async S3 service entrypoints
# test_s3_service_source_mentions_aioboto3_and_presigned_urls - Verifies MinIO integration markers
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-29: Added smoke coverage for S3 service.

from __future__ import annotations

import inspect

import app.services.s3_service as s3_service
from tests.helpers import read_repo_text


def test_s3_service_exports_async_entrypoints() -> None:
    assert inspect.iscoroutinefunction(s3_service.ensure_bucket_exists)
    assert inspect.iscoroutinefunction(s3_service.upload_product_image)


def test_s3_service_source_mentions_aioboto3_and_presigned_urls() -> None:
    source = read_repo_text('app/services/s3_service.py')
    assert 'aioboto3' in source
    assert 'generate_presigned_url' in source
