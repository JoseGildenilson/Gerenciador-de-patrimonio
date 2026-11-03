# Implementation Plan: Gerenciamento de Patrimônio — Modelo de Banco de Dados e Convergência Full-Stack

**Branch**: `001-gerenciamento-patrimonio` | **Date**: 2026-11-03 | **Spec**: [specs/001-gerenciamento-patrimonio/spec.md](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/specs/001-gerenciamento-patrimonio/spec.md)

**Input**: Feature specification from `specs/001-gerenciamento-patrimonio/spec.md` e diagnóstico completo de auditoria em `RELATORIO_AUDITORIA_COMPLETA.md`.

## Summary

Convergir integralmente o Banco de Dados (Alembic, ORM e SQL nativo), o Backend FastAPI, o Frontend React e as suítes de testes/Docker para o modelo canônico de 7 tabelas e 3 enums do SisPatrimonio:
1. **Banco de Dados e Migrações Alembic**: Garantir paridade de 100% entre `alembic/versions/`, `src/domain/models.py` e `database/schema.sql`, aplicando os tipos PostgreSQL `ENUM` nativos (`user_role`, `asset_status`, `maintenance_type`) diretamente nas colunas, `NULLS NOT DISTINCT` em `uq_locations_physical_space`, políticas `ON DELETE` (`RESTRICT`, `SET NULL`, `CASCADE`) nas `ForeignKey`s, os 4 `CheckConstraint`s, os 7 `Index`es de performance e remoção da função órfã `set_updated_at()`.
2. **Backend (Domínio, Casos de Uso e Rotas HTTP)**: Tipar rigorosamente `AssetStatus` e `MaintenanceTypeEnum` nos schemas Pydantic (`src/domain/schemas.py`), enriquecer `AssetResponse` e `AssetDetailResponse` com objetos aninhados (`category`, `location`, `assigned_user`, `last_maintenance_at`, `movements`, `maintenances`, `patrimony_history`), expor os endpoints `GET /api/v1/assets/export`, `GET /api/v1/assets/suggestions`, `GET /api/v1/users`, `DELETE /api/v1/categories/{id}`, `DELETE /api/v1/locations/{id}`, `PUT/DELETE /api/v1/assets/{id}/maintenances/{maintenance_id}`, liberar o perfil `administrador` em `import_routes.py`, validar `user.is_active` ao atribuir custódia, usar `model_fields_set` em `AssetUseCases.update_asset`, validar `requires_serial_number` e mapear custo/data/specs na importação de planilhas, e remover módulos stubs obsoletos.
3. **Frontend React (`frontend/src/`)**: Migrar toda a camada de tipos (`types/`), cliente HTTP (`api/equipmentApi.ts`), controle de acesso (`App.tsx`, `SideMenu.tsx`), páginas (`DashboardPage.tsx`, `EquipmentListPage.tsx`, `EquipmentDetailPage.tsx`, `ImportPage.tsx`) e modais (`NewEquipmentModal.tsx`, `ManageTagsModal.tsx`, `MovementModal.tsx`, `MaintenanceModal.tsx`, `EditMaintenanceModal.tsx`) das rotas extintas `/api/v1/equipments` e `/api/v1/equipments/tags` para os contratos canônicos (`/api/v1/assets`, `/api/v1/categories`, `/api/v1/locations`, `/api/v1/movements`, `/api/v1/users`, `/api/v1/dashboard/metrics`), incluindo suporte a renumeração de patrimônio, aceite de termo de custódia e permissão integral ao perfil `administrador`.
4. **Testes e Infraestrutura Docker**: Remover arquivos de teste stubs de 1 linha, atualizar e reativar a suíte `tests/e2e/`, atualizar os testes Vitest do Frontend (`frontend/src/__tests__/`) para os novos contratos, manter 100% de cobertura de linhas e branches no backend e montar `./database:/app/database` em `docker-compose.yml` e `Dockerfile`.

