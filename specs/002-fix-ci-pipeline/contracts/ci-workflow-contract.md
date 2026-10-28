# Contract Specification: CI Workflow (`ci.yml`)

**Feature**: `002-fix-ci-pipeline`  
**Contract Version**: `1.1.0`  
**Date**: 2026-10-28  

---

## 1. Disparos e Eventos de Entrada

O workflow expõe os seguintes contratos de disparo:

```yaml
on:
  push:
    branches:
      - main
      - develop
      - master
  pull_request:
    branches:
      - main
      - develop
  workflow_dispatch:
```

### Contrato de Execução Manual (`workflow_dispatch`)
- **Entrada:** Nenhuma entrada obrigatória (executa contra a branch selecionada).
- **Comportamento esperado:** Iniciar imediatamente os três jobs paralelos para a branch de referência informada.

---

## 2. Contrato do Job: `backend-tests`

### 2.1. Serviços Requeridos
- **PostgreSQL 16 Service**:
  ```yaml
  services:
    postgres:
      image: postgres:16-alpine
      env:
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: postgres
        POSTGRES_DB: test_patrimonio_db
      ports:
        - 5432:5432
      options: >-
        --health-cmd "pg_isready -U postgres -d test_patrimonio_db"
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5
  ```

### 2.2. Sequência Estrita de Comandos e Códigos de Saída

| Passo | Comando | Código Esperado | Ação em Falha |
|---|---|:---:|---|
| 1. Instalação | `uv sync --frozen --all-extras` | `0` | Bloqueia job (falha de dependência) |
| 2. Linting | `uv run ruff check src/` | `0` | Bloqueia job (violação estática) |
| 3. Formatação | `uv run ruff format --check src/` | `0` | Bloqueia job (estilo desalinhado) |
| 4. Migrações | `uv run alembic upgrade head` | `0` | Bloqueia job (erro estrutural de schema) |
| 5. Testes e Cobertura | `PYTHONPATH=. uv run pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=100` | `0` | Bloqueia job (falha funcional ou cobertura < 100%) |

---

## 3. Contrato do Job: `frontend-tests`

### 3.1. Sequência Estrita de Comandos e Códigos de Saída

| Passo | Comando | Código Esperado | Ação em Falha |
|---|---|:---:|---|
| 1. Instalação Limpa | `npm ci` | `0` | Bloqueia job |
| 2. Checagem de Tipos | `npx tsc --noEmit` | `0` | Bloqueia job (erro de tipagem TypeScript) |
| 3. Linting | `npm run lint` | `0` | Bloqueia job |
| 4. Compilação de Ativos | `npm run build` | `0` | Bloqueia job |
| 5. Suíte de Testes | `npm test -- --run` | `0` | Bloqueia job |

---

## 4. Contrato do Job: `docker-build-check`

### 4.1. Sequência Estrita de Comandos

| Imagem | Comando | Target | Código Esperado |
|---|---|---|:---:|
| Backend | `docker build -t backend:test --target production .` | `production` | `0` |
| Frontend | `docker build -t frontend:test --target production frontend/` | `production` | `0` |
