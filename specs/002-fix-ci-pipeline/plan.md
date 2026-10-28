# Implementation Plan: Correção e Estabilização do Pipeline de Integração Contínua (CI)

**Branch**: `JoseGildenilson/CI-Fix` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from [`specs/002-fix-ci-pipeline/spec.md`](spec.md)

## Summary

Estabilizar e corrigir as causas-raiz de falha do pipeline de Integração Contínua no GitHub Actions (`.github/workflows/ci.yml`). O plano abrange:
1. Correção do healthcheck do container de serviço PostgreSQL (`pg_isready -U postgres -d test_patrimonio_db`), eliminando falhas de conexão por ausência da role `root`.
2. Formatação estrita dos arquivos Python em `src/` (notadamente [`src/infrastructure/seed.py`](../../src/infrastructure/seed.py)) com o Ruff para garantir conformidade com `ruff format --check src/`.
3. Inclusão do gatilho `workflow_dispatch` para permitir acionamento e depuração sob demanda em branches de correção.
4. Preservação integral do Quality Gate constitucional de 100% de cobertura em testes de backend e validações paralelas de frontend e Docker.

## Technical Context

**Language/Version**: Python 3.13, TypeScript 5.6+ (Node.js 20+), YAML (GitHub Actions Workflow v2)

**Primary Dependencies**: 
- Backend: uv 0.5+, ruff 0.5+, alembic 1.13+, pytest 8+, pytest-cov 5+, FastAPI, SQLAlchemy 2.0
- Frontend: React 18, Vite, Vitest, TypeScript
- Infra/CI: GitHub Actions, Docker, PostgreSQL 16 Alpine

**Storage**: PostgreSQL 16 (`test_patrimonio_db`) instanciado como container de serviço nos runners `ubuntu-latest`

**Testing**: Pytest (100% de cobertura de linhas e branches no backend), Vitest (testes de componentes e utilitários no frontend), TypeScript `tsc --noEmit`

**Target Platform**: GitHub Actions CI Runners (`ubuntu-latest`)

**Project Type**: Fullstack Web Application com automação de CI/CD

**Performance Goals**: Execução completa do pipeline paralelo em menos de 3 minutos

**Constraints**:
- Cobertura obrigatória de 100% em linhas e branches no backend (`--cov-fail-under=100`)
- Proibição de raw SQL
- Preservação estrita dos identificadores canônicos estabelecidos na Constituição
- Zero erros de inicialização de serviços dependentes no GitHub Actions

**Scale/Scope**: Workflow `.github/workflows/ci.yml`, arquivos-fonte de backend em `src/`, testes e scripts de automação

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio Constitucional | Avaliação de Impacto | Status |
|---|---|:---:|
| **I. Preservação de Contratos Públicos** | Nenhuma rota de API ou contrato HTTP é alterado. | **PASS** |
| **II. Arquitetura em Camadas** | Nenhuma camada arquitetural é modificada; trata-se de infraestrutura de CI e formatação. | **PASS** |
| **III. Persistência Exclusiva SQLAlchemy 2.0** | Mantido uso estrito de ORM e Alembic migrations; sem introdução de raw SQL. | **PASS** |
| **IV. Controle Transacional Delimitado** | Mantido padrão do repositório. | **PASS** |
| **V. Governança via Migrações Alembic** | O CI executa `alembic upgrade head` diretamente contra o PostgreSQL 16 de teste. | **PASS** |
| **VI. Cobertura de 100% e Quality Gates** | Preservado e reforçado. A checagem de formatação e os gates de cobertura permanecem estritamente ativos. | **PASS** |
| **VII. Escopo Estrito e Não-Refatoração** | Alterações limitadas às causas-raiz das falhas do CI: `.github/workflows/ci.yml` e arquivos com divergência de formatação. | **PASS** |

## Project Structure

### Documentation (this feature)

```text
specs/002-fix-ci-pipeline/
├── plan.md              # Este documento de planejamento (/speckit-plan)
├── research.md          # Decisões de pesquisa da Fase 0
├── data-model.md        # Modelo declarativo do pipeline e máquinas de estado da Fase 1
├── quickstart.md        # Guia de validação local e remota da Fase 1
├── contracts/           # Contrato formal do workflow do CI
│   └── ci-workflow-contract.md
└── checklists/
    └── requirements.md  # Checklist de qualidade da especificação
```

### Source Code (repository root)

```text
.github/
└── workflows/
    └── ci.yml                          # Workflow do GitHub Actions (alvo da correção)

src/
├── core/                               # Configuração centralizada
├── domain/                             # Modelos e schemas de validação
├── infrastructure/
│   ├── seed.py                         # Arquivo com divergência de formatação no Ruff
│   └── repositories.py
└── api/                                # Endpoints HTTP FastAPI

frontend/
├── src/                                # Código-fonte da SPA React
└── package.json

tests/
├── conftest.py
└── test_*.py                           # Suíte de testes automatizados com cobertura
```

**Structure Decision**: Utilização direta da estrutura de repositório fullstack monorepo existente (`.github/workflows/` para automações, `src/` para backend, `frontend/` para UI e `tests/` para testes), sem introdução de novos módulos ou dependências.

## Complexity Tracking

> **Nenhuma violação constitucional detectada. Sem acréscimo de complexidade desnecessária.**

| Item | Justificativa | Alternativa Rejeitada |
|---|---|---|
| Healthcheck com `-U postgres -d test_patrimonio_db` | Necessário para evitar que o comando execute com o usuário `root` e cause `FATAL: role "root" does not exist`. | Desativar o healthcheck ou adicionar `sleep` arbitrário (vulnerável a race conditions). |
| Adição de `workflow_dispatch` | Permite disparo manual imediato para diagnosticar branches de correção antes do merge. | Exigir abertura de PR ou push direto para `develop` para testar correções de CI. |
| Formatação via Ruff de `seed.py` | Restaura a conformidade exigida pelo step `Check Backend Formatting (Ruff)`. | Adicionar exceção no linter ou remover o step de formatação. |
