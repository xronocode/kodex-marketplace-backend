# Kodex Backend

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI 0.115](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)

> **AI-Ready Marketplace Platform** — Backend service with Agentic Commerce layer

Part of the **Kodex** open-source marketplace platform built entirely using AI tools under the **GRACE** methodology (Graph-RAG Anchored Code Engineering).

## 🚀 Features

- **Public Catalog API** — Cursor-paginated product listing with 110+ seeded products
- **Admin CRUD** — Full product/catalog management with JWT authentication
- **Agent Layer** — Natural language search, structured context endpoint, `llms.txt` manifest
- **Image Storage** — MinIO integration with presigned URLs and auto-thumbnail generation
- **Async Architecture** — Fully async SQLAlchemy 2.x with asyncpg driver
- **Multi-Merchant Ready** — Schema prepared for Phase 2 RBAC expansion

## 📦 Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.115.x |
| Database | PostgreSQL 16 + SQLAlchemy 2.x (async) |
| Driver | asyncpg |
| Migrations | Alembic 1.14.x |
| Object Storage | MinIO (S3-compatible, aioboto3) |
| Auth | python-jose (JWT), passlib[bcrypt] |
| Validation | Pydantic 2.x |
| Testing | pytest 8.x |

## 🏁 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# From the kodex-infra directory
cd ../kodex-infra
docker compose up --build
```

Backend will be available at http://localhost:8000

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp ../kodex-infra/.env.example .env

# Run migrations
alembic upgrade head

# Seed test data (110 products)
python seed.py

# Start server
uvicorn app.main:app --reload --port 8000
```

## 📚 API Reference

| Endpoint | Description | Auth |
|----------|-------------|------|
| `GET /health` | Liveness probe | Public |
| `GET /v1/public/products` | Catalog listing (cursor pagination) | Public |
| `GET /v1/public/products/{id}` | Product detail with offers | Public |
| `POST /v1/admin/auth/login` | Admin JWT authentication | Public |
| `POST /v1/admin/products` | Create product | JWT Required |
| `PUT /v1/admin/products/{id}` | Update product | JWT Required |
| `POST /v1/admin/products/{id}/image` | Upload product image | JWT Required |
| `GET /v1/agent/context` | Structured capability JSON | Public |
| `POST /v1/agent/search` | Natural language product search | Public |
| `GET /llms.txt` | Machine-readable capability manifest | Public |

**Interactive Docs:**
- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test category
pytest tests/api/ -v          # API integration tests
pytest tests/services/ -v     # Service layer tests
pytest tests/repositories/ -v # Repository layer tests
```

## 📁 Project Structure

```
app/
├── core/          # Config, database connection, auth utilities
├── models/        # SQLAlchemy ORM models (catalog, platform)
├── repositories/  # Async data access layer
├── schemas/       # Pydantic request/response schemas
├── services/      # Business logic + S3 integration
├── api/v1/        # FastAPI routers (public, admin, agent)
└── main.py        # Application assembly + lifespan events

alembic/           # Database migrations
tests/             # Comprehensive test suite
docs/ai/           # AI workflow documentation
seed.py            # Test data generator (Faker)
```

## 🔑 Key Architecture Decisions

1. **Fully Async** — asyncpg driver, SQLAlchemy async sessions, aioboto3 for S3
2. **Cursor Pagination** — Base64-encoded UUID cursors with `X-Total-Count` header
3. **Dynamic Delivery Dates** — Computed on-the-fly via SQL subquery (never hardcoded)
4. **Presigned URLs** — 1-hour expiration for product images
5. **Auto-Thumbnails** — Max 300×300 JPEG generated on upload
6. **Schema Foresight** — `merchant_id`, `status`, `search_vector` fields ready for Phase 2
7. **Structured Logging** — `[Module][function][BLOCK_NAME]` format

## 🤖 AI-Ready Features

Kodex includes built-in support for AI agents and LLM integration:

- **`/llms.txt`** — Standardized machine-readable capability manifest
- **`/v1/agent/context`** — Structured JSON describing API capabilities
- **`/v1/agent/search`** — Natural language product search with intent parsing
- **Semantic Markup** — GRACE methodology with `MODULE_CONTRACT` and block markers

See `docs/ai/AI_WORKFLOW.md` for the complete AI development methodology.

## 🤖 AI Stack

This project was built 100% with AI coding assistants under human engineering supervision:

| Category | Tools |
|----------|-------|
| **AI IDEs** | [Antigravity](https://antigravity.ai/) / [VS Code](https://code.visualstudio.com/) |
| **Code Editors** | [VS Code](https://code.visualstudio.com/) / [Kilo Code](https://kilocode.ai/) / [QwenCode](https://github.com/QwenLM/Qwen) / [Codex](https://openai.com/codex) |
| **LLM Models** | [Claude](https://anthropic.com/) / [Gemini](https://deepmind.google/technologies/gemini/) / [Qwen](https://qwenlm.github.io/) / [GLM-5/5.1](https://www.zhipuai.cn/) |

### Development Methodology

- **GRACE** (Graph-RAG Anchored Code Engineering) — Contract-first development with semantic markup
- **Human-in-the-Loop** — All AI-generated code reviewed and validated by senior engineer
- **Verification-Driven** — Every module has contracts, tests, and knowledge graph links

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

## 🔗 Related Repositories

- **[kodex-marketplace-frontend](https://github.com/xronocode/kodex-marketplace-frontend)** — Vue 3 + TypeScript frontend
- **[kodex-marketplace-stack](https://github.com/xronocode/kodex-marketplace-stack)** — Docker Compose infrastructure

## 📖 Documentation

- [Development Plan](docs/development-plan.xml)
- [Knowledge Graph](docs/knowledge-graph.xml)
- [Requirements](docs/requirements.xml)
- [Technology Stack](docs/technology.xml)
- [Verification Plan](docs/verification-plan.xml)

## 🛠 Development Conventions

- All handlers must be `async def`
- No sync SQLAlchemy — async only
- Alembic is CLI-only (never run migrations in handlers)
- No secrets in code — all via environment variables
- Structured logging with module/function/block context

---

**Built with ❤️ using AI + Human Engineering Supervision**
