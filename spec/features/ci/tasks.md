# Plano de Tarefas: Pipeline de Integração Contínua (CI) com GitHub Actions

Este documento define o plano detalhado de implementação para o pipeline de **Integração Contínua (CI)** com GitHub Actions, mapeando cada requisito da especificação [`spec.md`](file:///home/gil/code/internal_management/spec/features/ci/spec.md) e cumprindo os princípios da [`constituicao.md`](file:///home/gil/code/internal_management/spec/constituicao.md).

---

## Mapeamento de Requisitos da Especificação

| Requisito / Regra | Descrição | Tarefa Correspondente |
|---|---|---|
| **RN-CI-01** | Gatilhos de push para branches `main`, `develop` e `master`. | **TASK-CI-01** |
| **RN-CI-02** | Estruturação de jobs paralelos e independentes (`backend-tests` e `frontend-tests`). | **TASK-CI-01**, **TASK-CI-02**, **TASK-CI-03** |
| **RN-CI-03 / RN-CI-04** | Backend: Setup Python 3.13, action `astral-sh/setup-uv` com cache e serviço PostgreSQL 16. | **TASK-CI-02** |
| **RN-CI-05 / RN-CI-06** | Backend: Validação de migrações (`alembic upgrade head`) e execução de Pytest com cobertura. | **TASK-CI-02** |
| **RN-CI-07 / RN-CI-08** | Frontend: Setup Node.js 20, cache NPM e instalação limpa com `npm ci`. | **TASK-CI-03** |
| **RN-CI-09 / RN-CI-10** | Frontend: Checagem estática TypeScript (`tsc --noEmit`) e testes com Vitest. | **TASK-CI-03** |
| **Cenários 1 a 4** | Validação BDD completa e verificação local dos comandos do CI. | **TASK-CI-04** |

---

## Lista de Tarefas de Implementação

### Fase 1: Criação do Workflow do GitHub Actions
- [x] **TASK-CI-01: Configuração Estrutural do Workflow (`.github/workflows/ci.yml`)**
  - [x] Criar diretório `.github/workflows/`.
  - [x] Definir o nome do workflow (`CI Pipeline`).
  - [x] Configurar os gatilhos `on: push: branches: [main, develop, master]`.

- [x] **TASK-CI-02: Configuração do Job de Backend (`backend-tests`)**
  - [x] Configurar runner `ubuntu-latest`.
  - [x] Configurar container de serviço PostgreSQL 16 (`postgres:16-alpine`) com variáveis de ambiente e healthcheck `pg_isready`.
  - [x] Configurar steps:
    - Checkout do repositório (`actions/checkout@v4`).
    - Setup do Python 3.13 (`actions/setup-python@v5`).
    - Setup do `uv` com cache (`astral-sh/setup-uv@v5`).
    - Sincronização de dependências (`uv sync --all-extras`).
    - Aplicação de migrações (`uv run alembic upgrade head`).
    - Execução do Pytest com cobertura (`PYTHONPATH=. uv run pytest --cov=src --cov-branch --cov-report=term-missing`).

- [x] **TASK-CI-03: Configuração do Job de Frontend (`frontend-tests`)**
  - [x] Configurar runner `ubuntu-latest`.
  - [x] Configurar working directory `frontend`.
  - [x] Configurar steps:
    - Checkout do repositório (`actions/checkout@v4`).
    - Setup do Node.js 20 com cache NPM (`actions/setup-node@v4`).
    - Instalação de dependências (`npm ci`).
    - Validação de tipagem (`npx tsc --noEmit`).
    - Execução da suíte de testes (`npm test -- --run`).

---

### Fase 2: Validação e Auditoria dos Comandos
- [x] **TASK-CI-04: Verificação Local e Execução Simulada dos Comandos do CI**
  - [x] Testar comandos do backend (`uv sync`, `alembic upgrade head`, `pytest --cov=src --cov-branch`).
  - [x] Testar comandos do frontend (`npm ci`, `npx tsc --noEmit`, `npm test -- --run`).
  - [x] Validar sintaxe do YAML do workflow.
