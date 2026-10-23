# Plano de Tarefas: Ambiente de Containers com Docker Compose

Este documento define o plano detalhado de tarefas para a implementação da infraestrutura de containers com Docker Compose, em conformidade com a especificação [`spec.md`](file:///home/gil/code/internal_management/spec/features/docker-compose/spec.md) e com a Constituição do Projeto em [`constituicao.md`](file:///home/gil/code/internal_management/spec/constituicao.md).

---

## Mapeamento de Requisitos da Especificação

| Requisito / Cenário | Descrição | Tarefa Correspondente |
|---|---|---|
| **RN-DK-01** | Idempotência da inicialização (migrações e seeds sem duplicidade). | **TASK-03**, **TASK-06** |
| **RN-DK-02** | Compatibilidade multi-driver no backend (SQLite e PostgreSQL via `psycopg2-binary`). | **TASK-01**, **TASK-06** |
| **RN-DK-03** | Isolamento de secrets e template `.env.example`. | **TASK-05** |
| **RN-DK-04** | Hot-Reload em desenvolvimento no Backend e Frontend. | **TASK-02**, **TASK-04**, **TASK-06** |
| **RN-DK-05** | Build multi-stage otimizado (desenvolvimento vs produção). | **TASK-02**, **TASK-04**, **TASK-07** |
| **Cenário 1** | Inicialização com `docker compose up` (Postgres, Backend, Frontend). | **TASK-06** |
| **Cenário 2** | Persistência de dados do PostgreSQL no volume `postgres_data`. | **TASK-06** |
| **Cenário 3** | Hot-reload do Backend FastAPI em desenvolvimento. | **TASK-02**, **TASK-06** |
| **Cenário 4** | Hot-reload do Frontend Vite em desenvolvimento. | **TASK-04**, **TASK-06** |
| **Cenário 5** | Execução de produção via `docker-compose.prod.yml` com Nginx. | **TASK-07** |

---

## Lista de Tarefas de Implementação

### Fase 1: Dependências e Configuração do Backend
- [x] **TASK-01: Adicionar driver PostgreSQL (`psycopg2-binary`) e compatibilizar Database Engine**
  - [x] Adicionar `psycopg2-binary>=2.9.9` no `pyproject.toml`.
  - [x] Atualizar o lockfile via `uv lock` / `uv sync`.
  - [x] Garantir que `src/core/database.py` e `src/core/config.py` tratem URLs de conexão do PostgreSQL (`postgresql://` e `postgresql+psycopg2://`).
  - *Critério de Aceite:* `PYTHONPATH=. uv run pytest` executa 100% dos testes existentes com sucesso.

- [x] **TASK-02: Criar Dockerfile e Script de Entrypoint do Backend**
  - [x] Criar `entrypoint.sh` com:
    - Verificação ativa de prontidão do PostgreSQL.
    - Execução do `alembic upgrade head`.
    - Execução idempotente do seed de tags e dados essenciais.
    - Inicialização do servidor Uvicorn.
  - [x] Dar permissão de execução (`chmod +x entrypoint.sh`).
  - [x] Criar `Dockerfile` multi-stage do Backend com suporte a dev (`uvicorn --reload`) e prod.
  - [x] Criar `.dockerignore` na raiz do projeto (ignorando `.venv`, `__pycache__`, `.pytest_cache`, `.git`, etc.).
  - *Critério de Aceite:* Imagem do backend constrói com sucesso via Docker.

---

### Fase 2: Configuração e Dockerização do Frontend
- [x] **TASK-03: Configurar Proxy e Host do Vite no Frontend**
  - [x] Ajustar `frontend/vite.config.ts` para habilitar `server.host = '0.0.0.0'` e proxy reverso para `http://backend:8000` em ambiente containerizado.
  - *Critério de Aceite:* Vite dev server aceita conexões de fora do container.

- [x] **TASK-04: Criar Dockerfile, Configuração Nginx e `.dockerignore` do Frontend**
  - [x] Criar `frontend/Dockerfile` com estágios `development` (Node.js 20-alpine / `npm run dev`) e `production` (build + Nginx).
  - [x] Criar `frontend/nginx.conf` com fallback para SPA (`try_files $uri $uri/ /index.html`) e proxy reverso para `/api/`.
  - [x] Criar `frontend/.dockerignore` (ignorando `node_modules`, `dist`, `coverage`, etc.).
  - *Critério de Aceite:* Build de ambas as etapas do frontend constrói sem erros.

---

### Fase 3: Orquestração e Compose
- [x] **TASK-05: Criar Arquivos de Configuração de Ambiente (`.env.example` e `.env`)**
  - [x] Criar `.env.example` com variáveis documentadas:
    - `POSTGRES_USER=postgres`
    - `POSTGRES_PASSWORD=postgres`
    - `POSTGRES_DB=internal_management`
    - `POSTGRES_PORT=5432`
    - `DATABASE_URL=postgresql://postgres:postgres@postgres:5432/internal_management`
    - `SECRET_KEY=...`
    - `BACKEND_PORT=8000`
    - `FRONTEND_PORT=5173`
    - `FRONTEND_PROD_PORT=3000`
  - [x] Gerar `.env` padrão local para execução imediata.
  - *Critério de Aceite:* Todas as variáveis necessárias estão mapeadas e desacopladas do código.

- [x] **TASK-06: Criar `docker-compose.yml` (Ambiente de Desenvolvimento)**
  - [x] Definir serviço `postgres` com healthcheck `pg_isready` e volume `postgres_data`.
  - [x] Definir serviço `backend` com `depends_on: { postgres: { condition: service_healthy } }`, portas expostas e volumes montados para live reload.
  - [x] Definir serviço `frontend` com target `development`, portas expostas e volumes montados para hot reload.
  - [x] Configurar rede interna unificada `internal-net`.
  - *Critério de Aceite:* `docker compose up` inicia os 3 serviços de forma ordenada e acessível.

- [x] **TASK-07: Criar `docker-compose.prod.yml` (Ambiente de Produção)**
  - [x] Definir serviços sem volumes de código do host e com frontend servido pelo Nginx na porta 3000.
  - *Critério de Aceite:* `docker compose -f docker-compose.prod.yml build` compila com sucesso.

---

### Fase 4: Validação e Testes de Integração
- [x] **TASK-08: Executar e Validar os Containers**
  - [x] Testar build e subida do ambiente de desenvolvimento.
  - [x] Validar healthcheck da API em `http://localhost:8000/health`.
  - [x] Validar acesso ao frontend em `http://localhost:5173`.
  - [x] Validar execução de migrações e persistência de dados no PostgreSQL.
  - [x] Executar suíte de testes backend e frontend para garantir zero regressão.
  - *Critério de Aceite:* 100% dos testes e cenários de aceitação passando.
