# Especificação: Padronização do .gitignore e Limpeza de Artefatos Versionados

## 1. Visão Geral

Esta especificação define as regras de exclusão de arquivos e diretórios versionados no Git para o projeto de **Gestão de Patrimônio e Suporte**. O objetivo é evitar que dependências baixadas (`node_modules/`, `.venv/`), artefatos de build (`dist/`, `build/`), relatórios de testes (`.coverage`, `.pytest_cache/`), arquivos de banco locais (`*.db`, `*.sqlite3`), planilhas de dados (`*.xlsx`, `*.xls`), segredos/variáveis de ambiente (`.env`) e arquivos de sistema/IDE poluam o histórico do repositório ou sobrecarreguem uploads para o GitHub.

---

## 2. Regras de Negócio e Requisitos

### 2.1 Desindexação de Dependências Previamente Versionadas
- **RN-IGN-01:** O diretório `frontend/node_modules/` deve ser removido do índice de rastreamento do Git (`git rm --cached`), preservando os arquivos intactos no sistema de arquivos local.

### 2.2 Escopo de Padrões Ignorados (.gitignore)
- **RN-IGN-02 (Python & Ambientes Virtuais):** Ignorar compilações de bytecode (`__pycache__/`, `*.py[cod]`, `*$py.class`), ambientes virtuais (`.venv/`, `venv/`, `env/`, `ENV/`), metadados de pacotes (`*.egg-info/`, `.eggs/`) e builds Python (`build/`, `dist/`).
- **RN-IGN-03 (Testes & Cobertura):** Ignorar caches do pytest (`.pytest_cache/`), arquivos de cobertura (`.coverage`, `.coverage.*`, `htmlcov/`, `coverage/`, `frontend/coverage/`) e relatórios XML/JSON.
- **RN-IGN-04 (Node.js & Frontend):** Ignorar diretórios de dependências (`node_modules/`, `frontend/node_modules/`), bundles de produção (`dist/`, `frontend/dist/`, `build/`, `frontend/build/`) e caches do bundler (`.vite/`, `.npm/`).
- **RN-IGN-05 (Segredos & Variáveis de Ambiente):** Ignorar arquivos com credenciais e chaves (`.env`, `.env.*`, `*.pem`, `*.key`), garantindo a preservação explícita do template de exemplo (`!.env.example`).
- **RN-IGN-06 (Bancos de Dados & Planilhas):** Ignorar bancos de dados locais (`*.db`, `*.sqlite`, `*.sqlite3`, `internal_management.db`) e planilhas de dados (`*.xlsx`, `*.xls`, `*.csv`).
- **RN-IGN-07 (Logs & Temporários):** Ignorar logs (`*.log`, `npm-debug.log*`, `yarn-debug.log*`, `yarn-error.log*`) e pastas temporárias (`tmp/`, `temp/`).
- **RN-IGN-08 (IDEs & Sistema Operacional):** Ignorar configurações de editores (`.vscode/`, `.idea/`, `*.swp`, `*.swo`) e metadados de SO (`.DS_Store`, `Thumbs.db`).

---

## 3. Cenários de Aceitação (BDD)

### Cenário 1: Desindexação de node_modules sem exclusão em disco
- **Dado** que `frontend/node_modules/` estava sendo rastreado pelo Git
- **Quando** a limpeza for executada com `git rm -r --cached frontend/node_modules`
- **Então** o Git deve marcar os arquivos como excluídos do controle de versão
- **E** a pasta `frontend/node_modules/` deve continuar existindo fisicamente no disco local.

### Cenário 2: Prevenção de versionamento de novos arquivos ignorados
- **Dado** que o arquivo `.gitignore` foi atualizado
- **Quando** um arquivo `.env`, `.coverage`, `novo_banco.db` ou `planilha.xlsx` for criado no workspace
- **Então** o comando `git status` não deve listar esses arquivos como não-rastreados (*untracked*).

### Cenário 3: Preservação de arquivos de template
- **Dado** o arquivo `.env.example`
- **Quando** verificado pelo Git
- **Então** ele deve continuar sendo rastreado normalmente como modelo de configuração.
