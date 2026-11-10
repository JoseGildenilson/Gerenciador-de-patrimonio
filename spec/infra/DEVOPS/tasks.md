# Plano de Tarefas: Engenharia DevOps, SRE & DevSecOps

Este documento define o plano detalhado de implementação técnica para mitigar os riscos, vulnerabilidades e inconformidades levantados no relatório de auditoria [`spec/infra/DEVOPS/plan.md`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/spec/infra/DEVOPS/plan.md), garantindo o alinhamento estrito com a [Constituição do Projeto](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/spec/constituicao.md) e com as especificações em `spec/features/`.

---

## Mapeamento de Vulnerabilidades x Tarefas de Implementação

| ID Vulnerabilidade / Requisito | Descrição Sintética | Tarefa Correspondente | Prioridade | Status |
|---|---|---|:---:|:---:|
| **DEV-CRIT-01 / RN-IGN-06** | Planilha real rastreada no Git e no contexto Docker (`PATRIMÔNIO CTM.xlsx`). | **TASK-DEV-01** | P0 (Imediata) | Concluído ✅ |
| **DEV-MED-01** | Quebra de script Linux por terminação CRLF (`entrypoint.sh`) e falta de `.gitattributes`. | **TASK-DEV-02** | P0 (Imediata) | Concluído ✅ |
| **DEV-CRIT-04** | Exposição pública das portas 5432 (Postgres) e 8000 (API) no host em produção. | **TASK-DEV-03** | P0 (Imediata) | Concluído ✅ |
| **DEV-CRIT-02 / RN-DK-01** | Injeção incondicional de credenciais padrão (`senha123`) e seeds em produção. | **TASK-DEV-04** | P0 (Imediata) | Concluído ✅ |
| **DEV-CRIT-05 / DEV-ALTO-04 / Art. 5** | CI sem gatilho de Pull Requests e sem portão `--cov-fail-under=100`. | **TASK-DEV-05** | P0 (Imediata) | Concluído ✅ |
| **DEV-ALTO-02 / DEV-MED-03** | Nginx com upload limitado a 1MB, rota `/health` sem proxy e falta de gzip/headers. | **TASK-DEV-06** | P1 (Alta) | Concluído ✅ |
| **DEV-ALTO-07** | Ausência de healthcheck no backend e dependência fraca no frontend no Compose. | **TASK-DEV-07** | P1 (Alta) | Concluído ✅ |
| **DEV-ALTO-06 / DEV-MED-06 / RN-DK-03** | Falta de obrigatoriedade de `SECRET_KEY`, limites de recursos e logs em produção. | **TASK-DEV-08** | P1 (Alta) | Concluído ✅ |
| **DEV-CRIT-03 / DEV-ALTO-01 / DEV-BAIX-02** | Falso multi-stage no backend, imagem rodando como root e `spec/` no container. | **TASK-DEV-09** | P1 (Alta) | Concluído ✅ |
| **DEV-CRIT-03 / DEV-MED-02** | Frontend rodando como root em produção e dependências via `npm install`. | **TASK-DEV-10** | P2 (Média) | Concluído ✅ |
| **DEV-ALTO-05 / DEV-MED-04 / DEV-BAIX-01** | CI sem validação de build frontend, sem `concurrency` e com `uv sync` não-frozen. | **TASK-DEV-11** | P2 (Média) | Concluído ✅ |
| **DEV-ALTO-05** | Ausência de validação de build dos Dockerfiles na esteira de CI. | **TASK-DEV-12** | P2 (Média) | Concluído ✅ |
| **DEV-MED-05** | Script `lint` quebrado no frontend e ausência de linter no backend. | **TASK-DEV-13** | P3 (Melhoria) | Concluído ✅ |

---

## Detalhamento das Tarefas por Fase

### Fase 1: Quick Wins e Segurança Crítica (Execução Imediata)

