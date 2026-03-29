# FILE: app/services/s3_service.py
# VERSION: 1.0.0
# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Upload original product images and generated thumbnails to MinIO using aioboto3 and Pillow.
# SCOPE: S3 client factory, bucket provisioning, thumbnail generation, image upload with presigned URLs.
# DEPENDS: M-CONFIG (app.core.config.BackendSettings)
# LINKS: M-S3, V-M-S3
# --- GRACE MODULE_MAP ---
# StoredImageRefs - Pydantic model with object keys and presigned URLs for image + thumbnail
# _get_s3_client - Async context manager yielding an aioboto3 S3 client
# ensure_bucket_exists - Async bucket provisioning (create if missing)
# _generate_thumbnail - Sync Pillow-based JPEG thumbnail generator
# upload_product_image - Async upload of original + thumbnail, returns StoredImageRefs
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial implementation — Phase 1 product image storage.
# 2026-03-28: v1.0.1 — Added explicit ExpiresIn=3600 to presigned URL generation.

from __future__ import annotations

import io
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

import aioboto3
from fastapi import UploadFile
from PIL import Image
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)
LOG_PREFIX = "[S3Service]"


# --- START_BLOCK_STORED_IMAGE_REFS ---
class StoredImageRefs(BaseModel):
    """
    CONTRACT:
        PURPOSE: Data holder for S3 object keys and presigned URLs of an uploaded image pair.
        INPUTS: { image_object_key: str, thumbnail_object_key: str, image_url: str, thumbnail_url: str }
        OUTPUTS: { BaseModel instance with four string fields }
        SIDE_EFFECTS: none
        LINKS: BLOCK_UPLOAD_THUMBNAIL_PAIR
    """

    image_object_key: str
    thumbnail_object_key: str
    image_url: str
    thumbnail_url: str


# --- END_BLOCK_STORED_IMAGE_REFS ---


# --- START_BLOCK_S3_CLIENT_FACTORY ---
@asynccontextmanager
async def _get_s3_client():  # type: ignore[no-untyped-def]
    """
    CONTRACT:
        PURPOSE: Async context manager that yields an aioboto3 S3 client configured from BackendSettings.
        INPUTS: { none - reads settings via get_settings() }
        OUTPUTS: { AsyncGenerator[aioboto3 S3 Client, None] }
        SIDE_EFFECTS: opens network connection to MinIO endpoint
        LINKS: M-CONFIG, BLOCK_MINIO_SETTINGS
    """
    settings = get_settings()
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_root_user,
        aws_secret_access_key=settings.minio_root_password,
    ) as client:
        yield client


# --- END_BLOCK_S3_CLIENT_FACTORY ---


# --- START_BLOCK_ENSURE_BUCKET ---
async def ensure_bucket_exists() -> None:
    """
    CONTRACT:
        PURPOSE: Verify the configured bucket exists; create it if missing.
        INPUTS: { none - reads settings via get_settings() }
        OUTPUTS: { None }
        SIDE_EFFECTS: may create an S3 bucket in MinIO
        LINKS: M-CONFIG, BLOCK_S3_CLIENT_FACTORY
    """
    settings = get_settings()
    async with _get_s3_client() as client:
        buckets = await client.list_buckets()
        bucket_names = [b["Name"] for b in buckets.get("Buckets", [])]
        if settings.minio_bucket not in bucket_names:
            await client.create_bucket(Bucket=settings.minio_bucket)
            logger.info(
                "%s[BLOCK_ENSURE_BUCKET] Created bucket: %s",
                LOG_PREFIX,
                settings.minio_bucket,
            )
        else:
            logger.debug(
                "%s[BLOCK_ENSURE_BUCKET] Bucket already exists: %s",
                LOG_PREFIX,
                settings.minio_bucket,
            )


# --- END_BLOCK_ENSURE_BUCKET ---


# --- START_BLOCK_GENERATE_THUMBNAIL ---
def _generate_thumbnail(
    image_bytes: bytes, max_size: tuple[int, int] = (300, 300)
) -> bytes:
    """
    START_CONTRACT: _generate_thumbnail
        PURPOSE: Create a JPEG thumbnail from image bytes.
        INPUTS: { image_bytes: bytes, max_size: tuple[int,int] }
        OUTPUTS: { bytes - JPEG thumbnail data }
        SIDE_EFFECTS: none (pure function)
    END_CONTRACT: _generate_thumbnail
    """
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail(max_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


# --- END_BLOCK_GENERATE_THUMBNAIL ---


# --- START_BLOCK_UPLOAD_THUMBNAIL_PAIR ---
async def upload_product_image(file: UploadFile) -> StoredImageRefs:
    """
    START_CONTRACT: upload_product_image
        PURPOSE: Store original plus 300x300 JPEG thumbnail and return presigned URLs.
        INPUTS: { file: UploadFile - uploaded image file }
        OUTPUTS: { StoredImageRefs - object keys and presigned URLs for both images }
        SIDE_EFFECTS: Writes two objects to MinIO S3 storage
    END_CONTRACT: upload_product_image
    """
    settings = get_settings()
    bucket = settings.minio_bucket

    image_key = f"products/{uuid4()}.jpg"
    thumbnail_key = f"products/thumbnails/{uuid4()}.jpg"

    content = await file.read()

    async with _get_s3_client() as client:
        await client.put_object(
            Bucket=bucket,
            Key=image_key,
            Body=content,
            ContentType=file.content_type or "image/jpeg",
        )
        logger.info(
            "%s[BLOCK_UPLOAD_THUMBNAIL_PAIR] Uploaded original: %s",
            LOG_PREFIX,
            image_key,
        )

        thumb_bytes = _generate_thumbnail(content)

        await client.put_object(
            Bucket=bucket,
            Key=thumbnail_key,
            Body=thumb_bytes,
            ContentType="image/jpeg",
        )
        logger.info(
            "%s[BLOCK_UPLOAD_THUMBNAIL_PAIR] Uploaded thumbnail: %s",
            LOG_PREFIX,
            thumbnail_key,
        )

        image_url: str = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": image_key},
            ExpiresIn=3600,  # 1 hour — explicit, not relying on MinIO default
        )
        thumbnail_url: str = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": thumbnail_key},
            ExpiresIn=3600,  # 1 hour — explicit, not relying on MinIO default
        )

    return StoredImageRefs(
        image_object_key=image_key,
        thumbnail_object_key=thumbnail_key,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
    )


# --- END_BLOCK_UPLOAD_THUMBNAIL_PAIR ---
