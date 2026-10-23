# Especificação: Documentação do Projeto (README.md)

## 1. Visão Geral

Esta especificação define os requisitos de documentação do projeto **Comunica - Gestão de Patrimônio e Suporte**. O objetivo é fornecer um guia completo, claro e objetivo no arquivo `README.md` da raiz do repositório, permitindo que novos desenvolvedores e avaliadores compreendam a arquitetura, executem a aplicação (via Docker ou ambiente local), realizem autenticação com os usuários de teste, executem a suíte de testes automatizados e compreendam o pipeline de CI/CD.

---

## 2. Requisitos de Documentação

### 2.1 Visão Geral e Badges
- **RN-DOC-01:** O `README.md` deve conter título claro, descrição sucinta do problema e badges de status (Stack, CI, Testes 100%, Python 3.13, React, Docker).

### 2.2 Stack Tecnológica e Arquitetura
- **RN-DOC-02:** Apresentar a stack completa do backend (Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic, uv, openpyxl, PostgreSQL) e frontend (React, TypeScript, Vite, Tailwind CSS, Lucide React).

### 2.3 Execução com Docker Compose (Recomendado)
- **RN-DOC-03:** Documentar comandos para subir o ambiente de desenvolvimento (`docker compose up --build`) e o ambiente de produção com Nginx (`docker compose -f docker-compose.prod.yml up --build -d`).
- **RN-DOC-04:** Listar as portas padrão mapeadas (Frontend Dev: 5173 / Prod: 3000, Backend: 8000, PostgreSQL: 5432).

### 2.4 Execução Local (Sem Docker)
- **RN-DOC-05:** Documentar passo a passo para configuração e execução do backend via `uv` e frontend via `npm`.
- **RN-DOC-06:** Documentar a execução de migrações (`alembic upgrade head`) e popular dados iniciais (`python -m src.infrastructure.seed`).

### 2.5 Credenciais Padrão de Acesso
- **RN-DOC-07:** Informar as contas e senhas padrão de teste criadas pelo seed:
  - **Técnico:** `tecnico@empresa.com` / `senha123` (Gestão total, tags, importação, exportação).
  - **Colaborador:** `colaborador@empresa.com` / `senha123` (Consulta e solicitações).

### 2.6 Testes Automatizados e Cobertura
- **RN-DOC-08:** Detalhar os comandos para execução dos testes de backend com Pytest e cobertura de 100% (`pytest --cov=src --cov-branch`) e frontend com Vitest (`npm test -- --run`) e checagem de tipos (`npx tsc --noEmit`).

### 2.7 Pipeline de CI/CD e Metodologia SDD
- **RN-DOC-09:** Explicar o funcionamento do GitHub Actions e a aderência ao **Spec-Driven Development (SDD)**.

---

## 3. Cenários de Aceitação (BDD)

### Cenário 1: Novo desenvolvedor inicia o projeto via Docker
- **Dado** que um desenvolvedor clona o repositório
- **Quando** ele seguir as instruções do `README.md` e executar `docker compose up --build`
- **Então** os serviços de banco, backend e frontend devem iniciar e estar acessíveis nos navegadores nas portas indicadas.

### Cenário 2: Execução de testes a partir da documentação
- **Dado** que um desenvolvedor deseja validar a qualidade do código
- **Quando** ele executar os comandos descritos na seção de testes do `README.md`
- **Então** as suítes de testes do backend e frontend devem rodar e passar com sucesso.