- [x] **TASK-DEV-01: Higienização de Dados Reais e Atualização do Contexto Docker**
  - [x] Remover a planilha corporativa do índice de rastreamento Git preservando o arquivo local:
    ```bash
    git rm --cached "PATRIMÔNIO CTM.xlsx"
    ```
  - [x] Atualizar [`.dockerignore`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.dockerignore) na raiz adicionando:
    ```dockerignore
    *.xlsx
    *.xls
    *.csv
    spec/
    .github/
    README.md
    tests/
    docker-compose*.yml
    ```
  - [x] Atualizar [`frontend/.dockerignore`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/.dockerignore) adicionando:
    ```dockerignore
    .env*
    *.test.tsx
    *.spec.tsx
    tests/
    README.md
    ```
  - *Critério de Aceite:* `git status` mostra a planilha como untracked (ignorada pelo `.gitignore`) e o contexto enviado ao Docker daemon é reduzido em tempo de build.

- [x] **TASK-DEV-02: Normalização de Line-Endings e Criação de `.gitattributes`**
  - [x] Criar o arquivo `.gitattributes` na raiz do projeto com as regras de normalização de finais de linha:
    ```gitattributes
    * text=auto
    *.sh text eol=lf
    Dockerfile* text eol=lf
    *.py text eol=lf
    *.json text eol=lf
    *.yml text eol=lf
    *.yaml text eol=lf
    *.md text eol=lf
    ```
  - [x] Normalizar o arquivo [`entrypoint.sh`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/entrypoint.sh) convertendo quebras `CRLF` (`\r\n`) para `LF` (`\n`).
  - [x] Garantir permissão de execução POSIX (`chmod +x entrypoint.sh`).
  - *Critério de Aceite:* `[System.IO.File]::ReadAllBytes("entrypoint.sh")` reporta zero ocorrências do byte 13 (`\r`).

- [x] **TASK-DEV-03: Fechamento de Portas e Isolamento de Rede em Produção**
  - [x] Em [`docker-compose.prod.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.prod.yml):
    - [x] Remover o bloco `ports:` do serviço `postgres` (`"${POSTGRES_PORT:-5432}:5432"`).
    - [x] Remover o bloco `ports:` do serviço `backend` (`"${BACKEND_PORT:-8000}:8000"`).
    - [x] Manter apenas o serviço `frontend` publicando portas no host (`"${FRONTEND_PROD_PORT:-3000}:8080"`).
  - *Critério de Aceite:* Serviços `postgres` e `backend` tornam-se inalcançáveis fora da rede bridge interna `patrimonio_net`, eliminando o risco de exposição do banco à internet.

- [x] **TASK-DEV-04: Proteção contra Injeção de Dados Mocks e Senhas Padrão em Produção**
  - [x] No arquivo [`entrypoint.sh`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/entrypoint.sh):
    - [x] Substituir a execução incondicional de `python -m src.infrastructure.seed` por condicional baseada na variável de ambiente `RUN_SEED`:
      ```sh
      if [ "$RUN_SEED" = "true" ]; then
          echo "==> [SEED] Executando seed de dados padrão..."
          python -m src.infrastructure.seed
      else
          echo "==> [SEED] Pulando seed de dados (RUN_SEED != true)."
      fi
      ```
  - [x] Em [`docker-compose.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.yml), definir `RUN_SEED: "true"` no backend para manter a ergonomia de desenvolvimento local.
  - [x] Em [`docker-compose.prod.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.prod.yml), definir explicitamente `RUN_SEED: "false"`.
  - *Critério de Aceite:* Instâncias de produção não sofrem injeção automática de contas com senha fraca `senha123` e nem poluição de tickets/equipamentos fictícios.

- [x] **TASK-DEV-05: Alinhamento Constitucional e Quality Gate Estrito no CI**
  - [x] Em [`.github/workflows/ci.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.github/workflows/ci.yml):
    - [x] Adicionar o gatilho `pull_request` para validar PRs direcionados para `main` e `develop` (Art. 5.2 da Constituição):
      ```yaml
      on:
        push:
          branches: [main, develop, master]
        pull_request:
          branches: [main, develop]
      ```
    - [x] Adicionar `--cov-fail-under=100` no step de testes do backend para bloquear commits com cobertura abaixo de 100% (Art. 2.4 da Constituição).
    - [x] Adicionar a flag `--frozen` no step de instalação do backend (`uv sync --frozen --all-extras`).
  - *Critério de Aceite:* O workflow é disparado automaticamente na abertura de Pull Requests e falha se a cobertura de linhas/branches for inferior a 100%.

---

### Fase 2: Hardening do Nginx e Orquestração Compose

