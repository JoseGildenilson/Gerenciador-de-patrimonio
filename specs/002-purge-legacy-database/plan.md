# Implementation Plan: Purge Legacy Database and Strict DBML Alignment

**Branch**: `002-purge-legacy-database` | **Date**: 2026-10-28 | **Spec**: [specs/002-purge-legacy-database/spec.md](spec.md)

**Input**: Feature specification from `/specs/002-purge-legacy-database/spec.md`

## Summary

Purge all legacy database tables, redundant columns, and obsolete ORM models from the project so that the PostgreSQL database and application domain strictly reflect the 7 DBML entities (`users`, `locations`, `categories`, `assets`, `patrimony_history`, `asset_movements`, `asset_maintenances`) and 3 enums (`user_role`, `asset_status`, `maintenance_type`), maintaining 100% test coverage and strict architectural boundaries.

## Technical Context

**Language/Version**: Python 3.13.2

**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0+, Alembic 1.13+, Pydantic v2, uv, psycopg2-binary, Argon2-cffi, PyJWT

**Storage**: PostgreSQL 16 (development, staging, production) / SQLite in-memory (test suite fixture)

**Testing**: Pytest 9+, pytest-cov 7+, httpx 0.28+

**Target Platform**: Linux / Docker (multi-stage non-privileged container) / Windows dev

**Project Type**: Web service REST API backend (`gerenciador_patrimonio`) + React frontend

**Performance Goals**: Migration execution under 5 seconds; 0 residual legacy tables; zero overhead from obsolete tables

**Constraints**: Inegotiable 100% line and branch test coverage (`--cov=src --cov-branch --cov-fail-under=100`); zero SQL injection risk (exclusive SQLAlchemy 2.0 ORM/Core usage)

**Scale/Scope**: Exact 7 tables, 3 enums; purge 8 legacy tables (`equipments`, `sectors`, `equipment_types`, `equipment_statuses`, `maintenance_types`, `equipment_movements`, `equipment_maintenances`, `login_attempts`) and 1 obsolete column (`users.hashed_password`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I (Preservação de Contratos Públicos)**: The spec formally defines the canonical `/api/v1/assets`, `/api/v1/locations`, `/api/v1/categories`, and `/api/v1/auth` as the public contracts, replacing prototype routes.
- [x] **Principle II (Arquitetura em Camadas e Desacoplamento)**: Clean layering preserved across `src/api`, `src/use_cases`, `src/domain`, `src/infrastructure`, `src/core`.
- [x] **Principle III (Persistência Exclusiva com SQLAlchemy 2.0)**: Purged models and queries use SQLAlchemy 2.0 declarative ORM; raw SQL strictly banned.
- [x] **Principle IV (Controle Transacional no Caso de Uso)**: Unit of work and transactional commits managed in use cases, not repositories.
- [x] **Principle V (Governança Estrita via Alembic)**: Decommissioning performed via a new versioned Alembic migration with full `upgrade()` and `downgrade()`.
- [x] **Principle VI (Cobertura de Código de 100%)**: 100% lines and branches coverage gate maintained.
- [x] **Principle VII (Escopo Estrito e Proibição de Refatorações Especulativas)**: Changes bounded strictly to purging legacy tables/models and updating their direct consumers.

## Project Structure

### Documentation (this feature)

```text
specs/002-purge-legacy-database/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0 research and decisions
├── data-model.md        # Canonical DBML data model
├── quickstart.md        # Verification and quickstart guide
├── contracts/           # API interface contracts
│   └── api-contracts.md
└── checklists/          # Quality validation checklists
    └── requirements.md
```

### Source Code (repository root)

```text
alembic/
└── versions/
    └── e5f6a7b8c9d0_purge_legacy_database_tables.py   # New migration dropping legacy tables and columns

src/
├── api/
│   ├── asset_routes.py        # Canonical asset endpoints
│   ├── category_routes.py     # Canonical category endpoints
│   ├── location_routes.py     # Canonical location endpoints
│   ├── movement_routes.py     # Canonical movement & maintenance endpoints
│   ├── routes.py              # Canonical auth and health endpoints
│   └── dependencies.py        # Auth & DB dependencies
├── domain/
│   ├── models.py              # Pure DBML ORM models (legacy models removed)
│   └── schemas.py             # Pure DBML Pydantic DTOs
├── infrastructure/
│   ├── repositories.py        # Repositories for Asset, Category, Location, User
│   └── seed.py                # Database seeder targeting canonical models
└── use_cases/
    ├── asset_use_cases.py
    ├── category_use_cases.py
    ├── location_use_cases.py
    ├── movement_use_cases.py
    ├── maintenance_use_cases.py
    └── authenticate_user.py

tests/
├── test_asset_api.py
├── test_asset_models.py
├── test_asset_schemas.py
├── test_movement_routes.py
├── test_category_routes.py
├── test_location_routes.py
├── test_auth.py
└── test_database.py
```

**Structure Decision**: Standard single project layout (`src/` and `tests/`) as mandated by the Project Constitution.

## Complexity Tracking

No constitutional violations. All implementations adhere strictly to the established architecture.
