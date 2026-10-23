# Implementation Plan: Gerenciamento de Patrimônio — Modelo de Banco de Dados

**Branch**: `001-gerenciamento-patrimonio` | **Date**: 2026-10-22 | **Spec**: [specs/001-gerenciamento-patrimonio/spec.md](file:///home/gil/Projects/Gerenciador de patrimonio/specs/001-gerenciamento-patrimonio/spec.md)

**Input**: Feature specification from `specs/001-gerenciamento-patrimonio/spec.md` baseada no modelo de dados do Gerenciamento de Patrimônio.

## Summary

Evoluir a arquitetura de persistência e camadas de domínio da aplicação para refletir o modelo relacional de Gerenciamento de Patrimônio:
1. Implementar Enums nativos PostgreSQL (`user_role`, `asset_status`, `maintenance_type`).
2. Implementar as 7 tabelas normalizadas (`users`, `locations`, `categories`, `assets`, `patrimony_history`, `asset_movements`, `asset_maintenances`).
3. Suportar restrição de unicidade composta `uq_locations_physical_space`, regras de serial obrigatório por categoria, depreciação contábil (`residual_value_rate`, `useful_life_months`), campo `specs` em JSONB e renumeração de patrimônio atômica.
4. Preservar 100% de cobertura de testes, Clean Architecture (FastAPI -> Use Cases -> Repositories -> SQLAlchemy 2.0) e migração versionada no Alembic.

## Technical Context

**Language/Version**: Python 3.13+ (Backend) e TypeScript 5.7+ / React 18 (Frontend).

**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0 (ORM/Core), Alembic 1.13+, Pydantic v2.8+, uv 0.13+, psycopg2-binary 2.9+, openpyxl 3.1+.

**Storage**: PostgreSQL 16 (SGBD obrigatório de produção e desenvolvimento; fallback in-memory SQLite para testes unitários locais rápidos).

**Testing**: Pytest 9+, pytest-cov 7+, httpx 0.27+ com Quality Gate inegociável de 100% de cobertura de branches (`--cov-fail-under=100`).

**Target Platform**: Linux / Docker containers com usuários não-privilegiados (`appuser` UID 10001).

**Project Type**: Web Application (API RESTful + SPA React).

**Performance Goals**: Tempo de resposta de consultas de ativos paginadas e filtradas < 100ms; migração Alembic idempotente sem bloqueio de catálogo.

**Constraints**: Zero Raw SQL; transações controladas no nível de casos de uso; tipos nativos de PostgreSQL compatíveis com fallback de teste; proteção contra Formula Injection em exportação.

**Scale/Scope**: 7 tabelas centrais, 3 enums, CRUDs de catálogos e ativos, rastreamento histórico de movimentações, manutenções e renumerações.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked post Phase 1 design.*

| Princípio Constitucional | Exigência | Avaliação de Conformidade no Design | Status |
|---|---|---|:---:|
| **I. Preservação de Contratos** | Contratos e DTOs estáveis | As novas rotas `/api/v1/assets`, `/api/v1/categories`, `/api/v1/locations` seguem OpenAPI formalizado em `contracts/`. | ✅ PASS |
| **II. Arquitetura em Camadas** | Domínio e Use Cases sem transporte HTTP | Modelos ORM em `src/domain/models.py`, schemas Pydantic em `src/domain/schemas.py`, orquestração em `src/use_cases/`, rotas em `src/api/`. | ✅ PASS |
| **III. Persistência SQLAlchemy 2.0** | Proibição absoluta de raw SQL | Todas as consultas modeladas com API idiomática (`select()`, `where()`, `join()`). Zero raw SQL. | ✅ PASS |
| **IV. Controle Transacional** | Transação no caso de uso | Repositórios não fazem `commit()` ou `rollback()`. Transação atômica delimitada em `use_cases`. | ✅ PASS |
| **V. Governança via Alembic** | Schema versionado e idempotente | Nova migração criada em `alembic/versions/` contendo `upgrade()` e `downgrade()` auditados. | ✅ PASS |
| **VI. Cobertura de 100%** | Linhas e branches cobertas | Bateria de testes planejada em `tests/` cobrindo 100% do novo modelo e casos de borda. | ✅ PASS |
| **VII. Escopo Estrito (YAGNI)** | Sem refatorações especulativas | Escopo estritamente delimitado às 7 tabelas e 3 enums do DBML `sispatrimonio`. | ✅ PASS |

## Project Structure

### Documentation (this feature)

```text
specs/001-gerenciamento-patrimonio/
├── spec.md                  # Especificação funcional BDD e requisitos
├── checklists/
│   └── requirements.md      # Validação de qualidade da especificação
├── plan.md                  # Este arquivo (Plano de implementação e arquitetura)
├── research.md              # Decisões técnicas da Fase 0 (Enums, JSONB, Unicidade composta)
├── data-model.md            # Modelo de dados formal da Fase 1 (Entidades, regras, transições)
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
│   ├── dependencies.py          # Autenticação e RBAC (administrador, tecnico, colaborador)
│   ├── routes.py                # Rotas de autenticação
│   ├── asset_routes.py          # Endpoints CRUD de assets e renumeração
│   ├── location_routes.py       # Endpoints CRUD de locations
│   ├── category_routes.py       # Endpoints CRUD de categories
│   └── movement_routes.py       # Endpoints de transferências e manutenções
├── core/
│   ├── config.py                # Configurações Pydantic
│   ├── database.py              # Engine SQLAlchemy 2.0 e gerador de sessão get_db()
│   └── security.py              # Criptografia Argon2id e JWT
├── domain/
│   ├── models.py                # Modelos ORM (User, Location, Category, Asset, etc.)
│   └── schemas.py               # Schemas DTO Pydantic v2
├── infrastructure/
│   ├── repositories.py          # Repositórios SQLAlchemy 2.0 (sem commit/rollback)
│   └── seed.py                  # Carga inicial padrão para categorias e locais
└── use_cases/
    ├── asset_use_cases.py       # Casos de uso de ativos e renumeração
    ├── location_use_cases.py    # Casos de uso de localizações físicas
    ├── category_use_cases.py    # Casos de uso de categorias e depreciação
    └── movement_use_cases.py    # Casos de uso de transferências e manutenções

alembic/
└── versions/
    └── d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py  # Nova migração oficial

tests/
├── conftest.py                  # Fixtures com suporte a PostgreSQL e fallback SQLite
├── test_asset_models.py         # Testes unitários dos novos modelos e enums
├── test_asset_repositories.py   # Testes de queries, filtros e índices
├── test_asset_use_cases.py      # Testes de regras de negócio, renumeração e termos
├── test_asset_api.py            # Testes de integração HTTP com httpx
└── test_migrations.py           # Teste de ciclo de vida completo Alembic (up/down/up)
```

**Structure Decision**: Preserva a Clean Architecture já consolidada no projeto, adicionando os módulos e adaptadores necessários para suportar com excelência as entidades do `sispatrimonio`.

## Complexity Tracking

> *Zero violações identificadas. Todos os mandamentos da Constituição do Projeto mantidos.*

| Item / Decisão | Justificativa | Alternativa mais simples descartada |
|---|---|---|
| Enums nativos PostgreSQL | Exigência explícita do DBML e da matéria de banco de dados | Strings soltas (descartado por falta de integridade de tipo) |
| Tabela `patrimony_history` | Auditoria contábil obrigatória de trocas de plaqueta | Sobrescrita direta (descartado por perda irreversível de histórico) |