- [x] **TASK-DEV-06: Configuração de Alta Resiliência e Hardening do Nginx**
  - [x] No arquivo [`frontend/nginx.conf`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/nginx.conf):
    - [x] Expandir o limite máximo de requisição para `client_max_body_size 50M;` para permitir upload de planilhas volumosas sem erro `413`.
    - [x] Adicionar rota dedicada de healthcheck para o proxy reverso:
      ```nginx
      location /health {
          proxy_pass http://backend:8000/health;
          proxy_http_version 1.1;
          proxy_set_header Host $host;
      }
      ```
    - [x] Habilitar compressão gzip com tipos MIME adequados (`text/plain`, `text/css`, `application/json`, `application/javascript`, `image/svg+xml`, etc.).
    - [x] Injetar cabeçalhos de segurança HTTP essenciais (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`, `server_tokens off`).
    - [x] Adicionar diretiva de cache imutável para assets estáticos empacotados pelo Vite (`/assets/` com `expires 1y; add_header Cache-Control "public, immutable";`).
  - *Critério de Aceite:* Testes com uploads de 10MB passam com sucesso, `/health` responde o status real da API FastAPI e auditoria de headers HTTP retorna parâmetros de proteção ativos.

- [x] **TASK-DEV-07: Implementação de Healthchecks e Orquestração Condicional**
  - [x] No serviço `backend` em [`docker-compose.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.yml) e [`docker-compose.prod.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.prod.yml):
    - [x] Adicionar healthcheck HTTP:
      ```yaml
      healthcheck:
        test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval: 10s
        timeout: 5s
        retries: 5
        start_period: 15s
      ```
  - [x] No serviço `frontend`, atualizar a diretiva `depends_on`:
    ```yaml
    depends_on:
      backend:
        condition: service_healthy
    ```
  - *Critério de Aceite:* `docker compose up` aguarda o backend aplicar migrações e retornar `200 OK` em `/health` antes de iniciar o Nginx/frontend, eliminando erros `502 Bad Gateway` na subida do ambiente.

- [x] **TASK-DEV-08: Governança de Recursos, Logs e Segredos no Compose Prod**
  - [x] Em [`docker-compose.prod.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.prod.yml):
    - [x] Enforçar a obrigatoriedade da variável `SECRET_KEY`:
      ```yaml
      SECRET_KEY: "${SECRET_KEY:?ERRO CRITICO - A variavel SECRET_KEY precisa ser configurada obrigatoriamente no arquivo .env para execucao em producao.}"
      ```
    - [x] Adicionar limites de CPU e memória em todos os serviços (`deploy.resources.limits`).
    - [x] Adicionar configuração de rotação de logs Docker:
      ```yaml
      logging:
        driver: "json-file"
        options:
          max-size: "10m"
          max-file: "3"
      ```
  - *Critério de Aceite:* O Compose de produção se recusa a iniciar se a chave criptográfica não for informada e o consumo de recursos e disco de logs fica sob controle rígido.

---

### Fase 3: Modernização de Dockerfiles (Multi-stage e Non-Root)

- [x] **TASK-DEV-09: Refatoração Multi-Stage e Usuário Não-Root no Backend**
  - [x] No arquivo [`Dockerfile`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/Dockerfile):
    - [x] Pinagem imutável da imagem base: `python:3.13-slim-bookworm` e `ghcr.io/astral-sh/uv:0.6.5`.
    - [x] Criar usuário e grupo de serviço `appuser` (UID/GID 10001).
    - [x] Estágio `builder`:
      - Copiar apenas `pyproject.toml` e `uv.lock`.
      - Executar `uv sync --frozen --no-dev --no-cache`.
    - [x] Estágio `production`:
      - Base limpa sem compiladores (`gcc`, `libpq-dev` removidos).
      - Copiar apenas o virtualenv `/app/.venv` do builder.
      - Copiar código-fonte da aplicação (`src/`, `alembic/`, `alembic.ini`).
      - NÃO copiar `spec/`.
      - Mudar propriedade dos arquivos para `appuser` e declarar `USER 10001`.
  - *Critério de Aceite:* A imagem final de produção é reduzida significativamente, não contém ferramentas de compilação e o processo do Uvicorn roda com UID 10001.

