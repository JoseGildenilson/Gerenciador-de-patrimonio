# Data Model & Configuration Schema: Padronização de Nomenclatura

Este documento descreve os identificadores canônicos, esquemas de configuração de infraestrutura e regras de validação que governam o projeto **Gerenciador de Patrimônio**.

---

## 1. Identificadores Canônicos do Sistema (Constitucionais)

O projeto é governado pelo conjunto estrito de identificadores canônicos imutáveis:

| Dimensão / Camada | Identificador Oficial | Formato / Padrão | Regras de Validação |
|-------------------|-----------------------|------------------|---------------------|
| **Nome Canônico** | `Gerenciador de Patrimônio` | Título / Nome Próprio | Deve ser utilizado em todos os títulos, cabeçalhos de documentação e interfaces. |
| **Backend / Pacote Python** | `gerenciador_patrimonio` | snake_case | Deve constar no `pyproject.toml` como `name`. |
| **Frontend / App SPA** | `patrimonio-frontend` | kebab-case | Deve constar no `package.json` como `name`. |
| **Banco de Dados (Dev/Prod)** | `patrimonio_db` | snake_case | Utilizado em URLs de conexão PostgreSQL e variáveis de ambiente `POSTGRES_DB`. |
| **Banco de Dados (Testes/CI)** | `test_patrimonio_db` | snake_case | Utilizado exclusivamente no ambiente efêmero de testes automatizados e CI. |
| **Contêiner Backend** | `patrimonio_backend` | snake_case | Nome do contêiner Docker para o serviço FastAPI em desenvolvimento (`patrimonio_backend_prod` em produção). |
| **Contêiner Frontend** | `patrimonio_frontend` | snake_case | Nome do contêiner Docker para o serviço SPA React em desenvolvimento (`patrimonio_frontend_prod` em produção). |
| **Contêiner Banco de Dados** | `patrimonio_postgres` | snake_case | Nome do contêiner Docker para o serviço PostgreSQL 16 (`patrimonio_postgres_prod` em produção). |
| **Rede Docker (Bridge)** | `patrimonio_net` | snake_case | Rede isolada de comunicação entre serviços Docker (`patrimonio_net_prod` em produção). |
| **Volume Docker** | `patrimonio_data` | snake_case | Volume persistente onde residem os dados físicos do PostgreSQL (`/var/lib/postgresql/data`). |

---

## 2. Proibição Estrita de Nomenclatura Legada

Qualquer entidade, arquivo, variável ou comentário que contenha os termos a seguir é considerado inválido e viola a Constituição:

- ❌ `internal_management` (exceto em cláusulas de proibição da Constituição)
- ❌ `internal-management` (exceto em cláusulas de proibição da Constituição)
- ❌ `patrimonio-net` (com hífen - deve ser `patrimonio_net`)
- ❌ `postgres_data` (como volume - deve ser `patrimonio_data`)

---

## 3. Estado de Configuração de Serviços Docker

```text
+-----------------------------------------------------------+
|                      patrimonio_net                       |
|                                                           |
|  +--------------------+           +--------------------+  |
|  | patrimonio_frontend| <=======> | patrimonio_backend |  |
|  |    (React SPA)     |           |     (FastAPI)      |  |
|  +--------------------+           +--------------------+  |
|                                             ||            |
|                                             \/            |
|                                   +--------------------+  |
|                                   | patrimonio_postgres|  |
|                                   |    (PostgreSQL)    |  |
|                                   +--------------------+  |
|                                             ||            |
|                                   [ patrimonio_data ]     |
+-----------------------------------------------------------+
```
