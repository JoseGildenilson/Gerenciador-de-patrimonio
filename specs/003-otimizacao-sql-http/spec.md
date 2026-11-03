# Feature Specification: Otimização de Consultas SQL e Requisições HTTP

**Feature Branch**: `003-otimizacao-sql-http`
**Created**: 2026-11-03
**Status**: In Progress
**Scope**: Frontend Cache & Deduplication, Backend SQLAlchemy Query Optimization, Auth Dependency Optimization, Baseline Comparison

---

## 1. Contexto e Objetivos

O sistema SisPatrimonio apresenta redundâncias no tráfego HTTP e na execução de consultas SQL:
1. **Frontend**: Componentes (`EquipmentListPage`, `EquipmentDetailPage`, `NewEquipmentModal`, `ManageTagsModal`) realizam buscas repetidas a `/api/v1/categories` e `/api/v1/locations` a cada navegação, montagem e re-renderização, agravado pelo `React.StrictMode` em desenvolvimento.
2. **Backend**:
   - `list_assets` carrega a coleção completa de manutenções (`selectinload(Asset.maintenances)`) exclusivamente para calcular `last_maintenance_at`, além de disparar 4 consultas separadas (`selectinload`) para entidades `Many-to-One`.
   - `get_asset` dispara até 14 consultas SQL individuais devido ao uso desarticulado de `selectinload` em múltiplos níveis de relacionamentos 1:1 e 1:N.
   - `get_current_user` carrega todas as colunas de `users` (incluindo `password_hash`) a cada requisição HTTP.

### Restrições Obrigatórias:
- **Zero alterações de banco**: Sem novas tabelas, colunas, tipos, constraints, chaves ou migrations.
- **Contratos preservados**: Nenhuma alteração nos payloads de resposta das rotas HTTP existentes.
- **Logs visuais preservados**: Logs SQL coloridos, temporizados e com badges mantidos integralmente para apresentação acadêmica.

---

## 2. User Scenarios & Acceptance Criteria (BDD)

### User Story 1 - Cache Compartilhado e Deduplicação no Frontend (Priority: P1)

Como usuário navegando pelo sistema de patrimônio, quero que categorias e localizações sejam carregadas uma única vez e reutilizadas entre páginas e modais, para que as telas abram instantaneamente sem requisições de rede duplicadas.

#### Acceptance Scenarios:
1. **Given** que o usuário acessa a listagem de equipamentos pela primeira vez, **When** a página monta, **Then** as requisições a `/api/v1/categories` e `/api/v1/locations` são disparadas apenas uma vez, mesmo sob `React.StrictMode` (deduplicação de promises em voo).
2. **Given** que categorias e localizações já foram carregadas em cache no frontend, **When** o usuário clica em um equipamento para abrir os detalhes ou navega de volta para a listagem, **Then** nenhuma requisição de rede para `/api/v1/categories` ou `/api/v1/locations` deve ser executada.
3. **Given** que o usuário cria, edita ou exclui uma categoria ou localização via modal, **When** a mutação for concluída com sucesso, **Then** o cache correspondente deve ser invalidado imediatamente e os dados atualizados devem ser refletidos.

---

### User Story 2 - Otimização de Consultas na Listagem de Equipamentos (Priority: P1)

Como técnico de TI consultando o inventário, quero listar ativos com alta performance, para que o banco de dados realize o menor número possível de consultas sem carregar históricos desnecessários.

#### Acceptance Scenarios:
1. **Given** uma requisição para `GET /api/v1/assets?page=1&limit=25`, **When** o backend processar a listagem, **Then** o relacionamento Many-to-One (`category`, `location`, `assigned_user`) deve ser carregado com `joinedload` em uma única consulta principal de dados, sem disparar SELECTs adicionais em lote para essas entidades.
2. **Given** a necessidade do campo `last_maintenance_at` na listagem, **When** a consulta de ativos for construída, **Then** o backend não deve carregar a coleção completa `Asset.maintenances` via `selectinload`, obtendo a data da última manutenção via subquery escalar correlacionada.
3. **Given** a execução completa de `GET /api/v1/assets`, **When** contabilizadas as consultas SQL geradas, **Then** o endpoint deve executar no máximo 2 consultas no repositório (1 COUNT + 1 SELECT com JOINs e subquery de última manutenção) além da autenticação.

---

### User Story 3 - Otimização Estruturada no Detalhe de Equipamento (Priority: P2)

Como administrador analisando um equipamento específico, quero visualizar todos os detalhes cadastrais, histórico de renumeração, movimentações e manutenções, com carregamento enxuto sem multiplicação desnecessária de queries SQL.

#### Acceptance Scenarios:
1. **Given** uma requisição para `GET /api/v1/assets/{id}`, **When** o ativo for recuperado com `eager_history=True`, **Then** as entidades Many-to-One diretas (`category`, `location`, `assigned_user`) devem ser unificadas via `joinedload` no SELECT principal do ativo.
2. **Given** as coleções filhas (`maintenances`, `patrimony_histories`, `movements`), **When** forem carregadas, **Then** devem utilizar `selectinload` para a coleção e `joinedload` para os relacionamentos Many-to-One filhos (ex: `AssetMaintenance.registered_by`, `PatrimonyHistory.changed_by`, `AssetMovement.origin_location`, `dest_location`, `moved_by`), reduzindo as 14 consultas originais para 4 consultas focadas.

---

### User Story 4 - Otimização da Dependência de Autenticação (Priority: P2)

Como sistema seguro, quero validar as credenciais do usuário autenticado a cada requisição sem trafegar hashes de senha desnecessários na memória do ORM.

#### Acceptance Scenarios:
1. **Given** uma requisição autenticada com token JWT válido, **When** a dependência `get_current_user` buscar o registro na tabela `users`, **Then** a consulta deve aplicar projeção restrita (`load_only`) para os campos essenciais (`id`, `name`, `email`, `role`, `is_active`, `deleted_at`), omitindo `password_hash`.
2. **Given** uma requisição que injete múltiplas dependências autorizativas (ex: `get_current_user` e `require_tecnico_or_admin`), **When** o FastAPI avaliar o grafo de dependências, **Then** a função deve ser executada apenas uma vez por requisição graças ao cache de dependências padrão (`use_cache=True`).

---

### User Story 5 - Preservação de Observabilidade Acadêmica (Priority: P3)

Como professor ou avaliador analisando a execução do sistema, quero ver os logs SQL nítidos e explicativos no terminal, para compreender com clareza as consultas geradas e a redução de sobrecarga obtida.

#### Acceptance Scenarios:
1. **Given** qualquer consulta SQL executada pelo backend, **When** interceptada pelos listeners do SQLAlchemy, **Then** o terminal deve exibir o box com badge colorido, tempo em ms e parâmetros sanitizados.
2. **Given** a execução das rotas otimizadas, **When** comparados os logs antes e depois, **Then** deve ser evidente a redução de queries redundantes sem perda de clareza das instruções SQL.
