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

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: Sem dependências — execução imediata.
- **Foundational (Phase 2)**: Depende de Setup (Phase 1) — **BLOQUEIA** todas as histórias de usuário.
- **User Story 1 (Phase 3)**: Depende de Foundational (Phase 2).
- **User Story 2 (Phase 4)**: Depende de Foundational (Phase 2). Pode executar em paralelo ou após US1.
- **User Story 3 (Phase 5)**: Depende de US1 e US2 (necessita de `assets` e `locations`).
- **User Story 4 (Phase 6)**: Depende de US1 (necessita de `assets`).
- **Polish (Phase 7)**: Depende da conclusão de todas as histórias desejadas.

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
