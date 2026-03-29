<!--
START_MODULE_CONTRACT
PURPOSE: Preserve the AI execution log for Kodex backend and shared planning artifacts.
SCOPE: Tool registry, methodology, phase log, and validation checklist state.
DEPENDS: /Users/myevdokimov/prj/kodex/kodex-backend/AGENTS.md, /Users/myevdokimov/prj/kodex/kodex-backend/docs/development-plan.xml
LINKS: M-GOVERNANCE, M-INFRA-COMPOSE, M-CONFIG
END_MODULE_CONTRACT
START_MODULE_MAP
tools-used - Declares the AI tool roster and ownership boundaries
methodology - Summarizes the GRACE operating model
phase-log - Tracks bootstrap and future delivery phases
validation-checklist - Defines cross-phase readiness checks
END_MODULE_MAP
-->
# AI_WORKFLOW.md — Kodex

## Tools used
- Antigravity: GRACE init/plan/refresh, architecture decisions, Phase 2+ design
- GLM-5: backend implementation (models, API, migrations, seed)
- Qwen Code: frontend FSD + Vue components
- Codex: async S3/MinIO service + presigned URL (reserved, limited tokens)

## Methodology
GRACE (Graph-RAG Anchored Code Engineering) by Vladimir Ivanov.
Contract-first. Knowledge graph as single source of truth.
Governed autonomy: WHAT from contracts, HOW from AI.

## Phase log
### Phase 0 — Bootstrap
Date: 2026-03-28
Tool: Antigravity
Output: repo structure, Docker Compose, GRACE artifacts, development-plan.xml
Decisions: Multi-repo split retained; backend owns shared GRACE artifacts; schema is prepared in Phase 1 for multi-merchant Phase 2; local infra standardizes PostgreSQL 16 + MinIO + hot reload; this session stops at structure and planning only.

### Phase 1 — Core platform (ТЗ)
Date: 2026-03-28
Tool: GLM-5
Status: COMPLETE
Output: 20 modules implemented — config, database, auth, catalog/platform models, migrations, product/offer/admin repos, S3 service, product/offer/admin/agent services, public/admin/agent APIs, app wiring, seed script.
Decisions: Async-only runtime with asyncpg; Alembic sync CLI with async online migrations; JWT with platform_admin role for Phase 2 RBAC compatibility; Pydantic schemas as API contracts; cursor pagination with base64-encoded UUID cursors; TSVECTOR generated column with GIN index for Russian full-text search; aioboto3 for MinIO uploads with Pillow thumbnail generation.

### Phase 1b — Frontend + Agent layer
Date: 2026-03-29
Tool: Codex
Status: COMPLETE
Output: Vue 3.5 + TypeScript frontend implemented across shared, entities, features, widgets, pages, and app bootstrap layers with router, Pinia, admin auth, agent search, voice fallback, and product/admin UI flows.
Modules generated: `M-FE-TOOLING`, `M-FE-SHARED-API`, `M-FE-SHARED-UI`, `M-FE-SHARED-LIB`, `M-FE-ENTITIES-PRODUCT`, `M-FE-ENTITIES-OFFER`, `M-FE-ENTITIES-SELLER`, `M-FE-FEATURE-SCROLL`, `M-FE-FEATURE-SORT`, `M-FE-FEATURE-AUTH`, `M-FE-FEATURE-VOICE`, `M-FE-WIDGET-CARD`, `M-FE-WIDGET-MODAL`, `M-FE-WIDGET-TABLE`, `M-FE-PAGE-CATALOG`, `M-FE-PAGE-ADMIN`, `M-FE-APP`
Decisions: Strict FSD is enforced through slice public APIs plus ESLint guardrails; all HTTP goes through `src/shared/api/client.ts`; product adapters normalize backend numeric prices into local `Money` objects; voice search degrades silently when the Speech API is unavailable; `ProductPage` remains a thin fallback over `ProductModal`; guarded `/admin` access redirects before admin page mount.
Type-check result: PASS (`npm run type-check`)
Lint result: PASS (`npm run lint`)
Build result: PASS (`npm run build`)
Vitest result: PASS (`npm exec vitest run`, 27 files / 59 tests)
Backend smoke result: PASS (`./.venv/bin/python -m pytest tests -q`, 37 passed)
### Phase 2+ — Post-ТЗ roadmap
Status: FUTURE — planned in development-plan.xml

## Validation checklist
Run after each phase. Mark [PASS] / [FAIL] / [PENDING].

Infrastructure:
- [PASS] PostgreSQL data outside container (bind mount ./data/postgres)
- [PASS] MinIO data outside container (bind mount ./data/minio)
- [PASS] Backend starts only after postgres healthcheck passes
- [PENDING] Hot reload works for both backend and frontend

Backend correctness:
- [PENDING] All route handlers are async def — zero sync handlers
- [PENDING] No psycopg2, no sync SQLAlchemy calls in request handlers
- [PENDING] Alembic runs sync via CLI only
- [PENDING] delivery_date = date.today() + timedelta(days=randint(0,6)) — NEVER hardcoded
- [PENDING] products.merchant_id column exists (nullable, FK to merchants)
- [PENDING] products.status column exists (default 'published')
- [PENDING] products.search_vector GENERATED column exists (tsvector russian)
- [PENDING] merchants table exists (empty, seed creates 1 demo merchant)
- [PENDING] agent_requests table exists (for audit log)

API correctness:
- [PENDING] GET /v1/public/products returns {items, next_cursor} with cursor pagination
- [PENDING] GET /v1/public/products/{id} returns attributes + sorted offers
- [PENDING] POST /v1/admin/auth/login returns JWT Bearer token
- [PENDING] POST /v1/admin/products/{id}/image stores in MinIO, returns presigned URLs
- [PENDING] GET /v1/agent/context returns capability manifest JSON
- [PENDING] POST /v1/agent/search accepts natural language query
- [PENDING] GET /llms.txt returns plain text per llmstxt.org spec
- [PENDING] X-Total-Count header present on list endpoints
- [PENDING] CORS configured for localhost:5173

Frontend correctness:
- [PASS] FSD layers exist: app/pages/widgets/features/entities/shared
- [PASS] No cross-slice internal imports — only via index.ts public API
- [PASS] Infinite scroll works (IntersectionObserver sentinel)
- [PASS] ProductModal shows attributes + sorted offers with SortButtons
- [PASS] AgentSearchBar with VoiceSearchButton (graceful fallback if no Speech API)
- [PASS] Admin login → JWT stored → all admin requests use Bearer

GRACE integrity:
- [PASS] Every module has MODULE_CONTRACT + MODULE_MAP
- [PASS] START_BLOCK / END_BLOCK markers present and paired
- [PASS] knowledge-graph.xml updated after each phase
- [PASS] grace-reviewer passes with 0 critical issues
