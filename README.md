# Comunica — Sistema de Gestão de Patrimônio e Suporte TI

[![CI Pipeline](https://github.com/JoseGildenilson/comunica-projeto/actions/workflows/ci.yml/badge.svg)](https://github.com/JoseGildenilson/comunica-projeto/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?style=flat&logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![Test Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen?style=flat)

---

## 📌 Visão Geral

O **Comunica** é uma plataforma corporativa completa desenvolvida para centralizar a gestão de equipamentos (computadores, monitores, periféricos e outros ativos de TI), rastrear histórico detalhado de manutenções e movimentações físicas, e gerenciar solicitações de suporte, substituindo controles informais e planilhas descentralizadas por um sistema robusto, rápido e seguro.

---

## 🚀 Funcionalidades Principais

- 🔐 **Autenticação & Segurança (RBAC):**
  - Autenticação via JWT (Access Token de curta duração + Refresh Token seguro).
  - Controle de Acesso Baseado em Perfis (**Técnico** e **Colaborador**).
  - Proteção contra força bruta (*Rate Limiting* por IP e e-mail).
- 🖥️ **Gestão Completa de Patrimônio:**
  - Cadastro, edição em lote e visualização unificada de equipamentos.
  - Tags dinâmicas por categoria (Tipos, Localizações e Situações) com gerenciador próprio.
  - Rastreamento cronológico de movimentações físicas (origem e destino).
  - Histórico completo de manutenções e intervenções técnicas.
- 🔍 **Filtros Avançados & Autocomplete:**
  - Busca global e filtros múltiplos estilo Google Sheets.
  - Sugestões em tempo real por *autocomplete* para Patrimônio, Nº de Série e Nº de Produto.
- 📥 **Importação em Lote (.xlsx e .csv):**
  - Upload de planilhas com normalização flexível de cabeçalhos.
  - Modo *dry-run* (pré-visualização com detecção de novos cadastros e atualizações/upsert).
  - Criação automática de tags inexistentes na importação.
- 📤 **Exportação em Planilha Excel Fiel ao Modelo:**
  - Download dinâmico de planilhas `.xlsx` respeitando os filtros ativos em tela.
  - Formatação visual idêntica ao modelo corporativo (cabeçalho ciano `#4DD0E1`, *freeze panes*, quebra de linha e manutenções cronológicas consolidadas).
- 📊 **Dashboard em Tempo Real:**
  - Métricas agregadas de equipamentos, manutenções recentes, equipamentos ociosos e tickets.

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologias |
|---|---|
| **Backend** | Python 3.13, FastAPI, SQLAlchemy 2.0 (ORM/Core), Alembic, Pydantic v2, uv, openpyxl, psycopg2 |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide React, Axios |
| **Banco de Dados** | PostgreSQL 16 (produção/dev) / SQLite in-memory (testes isolados) |
| **Infra & DevOps** | Docker, Docker Compose, Nginx, GitHub Actions CI |
| **Testes Automatizados** | Pytest (100% Cobertura de Branches), Vitest, Testing Library |

---

## ⚡ Como Executar

### Opção 1: Com Docker Compose (Recomendado)

Certifique-se de ter o [Docker](https://docs.docker.com/get-docker/) e o Docker Compose instalados.

#### 1. Modo de Desenvolvimento (Live Reload)
```bash
# Sobe todos os serviços (PostgreSQL, Backend FastAPI e Frontend Vite)
docker compose up --build
```
- **Frontend:** [http://localhost:5173](http://localhost:5173)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Swagger / OpenAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostgreSQL:** `localhost:5432`

#### 2. Modo de Produção (Otimizado com Nginx)
```bash
# Sobe a stack de produção em segundo plano
docker compose -f docker-compose.prod.yml up --build -d
```
- **Aplicação Web (Nginx):** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)

---

### Opção 2: Execução Local (Sem Docker)

#### Pré-requisitos
- Python 3.13+ e gerenciador [`uv`](https://github.com/astral-sh/uv)
- Node.js 20+ e `npm`
- PostgreSQL 16 em execução (ou SQLite para desenvolvimento rápido)

#### 1. Configuração do Backend
```bash
# 1. Clone o repositório
git clone git@github.com:JoseGildenilson/comunica-projeto.git
cd comunica-projeto

# 2. Crie e sincronize o ambiente virtual com uv
uv sync --all-extras

# 3. Configure as variáveis de ambiente (ou use os padrões)
cp .env.example .env

# 4. Aplique as migrações no banco de dados
uv run alembic upgrade head

# 5. Popule o banco com os dados e usuários iniciais (Seed)
uv run python -m src.infrastructure.seed

# 6. Inicie o servidor FastAPI
uv run uvicorn src.main:app --reload --port 8000
```

#### 2. Configuração do Frontend
```bash
# 1. Acesse o diretório frontend
cd frontend

# 2. Instale as dependências
npm ci

# 3. Inicie o servidor de desenvolvimento Vite
npm run dev
```
Acesse [http://localhost:5173](http://localhost:5173) no seu navegador.

---

## 🔑 Credenciais Padrão de Acesso

Ao rodar o script de seed ou iniciar via Docker, as seguintes contas estarão disponíveis:

| Perfil | E-mail | Senha | Permissões |
|---|---|---|---|
| **Técnico** (Admin) | `tecnico@empresa.com` | `senha123` | Acesso total, gerenciamento de tags, importação, exportação e manutenção de patrimônio |
| **Colaborador** | `colaborador@empresa.com` | `senha123` | Consulta ao inventário e abertura de chamados/tickets |

---

## 🧪 Testes Automatizados & Qualidade

Este projeto segue rigorosamente o princípio de **100% de cobertura de código** para regras de negócio e rotas.

```bash
# Execução da suíte de testes de Backend com verificação de cobertura (Pytest)
PYTHONPATH=. uv run pytest --cov=src --cov-branch --cov-report=term-missing

# Checagem estática de tipagem no Frontend (TypeScript)
cd frontend && npx tsc --noEmit

# Execução dos testes de Frontend (Vitest)
cd frontend && npm test -- --run
```

---

## 🔄 Integração Contínua (CI/CD)

O repositório conta com pipeline automatizado no **GitHub Actions** configurado em [`.github/workflows/ci.yml`](.github/workflows/ci.yml) que é executado a cada push nas branches `main`, `develop` e `master`:
- **Job `backend-tests`:** Executa em container Ubuntu com serviço PostgreSQL 16, valida todas as migrações com Alembic e roda a suíte Pytest com meta de 100% de cobertura.
- **Job `frontend-tests`:** Executa a checagem de tipos estáticos TypeScript (`tsc --noEmit`) e a suíte completa de testes no Vitest.

---

## 📐 Metodologia — Spec-Driven Development (SDD)

O projeto adota o **Spec-Driven Development (Spec-Anchored)**, onde nenhuma funcionalidade é implementada sem uma especificação prévia formal e um plano de tarefas correspondente em `.spec/features/`:

```
spec/
├── constituicao.md                   # Princípios e regras do projeto
├── vision.md                         # Visão geral do produto
└── features/
    ├── autenticacao/                 # Login, JWT e Rate Limit
    ├── equipamentos/                 # Gestão e autocomplete de patrimônio
    ├── importacao-planilha/          # Upload e upsert de planilhas
    ├── exportacao-planilha/          # Geração fiel de arquivos .xlsx
    ├── tags-crud/                    # Gerenciador de tags por categoria
    ├── dashboard/                    # Métricas em tempo real
    ├── docker-compose/               # Infraestrutura conteinerizada
    └── ci/                           # Pipeline do GitHub Actions
```

---

## 📄 Licença

Este projeto é desenvolvido para fins corporativos e acadêmicos. Distribuído sob a licença MIT.