## Technical Context

**Language/Version**: Python 3.13+ (Backend) e TypeScript 5.7+ / React 18 (Frontend).

**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0 (ORM/Core), Alembic 1.13+, Pydantic v2.8+, uv, psycopg2-binary 2.9+, openpyxl 3.1+, React Router v7, Axios, Tailwind CSS 3, Lucide React.

**Storage**: PostgreSQL 16 (SGBD obrigatório de produção e desenvolvimento; fallback in-memory SQLite para testes unitários rápidos).

**Testing**: Pytest 9+, pytest-cov 7+, httpx 0.28+ com Quality Gate inegociável de 100% de cobertura de linhas e branches (`--cov=src --cov-branch --cov-fail-under=100`); Vitest + React Testing Library + `tsc --noEmit` no Frontend.

**Observability/Logging**: SQLAlchemy event listeners (`before_cursor_execute` e `after_cursor_execute`) condicionados à configuração `LOG_SQL_STATEMENTS` (padrão `True` em dev, `False` em prod), formatando queries com tempo em ms, filtrando `SELECT 1` e mascarando credenciais e hashes via `[REDACTED]`.

**Target Platform**: Linux / Docker containers com usuários não-privilegiados (`appuser` UID 10001 no backend e `nginx-unprivileged` no frontend).

**Project Type**: Web Application (API RESTful FastAPI + SPA React).

**Performance Goals**: Tempo de resposta de consultas de ativos paginadas e filtradas < 100ms; migração Alembic idempotente sem bloqueio de catálogo.

**Constraints**: Zero Raw SQL na aplicação; transações controladas no nível de casos de uso; tipos nativos de PostgreSQL compatíveis com fallback de teste; proteção contra Formula Injection em exportação (`.xlsx`).

**Scale/Scope**: 7 tabelas centrais (`users`, `locations`, `categories`, `assets`, `patrimony_history`, `asset_movements`, `asset_maintenances`), 3 enums (`user_role`, `asset_status`, `maintenance_type`), 6 módulos de rotas FastAPI e 12 componentes/páginas React.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked post Phase 1 design.*

| Princípio Constitucional | Exigência | Avaliação de Conformidade no Design (Pré e Pós Fase 1) | Status |
|---|---|---|:---:|
| **I. Preservação de Contratos** | Contratos e DTOs estáveis e documentados | Contratos OpenAPI formalizados em `contracts/` (`assets-api.yaml`, `categories-api.yaml`, `locations-api.yaml`, `movements-maintenances-api.yaml`) e consumidos de forma unificada pelo Frontend React. | ✅ PASS |
| **II. Arquitetura em Camadas** | Domínio e Use Cases sem transporte HTTP | Modelos ORM em `src/domain/models.py`, schemas Pydantic em `src/domain/schemas.py`, orquestração em `src/use_cases/`, repositórios em `src/infrastructure/`, rotas em `src/api/`. | ✅ PASS |
| **III. Persistência SQLAlchemy 2.0** | Proibição absoluta de raw SQL | Todas as consultas modeladas com API idiomática (`select()`, `where()`, `selectinload()`, `func`). Zero raw SQL na aplicação. | ✅ PASS |
| **IV. Controle Transacional** | Transação no caso de uso | Repositórios não fazem `commit()` ou `rollback()`. Transação atômica delimitada nos casos de uso e rotas. | ✅ PASS |
| **V. Governança via Alembic** | Schema versionado e idempotente | Migrações em `alembic/versions/` contendo `upgrade()` e `downgrade()` auditados com paridade exata com `models.py` e `database/schema.sql`. | ✅ PASS |
| **VI. Cobertura de 100%** | Linhas e branches cobertas | Bateria de testes em `tests/` cobrindo 100% de linhas e branches (`--cov-fail-under=100`), além de suíte E2E e Vitest no Frontend. | ✅ PASS |
| **VII. Escopo Estrito (YAGNI)** | Sem refatorações especulativas | Escopo estritamente delimitado às 7 tabelas e 3 enums do DBML `sispatrimonio` e correção das quebras apontadas na auditoria. | ✅ PASS |

