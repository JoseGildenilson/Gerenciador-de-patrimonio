# Gerenciador de Patrimônio (SisPatrimonio)

[![CI Pipeline](https://github.com/JoseGildenilson/Gerenciador-de-patrimonio/actions/workflows/ci.yml/badge.svg)](https://github.com/JoseGildenilson/Gerenciador-de-patrimonio/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?style=flat&logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![Test Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen?style=flat)

---

## 📌 Visão Geral

O **Gerenciador de Patrimônio (SisPatrimonio)** é um sistema web robusto desenvolvido para centralizar a gestão de ativos patrimoniais (computadores, servidores, monitores, impressoras, mobiliário e periféricos), garantindo:
- **Rastreabilidade contábil e operacional**: cálculo de depreciação, taxa residual e vida útil por categoria.
- **Hierarquia física estrita**: organização do campus por prédio, andar, setor e sala, com restrição de unicidade física composta.
- **Rastreamento de custódia e movimentações**: histórico cronológico de transferências físicas e aceites de termo de responsabilidade.
- **Histórico de manutenções**: registro de intervenções preventivas e corretivas com custos, prestadores de serviço e justificativas.
- **Renumeração auditável**: auditoria imutável de substituição de plaquetas de patrimônio.

O projeto foi construído sob a metodologia **Spec-Driven Development (SDD)**, com **100% de cobertura de testes automatizados** e arquitetura limpa dividida em camadas (Domínio, Casos de Uso, Infraestrutura e Interfaces de API/Web).

---

## 🗄️ Modelo de Dados & Avaliação Acadêmica

Para avaliação na disciplina de **Banco de Dados**, o sistema adota um modelo relacional normalizado no **PostgreSQL 16** com tipos enumerados nativos, integridade referencial estrita e campos dinâmicos em JSONB.

### Diagrama Entidade-Relacionamento

```mermaid
erDiagram
    users ||--o{ assets : "custodia (assigned_user_id)"
    users ||--o{ patrimony_history : "alterado_por (changed_by_id)"
    users ||--o{ asset_movements : "origem_usuario (from_user_id)"
    users ||--o{ asset_movements : "destino_usuario (to_user_id)"
    users ||--o{ asset_movements : "responsavel_mov (moved_by_id)"
    users ||--o{ asset_maintenances : "registrado_por (registered_by_id)"

    categories ||--o{ assets : "classifica (category_id)"
    locations ||--o{ assets : "abriga (location_id)"
    locations ||--o{ asset_movements : "local_origem (origin_location_id)"
    locations ||--o{ asset_movements : "local_destino (dest_location_id)"

    assets ||--o{ patrimony_history : "renumeracoes"
    assets ||--o{ asset_movements : "movimentacoes"
    assets ||--o{ asset_maintenances : "manutencoes"

    users {
        int id PK
        string name
        string email UK
        string password_hash
        user_role role
        boolean is_active
        timestamp deleted_at
    }

    locations {
        int id PK
        string building
        string floor
        string sector
        string room_number
        text description
    }

    categories {
        int id PK
        string name UK
        int useful_life_months
        numeric residual_value_rate
        boolean requires_serial_number
    }

    assets {
        int id PK
        string patrimony_number UK
        string serial_number UK
        string description
        int category_id FK
        int location_id FK
        int assigned_user_id FK
        string brand
        string model
        numeric purchase_cost
        date purchase_date
        asset_status status
        jsonb specs
        timestamp deleted_at
    }

    patrimony_history {
        int id PK
        int asset_id FK
        string old_patrimony_number
        string new_patrimony_number
        string reason
        int changed_by_id FK
        timestamp changed_at
    }

    asset_movements {
        int id PK
        int asset_id FK
        int origin_location_id FK
        int dest_location_id FK
        int from_user_id FK
        int to_user_id FK
        int moved_by_id FK
        timestamp term_accepted_at
        timestamp movement_date
        text notes
    }

    asset_maintenances {
        int id PK
        int asset_id FK
        int registered_by_id FK
        maintenance_type maintenance_type
        string service_provider
        text description
        numeric cost
        timestamp maintenance_date
    }
```

### Tipos Enumerados (ENUMs Nativos)
- `user_role`: `'administrador'`, `'tecnico'`, `'colaborador'`
- `asset_status`: `'disponivel'`, `'em_uso'`, `'em_manutencao'`, `'baixado'`
- `maintenance_type`: `'preventiva'`, `'corretiva'`

---

## 🚀 Como Criar e Popular o Banco de Dados

Disponibilizamos **duas formas independentes** para criar a estrutura e carregar os dados de teste:

### Método 1: Comandos Automatizados via CLI (Recomendado)

Utilizando o gerenciador de pacotes [`uv`](https://github.com/astral-sh/uv), execute na raiz do projeto:

```bash
# 1. Cria todas as tabelas, tipos ENUM, restrições e índices
uv run db-create

# 2. Popula o banco com catálogo patrimonial e dados de exemplo
uv run db-seed
```

*(Você também pode invocar via módulo Python direto: `uv run python -m src.cli create-db` e `uv run python -m src.cli seed-db`)*

### Método 2: Scripts SQL Nativos PostgreSQL 16 (.sql)

Caso prefira executar scripts SQL puros através de clientes como **psql**, **DBeaver** ou **pgAdmin**, os arquivos estão no diretório `database/`:

```bash
# Execução direta via psql no terminal:
psql -h localhost -p 5432 -U postgres -d internal_management -f database/schema.sql
psql -h localhost -p 5432 -U postgres -d internal_management -f database/populate.sql
```

1. **[`database/schema.sql`](database/schema.sql)**:
   - Criação dos tipos `user_role`, `asset_status` e `maintenance_type`.
   - Criação das tabelas `users`, `locations`, `categories`, `assets`, `patrimony_history`, `asset_movements` e `asset_maintenances`.
   - Restrição de unicidade física: `uq_locations_physical_space UNIQUE NULLS NOT DISTINCT (building, floor, sector, room_number)`.
   - Índices de performance para chaves estrangeiras e campos de filtro.
2. **[`database/populate.sql`](database/populate.sql)**:
   - Inserção de usuários nos 3 perfis de acesso.
   - Categorias com vida útil contábil e taxas residuais (0% a 20%).
   - Alocações em prédios, andares, setores e salas.
   - Ativos de alta tecnologia (Notebooks, Workstations, Servidores Rack, Monitores) com especificações técnicas ricas em `jsonb`.
   - Histórico de renumerações de plaquetas danificadas.
   - Movimentações com carimbo de aceite digital de custodiante.
   - Intervenções de manutenção preventiva e corretiva com valores monetários.

---

## ⚡ Passo a Passo: Como Rodar a Aplicação

### Pré-requisitos do Sistema
- **Git** instalado.
- **Python 3.13+** instalado.
- Gerenciador **`uv`** (recomendado para Python moderno e rápido):
  ```bash
  # Instalação rápida do uv (Linux/macOS):
  curl -LsSf https://astral-sh.uv.pkg.in/install.sh | sh
  ```
- **Node.js 20+** e **npm**.
- **Docker** e **Docker Compose** (caso opte pela execução em containers).

---

### Opção A: Execução com Docker Compose (Mais Rápida e Prática)

O Docker Compose sobe automaticamente o banco de dados PostgreSQL 16, a API FastAPI do Backend e a aplicação Frontend React:

#### 1. Modo Desenvolvimento (com Live Reload)
```bash
# Na raiz do repositório, execute:
docker compose up --build
```
- **Frontend Web:** [http://localhost:5173](http://localhost:5173)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Documentação Swagger (OpenAPI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Documentação Redoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **PostgreSQL:** porta `5432`

#### 2. Modo Produção (Otimizado com Nginx)
```bash
docker compose -f docker-compose.prod.yml up --build -d
```
- **Frontend em Produção:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)

---

### Opção B: Execução Local Nativa (Sem Docker)

#### 1. Clonar o Repositório e Configurar Variáveis de Ambiente
```bash
# 1. Clone o repositório
git clone https://github.com/JoseGildenilson/Gerenciador-de-patrimonio.git
cd Gerenciador-de-patrimonio

# 2. Crie o arquivo .env a partir do modelo
cp .env.example .env
```

> **Nota sobre o Banco de Dados:**
> Por padrão, o `.env` aponta para `postgresql://postgres:postgres@localhost:5432/internal_management`.
> Caso queira rodar localmente sem PostgreSQL instalado, pode usar SQLite temporário alterando a linha no `.env`:
> `DATABASE_URL=sqlite:///./internal_management.db`

#### 2. Configurar e Iniciar o Backend (FastAPI)
```bash
# 1. Instala dependências do Python no ambiente virtual isolado com uv
uv sync --all-extras

# 2. Cria as tabelas e tipos no banco de dados
uv run db-create

# 3. Popula o banco com os dados de exemplo
uv run db-seed

# 4. Inicia o servidor backend com recarregamento automático
uv run uvicorn src.main:app --reload --port 8000
```
O Backend estará acessível em:
- API Base: [http://localhost:8000](http://localhost:8000)
- Swagger Interativo: [http://localhost:8000/docs](http://localhost:8000/docs)

#### 3. Configurar e Iniciar o Frontend (React + Vite)
Abra um novo terminal e execute:
```bash
# 1. Entre na pasta do frontend
cd frontend

# 2. Instale as dependências Node
npm ci

# 3. Inicie o servidor de desenvolvimento Vite
npm run dev
```
O Frontend estará acessível em [http://localhost:5173](http://localhost:5173).

---

## 🔑 Credenciais Padrão para Testes

Ao executar o comando de povoamento (`db-seed` ou `populate.sql`), as seguintes contas pré-configuradas estarão ativas para login:

| Papel | E-mail | Senha | Permissões |
|---|---|---|---|
| **Administrador** | `admin@sispatrimonio.edu.br` | `senha123` | Acesso pleno ao sistema, gerenciamento de usuários, categorias e auditoria contábil. |
| **Técnico de TI** | `tecnico@empresa.com` | `senha123` | Cadastro e edição de ativos, movimentações físicas, renumeração de placas e manutenções técnicas. |
| **Colaborador** | `colaborador@empresa.com` | `senha123` | Consulta dos ativos sob sua custódia e confirmação de aceite de termos de responsabilidade. |

---

## 🧪 Como Rodar a Suíte Completa de Testes

O projeto conta com rigoroso controle de qualidade, exigindo **100% de cobertura de código (linhas e branches)** em todos os módulos executáveis.

### 1. Testes do Backend (Pytest + Cobertura 100%)
```bash
# Executa todos os testes com checagem estrita de cobertura 100%
PYTHONPATH=. uv run pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=100
```

### 2. Verificação de Linter e Formatação (Ruff)
```bash
# Checagem de regras de linter
uv run ruff check src/

# Checagem de formatação do código
uv run ruff format --check src/
```

### 3. Testes do Frontend (Vitest & TypeScript)
```bash
cd frontend

# Checagem de tipos estáticos sem emissão de arquivos
npx tsc --noEmit

# Checagem de linter ESLint
npm run lint

# Execução da suíte completa de testes unitários e de integração
npm test -- --run

# Teste de build de produção Vite
npm run build
```

---

## 📂 Estrutura de Diretórios do Projeto

```
Gerenciador-de-patrimonio/
├── .github/workflows/ci.yml       # Pipeline automatizada de Integração Contínua
├── alembic/                       # Scripts e controle de versões de migração do banco
├── database/                      # Scripts SQL nativos para entrega e avaliação acadêmica
│   ├── schema.sql                 # DDL: Criação de tipos ENUM, tabelas, índices e FKs
│   └── populate.sql               # DML: Povoamento com dados de teste realistas
├── frontend/                      # Aplicação web React 18 + TypeScript + Vite + Tailwind
│   ├── src/
│   │   ├── api/                   # Clientes de comunicação HTTP (Axios)
│   │   ├── components/            # Modais, formulários, tabelas e componentes reutilizáveis
│   │   ├── context/               # Gerenciamento de estado de autenticação (AuthContext)
│   │   ├── pages/                 # Telas (Dashboard, Lista de Patrimônio, Detalhes, Login)
│   │   └── __tests__/             # Testes automatizados no Vitest
│   └── package.json
├── src/                           # Código-fonte da aplicação Backend (Python / FastAPI)
│   ├── api/                       # Rotas e controladores HTTP REST (v1)
│   │   ├── asset_routes.py        # Endpoints de Bens e Ativos
│   │   ├── category_routes.py     # Endpoints de Categorias Contábeis
│   │   ├── location_routes.py     # Endpoints de Localizações Físicas
│   │   └── movement_routes.py     # Endpoints de Movimentação e Manutenção
│   ├── core/                      # Configurações globais, segurança, JWT e conexão de banco
│   ├── domain/                    # Modelos ORM SQLAlchemy e Schemas de validação Pydantic
│   ├── infrastructure/            # Repositórios de dados e scripts de sementes (seed)
│   ├── use_cases/                 # Lógica de aplicação com controle transacional estrito
│   ├── cli.py                     # Comandos de terminal: db-create e db-seed
│   └── main.py                    # Ponto de entrada FastAPI e montagem de rotas
├── tests/                         # Suíte de testes automatizados do Backend (Pytest)
├── docker-compose.yml             # Orquestração dos containers em desenvolvimento
├── docker-compose.prod.yml        # Orquestração dos containers em produção
├── pyproject.toml                 # Configuração do projeto Python, dependências e scripts CLI
└── README.md                      # Documentação completa do projeto
```

---

## 🛠️ Resolução de Problemas Comuns (Troubleshooting / FAQ)

### 1. "Porta 5432 já em uso"
Se você já possui uma instância local do PostgreSQL rodando no seu computador e tentar subir o Docker Compose, pode haver conflito de porta.
- **Solução 1:** Pare o PostgreSQL local (`sudo systemctl stop postgresql`) antes de rodar `docker compose up`.
- **Solução 2:** Altere no `.env` o valor de `POSTGRES_PORT=5433` e suba o container.

### 2. "Erro de autenticação no PostgreSQL local (fe_sendauth: no password supplied)"
Certifique-se de que a variável `DATABASE_URL` no arquivo `.env` contenha usuário e senha corretos do seu PostgreSQL local:
```env
DATABASE_URL=postgresql://seu_usuario:sua_senha@localhost:5432/nome_do_banco
```

### 3. "Como resetar o banco de dados do zero?"
Para reiniciar totalmente o banco:
```bash
# Se estiver usando Docker Compose:
docker compose down -v
docker compose up --build

# Se estiver rodando comandos CLI:
uv run db-create
uv run db-seed
```

---

## 📄 Licença

Projeto desenvolvido para fins corporativos e avaliação na disciplina de Banco de Dados. Distribuído sob a licença MIT.
