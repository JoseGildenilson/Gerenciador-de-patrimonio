# Relatório de Correções: Estabilização do CI Pipeline

**Feature**: `002-fix-ci-pipeline`  
**Data**: 2026-10-28  
**Branch**: `JoseGildenilson/CI-Fix`  

---

## 1. Problemas Identificados e Diagnóstico

### 1.1. Healthcheck do Container de Serviço PostgreSQL
* **Sintoma:** O job `Backend Tests & Migrations` registrava logs repetidos `FATAL: role "root" does not exist` durante o healthcheck e inicialização de containers.
* **Causa-Raiz:** O comando configurado em `options: >-` era simplesmente `pg_isready`. Sem usuário especificado, o container Alpine executa o binário sob o usuário do sistema do container (`root`), o qual não existe no catálogo de usuários do PostgreSQL (apenas `postgres` foi criado).
* **Solução:** Atualizado em `.github/workflows/ci.yml` para:
  ```yaml
  options: >-
    --health-cmd "pg_isready -U postgres -d test_patrimonio_db"
    --health-interval 10s
    --health-timeout 5s
    --health-retries 5
  ```

### 1.2. Falha de Verificação de Formatação (`ruff format --check src/`)
* **Sintoma:** O step `Check Backend Formatting (Ruff)` falhava imediatamente com código de erro 1 (`5 files would be reformatted, 28 files already formatted`).
* **Causa-Raiz:** Após a sincronização com a branch `develop` (merge do PR #2 / commit `0986eb3`), 5 arquivos em `src/` apresentavam linhas acima do limite de 100 caracteres (`line-length = 100`) ou linhas em branco excedentes entre definições de classes: `src/domain/schemas.py`, `src/infrastructure/repositories.py`, `src/infrastructure/seed.py`, `src/use_cases/authenticate_user.py` e `src/use_cases/import_spreadsheet_use_cases.py`.
* **Solução:** Os 5 arquivos em `src/` foram reformatados seguindo estritamente o padrão do Ruff (`33 files already formatted`, 100% de conformidade).

### 1.3. Acionamento Manual e Flexibilidade de Testes (`workflow_dispatch`)
* **Sintoma:** Desenvolvedores trabalhando em branches de correção não conseguiam disparar o pipeline de validação sob demanda sem abrir pull request contra `develop` ou `main`.
* **Solução:** Adicionado o gatilho `workflow_dispatch:` na seção `on:` de `.github/workflows/ci.yml`.

### 1.4. Violação de Chave Estrangeira na Importação de Planilhas e Reversibilidade de Migrações no PostgreSQL
* **Sintoma:** No PostgreSQL do CI, os testes `test_execute_import_endpoint_success`, `test_execute_spreadsheet_import_creation_and_catalogs` e `test_execute_spreadsheet_import_upsert_all_fields` falhavam com `ForeignKeyViolation (registered_by_id=1)` em `asset_maintenances`, e `test_alembic_migrations_lifecycle` falhava no `downgrade("base")` com `UndefinedTable: relation "equipments" does not exist`.
* **Solução:** Parametrizado `registered_by_id` em `ExecuteSpreadsheetImportUseCase` (propagando `current_user.id` em `src/api/import_routes.py` e usuários criados nas fixtures em `tests/test_import_use_cases.py`), e completada a função `downgrade()` em `alembic/versions/e5f6a7b8c9d0_purge_legacy_database_tables.py` para recriar as tabelas e índices legados exigidos pelas revisões anteriores.

---

## 2. Validação da Qualidade e Cobertura Constitucional

A suíte completa de testes de backend foi executada com o seguinte resultado:

* **Total de Testes:** 125 aprovados, 0 ignorados, 0 falhas.
* **Cobertura Total de Código:** 100% (1.800 statements, 342 branches, 0 branches perdidas).
* **Status do Quality Gate:** Aprovado integralmente sem necessidade de bypass ou omissões indevidas.