## Project Structure

### Documentation (this feature)

```text
specs/001-gerenciamento-patrimonio/
├── spec.md                  # Especificação funcional BDD e requisitos (FR-001 a FR-017)
├── checklists/
│   ├── requirements.md      # Validação de qualidade da especificação
│   └── database-logging.md  # Checklist de observabilidade SQL (18 itens)
├── plan.md                  # Este arquivo (Plano de implementação e arquitetura)
├── research.md              # Decisões técnicas da Fase 0 (Enums, JSONB, Unicidade, Convergência Full-Stack)
├── data-model.md            # Modelo de dados formal da Fase 1 (Entidades, FKs ON DELETE, Checks, Índices)
├── contracts/               # Contratos OpenAPI da Fase 1
│   ├── assets-api.yaml
│   ├── locations-api.yaml
│   ├── categories-api.yaml
│   └── movements-maintenances-api.yaml
├── quickstart.md            # Guia de validação e verificação fim a fim
└── tasks.md                 # Checklist de execução da Fase 2 (gerado via /speckit-tasks)
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── deps.py                  # Autenticação e RBAC (administrador, tecnico, colaborador)
│   ├── routes.py                # Rotas de autenticação e listagem de usuários ativos (/api/v1/users)
│   ├── asset_routes.py          # Endpoints CRUD de assets, exportação (.xlsx), sugestões e renumeração
│   ├── location_routes.py       # Endpoints CRUD + DELETE de locations
│   ├── category_routes.py       # Endpoints CRUD + DELETE de categories
│   ├── movement_routes.py       # Endpoints de transferências, aceite de termo e manutenções (CRUD)
│   ├── import_routes.py         # Endpoints de preview e execução de importação de planilhas
│   └── dashboard_routes.py      # Endpoint de métricas agregadas do inventário
├── core/
│   ├── config.py                # Configurações Pydantic (incluindo LOG_SQL_STATEMENTS)
│   ├── database.py              # Engine SQLAlchemy 2.0, listener [SQL QUERY] e get_db()
│   ├── exceptions.py            # Exceções de domínio e handlers HTTP
│   └── security.py              # Criptografia Argon2id e JWT
├── domain/
│   ├── models.py                # Modelos ORM (User, Location, Category, Asset, PatrimonyHistory, etc.)
│   └── schemas.py               # Schemas DTO Pydantic v2 com validação estrita de Enums e relacionamentos
├── infrastructure/
│   ├── repositories.py          # Repositórios SQLAlchemy 2.0 (sem commit/rollback)
│   ├── spreadsheet_exporter.py  # Geração de planilha .xlsx de ativos com sanitização CWE-1236
│   ├── spreadsheet_parser.py    # Parser de planilha .xlsx (incluindo custo, data e especificações)
│   ├── seed.py                  # Carga inicial padrão
│   └── seed_rich_data.py        # Carga acadêmica completa do SisPatrimonio
└── use_cases/
    ├── asset_use_cases.py       # Casos de uso de ativos, renumeração, exportação e sugestões
    ├── location_use_cases.py    # Casos de uso de localizações físicas e bloqueio de exclusão em uso
    ├── category_use_cases.py    # Casos de uso de categorias, depreciação e bloqueio de exclusão em uso
    ├── movement_use_cases.py    # Casos de uso de transferências, custódia e aceite de termo
    ├── maintenance_use_cases.py # Casos de uso de manutenções preventivas/corretivas
    ├── import_spreadsheet_use_cases.py # Preview e importação em lote validando requires_serial_number
    └── dashboard_use_cases.py   # Agregações de métricas por status, categoria e localização

frontend/
└── src/
    ├── api/
    │   ├── authApi.ts           # Cliente de autenticação
    │   ├── dashboardApi.ts      # Cliente de métricas do dashboard
    │   ├── equipmentApi.ts      # Cliente unificado para /api/v1/assets, /categories, /locations, /movements, /users
    │   └── importApi.ts         # Cliente de importação de planilhas (/api/v1/assets/import)
    ├── components/
    │   ├── SideMenu.tsx         # Navegação lateral habilitada para tecnico e administrador
    │   ├── NewEquipmentModal.tsx # Modal de cadastro de ativo (patrimônio, categoria, local, custodiante, specs)
    │   ├── ManageTagsModal.tsx  # Modal de gestão de Categorias e Localizações Físicas
    │   ├── MovementModal.tsx    # Modal de movimentação física, custódia e baixa patrimonial
    │   ├── MaintenanceModal.tsx # Modal de registro de manutenção preventiva/corretiva com custo e prestador
    │   └── EditMaintenanceModal.tsx # Modal de edição de manutenção
    ├── pages/
    │   ├── DashboardPage.tsx    # Dashboard com métricas reais do banco e atalhos para tecnico/administrador
    │   ├── EquipmentListPage.tsx # Listagem paginada e filtrada de ativos com exportação .xlsx
    │   ├── EquipmentDetailPage.tsx # Detalhes do ativo, specs JSONB, renumeração, movimentações e manutenções
    │   ├── ImportPage.tsx       # Página de importação em lote (.xlsx)
    │   └── LoginPage.tsx        # Página de login
    ├── types/
    │   ├── auth.ts              # Tipagem User e UserRole ('administrador' | 'tecnico' | 'colaborador')
    │   ├── dashboard.ts         # Tipagem DashboardMetricsResponse
    │   └── equipment.ts         # Tipagens de Asset, Category, Location, PatrimonyHistory, AssetMovement, AssetMaintenance
    └── __tests__/               # Testes automatizados Vitest + React Testing Library

alembic/
└── versions/
    ├── d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py
    └── e5f6a7b8c9d0_purge_legacy_database_tables.py

database/
├── schema.sql                   # DDL canônico PostgreSQL 16
└── populate.sql                 # DML canônico PostgreSQL 16

tests/
├── conftest.py                  # Fixtures com suporte a PostgreSQL e fallback SQLite
├── test_asset_*.py              # Testes unitários e de integração das 7 entidades
├── test_migrations.py           # Teste de ciclo de vida completo Alembic (up/down/up) e paridade de schema
└── e2e/                         # Suíte E2E de 4 Tiers atualizada para /api/v1/assets
```

