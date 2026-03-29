<!--
START_MODULE_CONTRACT
PURPOSE: Index the prompts used to generate backend and project-wide GRACE artifacts.
SCOPE: Prompt chronology, scope notes, and produced artifact references.
DEPENDS: /Users/myevdokimov/prj/kodex/kodex-backend/docs/ai/AI_WORKFLOW.md
LINKS: M-GOVERNANCE
END_MODULE_CONTRACT
START_MODULE_MAP
entries - Chronological prompt index for backend work
END_MODULE_MAP
-->
# PROMPTS.md — Kodex

## Entries

### 2026-03-28 — Phase 0 bootstrap
Source: User bootstrap prompt for Kodex Phase 0 with `grace-init` and `grace-plan`.
Scope: Backend repo governance plus shared GRACE planning artifacts only. No application code.
Artifacts: `AGENTS.md`, `docs/requirements.xml`, `docs/technology.xml`, `docs/development-plan.xml`, `docs/verification-plan.xml`, `docs/knowledge-graph.xml`, `docs/ai/AI_WORKFLOW.md`.
Inputs referenced: `_input/20260302_080853_ai_only_dev_Тестовое_задание_midde_fullstack.pdf`, `_input/kodex_full_plan.svg`, `_input/agentic-commerce-architecture.svg`.

### 2026-03-28 — Phase 1 core backend implementation
Source: User `$grace-plan` command with full GRACE methodology contract.
Scope: All 20 Phase 1 backend modules — config, database, auth, ORM models, Alembic migrations, Pydantic schemas, repositories, services, API routes, app wiring, seed script.
Artifacts: `app/core/config.py`, `app/core/database.py`, `app/core/auth.py`, `app/models/catalog.py`, `app/models/platform.py`, `alembic/versions/001_initial_phase1_schema.py`, `app/schemas/*.py`, `app/repositories/*.py`, `app/services/*.py`, `app/api/v1/*.py`, `app/main.py`, `seed.py`, `pyproject.toml`, `Dockerfile`.
Inputs referenced: `docs/development-plan.xml`, `docs/requirements.xml`, `docs/technology.xml`, `docs/knowledge-graph.xml`, `docs/verification-plan.xml`, `../kodex-infra/.env.example`.
