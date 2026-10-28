# Quickstart Validation Guide: Purge Legacy Database

**Feature**: `002-purge-legacy-database` | **Date**: 2026-10-28

This guide outlines runnable verification steps to confirm that all legacy database structures have been purged and the database model strictly matches the DBML specification.

---

## 1. Prerequisites

- Python 3.13 installed
- `uv` package manager installed
- PostgreSQL 16 active (or SQLite contingency for test suite)

---

## 2. Apply Migrations

Run the Alembic migration chain to bring the database to the clean DBML state:

```powershell
uv run alembic upgrade head
```

---

## 3. Verify Database Table Catalog

Verify that PostgreSQL contains **strictly** the 7 DBML tables:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
  AND table_name != 'alembic_version'
ORDER BY table_name;
```

**Expected Result (exact 7 tables, nothing extra):**
1. `asset_maintenances`
2. `asset_movements`
3. `assets`
4. `categories`
5. `locations`
6. `patrimony_history`
7. `users`

---

## 4. Verify Column Cleanliness in `users`

Verify that `users` contains only the 9 DBML columns:

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;
```

**Expected Result:**
- `id`
- `name`
- `email`
- `password_hash`
- `role`
- `is_active`
- `deleted_at`
- `created_at`
- `updated_at`

*(The legacy `hashed_password` column MUST NOT exist).*

---

## 5. Execute Test Suite & Quality Gates

Run pytest with 100% line and branch coverage requirement:

```powershell
uv run pytest --cov=src --cov-branch --cov-report=term-missing
```

**Expected Result:**
- All tests pass (0 failures).
- Total coverage: **100%** across lines and branches.