- [x] **TASK-DEV-10: Refatoração Non-Root e Determinismo no Frontend**
  - [x] No arquivo [`frontend/Dockerfile`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/Dockerfile):
    - [x] No estágio `development`, substituir `npm install` por `npm ci`.
    - [x] Fixar imagem base do builder em `node:20.18-alpine3.20`.
    - [x] No estágio `production`, adotar a imagem base `nginxinc/nginx-unprivileged:alpine`.
    - [x] Ajustar o arquivo `frontend/nginx.conf` para escutar na porta não-privilegiada `8080`.
    - [x] Mapear as portas correspondentes no `docker-compose.prod.yml` (`${FRONTEND_PROD_PORT:-3000}:8080`).
  - *Critério de Aceite:* O frontend de produção executa com usuário sem privilégios (`nginx`, UID 101) na porta 8080 sem requerer privilégios de root para bind de portas.

---

### Fase 4: Pipeline de CI/CD e Quality Gates Avançados

- [x] **TASK-DEV-11: Concorrência, Privilégio Mínimo e Step de Build no CI**
  - [x] Em [`.github/workflows/ci.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.github/workflows/ci.yml):
    - [x] Adicionar bloco de permissões explícitas no nível de topo:
      ```yaml
      permissions:
        contents: read
      ```
    - [x] Adicionar bloco de controle de concorrência para cancelar builds duplicadas:
      ```yaml
      concurrency:
        group: ${{ github.workflow }}-${{ github.ref }}
        cancel-in-progress: true
      ```
    - [x] No job `frontend-tests`, adicionar step obrigatório de build de assets:
      ```yaml
      - name: Build Frontend Assets (Vite)
        run: npm run build
      ```
  - *Critério de Aceite:* Pushes sucessivos abortam execuções obsoletas economizando minutos de runner, e o processo de build do Vite é validado a cada commit.

- [x] **TASK-DEV-12: Job de Validação de Build dos Containers no CI**
  - [x] Em [`.github/workflows/ci.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.github/workflows/ci.yml):
    - [x] Adicionar job paralelo ou subsequente `docker-build-check`:
      ```yaml
      docker-build-check:
        name: Validate Docker Builds
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - name: Build Backend Docker Image
            run: docker build -t backend:test --target production .
          - name: Build Frontend Docker Image
            run: docker build -t frontend:test --target production frontend/
      ```
  - *Critério de Aceite:* Qualquer quebra de sintaxe, arquivo faltante ou erro em Dockerfile falha imediatamente o pipeline antes do merge.

- [x] **TASK-DEV-13: Padronização e Linters Estáticos no CI**
  - [x] No frontend:
    - [x] Instalar `eslint` e plugins necessários em `devDependencies` e configurar `frontend/.eslintrc.cjs`.
    - [x] Adicionar step `npm run lint` no job de frontend do CI.
  - [x] No backend:
    - [x] Adicionar `ruff>=0.5.0` nas dependências de desenvolvimento em `pyproject.toml`.
    - [x] Adicionar step `uv run ruff check` e `uv run ruff format --check` no job de backend do CI.
  - *Critério de Aceite:* Violações de formatação e análise estática são bloqueadas no pipeline automaticamente.

---

## Critérios de Aceite Globais (Definition of Done)

Para que a implementação deste plano de DevOps seja considerada concluída, todas as seguintes condições foram verificadas com sucesso:

1. **Repositório Higienizado:** `git ls-files` não lista nenhum arquivo de planilha corporativa (`*.xlsx`, `*.xls`) e `.dockerignore` previne vazamentos para o daemon. [Concluído ✅]
2. **Postgres & Backend Isolados em Produção:** Nenhuma porta de banco ou API exposta na interface de rede pública do host no `docker-compose.prod.yml`. [Concluído ✅]
3. **Containers Não-Root:** Usuários sem privilégios configurados tanto no backend (`appuser`, UID 10001) quanto no frontend (`nginxinc/nginx-unprivileged:alpine`). [Concluído ✅]
4. **Resiliência do Nginx:** Upload de planilhas de teste de até 50MB aceito sem erro 413, e `/health` espelha o status real da aplicação. [Concluído ✅]
5. **Conformidade Constitucional 100%:** O GitHub Actions executa a suíte de testes em Pull Requests e bloqueia qualquer commit que resulte em cobertura inferior a 100% em linhas e branches. [Concluído ✅]
