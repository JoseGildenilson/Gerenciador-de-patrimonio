# Bug Fix: Backend Startup Missing db_readiness and Enum Reconciliation

- **Slug**: bug-backend
- **Fixed**: 2026-11-01T02:06:00-03:00
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Incorporado módulo `src/infrastructure/db_readiness.py` com polling de banco, reconciliação de migrações Alembic e criação segura de enums PostgreSQL, atualizando `entrypoint.sh` e `src/cli.py` com 100% de cobertura de testes.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/infrastructure/db_readiness.py` | added | Polling de banco de dados, reconciliação de schema Alembic e `ensure_pg_enums` |
| `entrypoint.sh` | modified | Executa `python -m src.infrastructure.db_readiness` antes do `alembic upgrade head` |
| `src/cli.py` | modified | Carimba `head` com `command.stamp(cfg, "head")` após `Base.metadata.create_all()` |
| `tests/test_db_readiness.py` | added | 13 testes unitários e de integração cobrindo 100% de linhas e branches |

## Diff Highlights (optional)

```bash
# entrypoint.sh
-echo "==> Aguardando Banco de Dados PostgreSQL ficar pronto..."
-python - << 'EOF'
-...
-EOF
+echo "==> Verificando prontidão do Banco de Dados e reconciliando versões..."
+python -m src.infrastructure.db_readiness
```

```python
# src/infrastructure/db_readiness.py
def ensure_pg_enums(engine) -> None:
    if engine.dialect.name != "postgresql":
        return
    with engine.connect() as conn:
        conn.execute(text("DO $$ BEGIN ... CREATE TYPE ... IF NOT EXISTS; END $$;"))
        conn.commit()
```

## Tests Added or Updated

- `tests/test_db_readiness.py::test_wait_for_database_success_with_credentials` — Valida conexão com PostgreSQL com credenciais na URL
- `tests/test_db_readiness.py::test_wait_for_database_sqlite_success` — Valida conexão com SQLite e parâmetros `connect_args`
- `tests/test_db_readiness.py::test_wait_for_database_retry_and_timeout` — Valida retry e timeout de prontidão do banco
- `tests/test_db_readiness.py::test_reconcile_alembic_schema_already_managed` — Garante que banco já versionado não é alterado
- `tests/test_db_readiness.py::test_reconcile_alembic_schema_fresh_database` — Valida banco novo sem tabelas
- `tests/test_db_readiness.py::test_reconcile_alembic_schema_legacy_equipments_table` — Valida carimbo `d4e5f6a7b8c9` em base com tabela legada `equipments`
- `tests/test_db_readiness.py::test_reconcile_alembic_schema_canonical_assets_table` — Valida carimbo `head` em base com tabela canônica `assets`
- `tests/test_db_readiness.py::test_reconcile_alembic_schema_only_users_table` — Valida carimbo `001_initial_auth` em base contendo apenas tabela `users`
- `tests/test_db_readiness.py::test_main_success_sqlite` — Valida execução completa do CLI em SQLite
- `tests/test_db_readiness.py::test_main_failure_timeout` — Valida código de saída 1 em timeout
- `tests/test_db_readiness.py::test_ensure_pg_enums_non_postgresql` — Valida no-op de criação de enums para dialetos não-PostgreSQL
- `tests/test_db_readiness.py::test_ensure_pg_enums_postgresql` — Valida execução DDL de criação idempotente de enums PostgreSQL
- `tests/test_db_readiness.py::test_main_fallback_settings_database_url` — Valida fallback para `settings.DATABASE_URL` quando `os.environ` não define `DATABASE_URL`

## Local Verification

- Commands run:
  - `docker compose up -d --build backend` → Container `patrimonio_backend` inicializado com status `Up (healthy)`
  - `curl -s http://localhost:8000/health` → `{"status":"ok","app":"Gerenciador de Patrimônio"}`
  - `PYTHONPATH=. uv run pytest --cov=src --cov-branch --cov-fail-under=100` → 144 passed, 100.00% coverage
  - `uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/` → All checks passed, 76 files formatted
- Manual checks:
  - Verificada inicialização limpa nos logs de `patrimonio_backend` e sincronização do container com o banco `patrimonio_postgres`.

## Deviations from Assessment

Adicionada a função `ensure_pg_enums()` em `src/infrastructure/db_readiness.py` para criar idempotentemente os tipos PostgreSQL ENUM (`user_role`, `asset_status`, `maintenance_type`) antes da execução do seed/migrations, prevenindo erro `type "user_role" does not exist` ao executar `seed_db`.

## Follow-ups

- Executar `/speckit-bug-test slug=bug-backend` para validação formal e encerramento do ciclo.
