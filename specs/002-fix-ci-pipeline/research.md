# Phase 0 Research: Correção e Estabilização do Pipeline de Integração Contínua (CI)

**Feature**: `002-fix-ci-pipeline`  
**Date**: 2026-10-28  
**Status**: Completed  

---

## 1. Pesquisa & Decisões Arquiteturais

### 1.1. Healthcheck do Container de Serviço PostgreSQL no GitHub Actions
- **Contexto**: No workflow `.github/workflows/ci.yml`, o container de serviço `postgres:16-alpine` estava configurado com:
  ```yaml
  options: >-
    --health-cmd pg_isready
    --health-interval 10s
    --health-timeout 5s
    --health-retries 5
  ```
  Ao executar `pg_isready` sem argumentos, o comando tenta se conectar usando o usuário ativo no shell do container (que é `root`). Como a imagem `postgres:16-alpine` cria exclusivamente o usuário definido em `POSTGRES_USER` (`postgres`), o daemon do PostgreSQL rejeita a conexão com `FATAL: role "root" does not exist`. Consequentemente, o healthcheck falha repetidamente, fazendo com que o GitHub Actions interrompa a inicialização ou falhe o job de backend antes ou durante a execução dos steps.
- **Decisão**: Configurar explicitamente o usuário e o banco de dados no comando de verificação:
  ```yaml
  options: >-
    --health-cmd "pg_isready -U postgres -d test_patrimonio_db"
    --health-interval 10s
    --health-timeout 5s
    --health-retries 5
  ```
- **Rationale**: Ao declarar `-U postgres -d test_patrimonio_db`, o utilitário `pg_isready` consulta diretamente a role existente e o banco já inicializado, garantindo que o status `healthy` seja alcançado de forma imediata e determinística.
- **Alternativas Consideradas**:
  - `sleep 5` em um step: Rejeitado por ser frágil, não garantir que a porta está pronta e violar as melhores práticas do GitHub Actions.
  - Omitir healthcheck: Rejeitado por expor o workflow a condições de corrida (*race conditions*) em que o Alembic tenta se conectar antes do PostgreSQL aceitar conexões.

---

### 1.2. Conformidade de Formatação com Ruff (`ruff format --check src/`)
- **Contexto**: A execução `39992303153` no GitHub Actions falhou no step `Check Backend Formatting (Ruff)` com a mensagem:
  ```text
  1 file would be reformatted, 32 files already formatted
  ##[error]Process completed with exit code 1.
  ```
  O arquivo com discrepância é [`src/infrastructure/seed.py`](file:///C:/Users/70486375447/orca/workspaces/Gerenciador-de-patrimonio/CI-Fix/src/infrastructure/seed.py), introduzido/expandido no commit anterior com espaçamento e indentação de tuplas que divergem da regra padrão do formatador do Ruff.
- **Decisão**: Executar a formatação oficial do Ruff (`uv run ruff format src/infrastructure/seed.py` ou padronização equivalente do arquivo) para que 100% dos arquivos Python em `src/` passem na checagem `--check` sem alterações pendentes.
- **Rationale**: Atende rigorosamente ao Quality Gate do pipeline de CI e ao princípio constitucional VI de qualidade estrita.
- **Alternativas Consideradas**:
  - Adicionar `--exclude src/infrastructure/seed.py` no comando do CI: Rejeitado para preservar a consistência e integridade do código do projeto.
  - Remover o step `Check Backend Formatting (Ruff)`: Rejeitado porque a verificação de estilo garante padronização e evita diffs ruidosos em pull requests.

---

### 1.3. Ampliação de Gatilhos e Suporte a Acionamento Manual (`workflow_dispatch`)
- **Contexto**: O CI atualmente monitora apenas `push` em `main`, `develop`, `master` e `pull_request` em `main`, `develop`. Quando um desenvolvedor trabalha em uma branch de correção (ex: `JoseGildenilson/CI-Fix`) ou deseja re-executar a validação sem alterar o código, não há mecanismo para acionar o pipeline sem abrir previamente um PR ou fazer push direto para develop.
- **Decisão**: 
  1. Adicionar o gatilho `workflow_dispatch:` ao workflow do GitHub Actions, permitindo execução sob demanda diretamente pelo GitHub CLI (`gh workflow run`) ou interface web.
  2. Manter os gatilhos em `push` para `main`, `develop`, `master` e `pull_request` para `main` e `develop`.
- **Rationale**: Proporciona autonomia e facilidade de depuração imediata para os desenvolvedores em qualquer branch ativa sem sobrecarregar a infraestrutura com builds desnecessários em branches de rascunho (*draft*).
- **Alternativas Consideradas**:
  - `push: branches: ['**']`: Rejeitado por consumir quota excessiva do GitHub Actions a cada commit intermediário de desenvolvimento local.

---

### 1.4. Otimização e Estabilidade do Job de Frontend
- **Contexto**: O job `frontend-tests` executa `npm ci`, `npx tsc --noEmit`, `npm run lint`, `npm run build` e `npm test -- --run`. Avisos sobre ciclo de vida do runner Node.js no GitHub Actions foram observados nos logs.
- **Decisão**: Manter o setup com `actions/setup-node@v4` com cache mapeado em `frontend/package-lock.json`, garantindo que a versão do Node.js utilizada seja suportada e não cause falhas na compilação do Vite e testes Vitest.
- **Rationale**: Assegura estabilidade contínua sem quebras de dependências npm ou de tipos TypeScript.
