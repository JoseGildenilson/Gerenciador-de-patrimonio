# CI/CD Data Model & Configuration Architecture

**Feature**: `002-fix-ci-pipeline`  
**Date**: 2026-10-28  
**Status**: Completed  

---

## 1. Visão Geral do Modelo de Configuração

Esta especificação modela a estrutura de dados declarativa, o ciclo de vida dos jobs de integração e as restrições dos *Quality Gates* do pipeline automatizado no GitHub Actions.

---

## 2. Entidades de Configuração

### 2.1. Entidade: Pipeline Workflow (`ci.yml`)

Representa o arquivo de orquestração do GitHub Actions.

| Propriedade | Tipo | Obrigatório | Descrição / Restrição |
|---|---|:---:|---|
| `name` | String | Sim | Nome canônico: `CI Pipeline` |
| `on` | Map / EventList | Sim | Eventos de disparo: `push`, `pull_request`, `workflow_dispatch` |
| `permissions` | Map | Sim | `contents: read` |
| `concurrency` | Map | Sim | Grupo por workflow e branch com `cancel-in-progress: true` |
| `jobs` | Map<String, Job> | Sim | Conjunto de jobs executados: `backend-tests`, `frontend-tests`, `docker-build-check` |

### 2.2. Entidade: Container de Serviço PostgreSQL (`postgres-service`)

Representa a infraestrutura efêmera de banco de dados provisionada para os testes de backend.

| Parâmetro | Valor / Tipo | Descrição / Justificativa |
|---|---|---|
| `image` | `postgres:16-alpine` | Imagem oficial PostgreSQL 16 em container mínimo Alpine |
| `POSTGRES_USER` | `postgres` | Usuário administrador do banco |
| `POSTGRES_PASSWORD` | `postgres` | Senha padrão de teste |
| `POSTGRES_DB` | `test_patrimonio_db` | Banco canônico de teste em conformidade com a Constituição |
| `ports` | `5432:5432` | Mapeamento da porta TCP para o host do runner |
| `health-cmd` | `"pg_isready -U postgres -d test_patrimonio_db"` | **Crítico:** verificação autenticada com role explícita |
| `health-interval` | `10s` | Intervalo entre sondagens de prontidão |
| `health-timeout` | `5s` | Tempo limite por verificação |
| `health-retries` | `5` | Número máximo de tentativas até considerar o serviço saudável |

### 2.3. Entidade: Quality Gates de Validação

Define as regras inegociáveis de aprovação em cada job.

```mermaid
flowchart TD
    subgraph Backend_Gate["Quality Gates: Backend"]
        B1["Lint Check (Ruff)"] --> B2["Format Check (Ruff)"]
        B2 --> B3["Alembic Migrations"]
        B3 --> B4["Pytest (100% Coverage Gate)"]
    end

    subgraph Frontend_Gate["Quality Gates: Frontend"]
        F1["NPM Clean Install (npm ci)"] --> F2["TypeScript Compile (tsc --noEmit)"]
        F2 --> F3["ESLint (npm run lint)"]
        F3 --> F4["Vite Build (npm run build)"]
        F4 --> F5["Vitest Unit Tests (npm test -- --run)"]
    end

    subgraph Docker_Gate["Quality Gates: Containers"]
        D1["Build Backend Multi-stage (production)"]
        D2["Build Frontend Multi-stage (production)"]
    end
```

---

## 3. Matriz de Parâmetros e Variáveis de Ambiente

| Variável | Escopo | Valor Padrão em CI | Finalidade |
|---|---|---|---|
| `DATABASE_URL` | `backend-tests` | `postgresql://postgres:postgres@localhost:5432/test_patrimonio_db` | Conexão para migrações do Alembic |
| `TEST_DATABASE_URL` | `backend-tests` | `postgresql://postgres:postgres@localhost:5432/test_patrimonio_db` | Conexão para fixtures do Pytest |
| `SECRET_KEY` | `backend-tests` | `ci-test-secret-key-that-is-at-least-32-characters-long` | Chave de criptografia e assinatura JWT |
| `PYTHONPATH` | `backend-tests` | `.` | Resolução correta do pacote `src` |

---

## 4. Máquina de Estados do Pipeline

```mermaid
stateDiagram-v2
    [*] --> Triggered: Push / PR / Manual Dispatch
    Triggered --> InProgress: Runner alocado
    state InProgress {
        [*] --> Backend: backend-tests
        [*] --> Frontend: frontend-tests
        [*] --> Docker: docker-build-check
        
        state Backend {
            InitPostgres --> LintAndFormat
            LintAndFormat --> RunMigrations
            RunMigrations --> RunTests100Cov
        }
        
        state Frontend {
            InstallDeps --> TypeCheck
            TypeCheck --> LintAndBuild
            LintAndBuild --> RunVitest
        }
        
        state Docker {
            BuildBackendImg --> BuildFrontendImg
        }
    }
    InProgress --> Success: Todos os jobs passaram (Exit 0)
    InProgress --> Failure: Qualquer step falhou (Exit != 0)
    Success --> [*]
    Failure --> [*]
```
