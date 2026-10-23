# Especificação: Ambiente de Containers com Docker Compose (PostgreSQL, Backend e Frontend)

## 1. Visão Geral

Esta especificação define a arquitetura, configuração e ciclo de vida dos containers Docker e da orquestração via Docker Compose para a aplicação de **Gestão de Patrimônio e Suporte**. O objetivo é padronizar os ambientes de desenvolvimento e produção, garantindo isolamento de dependências, persistência dos dados no PostgreSQL, execução automatizada e idempotente de migrações e seeds, além de suportar tanto o fluxo de desenvolvimento com *live reload* quanto builds otimizados para produção.

---

## 2. Topologia e Serviços dos Containers

### 2.1 Serviço de Banco de Dados (`postgres`)
- **Imagem:** `postgres:16-alpine`.
- **Porta Exposta:** `5432:5432` (mapeada para acesso local e depuração).
- **Volume de Dados:** Volume nomeado `postgres_data` montado em `/var/lib/postgresql/data` para persistência permanente.
- **Variáveis de Ambiente:**
  - `POSTGRES_USER`: Usuário do banco (padrão: `postgres`).
  - `POSTGRES_PASSWORD`: Senha do banco (padrão: `postgres`).
  - `POSTGRES_DB`: Nome da base de dados (padrão: `internal_management`).
- **Healthcheck:** Utiliza `pg_isready -U postgres -d internal_management` com intervalo de 5s, timeout de 3s e 5 tentativas para garantir que o serviço esteja pronto antes do início do backend.

### 2.2 Serviço de Backend (`backend`)
- **Base da Imagem:** `python:3.13-slim`.
- **Gerenciador de Pacotes:** `uv` para instalação e resolução ultrarrápida de dependências.
- **Driver de Banco:** `psycopg2-binary>=2.9.9` adicionado ao `pyproject.toml`.
- **Porta Exposta:** `8000:8000`.
- **Dependência de Serviço:** `depends_on` apontando para `postgres` com condição `condition: service_healthy`.
- **Entrypoint Automatizado (`entrypoint.sh`):**
  1. Aguarda ativamente a conectividade com o PostgreSQL.
  2. Executa `alembic upgrade head` para sincronizar o schema do banco com as últimas migrações.
  3. Executa a criação de tags padrão e usuário inicial via script de seed de forma idempotente.
  4. Inicia o servidor ASGI Uvicorn (`uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload` em desenvolvimento).
- **Volumes em Desenvolvimento:** Montagem do diretório `./src`, `./tests`, `./alembic` e `./spec` para suportar recarregamento a quente (*hot-reload*).

### 2.3 Serviço de Frontend (`frontend`)
- **Target de Desenvolvimento (`development`):**
  - Base: `node:20-alpine`.
  - Servidor: Vite Dev Server ouvindo em `0.0.0.0:5173`.
  - Porta: `5173:5173`.
  - Volumes: Montagem de `./frontend/src`, `./frontend/public`, `./frontend/index.html` e exclusão de `/app/node_modules`.
  - Variáveis: `VITE_API_URL=/api/v1` com proxy reverso configurado no `vite.config.ts` apontando para `http://backend:8000`.
- **Target de Produção (`production`):**
  - Estágio 1 (Builder): Build com `npm run build` gerando bundle estático em `/app/dist`.
  - Estágio 2 (Runner): Servidor web `nginx:alpine` servindo os arquivos estáticos na porta `80` (mapeada para `3000`), com regras de fallback SPA (`try_files $uri $uri/ /index.html`) e proxy reverso para `/api/` direcionado ao container do backend.

### 2.4 Rede Compartilhada (`internal-net`)
- Uma rede bridge customizada (`internal-net`) que permite a comunicação direta por nome de host (`postgres`, `backend`, `frontend`) entre todos os serviços.

---

## 3. Regras de Negócio e Infraestrutura

