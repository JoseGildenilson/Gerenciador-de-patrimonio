# Especificação: Pipeline de Integração Contínua (CI) com GitHub Actions

## 1. Visão Geral

Esta especificação define o pipeline automatizado de **Integração Contínua (CI)** utilizando GitHub Actions para o projeto de **Gestão de Patrimônio e Suporte**. O objetivo é garantir a integridade, compatibilidade, cobertura de testes (100%) e validação das migrações do banco de dados em cada push nas branches protegidas e ativas (`main`, `develop`, `master`), assegurando conformidade com a Constituição do Projeto.

---

## 2. Regras de Negócio e Requisitos de Infraestrutura

### 2.1 Gatilhos e Branches
- **RN-CI-01 (Gatilhos de Push):** O workflow de CI deve ser disparado automaticamente a cada evento de `push` direcionado para as branches `main`, `develop` e `master`.

### 2.2 Estrutura de Jobs Paralelos
- **RN-CI-02 (Paralelismo e Isolamento):** O workflow deve ser estruturado em **dois jobs paralelos e independentes** (`backend-tests` e `frontend-tests`), permitindo que as validações de backend e frontend sejam executadas concorrentemente com isolamento de falhas e feedback rápido.

### 2.3 Job de Backend (`backend-tests`)
- **RN-CI-03 (Ambiente Python 3.13 e Gerenciamento com uv):** O job deve utilizar o runner `ubuntu-latest`, Python versão `3.13` e a action oficial `astral-sh/setup-uv` com cache habilitado para instalação e sincronização ultrarrápida de dependências.
- **RN-CI-04 (Serviço de Banco de Dados PostgreSQL 16):** Em conformidade com a Constituição, o job de backend deve instanciar um serviço de PostgreSQL 16 (`postgres:16-alpine`) com *healthcheck* ativo (`pg_isready`).
- **RN-CI-05 (Validação de Migrations):** O job deve executar `alembic upgrade head` contra a instância PostgreSQL antes dos testes para garantir que todas as migrações estão íntegras e aplicáveis sem erros.
- **RN-CI-06 (Execução de Testes e Cobertura Pytest):** O job deve executar a suíte completa de testes automatizados com relatório de cobertura de linhas e branches (`uv run pytest --cov=src --cov-branch --cov-report=term-missing`).

### 2.4 Job de Frontend (`frontend-tests`)
- **RN-CI-07 (Ambiente Node.js 20 e Cache NPM):** O job deve utilizar o runner `ubuntu-latest`, Node.js versão `20` e cache nativo do `actions/setup-node` mapeado para o diretório `frontend/package-lock.json`.
- **RN-CI-08 (Instalação Limpa de Dependências):** O job deve utilizar `npm ci` dentro do diretório `frontend` para garantir reprodutibilidade estrita.
- **RN-CI-09 (Checagem de Tipagem Estática):** O job deve executar a validação estrita do compilador TypeScript (`npx tsc --noEmit`), falhando caso haja qualquer erro de tipagem.
- **RN-CI-10 (Execução de Testes com Vitest):** O job deve executar a suíte completa de testes unitários e de componentes (`npm test -- --run`).

---

## 3. Cenários de Aceitação (BDD)

### Cenário 1: Disparo automático em push para a branch develop
- **Dado** que um desenvolvedor envie novos commits via push para a branch `develop`
- **Quando** o GitHub receber os commits
- **Então** o workflow de CI deve iniciar automaticamente
- **E** executar os jobs `backend-tests` e `frontend-tests` em paralelo.

### Cenário 2: Execução e validação completa do Job de Backend
- **Dado** que o job `backend-tests` seja iniciado
- **Quando** o container de serviço PostgreSQL estiver saudável
- **Então** as migrações do Alembic devem ser aplicadas com sucesso
- **E** todos os testes do Pytest devem passar com sucesso sem falhas de cobertura.

### Cenário 3: Execução e validação completa do Job de Frontend
- **Dado** que o job `frontend-tests` seja iniciado
- **Quando** as dependências forem instaladas via `npm ci`
- **Então** a checagem de tipos (`tsc --noEmit`) deve passar sem erros
- **E** todos os testes do Vitest devem ser executados e aprovados.

### Cenário 4: Bloqueio imediato em caso de falha de teste ou quebra de tipos
- **Dado** que um commit introduza uma regressão ou erro de tipagem TypeScript no frontend
- **Quando** o job `frontend-tests` for executado
- **Então** o job deve falhar imediatamente, sinalizando o status com falha no commit do GitHub.
