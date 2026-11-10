# Bug Fix: Backend Container Startup Crash on Duplicate Table Users

- **Slug**: backend-container
- **Fixed**: 2026-10-29T15:49:00-03:00
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Criado módulo Python de prontidão e reconciliação automática de versões (`src/infrastructure/db_readiness.py`), integrado ao `entrypoint.sh` e `src/cli.py`. O sistema detecta esquemas pré-existentes sem `alembic_version`, carimba a revisão apropriada sem mascarar senhas e executa `alembic upgrade head` sem colisões.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/infrastructure/db_readiness.py` | added | Módulo com `wait_for_database`, `reconcile_alembic_schema` e `main` |
| `entrypoint.sh` | modified | Substitui script inline por `python -m src.infrastructure.db_readiness` |
| `src/cli.py` | modified | Carimba `head` com `command.stamp` após `create_db()` |
| `tests/test_db_readiness.py` | added | Suíte completa com 100% de cobertura (linhas e branches) |
| `tests/conftest.py` | modified | Formatação Ruff |
| `tests/test_sispatrimonio_coverage_100.py` | modified | Formatação Ruff |

## Diff Highlights (optional)

```python
# src/infrastructure/db_readiness.py
def reconcile_alembic_schema(engine, alembic_cfg: Config | None = None) -> str | None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "alembic_version" in tables or "users" not in tables:
        return None

    if "equipments" in tables:
        target_revision = "d4e5f6a7b8c9"
    elif "assets" in tables:
        target_revision = "head"
    else:
        target_revision = "001_initial_auth"

    cfg = alembic_cfg or Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False))
    command.stamp(cfg, target_revision)
    return target_revision
```

## Tests Added or Updated

- `tests/test_db_readiness.py::test_wait_for_database_success_with_credentials` — valida verificação com URL contendo senha.
- `tests/test_db_readiness.py::test_wait_for_database_sqlite_success` — valida conexão SQLite e connect_args.
- `tests/test_db_readiness.py::test_wait_for_database_retry_and_timeout` — valida tentativas e timeout.
- `tests/test_db_readiness.py::test_reconcile_alembic_schema_already_managed` — valida no-op para bancos já controlados por Alembic.
- `tests/test_db_readiness.py::test_reconcile_alembic_schema_fresh_database` — valida no-op para bancos vazios.
- `tests/test_db_readiness.py::test_reconcile_alembic_schema_legacy_equipments_table` — valida carimbo da revisão `d4e5f6a7b8c9` quando tabelas legadas existem.
- `tests/test_db_readiness.py::test_reconcile_alembic_schema_canonical_assets_table` — valida carimbo da revisão `head` quando modelo canônico existe.
- `tests/test_db_readiness.py::test_reconcile_alembic_schema_only_users_table` — valida carimbo de `001_initial_auth` para base mínima.
- `tests/test_db_readiness.py::test_main_success_sqlite` — valida fluxo completo CLI.
- `tests/test_db_readiness.py::test_main_failure_timeout` — valida saída 1 em timeout.
- `tests/test_db_readiness.py::test_main_fallback_settings_database_url` — valida fallback para settings.

## Local Verification

- Commands run:
  - `uv run pytest` → 136 passed, 100% de cobertura em linhas e branches (1860 stmts, 358 branches, 0 miss).
  - `uv run ruff check src/ tests/` → All checks passed.
  - `uv run ruff format --check src/ tests/` → 76 files already formatted.
  - `docker compose -p gerenciadordepatrimonio up -d --build backend` → Container `patrimonio_backend` reconstruído e inicializado com sucesso.
  - `docker logs patrimonio_backend` → Migrações aplicadas, seed executado, uvicorn rodando.
  - `curl -s http://localhost:8000/health` → `{"status":"ok","app":"Gerenciador de Patrimônio"}`.
  - `docker ps` → `patrimonio_backend` com status `healthy`, `patrimonio_postgres` com status `healthy`, `patrimonio_frontend` `Up`.

## Deviations from Assessment

Nenhuma. A remediação seguiu exatamente o plano proposto no assessment.

## Follow-ups

- Executar `/speckit-bug-test slug=backend-container` para formalizar o relatório de validação.