- **RN-DK-01 (Idempotência da Inicialização):** A inicialização automática de migrações (`alembic upgrade head`) e seeds não deve gerar erros ou duplicidades caso o banco de dados já possua as tabelas e dados pré-existentes.
- **RN-DK-02 (Compatibilidade Multi-Driver):** A aplicação deve suportar conexão tanto com SQLite (para testes unitários locais ultrarrápidos em memória ou arquivo) quanto com PostgreSQL (para ambiente Docker e produção), chaveando automaticamente através da variável `DATABASE_URL`.
- **RN-DK-03 (Isolamento de Secrets):** Nenhuma credencial sensível de produção deve estar gravada estaticamente nos Dockerfiles ou commits do repositório. Um arquivo `.env.example` deve documentar todas as variáveis obrigatórias.
- **RN-DK-04 (Hot-Reload em Desenvolvimento):** Alterações no código Python em `src/` ou no código TypeScript em `frontend/src/` devem ser refletidas instantaneamente nos containers de desenvolvimento sem necessidade de rebuild de imagem.
- **RN-DK-05 (Build Otimizado Multi-Stage):** Os Dockerfiles devem utilizar múltiplos estágios para manter as imagens de produção limpas, sem dependências de compilação ou ferramentas desnecessárias.

---

## 4. Cenários de Aceitação (BDD)

### Cenário 1: Inicialização do ambiente de desenvolvimento com Docker Compose
- **Dado** que o desenvolvedor execute `docker compose up --build`
- **Quando** todos os containers forem iniciados
- **Então** o container `postgres` deve passar no healthcheck
- **E** o container `backend` deve aplicar as migrações do Alembic automaticamente
- **E** o servidor FastAPI deve ficar acessível em `http://localhost:8000/health` retornando status `ok`
- **E** a interface React deve ficar acessível em `http://localhost:5173`.

### Cenário 2: Persistência de dados após reinicialização do container PostgreSQL
- **Dado** que novos equipamentos e usuários tenham sido criados no sistema rodando em container
- **Quando** os containers forem parados com `docker compose down` e iniciados novamente com `docker compose up`
- **Então** todos os dados cadastrados no PostgreSQL devem permanecer íntegros através do volume `postgres_data`.

### Cenário 3: Hot-Reload do Backend no Container
- **Dado** que o container do backend esteja em execução em modo de desenvolvimento
- **Quando** um arquivo de rota em `src/api/` for modificado no sistema de arquivos do host
- **Então** o Uvicorn dentro do container deve detectar a alteração e reiniciar automaticamente o processo.

### Cenário 4: Hot-Reload do Frontend no Container
- **Dado** que o container do frontend esteja em execução em modo de desenvolvimento
- **Quando** um componente em `frontend/src/` for modificado no sistema de arquivos do host
- **Então** o Vite deve realizar o Hot Module Replacement (HMR) instantaneamente no navegador.

### Cenário 5: Execução do ambiente de produção com Nginx (`docker-compose.prod.yml`)
- **Dado** que o comando `docker compose -f docker-compose.prod.yml up --build` seja executado
- **Quando** a aplicação for construída
- **Então** o frontend deve ser servido pelo Nginx na porta `3000`
- **E** as requisições para `/api/v1/*` devem ser roteadas transparentemente pelo Nginx para o container `backend:8000`.

---

## 5. Estrutura de Arquivos da Infraestrutura

```text
├── Dockerfile                  # Multi-stage Dockerfile do Backend (dev e prod)
├── entrypoint.sh               # Script de inicialização do Backend (wait-for-pg, migrate, seed, start)
├── docker-compose.yml          # Compose padrão para desenvolvimento (com hot-reload)
├── docker-compose.prod.yml     # Compose para produção (builds compilados e Nginx)
├── .dockerignore               # Arquivos ignorados no contexto de build do backend
├── .env.example                # Template de variáveis de ambiente
├── frontend/
│   ├── Dockerfile              # Multi-stage Dockerfile do Frontend (dev e prod)
│   ├── nginx.conf              # Configuração do Nginx (SPA fallback + proxy reverso)
│   └── .dockerignore           # Arquivos ignorados no contexto de build do frontend
```
