# --- GRACE MODULE_CONTRACT ---
# PURPOSE: Container image definition for Kodex backend service.
# SCOPE: Build stage, runtime image, entrypoint.
# DEPENDS: python:3.12-slim base image, pyproject.toml dependencies.
# LINKS: pyproject.toml (deps), app/main.py (entrypoint)
# --- GRACE MODULE_MAP ---
# EXPORTS: Docker image exposing port 8000 with uvicorn server
# --- GRACE CHANGE_SUMMARY ---
# 2026-03-28: Initial Dockerfile — single-stage build.

# --- START_BLOCK_BASE ---
FROM python:3.12-slim

WORKDIR /app
# --- END_BLOCK_BASE ---

# --- START_BLOCK_DEPS ---
COPY pyproject.toml ./
RUN pip install --no-cache-dir fastapi==0.115.6 sqlalchemy==2.0.36 asyncpg==0.30.0 \
    alembic==1.14.1 aioboto3==13.2.0 pydantic-settings==2.7.0 python-jose==3.3.0 \
    passlib==1.7.4 bcrypt==4.2.1 Pillow==10.4.0 Faker==24.8.0 uvicorn==0.30.6 \
    python-multipart==0.0.18
# --- END_BLOCK_DEPS ---

# --- START_BLOCK_APP_COPY ---
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
# --- END_BLOCK_APP_COPY ---

# --- START_BLOCK_RUNTIME ---
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# --- END_BLOCK_RUNTIME ---
