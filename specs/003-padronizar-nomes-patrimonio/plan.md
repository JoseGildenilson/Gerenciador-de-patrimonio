# Implementation Plan: Padronização de Nomenclatura e Conformidade Constitucional

**Branch**: `fix/names-project` | **Date**: 2026-10-29 | **Spec**: [spec.md](file:///C:/Users/70486375447/orca/workspaces/Gerenciador-de-patrimonio/Fix-names/specs/003-padronizar-nomes-patrimonio/spec.md)

**Input**: Feature specification from `/specs/003-padronizar-nomes-patrimonio/spec.md`

## Summary

O objetivo desta feature é auditar, verificar e padronizar toda a nomenclatura do repositório em conformidade com as regras estabelecidas na Constituição do Projeto. A abordagem consiste em:
1. Eliminar divergências sintáticas nos arquivos Docker Compose (`docker-compose.yml` e `docker-compose.prod.yml`), padronizando o identificador de rede para `patrimonio_net` e o volume de dados para `patrimonio_data`.
2. Assegurar que nenhuma ocorrência de `internal_management` / `internal-management` exista em código executável, docstrings, configurações ou scripts.
3. Validar a execução completa das suítes de testes (Backend e Frontend) para assegurar ausência de regressões e manutenção da cobertura de 100%.

## Technical Context

**Language/Version**: Python 3.13 (Backend) e TypeScript 5.7+ / Node.js 20+ (Frontend)

**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0, Alembic, Docker Compose, React 18, Vite 6

**Storage**: PostgreSQL 16 (dev/prod: `patrimonio_db`, testes/CI: `test_patrimonio_db`)

**Testing**: Pytest (Backend, com exigência de 100% de cobertura) e Vitest / React Testing Library (Frontend)

**Target Platform**: Contêineres Linux (Docker) / Servidor Web

**Project Type**: Aplicação Web Full-Stack (Backend API FastAPI + Frontend React SPA)

**Performance Goals**: N/A (não afeta tempo de resposta ou throughput da aplicação)

**Constraints**: Preservação integral de contratos HTTP públicos e 100% de cobertura de código no backend

**Scale/Scope**: Ajustes de configuração em Docker Compose, docstrings e verificação de integridade no repositório

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio Constitucional | Status | Avaliação |
|--------------------------|--------|-----------|
| **I. Preservação de Contratos Públicos** | PASS | Nenhuma rota de API, payload ou esquema JSON é modificado. |
| **II. Arquitetura em Camadas** | PASS | Nenhuma violação ou acoplamento introduzido entre camadas. |
| **III. Persistência com SQLAlchemy 2.0** | PASS | Nenhuma consulta SQL pura adicionada. |
| **IV. Controle Transacional em Use Cases** | PASS | Nenhuma alteração no controle de transações. |
| **V. Governança via Migrações Alembic** | PASS | O esquema de dados já reflete o DBML oficial; apenas ajustes textuais seguros em docstrings descritivas. |
| **VI. Cobertura de 100% e Quality Gates** | PASS | Todas as alterações mantêm os testes e pipelines de CI passando com 100% de cobertura. |
| **VII. Escopo Estrito (YAGNI)** | PASS | Foco exclusivo e estrito na padronização de nomenclatura solicitada pelo usuário. |
| **Nomenclatura Canônica Obrigatória** | PASS | Alinhamento direto com `gerenciador_patrimonio`, `patrimonio-frontend`, `patrimonio_db`, `patrimonio_net` e `patrimonio_data`. |

## Project Structure

### Documentation (this feature)

```text
specs/003-padronizar-nomes-patrimonio/
├── plan.md              # Este arquivo (plano de implementação)
├── research.md          # Decisões de padronização e justificativas
├── data-model.md        # Esquema de identificadores canônicos
├── quickstart.md        # Guia de validação prática
├── contracts/
│   ├── docker-compose-contract.md
│   └── naming-policy-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Tarefas a serem geradas pelo /speckit-tasks
```

### Source Code (repository root)

```text
├── docker-compose.yml           # Ajustar rede patrimonio_net e volume patrimonio_data
├── docker-compose.prod.yml      # Ajustar rede patrimonio_net e volume patrimonio_data
├── Dockerfile                   # Dockerfile multi-stage backend
├── alembic/
│   └── versions/                # Higienizar docstrings com termos genéricos antigos
├── src/
│   ├── api/                     # Rotas e controladores FastAPI
│   ├── core/                    # Configurações e segurança
│   ├── domain/                  # Entidades e schemas
│   ├── infrastructure/          # Repositórios e seed
│   └── use_cases/               # Regras de negócio
├── frontend/
│   ├── package.json             # Nome: patrimonio-frontend
│   ├── Dockerfile               # Dockerfile multi-stage frontend
│   └── src/                     # Código React SPA
└── tests/                       # Suíte de testes unitários, integração e E2E
```

**Structure Decision**: A estrutura segue rigorosamente o padrão arquitetural modular existente no repositório, aplicando alterações apenas nos arquivos de orquestração Docker e alinhando comentários/docstrings sem alterar a organização das pastas.

## Complexity Tracking

> Nenhuma violação constitucional detectada. Sem necessidade de rastreamento de complexidade adicional.
