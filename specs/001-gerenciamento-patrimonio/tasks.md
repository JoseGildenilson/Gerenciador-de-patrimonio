---
description: "Lista de tarefas de implementação para o Modelo de Banco de Dados de Gerenciamento de Patrimônio"
---

# Tasks: Gerenciamento de Patrimônio — Modelo de Banco de Dados

**Input**: Design documents from `/specs/001-gerenciamento-patrimonio/`  
**Prerequisites**: [plan.md](file:///home/gil/Projects/Gerenciador de patrimonio/specs/001-gerenciamento-patrimonio/plan.md), [spec.md](file:///home/gil/Projects/Gerenciador de patrimonio/specs/001-gerenciamento-patrimonio/spec.md), [research.md](file:///home/gil/Projects/Gerenciador de patrimonio/specs/001-gerenciamento-patrimonio/research.md), [data-model.md](file:///home/gil/Projects/Gerenciador de patrimonio/specs/001-gerenciamento-patrimonio/data-model.md), [contracts/](file:///home/gil/Projects/Gerenciador de patrimonio/specs/001-gerenciamento-patrimonio/contracts/)  
**Organization**: Tarefas organizadas por história de usuário (User Story) para garantir implementação e testes independentes de cada fase, com Quality Gate de 100% de cobertura.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialização das definições fundamentais de enums e estrutura de migração

- [x] T001 Configure native PostgreSQL and Python Enums (`user_role`: 'administrador', 'tecnico', 'colaborador'; `asset_status`: 'disponivel', 'em_uso', 'em_manutencao', 'baixado'; `maintenance_type`: 'preventiva', 'corretiva') in `src/domain/models.py`
- [x] T002 [P] Create Alembic migration script skeleton `alembic/versions/d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py` with downgrade and upgrade stubs

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Estrutura base de usuários, migração de dados e framework de acesso que bloqueia as histórias

**⚠️ CRITICAL**: Nenhuma história de usuário pode ser iniciada antes da conclusão desta fase

- [x] T003 Evolve User ORM model in `src/domain/models.py` adding `name varchar(255) not null`, `password_hash varchar(255) not null`, updating `role user_role default 'colaborador'`, `is_active boolean default true`, and `deleted_at timestamptz null`
- [x] T004 [P] Implement updated User DTO schemas in `src/domain/schemas.py` matching new fields (`name`, `role`, `is_active`, `deleted_at`)
- [x] T005 Update UserRepository in `src/infrastructure/repositories.py` without commit/rollback
- [x] T006 Implement complete Alembic migration in `alembic/versions/d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py` creating enums and tables (`users`, `locations`, `categories`, `assets`, `patrimony_history`, `asset_movements`, `asset_maintenances`)
- [x] T007 [P] Update Alembic migration lifecycle tests in `tests/test_migrations.py` validating up/down/up idempotency

**Checkpoint**: Base do banco pronta — início das histórias de usuário desbloqueado

---

## Phase 3: User Story 1 - Cadastro e Gestão de Ativos com Categorias e Depreciação (Priority: P1) 🎯 MVP

**Goal**: Permitir o cadastro de categorias com diretrizes contábeis e ativos patrimoniais com especificações flexíveis em JSONB e número de série condicional.

**Independent Test**: Cadastrar categoria com `requires_serial_number=true`, cadastrar ativo com especificações JSONB e validar rejeição caso serial não seja informado.

### Tests for User Story 1
- [x] T008 [P] [US1] Unit and schema validation tests for Category and Asset DTOs in `tests/test_asset_schemas.py`
- [x] T009 [P] [US1] Unit tests for Category and Asset ORM models and constraints in `tests/test_asset_models.py`

### Implementation for User Story 1
- [x] T010 [P] [US1] Implement Category ORM model in `src/domain/models.py` with `name varchar(100) unique not null`, `useful_life_months integer null`, `residual_value_rate numeric(5,2) not null default 0.00` (range 0 to 100), `requires_serial_number boolean not null default false`
- [x] T011 [P] [US1] Implement Asset ORM model in `src/domain/models.py` with `patrimony_number varchar(100) unique not null`, `serial_number varchar(100) unique null`, `description varchar(255) not null`, `category_id int FK`, `location_id int FK`, `assigned_user_id int FK null`, `brand varchar(100) not null`, `model varchar(100) null`, `purchase_cost numeric(12,2) null`, `purchase_date date null`, `status asset_status default 'disponivel'`, `specs jsonb not null default '{}'`, `deleted_at timestamptz null`
- [x] T012 [P] [US1] Implement Category and Asset Pydantic schemas in `src/domain/schemas.py` with validators for `residual_value_rate` (0.00 to 100.00) and `specs` JSON dictionary
- [x] T013 [P] [US1] Implement CategoryRepository in `src/infrastructure/repositories.py` (CRUD operations and active filter, no commit/rollback)
- [x] T014 [US1] Implement AssetRepository in `src/infrastructure/repositories.py` (filtering by category, status, location, text search, pagination, no commit/rollback)
- [x] T015 [US1] Implement CategoryUseCases in `src/use_cases/category_use_cases.py` (create/update/list categories with transactional commit/rollback)
- [x] T016 [US1] Implement AssetUseCases in `src/use_cases/asset_use_cases.py` (create/update assets enforcing `requires_serial_number` validation from category)
- [x] T017 [P] [US1] Implement Category HTTP router in `src/api/category_routes.py` per contract `specs/001-gerenciamento-patrimonio/contracts/categories-api.yaml`
- [x] T018 [US1] Implement Asset HTTP router in `src/api/asset_routes.py` per contract `specs/001-gerenciamento-patrimonio/contracts/assets-api.yaml`
- [x] T019 [US1] Integration tests for Category and Asset APIs in `tests/test_asset_api.py`

**Checkpoint**: User Story 1 (MVP) funcional e testável de forma independente

---

## Phase 4: User Story 2 - Localização Física Estruturada e Espaço Físico Único (Priority: P2)

**Goal**: Organizar os espaços físicos por Prédio, Andar, Setor e Sala, garantindo unicidade contra duplicidade de alocações.

**Independent Test**: Cadastrar localização e verificar rejeição por conflito HTTP 409 quando combinação idêntica `(building, floor, sector, room_number)` for reinserida.

### Tests for User Story 2
- [x] T020 [P] [US2] Unit tests for Location model and composite uniqueness `uq_locations_physical_space` in `tests/test_location_models.py`
- [x] T021 [P] [US2] Unit and schema validation tests for Location schemas in `tests/test_location_schemas.py`

### Implementation for User Story 2
- [x] T022 [P] [US2] Implement Location ORM model in `src/domain/models.py` with `building varchar(100) not null`, `floor varchar(50) not null`, `sector varchar(100) not null`, `room_number varchar(50) null`, `description text null`, and unique index `uq_locations_physical_space`
- [x] T023 [P] [US2] Implement Location Pydantic schemas in `src/domain/schemas.py` (`LocationCreate`, `LocationUpdate`, `LocationResponse`)
- [x] T024 [US2] Implement LocationRepository in `src/infrastructure/repositories.py` (lookup by physical space, list active, no commit/rollback)
- [x] T025 [US2] Implement LocationUseCases in `src/use_cases/location_use_cases.py` (manage locations, transaction control)
- [x] T026 [US2] Implement Location HTTP router in `src/api/location_routes.py` per contract `specs/001-gerenciamento-patrimonio/contracts/locations-api.yaml`
- [x] T027 [US2] Integration tests for Location API in `tests/test_location_api.py`

**Checkpoint**: User Story 2 operacional e integrada com o cadastro de ativos

---

## Phase 5: User Story 3 - Movimentação Física, Transferência de Custódia e Aceite de Termo (Priority: P3)

**Goal**: Registrar transferências físicas e de custodiante com geração e carimbo de aceite do termo de responsabilidade.

**Independent Test**: Registrar movimentação com `to_user_id` e efetuar aceite do termo registrando timestamp em `term_accepted_at`.

### Tests for User Story 3
- [x] T028 [P] [US3] Unit tests for AssetMovement model in `tests/test_movement_models.py`
- [x] T029 [P] [US3] Unit and schema validation tests for AssetMovement schemas in `tests/test_movement_schemas.py`

### Implementation for User Story 3
- [x] T030 [P] [US3] Implement AssetMovement ORM model in `src/domain/models.py` with `asset_id int FK`, `origin_location_id int FK`, `dest_location_id int FK null`, `from_user_id int FK null`, `to_user_id int FK null`, `moved_by_id int FK`, `term_accepted_at timestamptz null`, `movement_date timestamptz not null`, `notes text null`
- [x] T031 [P] [US3] Implement AssetMovement Pydantic schemas in `src/domain/schemas.py`
- [x] T032 [US3] Implement AssetMovementRepository in `src/infrastructure/repositories.py` (chronological list, no commit/rollback)
- [x] T033 [US3] Implement AssetMovementUseCases in `src/use_cases/movement_use_cases.py` (transfer asset, update current location/assigned user, accept custody term, atomic transaction)
- [x] T034 [US3] Implement Movement HTTP router in `src/api/movement_routes.py` per contract `specs/001-gerenciamento-patrimonio/contracts/movements-maintenances-api.yaml`
- [x] T035 [US3] Integration tests for AssetMovement API in `tests/test_movement_api.py`

**Checkpoint**: User Story 3 funcional com rastreabilidade completa de custódia

---

## Phase 6: User Story 4 - Rastreabilidade de Renumeração de Patrimônio e Manutenções Técnicas (Priority: P4)

**Goal**: Registrar substituições de plaquetas físicas com justificativa e histórico imutável, além de intervenções de manutenção preventiva/corretiva com prestador e custo.

**Independent Test**: Renumerar patrimônio garantindo persistência em `patrimony_history` e lançar manutenção com `cost numeric(12,2)`.

### Tests for User Story 4
- [x] T036 [P] [US4] Unit tests for PatrimonyHistory and AssetMaintenance models in `tests/test_maintenance_models.py`
- [x] T037 [P] [US4] Unit and schema validation tests for PatrimonyHistory and Maintenance schemas in `tests/test_maintenance_schemas.py`

### Implementation for User Story 4
- [x] T038 [P] [US4] Implement PatrimonyHistory ORM model in `src/domain/models.py` with `asset_id int FK`, `old_patrimony_number varchar(100) not null`, `new_patrimony_number varchar(100) not null`, `reason varchar(255) not null`, `changed_by_id int FK`, `changed_at timestamptz not null`
- [x] T039 [P] [US4] Implement AssetMaintenance ORM model in `src/domain/models.py` with `asset_id int FK`, `registered_by_id int FK`, `maintenance_type maintenance_type not null`, `service_provider varchar(150) null`, `description text not null`, `cost numeric(12,2) null`, `maintenance_date timestamptz not null`
- [x] T040 [P] [US4] Implement PatrimonyHistory and AssetMaintenance schemas in `src/domain/schemas.py`
- [x] T041 [US4] Implement PatrimonyHistoryRepository and AssetMaintenanceRepository in `src/infrastructure/repositories.py` (no commit/rollback)
- [x] T042 [US4] Implement RenumberPatrimonyUseCase in `src/use_cases/asset_use_cases.py` (atomic renumbering, duplicate prevention, history logging)
- [x] T043 [US4] Implement MaintenanceUseCases in `src/use_cases/maintenance_use_cases.py` (record preventive/corrective maintenance with cost and provider)
- [x] T044 [US4] Implement Renumber endpoint in `src/api/asset_routes.py` and Maintenance endpoints in `src/api/movement_routes.py` per contracts
- [x] T045 [US4] Integration tests for Renumbering and Maintenance APIs in `tests/test_maintenance_api.py`

**Checkpoint**: Todas as 4 User Stories operacionais e integradas

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Sementes de dados, montagem de rotas na aplicação, validação de lint e quality gate de 100% de cobertura

- [x] T046 [P] Update database seed in `src/infrastructure/seed.py` with initial categories and campus locations
- [x] T047 Register new routers (`asset_routes`, `location_routes`, `category_routes`, `movement_routes`) in `src/main.py`
- [x] T048 Run complete test suite and verify 100% branch coverage with `PYTHONPATH=. uv run --extra dev pytest --cov=src --cov-branch --cov-fail-under=100`
- [x] T049 [P] Run code linter and formatting checks with `uv run --extra dev ruff check src/ && uv run --extra dev ruff format --check src/`
- [x] T050 Validate end-to-end scenarios executing the steps in `specs/001-gerenciamento-patrimonio/quickstart.md`

---

## Phase 8: User Story 5 - Comandos e Scripts de Criação e Povoamento do BD (Priority: P2)

**Goal**: Disponibilizar comandos CLI automatizados (`uv run db-create`, `uv run db-seed`) e scripts SQL nativos (`database/schema.sql`, `database/populate.sql`) para atender às exigências acadêmicas do professor da disciplina de Banco de Dados.

**Independent Test**: Executar `uv run db-create` e `uv run db-seed` e verificar a criação e carga do banco de dados, além de validar a sintaxe e integridade dos scripts SQL nativos.

- [x] T051 [P] [US5] Generate native PostgreSQL DDL script in `database/schema.sql` declaring all enums and tables (`users`, `locations`, `categories`, `assets`, `patrimony_history`, `asset_movements`, `asset_maintenances`) with unique indexes, check constraints and foreign keys
- [x] T052 [P] [US5] Generate native PostgreSQL DML script in `database/populate.sql` with rich sample data across all entities
- [x] T053 [P] [US5] Implement CLI commands module in `src/cli.py` with `create_db()` and `seed_db()` functions
- [x] T054 [P] [US5] Register `db-create = "src.cli:create_db"` and `db-seed = "src.cli:seed_db"` in `pyproject.toml` under `[project.scripts]`
- [x] T055 [US5] Unit and integration tests for `src/cli.py` ensuring 100% line and branch coverage in `tests/test_cli.py`
- [x] T056 [US5] Verify CLI commands and test suite locally with `uv run db-create`, `uv run db-seed` and `PYTHONPATH=. uv run pytest --cov=src --cov-branch --cov-fail-under=100`
- [x] T057 [US5] Update `README.md` with explicit database creation and population instructions for professor evaluation

---

## Phase 8B: Correções, Conformidade Constitucional e Quality Gate 100%

**Purpose**: Resolver pendências identificadas pela auditoria de testes (violações constitucionais, bug de Docker prod, lint no backend e cobertura 100% no frontend)

- [x] T058 [P] Remover arquivo de banco de dados remanescente `internal_management.db` da raiz para cumprir proibição constitucional de nome legado
- [x] T059 [P] Corrigir nome do volume de persistência para `patrimonio_data` em `docker-compose.yml` conforme especificado na Constituição
- [x] T060 Corrigir `DATABASE_URL` no serviço backend em `docker-compose.prod.yml` alterando host de `localhost:5432` para `postgres:5432`
- [x] T061 [P] Corrigir avisos de linter em `tests/conftest.py` reorganizando imports ou adicionando `# noqa: E402` onde a injeção prévia de variáveis de ambiente for requerida
- [x] T062 [P] Eliminar imports redundantes `validate_host_ip` e `EquipmentUpdate` em `tests/test_equipment_schemas.py` resolvendo `F811`
- [x] T063 [P] Renomear variável de iteração ambígua `l` para `line` em `tests/test_spreadsheet_exporter.py` resolvendo `E741`
- [x] T064 [P] Criar suíte de testes unitários em `frontend/src/__tests__/ErrorBoundary.test.tsx` cobrindo renderização padrão, captura de erros e fallback visual do `frontend/src/components/ErrorBoundary.tsx`
- [x] T065 [P] Criar suíte de testes em `frontend/src/__tests__/errorUtils.test.ts` cobrindo todas as ramificações de erro Axios e mensagens genéricas em `frontend/src/utils/errorUtils.ts`
- [x] T066 [P] Adicionar casos de testes em `frontend/src/__tests__/EquipmentDetailPage.test.tsx` para cobrir branches residuais (linhas 978, 1050, 1052 e condicionais de renderização)
- [x] T067 [P] Adicionar casos de testes em `frontend/src/__tests__/EquipmentPage.test.tsx` para cobrir branches residuais de paginação e filtros (linhas 502, 518, 520)
- [x] T068 [P] Adicionar casos de testes em `frontend/src/__tests__/ImportPage.test.tsx` para cobrir ramificações de importação e processamento (linhas 76, 368-378, 386)
- [x] T069 Validar suíte completa de qualidade executando `uv run ruff check .`, `PYTHONPATH=. uv run pytest --cov=src --cov-branch --cov-fail-under=100`, e `npm run test` garantindo 100% de cobertura de linhas e branches em todo o código executável

---

## Phase 9: User Story 6 - Observabilidade e Logs Descritivos de Banco de Dados (Priority: P2 - FR-012, SC-006)

**Goal**: Permitir visualização limpa de queries SQL no terminal (SELECT ao listar, INSERT ao cadastrar, UPDATE/DELETE em alterações) com parâmetros legíveis, tempo em ms e higienização de senhas (`[REDACTED]`), filtrando consultas automáticas de healthcheck (`SELECT 1`).

**Independent Test**: Executar uma requisição de listagem e outra de cadastro e verificar no terminal a emissão de `[SQL QUERY]` com parâmetros formatados e duração em ms, sem ocorrência de `SELECT 1` e com dados sensíveis mascarados.

### Implementation for User Story 6

- [x] T070 [P] [US6] Add LOG_SQL_STATEMENTS configuration flag in `src/core/config.py` with default true in development and false in production
- [x] T071 [US6] Implement SQLAlchemy `before_cursor_execute` and `after_cursor_execute` event listeners in `src/core/database.py` with `SELECT 1` filtering, elapsed time in ms, and sensitive parameter sanitization (`[REDACTED]`)
- [x] T072 [P] [US6] Implement unit tests for SQL statement logging, timer calculation, healthcheck filtering, and password redaction in `tests/test_database.py`
- [x] T073 [US6] Validate SQL query logging during HTTP endpoint requests (listing, creation) in `tests/test_database.py` with `LOG_SQL_STATEMENTS` enabled
- [x] T074 [P] [US6] Update documentation in `README.md` and `specs/001-gerenciamento-patrimonio/quickstart.md` with instructions for observing database logs during professor demonstration
- [x] T075 [US6] Verify complete test suite coverage with `PYTHONPATH=. uv run pytest --cov=src --cov-branch --cov-fail-under=100` and code formatting with `uv run ruff check .`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: Sem dependências — execução imediata.
- **Foundational (Phase 2)**: Depende de Setup (Phase 1) — **BLOQUEIA** todas as histórias de usuário.
- **User Story 1 (Phase 3)**: Depende de Foundational (Phase 2).
- **User Story 2 (Phase 4)**: Depende de Foundational (Phase 2). Pode executar em paralelo ou após US1.
- **User Story 3 (Phase 5)**: Depende de US1 e US2 (necessita de `assets` e `locations`).
- **User Story 4 (Phase 6)**: Depende de US1 (necessita de `assets`).
- **User Story 5 (Phase 8)**: Comandos CLI e scripts SQL nativos.
- **User Story 6 (Phase 9)**: Depende de `src/core/database.py` e `src/core/config.py`.
- **Phase 10 (Convergence)**: Ajustes de prontidão SQLAlchemy Core, credenciais e regras de baixa.
- **Phase 11 (Foundational Schema & Stub Cleanup)**: Paridade estrita entre Alembic, `models.py` e `database/schema.sql` — **BLOQUEIA** a Phase 12 (User Story 7).
- **User Story 7 (Phase 12)**: Depende da Phase 11; integra Contratos Backend enriquecidos, RBAC `administrador` e migração completa do Frontend React para as 7 tabelas canônicas.
- **Phase 13 (Polish, E2E & Docker)**: Depende da conclusão da Phase 12 (User Story 7).

### Parallel Execution Examples

#### Setup & Foundational
```bash
# Executar modelos de enums e migração esqueleto:
T001: "src/domain/models.py (enums)"
T002: "alembic/versions/d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py"
```

#### User Story 1 (MVP)
```bash
# Executar testes unitários e schemas em paralelo:
T008: "tests/test_asset_schemas.py"
T009: "tests/test_asset_models.py"
T010: "Category model in src/domain/models.py"
T011: "Asset model in src/domain/models.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Concluir Phase 1 (Setup) e Phase 2 (Foundational).
2. Concluir Phase 3 (User Story 1 - Ativos e Categorias).
3. **STOP e VALIDAR**: Testar cadastro de categorias e ativos com serial e JSONB isoladamente via Pytest.

### Incremental Delivery
1. Setup + Foundational concluídos.
2. User Story 1 (MVP) entregue e testada.
3. User Story 2 (Localizações estruturadas) integrada.
4. User Story 3 (Movimentações e Termo) integrada.
5. User Story 4 (Renumeração e Manutenções) integrada.
6. Phase 7 (Polish, CI 100% coverage e Quickstart) validado.


---

## Phase 10: Convergence

- [x] T076 CRITICAL: Replace raw SQL `text()` calls in `src/infrastructure/db_readiness.py` with SQLAlchemy 2.0 Core `select(1)` and `postgresql.ENUM(...).create(checkfirst=True)` and update `tests/test_db_readiness.py` per Constitution III (contradicts)
- [x] T077 Align default test user credentials in `README.md` and placeholder in `frontend/src/components/LoginForm.tsx` with the canonical `@sispatrimonio.edu.br` accounts seeded by `db-seed` per FR-010, US5/AC2, T057 (contradicts)
- [x] T078 Replace truncated Argon2 password hashes in `database/populate.sql` with a valid Argon2id hash for `'senha123'` and include canonical user emails (`admin`, `tecnico`, `colaborador`) per FR-011, US5/AC3, T052 (contradicts)
- [x] T079 Enforce `requires_serial_number` validation during asset updates in `src/use_cases/asset_use_cases.py` and add unit/API test coverage in `tests/test_asset_api.py` per FR-005 (partial)
- [x] T080 Block movements and new maintenances on decommissioned (`'baixado'`) assets in `src/use_cases/movement_use_cases.py` and `src/use_cases/maintenance_use_cases.py` with corresponding tests per spec: Edge Case 3 (missing)
- [x] T081 Synchronize `src/infrastructure/seed.py` dataset with `database/populate.sql` and ensure PostgreSQL enum lifecycle in `alembic/versions/d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py` per FR-001, SC-001, US5/AC2 (partial)

---

## Phase 11: Foundational — Paridade Estrita de Banco/Alembic/ORM e Limpeza de Stubs (Blocking Prerequisites - FR-013)

**Purpose**: Garantir que `alembic/versions/`, `src/domain/models.py` e `database/schema.sql` possuam exatamente os mesmos tipos ENUM nas colunas, restrições `ON DELETE`, `NULLS NOT DISTINCT`, `CheckConstraint`s e `Index`es, além de remover módulos órfãos de 1 linha antes da integração full-stack.

**⚠️ CRITICAL**: Bloqueia a execução da User Story 7 (Phase 12).

- [x] T082 Align ORM models in `src/domain/models.py` with `database/schema.sql` enforcing `ondelete="RESTRICT"` (`assets.category_id`, `assets.location_id`, `patrimony_history.changed_by_id`, `asset_movements.origin_location_id`, `asset_movements.dest_location_id`, `asset_movements.moved_by_id`, `asset_maintenances.registered_by_id`), `ondelete="SET NULL"` (`assets.assigned_user_id`, `asset_movements.from_user_id`, `asset_movements.to_user_id`), `ondelete="CASCADE"` (`patrimony_history.asset_id`, `asset_movements.asset_id`, `asset_maintenances.asset_id`), `postgresql_nulls_not_distinct=True` on `uq_locations_physical_space`, 4 `CheckConstraint`s (`useful_life_months > 0`, `residual_value_rate >= 0.00 AND residual_value_rate <= 100.00`, `purchase_cost >= 0.00`, `cost >= 0.00`), and 7 performance `Index`es (`idx_assets_category_id`, `idx_assets_location_id`, `idx_assets_assigned_user_id`, `idx_assets_status`, `idx_asset_movements_asset_id`, `idx_asset_maintenances_asset_id`, `idx_patrimony_history_asset_id`)
- [x] T083 Update Alembic migrations in `alembic/versions/d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py` and `alembic/versions/e5f6a7b8c9d0_purge_legacy_database_tables.py` so `users.role` uses native ENUM `user_role` (default `'colaborador'`), `assets.status` uses `asset_status` (default `'disponivel'`), `asset_maintenances.maintenance_type` uses `maintenance_type`, `uq_locations_physical_space` includes `postgresql_nulls_not_distinct=True`, all `ON DELETE` rules, 4 `CheckConstraint`s and 7 `Index`es are applied, and orphan PL/pgSQL function `set_updated_at()` is dropped
- [x] T084 [P] Delete obsolete 1-line stub modules `src/api/equipment_routes.py`, `src/api/catalog_routes.py`, `src/use_cases/equipment_use_cases.py` and obsolete 1-line test files `tests/test_equipment_api.py`, `tests/test_equipment_models.py`, `tests/test_equipment_repositories.py`, `tests/test_equipment_schemas.py`, `tests/test_equipment_use_cases.py`, `tests/test_tags_and_coverage.py`
- [x] T085 Add schema parity and constraint verification tests in `tests/test_migrations.py` and `tests/test_asset_models.py` confirming native ENUM columns, `ON DELETE` behaviors, `CheckConstraint`s, and `uq_locations_physical_space` (`NULLS NOT DISTINCT`)

**Checkpoint**: Esquema relacional 100% convergente entre Alembic, SQLAlchemy ORM e `database/schema.sql`.

---

## Phase 12: User Story 7 - Integração Ponta a Ponta do Frontend React e Contratos de API com o Modelo Canônico (Priority: P1 - FR-014, FR-015, FR-016, FR-017, SC-007)

**Goal**: Conectar integralmente o Frontend React e o Backend FastAPI às 7 tabelas e 3 enums do SisPatrimonio, expondo rotas de exportação, usuários ativos, sugestões e exclusão protegida de catálogos, enriquecendo DTOs de resposta e habilitando o perfil `administrador` em todo o sistema.

**Independent Test**: Autenticar como `administrador` e `tecnico`, carregar métricas reais no Dashboard, listar/filtrar/exportar ativos, criar/editar/excluir categorias e localizações físicas, cadastrar/editar ativos com JSONB `specs`, renumerar patrimônio com histórico, movimentar ativo com aceite de termo e registrar/editar/excluir manutenção sem nenhum erro 404, 403 ou 500.

### Backend Contracts, Use Cases & Tests for User Story 7

- [x] T086 [P] [US7] Enforce `AssetStatus` (`'disponivel'`, `'em_uso'`, `'em_manutencao'`, `'baixado'`) and `MaintenanceTypeEnum` (`'preventiva'`, `'corretiva'`) in `AssetCreate`, `AssetUpdate`, `AssetMaintenanceCreate`, and `AssetMaintenanceUpdate`, and add `UserSummaryResponse`, enriched `AssetResponse` (`category`, `location`, `assigned_user`, `last_maintenance_at`), and enriched `AssetDetailResponse` (`movements`, `maintenances`, `patrimony_history`) in `src/domain/schemas.py`
- [x] T087 [US7] Update `AssetRepository`, `CategoryRepository`, `LocationRepository`, `UserRepository`, `AssetMovementRepository`, and `AssetMaintenanceRepository` in `src/infrastructure/repositories.py` to eager-load relationships (`category`, `location`, `assigned_user`), compute `last_maintenance_at`, list active users (`is_active == True`, `deleted_at IS NULL`), query distinct field suggestions, and support maintenance update/delete without `commit()`/`rollback()`
- [x] T088 [US7] Update `AssetUseCases` in `src/use_cases/asset_use_cases.py` to validate `user.is_active == True` and `user.deleted_at is None` when assigning `assigned_user_id`, use `data.model_fields_set` in `update_asset` to allow clearing nullable fields (`assigned_user_id`, `model`, `purchase_cost`, `purchase_date`, `serial_number`), and implement `export_assets` and `get_asset_suggestions`
- [x] T089 [P] [US7] Update `CategoryUseCases` in `src/use_cases/category_use_cases.py` and `LocationUseCases` in `src/use_cases/location_use_cases.py` to implement `delete_category` and `delete_location` (raising HTTP 409 `ConflictError` when linked assets or movements exist per `ON DELETE RESTRICT`) and enforce duplicate check on `(building, floor, sector, room_number)` when `room_number IS NULL`
- [x] T090 [P] [US7] Update `AssetMovementUseCases` in `src/use_cases/movement_use_cases.py` to reject inactive `to_user_id` (`is_active == False`) and update `MaintenanceUseCases` in `src/use_cases/maintenance_use_cases.py` to implement `update_maintenance` and `delete_maintenance` (validating `cost >= 0.00` and `maintenance_type` enum)
- [x] T091 [P] [US7] Update `src/infrastructure/spreadsheet_parser.py` and `src/use_cases/import_spreadsheet_use_cases.py` to parse `CUSTO AQUISIÇÃO` (`purchase_cost >= 0.00`), `DATA AQUISIÇÃO` (`purchase_date`), and `ESPECIFICAÇÕES` (`specs` JSONB) and enforce `category.requires_serial_number == True` validation during spreadsheet import
- [x] T092 [US7] Expose `GET /api/v1/assets/export` and `GET /api/v1/assets/suggestions` in `src/api/asset_routes.py`, `GET /api/v1/users` in `src/api/routes.py`, `DELETE /api/v1/categories/{category_id}` in `src/api/category_routes.py`, `DELETE /api/v1/locations/{location_id}` in `src/api/location_routes.py`, `PUT` and `DELETE /api/v1/assets/{asset_id}/maintenances/{maintenance_id}` in `src/api/movement_routes.py`, and replace `require_tecnico_role` with `require_tecnico_or_admin` in `src/api/import_routes.py`
- [x] T093 [US7] Add unit and integration tests in `tests/test_asset_api.py`, `tests/test_location_api.py`, `tests/test_movement_api.py`, `tests/test_maintenance_api.py`, `tests/test_import_routes.py`, and `tests/test_spreadsheet_parser.py` achieving 100% line and branch coverage for all new endpoints and validations

### Frontend React Implementation & Tests for User Story 7

- [x] T094 [P] [US7] Update TypeScript interfaces in `frontend/src/types/auth.ts` (`UserRole = 'administrador' | 'tecnico' | 'colaborador'`, `name: string`), `frontend/src/types/dashboard.ts` (`DashboardMetrics` matching `/api/v1/dashboard/metrics`), and `frontend/src/types/equipment.ts` (`Asset`, `Category`, `Location`, `UserSummary`, `PatrimonyHistory`, `AssetMovement`, `AssetMaintenance`)
- [x] T095 [US7] Refactor HTTP clients in `frontend/src/api/equipmentApi.ts` and `frontend/src/api/dashboardApi.ts` to consume `/api/v1/assets`, `/api/v1/assets/export`, `/api/v1/assets/suggestions`, `/api/v1/categories`, `/api/v1/locations`, `/api/v1/movements`, `/api/v1/users`, and `/api/v1/dashboard/metrics`
- [x] T096 [P] [US7] Update RBAC guards in `frontend/src/App.tsx`, `frontend/src/components/SideMenu.tsx`, and `frontend/src/pages/DashboardPage.tsx` to authorize `administrador` alongside `tecnico`, and connect `frontend/src/pages/DashboardPage.tsx` to `dashboardApi.getMetrics()` displaying `assets_total`, `assets_in_use`, `assets_in_maintenance`, `assets_available`, and `assets_decommissioned`
- [x] T097 [US7] Refactor `frontend/src/pages/EquipmentListPage.tsx` to load categories (`/api/v1/categories`), locations (`/api/v1/locations`), and `asset_status` enum options (`disponivel`, `em_uso`, `em_manutencao`, `baixado`), filter via `GET /api/v1/assets`, render category/location/custodian names on cards, and download `.xlsx` via `GET /api/v1/assets/export`
- [x] T098 [P] [US7] Refactor `frontend/src/components/NewEquipmentModal.tsx` to create assets via `POST /api/v1/assets` with required `patrimony_number` and `brand`, conditional `serial_number` based on `category.requires_serial_number`, `category_id`, `location_id`, `assigned_user_id`, `purchase_cost`, `purchase_date`, `status` enum, and `specs` JSONB fields
- [x] T099 [P] [US7] Refactor `frontend/src/components/ManageTagsModal.tsx` to manage Categories (`/api/v1/categories`: `name`, `useful_life_months`, `residual_value_rate`, `requires_serial_number`) and Physical Locations (`/api/v1/locations`: `building`, `floor`, `sector`, `room_number`, `description`) with create, edit, and delete support
- [x] T100 [US7] Refactor `frontend/src/pages/EquipmentDetailPage.tsx` to view/edit canonical `Asset` fields and `specs` JSONB, execute atomic patrimony renumbering (`POST /api/v1/assets/{id}/renumber`) displaying `patrimony_history`, and accept custody terms (`POST /api/v1/movements/{movement_id}/accept-term`)
- [x] T101 [P] [US7] Refactor `frontend/src/components/MovementModal.tsx`, `frontend/src/components/MaintenanceModal.tsx`, and `frontend/src/components/EditMaintenanceModal.tsx` for the canonical schemas (`origin_location_id`, nullable `dest_location_id` for decommission, `from_user_id`, `to_user_id`, `maintenance_type` `'preventiva' | 'corretiva'`, `service_provider`, `description`, `cost`, `maintenance_date`)
- [x] T102 [US7] Update Frontend test suites in `frontend/src/__tests__/EquipmentPage.test.tsx`, `frontend/src/__tests__/EquipmentDetailPage.test.tsx`, `frontend/src/__tests__/DashboardPage.test.tsx`, `frontend/src/__tests__/ImportPage.test.tsx`, and `frontend/src/__tests__/App.test.tsx` to validate the new `/api/v1/assets`, `/api/v1/categories`, `/api/v1/locations`, and `administrador` flows

**Checkpoint**: Frontend React e Backend 100% integrados sob o modelo canônico de 7 tabelas.

---

## Phase 13: Polish & Cross-Cutting Concerns (E2E Suite, Docker & Final Quality Gate)

**Purpose**: Alinhar volumes e identificadores Docker, reativar a suíte End-to-End (`tests/e2e/`) no modelo canônico e comprovar 100% de aprovação em todas as suítes.

- [x] T103 [P] Update `docker-compose.yml`, `docker-compose.prod.yml`, and `Dockerfile` to copy/mount `./database:/app/database` and enforce canonical container, volume, and network names (`patrimonio_backend`, `patrimonio_frontend`, `patrimonio_postgres`, `patrimonio_net`, `patrimonio_data`)
- [x] T104 Refactor E2E test suite in `tests/e2e/conftest.py`, `tests/e2e/test_tier1_feature_coverage.py`, `tests/e2e/test_tier2_boundary_corner.py`, `tests/e2e/test_tier3_cross_feature.py`, and `tests/e2e/test_tier4_real_world.py` to use `User(password_hash=...)` and canonical `/api/v1/assets`, `/api/v1/categories`, `/api/v1/locations`, and `/api/v1/movements` endpoints, removing `--ignore=tests/e2e` from `pyproject.toml`
- [x] T105 Run full validation gate: `uv run ruff check .`, `PYTHONPATH=. uv run pytest --cov=src --cov-branch --cov-fail-under=100`, `PYTHONPATH=. uv run pytest tests/e2e/`, and `cd frontend && npx tsc --noEmit && npm test -- --run`
