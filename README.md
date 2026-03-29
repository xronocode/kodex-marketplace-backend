# Kodex Backend

FastAPI backend for Kodex marketplace prototype.

## Stack

Python 3.12, FastAPI 0.115.x, SQLAlchemy 2.x async (asyncpg),
PostgreSQL 16, Alembic, MinIO (aioboto3), Pydantic 2.x, JWT auth.

## Run (via Docker Compose)

See `../kodex-infra/README.md` for the recommended full-stack start.

## Run standalone (development)

```bash
cd kodex-backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp ../kodex-infra/.env.example .env   # edit DB/S3 URLs for local services
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000
```

## Run tests

```bash
pytest tests/ -v
```

## API reference

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Agent manifest: http://localhost:8000/v1/agent/context
- llms.txt: http://localhost:8000/llms.txt

## Project structure

```
app/
  core/          config, database, auth
  models/        SQLAlchemy ORM models
  repositories/  async data access layer
  schemas/       Pydantic request/response schemas
  services/      business logic + S3
  api/v1/        FastAPI routers (public, admin, agent)
  main.py        app assembly + lifespan
seed.py          test data (110 products, dynamic dates)
alembic/         migrations
tests/           smoke tests
docs/ai/         AI_WORKFLOW.md, PROMPTS.md, session exports
```

## Key architecture decisions

- Fully async — asyncpg driver, SQLAlchemy async session, aioboto3
- Cursor pagination with base64 UUID cursors
- Presigned URLs for images (ExpiresIn=3600)
- Thumbnail generation via Pillow (max 300×300 JPEG)
- Agent layer: /v1/agent/context, /v1/agent/search, /llms.txt
- Schema foresight: merchant_id + status + search_vector on products
  (Phase 2 multi-merchant preparation)
