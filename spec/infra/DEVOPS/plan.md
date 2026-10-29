# Plano de Ação e Auditoria de DevOps & SRE — Gestão de Patrimônio e Suporte

**Data da Auditoria:** 14/10/2026  
**Responsável:** Engenharia de DevOps e SRE Sênior (DevSecOps)  
**Status do Projeto:** ATENÇÃO / RISCO ELEVADO (Vulnerabilidades de segurança em produção, dados reais versionados e inconformidade constitucional no CI)  
**Metodologia:** Spec-Driven Development (Spec-Anchored) & Boas Práticas DevSecOps (12-Factor App / CIS Docker Benchmark)

---

## 1. Diagnóstico Executivo de Infraestrutura

A auditoria completa da arquitetura de containers, orquestração Docker Compose (desenvolvimento e produção), script de inicialização (`entrypoint.sh`), proxy reverso Nginx, política de arquivos ignorados (`.dockerignore`/`.gitignore`) e esteira de CI (`.github/workflows/ci.yml`) — confrontada com a [Constituição do Projeto](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/spec/constituicao.md) e as especificações de infraestrutura em `spec/features/` — identificou os seguintes pontos críticos:

- **Segurança de Dados e Segredos:** Planilha com 248 KB de dados reais de patrimônio corporativo (`PATRIMÔNIO CTM.xlsx`) continua versionada no índice Git e é transferida no contexto Docker; credenciais administrativas mockadas com senha pública (`senha123`) e registros fictícios são injetados incondicionalmente no banco de produção pelo `entrypoint.sh`; `SECRET_KEY` possui fallback silencioso para uma chave pública fraca.
- **Isolamento de Ambientes e Rede:** Em [`docker-compose.prod.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.prod.yml), tanto a porta do PostgreSQL (`5432`) quanto a do Backend FastAPI (`8000`) estão expostas publicamente no host, contornando o Nginx e abrindo o banco para a internet.
- **Arquitetura de Imagens (Docker):** O backend utiliza um "falso multi-stage" onde a imagem de produção carrega compiladores (`gcc`), bibliotecas de desenvolvimento (`libpq-dev`), binário do `uv` e dependências de teste (`pytest`). Todos os containers rodam como `root` (UID 0).
- **Proxy Reverso (Nginx):** Limite de upload herdado no padrão (1MB) provocará erro `413` na importação de planilhas; o endpoint de monitoramento `/health` não é roteado pelo Nginx (retornando o HTML da SPA como falso-positivo 200); ausência de compressão gzip, cache de assets e headers de proteção.
- **Pipeline de Integração Contínua (CI):** Descumprimento mandatório da Constituição do Projeto: **o workflow não roda em Pull Requests**, não bloqueia merges se a cobertura de testes for inferior a 100% (`--cov-fail-under=100` ausente), não valida o build do frontend nem das imagens Docker, e não possui controle de concorrência ou permissões mínimas.

---

## 2. Matriz de Conformidade com a Constituição e Specs

| Regra / Especificação | Status Atual | Diagnóstico de DevOps / SRE |
| :--- | :---: | :--- |
| **Constituição Art. 5.1 & 5.2 — CI em Push e Pull Requests** | ❌ **Não Conforme** | O `.github/workflows/ci.yml` só dispara em `push`. PRs de `develop` para `main` não disparam testes no GitHub Actions. |
| **Constituição Art. 2.4 — Cobertura 100% Obrigatória** | ⚠️ **Parcial** | O CI executa `pytest --cov`, mas sem `--cov-fail-under=100`. Quedas de cobertura para <100% passam com status verde. |
| **RN-DK-01 — Idempotência e Segurança na Inicialização** | ❌ **Não Conforme** | O `entrypoint.sh` executa seeds fictícios com usuários padrão (`tecnico@empresa.com` / `senha123`) inclusive em produção. |
| **RN-DK-03 — Isolamento Estrito de Segredos** | ⚠️ **Atenção** | `docker-compose.prod.yml` usa `${SECRET_KEY:-super-secret-key...}` permitindo boot de produção com chave pública. |
| **RN-DK-05 — Build Otimizado Multi-Stage** | ❌ **Não Conforme** | `Dockerfile` de backend apenas troca o `CMD`; mantém `gcc`, `libpq-dev` e dependências `dev` no container de produção. |
| **RN-IGN-06 — Ignorar Planilhas e Desindexar** | ❌ **Não Conforme** | `PATRIMÔNIO CTM.xlsx` está rastreado no Git (`git ls-files`) e ausente no `.dockerignore`, vazando para builds. |
| **Topologia Compose Prod — Nginx como Gateway Único** | ❌ **Não Conforme** | `docker-compose.prod.yml` expõe portas `5432` (Postgres) e `8000` (FastAPI) diretamente no host em vez de isolar na rede. |

---

## 3. Mapeamento Detalhado de Vulnerabilidades e Riscos

### 🔴 Severidade Crítica [CRÍTICO]

#### [DEV-CRIT-01] Dados Reais de Patrimônio Rastreados no Git e Inclusos no Contexto Docker
- **Localização:** [`PATRIMÔNIO CTM.xlsx`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/PATRIMÔNIO%20CTM.xlsx) e [`.dockerignore`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.dockerignore)
- **Causa Raiz:** A planilha foi versionada no commit `24ae1d5`. No commit `d6de711` a regra `*.xlsx` foi adicionada ao `.gitignore`, mas o arquivo nunca foi desindexado com `git rm --cached`. O `.dockerignore` também não filtra arquivos `.xlsx`.
- **Impacto / Risco:** Vazamento de dados institucionais sensíveis em repositórios remotos (infração de LGPD) e inchaço desnecessário do contexto enviado ao Docker daemon a cada build.
- **Ação:** Executar `git rm --cached "PATRIMÔNIO CTM.xlsx"` e adicionar `*.xlsx`, `*.xls`, `*.csv` ao `.dockerignore`.

#### [DEV-CRIT-02] Injeção de Contas Administrativas com Senha Padrão e Dados Mocks em Produção
- **Localização:** [`entrypoint.sh`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/entrypoint.sh#L38-L40) e [`src/infrastructure/seed.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/src/infrastructure/seed.py#L52-L71)
- **Causa Raiz:** O script de inicialização do container executa incondicionalmente `python -m src.infrastructure.seed`, que cria usuários `tecnico@empresa.com` e `colaborador@empresa.com` com senha conhecida `senha123`.
- **Impacto / Risco:** Qualquer instância de produção sobe com contas de acesso pré-configuradas e públicas, permitindo comprometimento total imediato da API, além de poluir o banco produtivo com tickets e equipamentos falsos.
- **Ação:** Proteger a execução do seed no `entrypoint.sh` através da variável `RUN_SEED=true`, desativada por padrão em produção.

#### [DEV-CRIT-03] Containers Executando como `root` (Ausência de Diretiva `USER`)
- **Localização:** [`Dockerfile`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/Dockerfile) e [`frontend/Dockerfile`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/Dockerfile)
- **Causa Raiz:** Nenhuma imagem declara usuário não-privilegiado. Os processos rodam com UID 0.
- **Impacto / Risco:** Em caso de vulnerabilidade em bibliotecas da aplicação (como RCE em parsers de multipart ou planilhas), o invasor ganha privilégios de `root` no container, aumentando drasticamente o potencial de escape e adulteração de arquivos no host.
- **Ação:** Criar usuário de serviço sem privilégios (`appuser` com UID 10001) no backend e migrar o frontend produtivo para imagem não-root (`nginxinc/nginx-unprivileged:alpine`).

#### [DEV-CRIT-04] Exposição Pública Desnecessária das Portas do Banco e do Backend em Produção
- **Localização:** [`docker-compose.prod.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.prod.yml#L10-L36)
- **Causa Raiz:** O compose de produção publica `5432:5432` e `8000:8000` no host.
- **Impacto / Risco:** O banco PostgreSQL fica sujeito a ataques de força bruta diretamente pela rede externa. A API FastAPI pode ser acessada diretamente contornando o Nginx (anulando regras de proxy, rate limit e headers de segurança).
- **Ação:** Remover as seções `ports` dos serviços `postgres` e `backend` no `docker-compose.prod.yml`, mantendo-os acessíveis apenas internamente via `patrimonio_net`.

#### [DEV-CRIT-05] Violação Constitucional: Ausência de Validação de Pull Requests no Pipeline de CI
- **Localização:** [`.github/workflows/ci.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.github/workflows/ci.yml#L3-L8)
- **Causa Raiz:** O bloco `on` possui apenas `push: branches: [main, develop, master]`.
- **Impacto / Risco:** Descumpre o Artigo 5 da Constituição do Projeto. Código com bugs, falhas de cobertura ou regressões pode ser mesclado em `main` via PR sem disparar a suíte de testes.
- **Ação:** Adicionar `pull_request: branches: [main, develop]` no workflow de CI.

---

### 🟠 Severidade Alta [ALTO]

#### [DEV-ALTO-01] Falso Multi-Stage no Backend e Dependências de Desenvolvimento na Imagem de Produção
- **Localização:** [`Dockerfile`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/Dockerfile#L46-L53)
- **Causa Raiz:** O target `production` herda diretamente de `base`, mantendo `gcc`, `libpq-dev`, `uv` e dependências de teste instaladas via `uv sync` sem a flag `--no-dev`.
- **Impacto / Risco:** Imagem com tamanho inflado (+300MB), superfície de ataque desnecessária com compiladores em runtime e violação da regra **RN-DK-05**.
- **Ação:** Refatorar para um builder stage isolado que gera o ambiente virtual com `uv sync --frozen --no-dev --no-cache`, copiando apenas o `.venv` gerado para o estágio final enxuto.

#### [DEV-ALTO-02] Nginx com Bloqueio de Upload (1MB) e Ausência de Roteamento para `/health`
- **Localização:** [`frontend/nginx.conf`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/nginx.conf) e [`src/main.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/src/main.py#L36-L39)
- **Causa Raiz:** Falta diretiva `client_max_body_size` e falta bloco `location /health` (o Nginx apenas redireciona `/api/`).
- **Impacto / Risco:** Importações de planilhas de patrimônio com mais de 1MB falham com erro `413 Request Entity Too Large`. Monitoramentos de saúde de load balancers externos recebem status 200 do `index.html` estático do React mesmo se o backend estiver inoperante.
- **Ação:** Adicionar `client_max_body_size 50M;` e `location /health { proxy_pass http://backend:8000/health; }` no Nginx.

#### [DEV-ALTO-03] Race Condition na Execução de Migrações do Banco via `entrypoint.sh`
- **Localização:** [`entrypoint.sh`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/entrypoint.sh#L35-L36)
- **Causa Raiz:** Todo container de backend executa `alembic upgrade head` no boot.
- **Impacto / Risco:** Ao escalar o backend horizontalmente (2 ou mais instâncias), réplicas concorrentes disputam locks DDL no PostgreSQL, causando falhas de inicialização ou corrupção de schema.
- **Ação:** Controlar a execução da migração por variável de ambiente (`RUN_MIGRATIONS=true`) ou criar um serviço efêmero de migração no Compose de produção.

#### [DEV-ALTO-04] Ausência de Quality Gate para Cobertura de 100% no CI
- **Localização:** [`.github/workflows/ci.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.github/workflows/ci.yml#L58) e [`pyproject.toml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/pyproject.toml#L33)
- **Causa Raiz:** O pytest roda sem a flag `--cov-fail-under=100`.
- **Impacto / Risco:** Falta de bloqueio automático para garantir a regra constitucional de 100% de cobertura de código executável.
- **Ação:** Adicionar `--cov-fail-under=100` no CI e na configuração do Pytest.

#### [DEV-ALTO-05] Falta de Validação de Build do Frontend e Imagens Docker no CI
- **Localização:** [`.github/workflows/ci.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.github/workflows/ci.yml)
- **Causa Raiz:** O CI executa apenas testes e checagem de tipos, mas não roda `npm run build` nem valida a compilação dos Dockerfiles.
- **Impacto / Risco:** Quebras de empacotamento no Vite ou falhas em instruções de Dockerfile passam batidas pelo pipeline e quebram deploys em produção.
- **Ação:** Incluir step `npm run build` no job de frontend e um job de validação de build Docker (`docker build`).

#### [DEV-ALTO-06] Fallback Silencioso para Chave Criptográfica Fraca em Produção
- **Localização:** [`docker-compose.prod.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.prod.yml#L32) e [`src/core/config.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/src/core/config.py#L9)
- **Causa Raiz:** Valor padrão hardcoded `${SECRET_KEY:-super-secret-key-change-in-production-1234567890}`.
- **Impacto / Risco:** Assinatura insegura de tokens de autenticação caso a variável seja omitida no ambiente.
- **Ação:** Tornar o parâmetro estritamente obrigatório com `${SECRET_KEY:?SECRET_KEY obrigatoria}` no Compose.

#### [DEV-ALTO-07] Ausência de Healthchecks nos Serviços e Dependência Fraca no Compose
- **Localização:** [`docker-compose.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.yml#L43-L68) e [`docker-compose.prod.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.prod.yml#L52-L54)
- **Causa Raiz:** O backend não possui healthcheck configurado, e o frontend possui `depends_on: - backend` sem `condition: service_healthy`.
- **Impacto / Risco:** O frontend inicia antes da API estar pronta para responder, gerando falhas de conexão imediatas para usuários no boot.
- **Ação:** Adicionar healthcheck HTTP no backend e aplicar `condition: service_healthy` nas dependências.

---

### 🟡 Severidade Média [MÉDIO]

#### [DEV-MED-01] Quebra de Execução por Terminações de Linha CRLF e Falta de `.gitattributes`
- **Localização:** `.gitattributes` (ausente) e [`entrypoint.sh`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/entrypoint.sh)
- **Causa Raiz:** O script `entrypoint.sh` possui quebras de linha no padrão Windows (`\r\n`), que geram erros no `/bin/sh` do Linux.
- **Ação:** Criar `.gitattributes` forçando `eol=lf` em scripts `.sh` e normalizar o arquivo.

#### [DEV-MED-02] Uso de Tags Mutáveis (`:latest` e flutuantes) e Falta de Determinismo
- **Localização:** [`Dockerfile`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/Dockerfile), [`frontend/Dockerfile`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/Dockerfile)
- **Causa Raiz:** Uso de `uv:latest`, `python:3.13-slim`, `node:20-alpine`, `nginx:alpine` e uso de `npm install` no stage de dev do frontend.
- **Ação:** Fixar versões imutáveis (`python:3.13-slim-bookworm`, `node:20.18-alpine3.20`, `nginx:1.27-alpine`, `uv:0.6.5`) e substituir `npm install` por `npm ci`.

#### [DEV-MED-03] Ausência de Gzip, Cache de Assets e Headers de Segurança no Nginx
- **Localização:** [`frontend/nginx.conf`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/nginx.conf)
- **Causa Raiz:** O Nginx não possui configurações de otimização de banda nem hardening HTTP.
- **Ação:** Habilitar gzip, cache imutável para a pasta `/assets/` e headers `X-Content-Type-Options`, `X-Frame-Options` e `Referrer-Policy`.

#### [DEV-MED-04] Ausência de Concorrência (`concurrency`) e Permissões Explícitas (`permissions`) no CI
- **Localização:** [`.github/workflows/ci.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.github/workflows/ci.yml)
- **Causa Raiz:** Falta diretiva `concurrency` e `permissions: contents: read`.
- **Ação:** Configurar cancelamento automático de execuções concorrentes redundantes e privilégio mínimo no workflow.

#### [DEV-MED-05] Script `lint` Quebrado no Frontend e Falta de Linter no Backend
- **Localização:** [`frontend/package.json`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/package.json#L9) e [`.github/workflows/ci.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.github/workflows/ci.yml)
- **Causa Raiz:** Script invoca `eslint`, mas o pacote não está instalado nas dependências. Backend não possui Ruff configurado.
- **Ação:** Configurar ferramentas oficiais de linting e formatador em ambos os projetos e integrar ao pipeline.

#### [DEV-MED-06] Falta de Limites de Recursos e Rotação de Logs no Compose
- **Localização:** [`docker-compose.prod.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.prod.yml)
- **Causa Raiz:** Nenhum serviço declara cotas de CPU/Memória ou política de log driver.
- **Ação:** Configurar `deploy.resources.limits` e rotação de logs (`max-size: 10m`, `max-file: 3`).

---

### 🟢 Severidade Baixa [BAIXO]

#### [DEV-BAIX-01] Sincronização Não-Frozen de Dependências no CI do Backend
- **Localização:** [`.github/workflows/ci.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.github/workflows/ci.yml#L50)
- **Causa Raiz:** O job roda `uv sync --all-extras` sem a flag `--frozen`.
- **Ação:** Adicionar `--frozen` para garantir reprodutibilidade estrita.

#### [DEV-BAIX-02] Especificações (`spec/`) Sendo Copiadas no Dockerfile de Backend
- **Localização:** [`Dockerfile`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/Dockerfile#L40)
- **Causa Raiz:** `COPY spec/ /app/spec/` presente no build de produção.
- **Ação:** Remover instrução, pois arquivos de especificação não possuem uso em tempo de execução.

---

## 4. Plano de Execução Priorizado (Roadmap de DevOps)

```mermaid
flowchart TD
    subgraph Fase 1 - Quick Wins e Segurança Crítica
        F1A["Desindexar PATRIMÔNIO CTM.xlsx e atualizar .dockerignore"]
        F1B["Criar .gitattributes e converter CRLF para LF"]
        F1C["Fechar portas do Postgres e Backend no Compose Prod"]
        F1D["Proteger seed no entrypoint.sh (RUN_SEED=false)"]
        F1E["Adicionar pull_request e --cov-fail-under no CI"]
    end

    subgraph Fase 2 - Hardening de Nginx e Orquestração
        F2A["Ajustar Nginx: upload 50M, rota /health, gzip e headers"]
        F2B["Healthchecks no Backend e Frontend com depends_on estrito"]
        F2C["Limites de recursos e rotação de logs no Compose Prod"]
        F2D["Tornar SECRET_KEY estritamente obrigatória"]
    end

    subgraph Fase 3 - Refatoração de Dockerfiles (Multi-stage e Non-Root)
        F3A["Multi-stage real no Backend (builder limpo e runtime sem gcc/uv)"]
        F3B["Configurar usuário não-privilegiado (appuser) no Backend"]
        F3C["Migrar Frontend Prod para nginx-unprivileged"]
        F3D["Pinagem determinística de tags de imagens base"]
    end

    subgraph Fase 4 - Pipeline e Quality Gates Avançados
        F4A["Step de npm run build no Frontend CI"]
        F4B["Job de validação de build Docker no CI"]
        F4C["Configuração de Concurrency e Least Privilege no CI"]
        F4D["Configuração de Linter (Ruff no Backend / ESLint no Frontend)"]
    end

    F1A --> F2A
    F1C --> F2B
    F1D --> F3A
    F2A --> F3C
    F2B --> F4A
    F3A --> F4B
```

---

## 5. Checklist Detalhado das Ações

### 🔹 Fase 1: Quick Wins e Segurança Crítica (Execução Imediata)
- [ ] **[Segurança]** Executar `git rm --cached "PATRIMÔNIO CTM.xlsx"`.
- [ ] **[Higiene]** Atualizar [`.dockerignore`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.dockerignore) adicionando `*.xlsx`, `*.xls`, `*.csv`, `spec/`, `.github/`, `README.md`, `tests/` e `docker-compose*.yml`.
- [ ] **[Higiene]** Atualizar [`frontend/.dockerignore`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/.dockerignore) adicionando `.env*`, `*.test.tsx`, `*.spec.tsx` e `tests/`.
- [ ] **[Compatibilidade]** Criar `.gitattributes` com `* text=auto` e `*.sh text eol=lf`. Normalizar quebras de linha do [`entrypoint.sh`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/entrypoint.sh).
- [ ] **[DevSecOps]** No [`docker-compose.prod.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.prod.yml), remover os blocos `ports:` dos serviços `postgres` (5432) e `backend` (8000).
- [ ] **[DevSecOps]** No [`entrypoint.sh`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/entrypoint.sh), condicionar o seed com flag `if [ "$RUN_SEED" = "true" ]; then python -m src.infrastructure.seed; fi`.
- [ ] **[CI/CD]** No [`.github/workflows/ci.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.github/workflows/ci.yml), adicionar `pull_request: branches: [main, develop]`.
- [ ] **[CI/CD]** No [`.github/workflows/ci.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.github/workflows/ci.yml), adicionar `--cov-fail-under=100` e a flag `--frozen` no `uv sync`.

### 🔹 Fase 2: Hardening de Nginx e Orquestração Compose
- [ ] **[Nginx]** No [`frontend/nginx.conf`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/nginx.conf):
  - Adicionar `client_max_body_size 50M;`.
  - Adicionar bloco `location /health { proxy_pass http://backend:8000/health; }`.
  - Ativar `gzip on;` e especificar MIME types.
  - Adicionar cabeçalhos de segurança (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`) e `server_tokens off;`.
  - Configurar cache imutável para `/assets/`.
- [ ] **[Compose]** Adicionar healthcheck com `curl` no serviço `backend` em `docker-compose.yml` e `docker-compose.prod.yml`.
- [ ] **[Compose]** Configurar `depends_on: backend: { condition: service_healthy }` no serviço `frontend`.
- [ ] **[Compose]** No [`docker-compose.prod.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/docker-compose.prod.yml), definir `SECRET_KEY: ${SECRET_KEY:?SECRET_KEY obrigatoria}` e adicionar limites de recursos e rotação de logs em todos os serviços.

### 🔹 Fase 3: Refatoração de Dockerfiles (Multi-stage e Non-Root)
- [ ] **[Docker]** Refatorar [`Dockerfile`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/Dockerfile) do backend:
  - Estágio `builder`: instalar dependências via `uv sync --frozen --no-dev --no-cache`.
  - Estágio `production`: base `python:3.13-slim-bookworm`, sem compiladores, copiando `.venv`.
  - Criar e definir `USER appuser` (UID 10001).
  - Remover `COPY spec/ /app/spec/`.
  - Fixar versão do binário `uv` (`ghcr.io/astral-sh/uv:0.6.5`).
- [ ] **[Docker]** Refatorar [`frontend/Dockerfile`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/Dockerfile):
  - Usar `npm ci` no estágio de desenvolvimento.
  - Pinagem de imagens base (`node:20.18-alpine3.20` e `nginxinc/nginx-unprivileged:alpine`).
  - Ajustar porta exposta para `8080` (não-privilegiada).

### 🔹 Fase 4: Pipeline de CI/CD e Quality Gates Avançados
- [ ] **[CI/CD]** Adicionar controle de concorrência (`concurrency`) e permissões (`permissions: contents: read`) no [`.github/workflows/ci.yml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/.github/workflows/ci.yml).
- [ ] **[CI/CD]** Adicionar step `npm run build` no job `frontend-tests`.
- [ ] **[CI/CD]** Adicionar job `docker-build-check` validando a construção das imagens de backend e frontend no CI.
- [ ] **[Qualidade]** Configurar ESLint funcional no frontend e Ruff no backend, integrando ambos como gates obrigatórios no workflow.

---

## 6. Critérios de Aceite (Quality Gates) para o Release de Infraestrutura

1. **Vazamento Zero de Dados:** Planilhas e dados corporativos não são rastreados no Git nem incluídos em contextos Docker.
2. **Ambiente de Produção Isolado:** Nenhuma porta de banco de dados ou backend exposta diretamente ao host em produção (apenas o proxy reverso Nginx publica portas).
3. **Imagens Seguras e Não-Root:** Todos os containers rodam com usuários sem privilégios e sem ferramentas de compilação em produção.
4. **Resiliência do Nginx:** Upload de arquivos de até 50MB permitido sem erro 413, e rota `/health` reportando o estado real da API.
5. **Aderência Constitucional Estrita:** Pipeline de CI executando automaticamente em Pull Requests (`develop` -> `main`) e falhando se a cobertura for inferior a 100% (`--cov-fail-under=100`).