**Structure Decision**: Arquitetura Web Application integrada (`src/` para Backend em camadas limpas, `frontend/src/` para SPA React, `alembic/` e `database/` para governança de dados e `tests/` para validação unitária, integração e E2E).

## Complexity Tracking

> *Zero violações constitucionais identificadas. Todos os 7 princípios da Constituição do Projeto foram verificados e mantidos.*

| Item / Decisão | Justificativa | Alternativa mais simples descartada |
|---|---|---|
| Enums nativos PostgreSQL nas colunas | Exigência explícita do DBML (`FR-001`, `FR-013`) e paridade com `database/schema.sql` | Manter `VARCHAR(50)` na migração (descartado por divergência com `schema.sql` e falta de integridade no SGBD) |
| DTOs enriquecidos em `AssetResponse` / `AssetDetailResponse` | Evita N+1 queries do Frontend para renderizar nomes de categoria, localização física, custodiante e histórico | Retornar apenas IDs numéricos (descartado por quebrar a renderização dos cards e detalhes no Frontend) |
| Migração completa de `frontend/src/` para `/api/v1/assets` | As rotas legadas `/api/v1/equipments` foram expurgadas na especificação `002-purge-legacy-database` | Criar rotas proxy legadas (descartado por violar o descomissionamento total de estruturas fora do DBML) |
