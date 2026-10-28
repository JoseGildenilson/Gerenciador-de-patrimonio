# Research: Purge Legacy Database and Strict DBML Alignment

**Feature**: `002-purge-legacy-database` | **Date**: 2026-10-28

## Overview

This research evaluates the technical strategy to purge all residual database objects, legacy tables, and obsolete columns from the repository, ensuring the PostgreSQL schema and SQLAlchemy domain models match the DBML specification 1:1 with zero extras.

---

### Decision 1: Alembic Migration Strategy for Legacy Table & Column Drops

- **Decision**: Create a dedicated, versioned Alembic migration (`008_purge_legacy_database_tables.py` or new revision descending from `d4e5f6a7b8c9`) that executes explicit `op.drop_table` for legacy tables and `op.drop_column` for `users.hashed_password`.
- **Rationale**:
  - Adheres strictly to Principle V of the Constitution (governance via Alembic migrations).
  - Preserves migration chain history for existing environments while bringing target database state to the exact 7 DBML tables: `users`, `locations`, `categories`, `assets`, `patrimony_history`, `asset_movements`, `asset_maintenances`.
  - Drop order must respect foreign key dependencies:
    1. `equipment_maintenances` (depends on `equipments`, `maintenance_types`, `users`)
    2. `equipment_movements` (depends on `equipments`, `sectors`, `users`)
    3. `equipments` (depends on `equipment_types`, `sectors`, `equipment_statuses`)
    4. `equipment_statuses`
    5. `maintenance_types`
    6. `sectors`
    7. `equipment_types`
    8. `login_attempts`
    9. Column `hashed_password` on `users` table.
- **Alternatives Considered**:
  - *Wiping all migrations and creating a single initial migration:* Rejected because it breaks upgrade paths for existing databases and violates Alembic migration history governance.

---

### Decision 2: Domain ORM Models Cleanup in `src/domain/models.py`

- **Decision**: Remove legacy classes (`Equipment`, `EquipmentType`, `Sector`, `EquipmentStatus`, `MaintenanceType`, `EquipmentMovement`, `EquipmentMaintenance`, `LoginAttempt`, `IPAddressType`, `MACAddressType`) from [`src/domain/models.py`](file:///src/domain/models.py). In `User`, remove the legacy `hashed_password = synonym("password_hash")`. Retain strictly `User`, `Location`, `Category`, `Asset`, `PatrimonyHistory`, `AssetMovement`, `AssetMaintenance`, and Enums `UserRole`, `AssetStatus`, `MaintenanceTypeEnum`.
- **Rationale**:
  - The user explicitly requested: "retirar tudo do banco de dados que não esteja no DBML de exemplo, não devemos mudar nada, deve tem exatamente o mesmo modelo, nada a mais".
  - Keeping legacy ORM models in `src/domain/models.py` would cause SQLAlchemy metadata to generate obsolete tables in testing environments (`Base.metadata.create_all()`).
- **Alternatives Considered**:
  - *Deprecating models with warnings:* Rejected because user explicitly demanded zero extra entities.

---

### Decision 3: API Routes and Use Cases Alignment

- **Decision**: Remove or retire legacy route modules that specifically manipulate obsolete tables (`equipment_routes.py`, `catalog_routes.py`) and replace any dependent logic in import/export/dashboard with canonical asset services. Ensure all application traffic flows through canonical routes:
  - `/api/v1/auth` (operates strictly on `users`)
  - `/api/v1/assets` (operates on `assets`, `patrimony_history`)
  - `/api/v1/categories` (operates on `categories`)
  - `/api/v1/locations` (operates on `locations`)
  - `/api/v1/movements` (operates on `asset_movements`)
  - `/api/v1/maintenances` (operates on `asset_maintenances`)
  - `/api/v1/dashboard` (aggregates metrics from `assets`, `categories`, `locations`)
- **Rationale**:
  - Clean separation of concerns and prevention of runtime crashes trying to query non-existent tables.
- **Alternatives Considered**:
  - *Simulating legacy equipment responses from assets:* Unnecessary complexity that maintains technical debt; the canonical asset APIs already fulfill all operational requirements.

---

### Decision 4: Preserving 100% Test Coverage

- **Decision**: Refactor and clean the test suite:
  - Remove test files dedicated solely to obsolete legacy tables (`test_equipment_api.py`, `test_equipment_models.py`, `test_tags_and_coverage.py` legacy parts).
  - Expand test suites for canonical entities (`test_asset_api.py`, `test_asset_models.py`, `test_asset_schemas.py`, `test_movement_routes.py`, `test_category_routes.py`, `test_location_routes.py`).
  - Run pytest with `--cov=src --cov-branch --cov-fail-under=100` to verify that 100% coverage is maintained without a single gap.
- **Rationale**:
  - In line with Principle VI of the Constitution (inegotiable 100% line and branch coverage).
