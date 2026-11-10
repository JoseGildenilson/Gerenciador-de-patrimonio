# Relatório de Auditoria Completa — Banco de Dados, Backend, Frontend, Testes e Infraestrutura

**Data da Verificação:** 03/11/2026  
**Escopo:** Verificação ponta a ponta após a migração do esquema de banco de dados do modelo legado (`equipments`, `sectors`, `equipment_types`, `equipment_statuses`, `maintenance_types`, `equipment_tags`, `login_attempts`) para o modelo canônico **SisPatrimonio** (`users`, `locations`, `categories`, `assets`, `patrimony_history`, `asset_movements`, `asset_maintenances`).

---

## Resumo Executivo

A causa raiz de grande parte do sistema não funcionar ao subir os containers é uma **desconexão total entre o Frontend e o Backend**, somada a **divergências entre as migrações Alembic, os modelos ORM (`models.py`), o DDL oficial (`database/schema.sql`) e rotas ausentes na API**:

1. **Frontend 100% no modelo legado (`equipments` / `tags`):** O backend teve os módulos `src/api/equipment_routes.py` e `src/api/catalog_routes.py` esvaziados (substituídos por stubs de 1 linha) e passou a expor `/api/v1/assets`, `/api/v1/categories` e `/api/v1/locations`. Porém, **todo o Frontend (`frontend/src/`) continua chamando `/api/v1/equipments` e `/api/v1/equipments/tags`**, recebendo `404 Not Found` em todas as telas (conforme comprovado nos logs do container `patrimonio_backend`).
2. **Bloqueio do perfil `administrador` (RBAC):** O novo banco introduziu o papel `'administrador'` no enum `user_role`, mas o Frontend (`App.tsx`, `DashboardPage.tsx`, `SideMenu.tsx`) e a rota de importação do Backend (`src/api/import_routes.py`) verificam estritamente `role === 'tecnico'`, bloqueando o Administrador de acessar inventário, detalhes e importação.
3. **Funcionalidades do Frontend sem rota correspondente no Backend (ou vice-versa):**
   - Exportação de planilha (`src/infrastructure/spreadsheet_exporter.py` existe, mas não há rota `GET /api/v1/assets/export`).
   - Sugestões de autocomplete (`GET /api/v1/equipments/suggestions` não existe em `asset_routes.py`).
   - Edição/Exclusão de manutenções (`PUT` e `DELETE` chamados pelo frontend não existem em `movement_routes.py`).
   - Listagem de usuários (`GET /api/v1/users`) não existe para popular combos de custodiante (`assigned_user_id`, `from_user_id`, `to_user_id`).
   - Renumeração de patrimônio (`POST /api/v1/assets/{id}/renumber`) e aceite de termo de custódia (`POST /api/v1/movements/{movement_id}/accept-term`) existem no Backend, mas não possuem interface no Frontend.
4. **Divergências no Banco de Dados (Alembic vs `models.py` vs `database/schema.sql`):** Colunas `ENUM` criadas como `VARCHAR(50)` na migração `d4e5f6a7b8c9`, falta de `NULLS NOT DISTINCT` no índice único de `locations`, falta de cláusulas `ON DELETE CASCADE / RESTRICT / SET NULL` e `CheckConstraint`s em `models.py`, e ausência de validação de Enum nos schemas Pydantic (causando erro 500 no PostgreSQL em vez de 422).

---

## 1. Problemas Críticos no Frontend (`frontend/src/`)

### 1.1. Cliente HTTP apontando para rotas extintas (`/api/v1/equipments`)
- **Arquivo:** [equipmentApi.ts](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/api/equipmentApi.ts#L14-L154)
- **Problema:** `equipmentHttpClient` usa `baseURL: '${API_BASE_URL}/api/v1/equipments'`. Todas as chamadas retornam `404 Not Found` no backend:
  - `GET /api/v1/equipments` → deveria consumir `GET /api/v1/assets`
  - `GET /api/v1/equipments/{id}` → deveria consumir `GET /api/v1/assets/{id}` (e buscar movimentações/manutenções)
  - `POST /api/v1/equipments` → deveria consumir `POST /api/v1/assets`
  - `PUT /api/v1/equipments/{id}` → deveria consumir `PUT /api/v1/assets/{id}`
  - `GET / POST / PUT / DELETE /api/v1/equipments/tags` → **rota inexistente**; no novo banco não existe tabela `tags`:
    - Categorias ficam em `/api/v1/categories`
    - Localizações físicas ficam em `/api/v1/locations`
    - Situações (`status`) são valores fixos do Enum `asset_status` (`disponivel`, `em_uso`, `em_manutencao`, `baixado`)
  - `POST /api/v1/equipments/{id}/movements` → deveria ser `POST /api/v1/assets/{id}/movements`
  - `POST /api/v1/equipments/{id}/maintenances` → deveria ser `POST /api/v1/assets/{id}/maintenances`
  - `PUT / DELETE /api/v1/equipments/{id}/maintenances/{maintenanceId}` → rotas inexistentes no backend
  - `GET /api/v1/equipments/suggestions` → rota inexistente no backend
  - `GET /api/v1/equipments/export` → rota inexistente no backend
- **Correção necessária:** Refatorar a camada de API do frontend para os endpoints canônicos (`/api/v1/assets`, `/api/v1/categories`, `/api/v1/locations`, `/api/v1/movements`) e alinhar payloads e query params.

### 1.2. Perfil `administrador` bloqueado no Frontend
- **Arquivos:**
  - [auth.ts](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/types/auth.ts#L1-L8)
  - [App.tsx](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/App.tsx#L26-L69)
  - [DashboardPage.tsx](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/pages/DashboardPage.tsx#L11-L65)
  - [SideMenu.tsx](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/components/SideMenu.tsx#L51-L167)
- **Problema:**
  - `App.tsx` exige `requiredRole="tecnico"` com comparação estrita `user?.role !== requiredRole`. Quando o usuário loga com `admin@sispatrimonio.edu.br` (`role: "administrador"`), ele é impedido de acessar `/equipamentos`, `/equipamentos/:id` e `/importar`.
  - `DashboardPage.tsx` e `SideMenu.tsx` usam `const isTecnico = user?.role === 'tecnico'`. O `administrador` cai na visualização restrita de `colaborador` e não vê os itens do menu lateral nem o card de acesso ao inventário.
  - `User` em `auth.ts` não declara o campo `name: string` retornado pelo backend nem inclui `'administrador'` explicitamente na união `UserRole`.
- **Correção necessária:** Permitir `user?.role === 'tecnico' || user?.role === 'administrador'` em `ProtectedRoute`, `DashboardPage` e `SideMenu`, e atualizar `types/auth.ts`.

### 1.3. Tipos TypeScript defasados em relação às 7 tabelas do Banco
- **Arquivos:**
  - [equipment.ts](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/types/equipment.ts#L1-L107)
  - [dashboard.ts](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/types/dashboard.ts#L1-L5)
  - [importApi.ts](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/api/importApi.ts#L1-L37)
- **Problema:**
  - `types/dashboard.ts` define `tickets_pending` e `tickets_in_progress` (da antiga tabela `tickets` removida), enquanto o backend (`DashboardMetricsResponse`) retorna `assets_total`, `assets_in_maintenance`, `assets_in_use`, `assets_available`, `assets_decommissioned`, `by_status`, `by_category`, `by_location`.
  - `types/equipment.ts` modela a antiga tabela `equipments` (`equipment_type_id`, `sector_id`, `status_id`, `hostname`, `product_number`, `windows_key`, `ip_address`, `mac_address`, `printer_identifier`, `last_maintenance_at`, `notes`) em vez da tabela `assets` (`patrimony_number`, `serial_number`, `description`, `category_id`, `location_id`, `assigned_user_id`, `brand`, `model`, `purchase_cost`, `purchase_date`, `status`, `specs`).
  - `EquipmentMovement` usa `origin_sector_id` / `destination_sector_id` / `performed_by_user_id` em vez de `origin_location_id`, `dest_location_id`, `from_user_id`, `to_user_id`, `moved_by_id`, `term_accepted_at`.
  - `EquipmentMaintenance` usa `maintenance_type_id`, `started_at`, `completed_at`, `notes` em vez de `registered_by_id`, `maintenance_type` (`'preventiva' | 'corretiva'`), `service_provider`, `description`, `cost`, `maintenance_date`.

### 1.4. Tela de Listagem (`EquipmentListPage.tsx`) incompatível com `GET /api/v1/assets`
- **Arquivo:** [EquipmentListPage.tsx](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/pages/EquipmentListPage.tsx#L81-L598)
- **Problema:**
  1. `fetchTags()` chama `equipmentApi.getTags()` (404). Deveria carregar categorias de `GET /api/v1/categories`, localizações de `GET /api/v1/locations` e usar os 4 status do enum `asset_status` (`disponivel`, `em_uso`, `em_manutencao`, `baixado`).
  2. `fetchEquipments()` envia filtros `type[]`, `location[]`, `status[]`, `patrimony_number[]`, `serial_number[]`, `product_number[]`, `sort_by`, `sort_dir`, mas o backend `GET /api/v1/assets` ([asset_routes.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/api/asset_routes.py#L23-L43)) só aceita `page`, `limit`, `category_id: int`, `location_id: int`, `status: str` e `search: str`.
  3. Os cards da listagem tentam exibir `item.equipment_type`, `item.location` e `item.last_maintenance_at`, mas `AssetResponse` retorna apenas `category_id` e `location_id` (numéricos) e não retorna o nome da categoria/localização nem a data da última manutenção.

### 1.5. Modal de Cadastro (`NewEquipmentModal.tsx`) incompatível com `POST /api/v1/assets`
- **Arquivo:** [NewEquipmentModal.tsx](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/components/NewEquipmentModal.tsx#L13-L477)
- **Problema:**
  1. Exige `serial_number` obrigatoriamente no HTML (`required`) e deixa `patrimony_number` e `brand` opcionais, quando no banco `assets` `patrimony_number` e `brand` são `NOT NULL` e `serial_number` só é obrigatório se `category.requires_serial_number == true`.
  2. Envia `status: "Em uso"`, que é inválido para o Enum `asset_status` (`disponivel`, `em_uso`, `em_manutencao`, `baixado`).
  3. Não possui campos para `purchase_cost`, `purchase_date`, `assigned_user_id` e empacotamento de atributos extras (`hostname`, `windows_key`, `notes`, etc.) dentro do JSONB `specs`.
  4. Tenta criar tags inline via `equipmentApi.createTag()`, que falha com 404.

### 1.6. Modal de Gerenciamento de Tags (`ManageTagsModal.tsx`) incompatível com `categories` e `locations`
- **Arquivo:** [ManageTagsModal.tsx](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/components/ManageTagsModal.tsx#L81-L575)
- **Problema:**
  - Tenta listar, criar, renomear e excluir "tags" de 3 abas (`tipo`, `localizacao`, `situacao`) via `/api/v1/equipments/tags`.
  - No novo esquema:
    - **Categorias** (`/api/v1/categories`) possuem `name`, `useful_life_months`, `residual_value_rate` e `requires_serial_number`.
    - **Localizações** (`/api/v1/locations`) são estruturadas com `building` (obrigatório), `floor` (obrigatório), `sector` (obrigatório), `room_number` (opcional) e `description` (opcional).
    - **Situações (Status)** são um `ENUM` fixo do banco (`disponivel`, `em_uso`, `em_manutencao`, `baixado`) e não podem ser criadas, renomeadas ou excluídas pelo usuário.

### 1.7. Página de Detalhes e Modais de Movimentação / Manutenção (`EquipmentDetailPage.tsx`, `MovementModal.tsx`, `MaintenanceModal.tsx`, `EditMaintenanceModal.tsx`)
- **Arquivos:**
  - [EquipmentDetailPage.tsx](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/pages/EquipmentDetailPage.tsx#L109-L1076)
  - [MovementModal.tsx](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/components/MovementModal.tsx#L58-L90)
  - [MaintenanceModal.tsx](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/components/MaintenanceModal.tsx#L48-L73)
  - [EditMaintenanceModal.tsx](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/components/EditMaintenanceModal.tsx#L45-L69)
- **Problema:**
  1. `EquipmentDetailPage` espera que `GET /api/v1/assets/{id}` retorne `movements` e `maintenances` embutidos, mas `AssetDetailResponse` no backend retorna apenas `patrimony_history` (as movimentações e manutenções ficam em `GET /api/v1/assets/{id}/movements` e `GET /api/v1/assets/{id}/maintenances`).
  2. `EquipmentDetailPage` tenta editar `patrimony_number` via `PUT`, mas `AssetUpdate` no backend não aceita `patrimony_number` — a renumeração exige chamada a `POST /api/v1/assets/{id}/renumber` informando `{ new_patrimony_number, reason }`.
  3. Não há exibição do histórico de renumeração (`patrimony_history`), nem dos dados contábeis (`purchase_cost`, `purchase_date`), nem do `specs` (JSONB), nem botão de aceite de termo (`POST /api/v1/movements/{movement_id}/accept-term`).
  4. `MovementModal` envia `origin_sector_id` e `destination_sector_id` em vez de `origin_location_id`, `dest_location_id` (que pode ser `null` para baixa patrimonial), `from_user_id` e `to_user_id`.
  5. `MaintenanceModal` busca tipos de manutenção em `/api/v1/equipments/tags?category=tipo_manutencao` (que falha com 404, deixando o `<select>` vazio!) e envia `maintenance_type_id` e `started_at`, quando o backend exige `maintenance_type` (`'preventiva'` ou `'corretiva'`), `service_provider`, `description`, `cost` e `maintenance_date`.
  6. `EditMaintenanceModal` e o botão de excluir manutenção chamam `PUT` e `DELETE` em `/maintenances/{id}`, que não existem no backend.

### 1.8. Dashboard (`DashboardPage.tsx` e `dashboardApi.ts`) não exibe métricas reais do banco
- **Arquivos:**
  - [DashboardPage.tsx](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/pages/DashboardPage.tsx#L7-L140)
  - [dashboardApi.ts](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/frontend/src/api/dashboardApi.ts#L1-L19)
- **Problema:** O backend possui `GET /api/v1/dashboard/metrics` retornando contagens por status (`assets_total`, `assets_in_use`, `assets_in_maintenance`, `assets_available`, `assets_decommissioned`, `by_category`, `by_location`), mas `DashboardPage.tsx` nem sequer chama `dashboardApi.getMetrics()`.

---

## 2. Problemas no Backend (`src/`)

### 2.1. Módulos Órfãos / Stubs Descontinuados
- **Arquivos:**
  - [equipment_routes.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/api/equipment_routes.py#L1)
  - [catalog_routes.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/api/catalog_routes.py#L1)
  - [equipment_use_cases.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/use_cases/equipment_use_cases.py#L1)
- **Problema:** Arquivos com apenas 1 linha de docstring indicando descontinuação ainda permanecem na árvore `src/`.

### 2.2. Rota de Exportação de Planilha Ausente (`GET /api/v1/assets/export`)
- **Arquivos:**
  - [spreadsheet_exporter.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/infrastructure/spreadsheet_exporter.py#L73-L132)
  - [asset_routes.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/api/asset_routes.py#L1-L125)
- **Problema:** A função `generate_assets_spreadsheet(assets)` já está implementada e adaptada para `Asset`, mas **nenhuma rota HTTP** em `src/api/` a expõe para download pelo frontend.

### 2.3. Rota de Importação bloqueia `administrador` (`403 Forbidden`)
- **Arquivo:** [import_routes.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/api/import_routes.py#L5-L52)
- **Problema:** As rotas `/api/v1/assets/import/preview` e `/api/v1/assets/import/execute` usam `Depends(require_tecnico_role)` (`current_user.role != "tecnico"`), rejeitando usuários com perfil `administrador`. Todas as demais rotas de escrita usam `Depends(require_tecnico_or_admin)`.

### 2.4. Ausência de Validação de Enum nos Schemas Pydantic (Causa Erro 500 no PostgreSQL)
- **Arquivo:** [schemas.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/domain/schemas.py#L163-L284)
- **Problema:**
  - `AssetCreate.status: str = Field(default="disponivel")` e `AssetUpdate.status: str | None = None` aceitam qualquer string no Pydantic. Se um cliente enviar um valor fora de `('disponivel', 'em_uso', 'em_manutencao', 'baixado')`, o PostgreSQL lança `DataError: invalid input value for enum asset_status`, resultando em **HTTP 500 Internal Server Error** em vez de **HTTP 422**.
  - O mesmo ocorre em `AssetMaintenanceCreate.maintenance_type: str` se o valor enviado não for `'preventiva'` ou `'corretiva'`.
- **Correção necessária:** Tipar `status` com `AssetStatus` e `maintenance_type` com `MaintenanceTypeEnum` em `src/domain/schemas.py`.

### 2.5. Atribuição de Custódia a Usuário Inativo (`is_active == False`)
- **Arquivos:**
  - [asset_use_cases.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/use_cases/asset_use_cases.py#L100-L106) e [linhas 161-165](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/use_cases/asset_use_cases.py#L161-L165)
  - [movement_use_cases.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/use_cases/movement_use_cases.py#L71-L75)
- **Problema:** Conforme [data-model.md](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/specs/001-gerenciamento-patrimonio/data-model.md#L148), um usuário custodiante (`assigned_user_id` / `to_user_id`) deve possuir `is_active == true` e `deleted_at == null`. Atualmente `user_repo.get_by_id` verifica apenas `deleted_at.is_(None)`, permitindo atribuir ativos a usuários desativados (`is_active=False`).

### 2.6. Impossibilidade de Limpar Campos Opcionais (`null`) no `AssetUpdate`
- **Arquivo:** [asset_use_cases.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/use_cases/asset_use_cases.py#L161-L193)
- **Problema:** Em `update_asset`, todos os campos usam `if data.<campo> is not None:`. Isso impede que uma requisição `PUT /api/v1/assets/{id}` remova o custodiante (`"assigned_user_id": null`), o modelo (`"model": null`), o custo (`"purchase_cost": null`) ou a data de compra (`"purchase_date": null`). Deve-se verificar `data.model_fields_set`.

### 2.7. Importação de Planilha ignora `requires_serial_number` e não lê Custo/Data de Aquisição
- **Arquivos:**
  - [import_spreadsheet_use_cases.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/use_cases/import_spreadsheet_use_cases.py#L41-L43) e [linhas 131-198](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/use_cases/import_spreadsheet_use_cases.py#L131-L198)
  - [spreadsheet_parser.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/infrastructure/spreadsheet_parser.py#L58-L116)
- **Problema:**
  1. Quando a planilha referencia uma categoria existente que possui `requires_serial_number = True` e a linha não possui `serial_number`, `ExecuteSpreadsheetImportUseCase` insere o ativo com `serial_number = None`, violando `FR-005`.
  2. `spreadsheet_exporter.py` exporta as colunas `CUSTO AQUISIÇÃO`, `DATA AQUISIÇÃO` e `ESPECIFICAÇÕES`, mas `spreadsheet_parser.py` não mapeia essas colunas no cabeçalho, fazendo com que uma planilha exportada pelo sistema perca esses dados ao ser reimportada.

### 2.8. Ausência de Endpoints de Apoio para o Frontend e de Exclusão de Catálogos
- **Arquivos:**
  - [category_routes.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/api/category_routes.py#L1-L67)
  - [location_routes.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/api/location_routes.py#L1-L69)
  - [asset_routes.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/api/asset_routes.py#L23-L76)
- **Problema:**
  1. Não há endpoint `GET /api/v1/users` para listar os usuários ativos na seleção de custodiante (`assigned_user_id`, `from_user_id`, `to_user_id`) no frontend.
  2. Não há `DELETE /api/v1/categories/{id}` nem `DELETE /api/v1/locations/{id}` (com bloqueio `409 Conflict` caso existam ativos vinculados, conforme previsto em `specs/002-purge-legacy-database/spec.md` User Story 3).
  3. `AssetResponse` e `AssetDetailResponse` retornam apenas IDs (`category_id`, `location_id`, `assigned_user_id`), obrigando o frontend a fazer múltiplas requisições extras ou cruzar mapas manualmente para exibir nomes de categoria, localização, custodiante, movimentações e manutenções.

---

## 3. Problemas no Banco de Dados, Modelos ORM e Migrações Alembic

### 3.1. Divergência de Tipos `ENUM` vs `VARCHAR(50)` na Migração `d4e5f6a7b8c9`
- **Arquivo:** [d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/alembic/versions/d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py#L20-L29), [linha 94](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/alembic/versions/d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py#L94) e [linha 155](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/alembic/versions/d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py#L155)
- **Problema:**
  - A migração cria os tipos PostgreSQL `user_role`, `asset_status` e `maintenance_type` (linhas 20–29), mas **não os aplica nas colunas**:
    - `users.role` continua como `VARCHAR(50)` (criada em `001_initial_auth_tables.py` com default `'tecnico'`, enquanto `schema.sql` e `models.py` definem `user_role` com default `'colaborador'`).
    - `assets.status` é criada como `sa.String(length=50)` (linha 94) em vez do Enum `asset_status`.
    - `asset_maintenances.maintenance_type` é criada como `sa.String(length=50)` (linha 155) em vez do Enum `maintenance_type`.
  - Como resultado, um banco criado via `alembic upgrade head` (usado no Docker e no CI) tem esquema diferente de um banco criado via `uv run db-create` (`Base.metadata.create_all`) ou `database/schema.sql`.

### 3.2. Restrição `uq_locations_physical_space` sem `NULLS NOT DISTINCT` no ORM e no Alembic
- **Arquivos:**
  - [schema.sql](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/database/schema.sql#L46)
  - [models.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/domain/models.py#L107-L114)
  - [d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/alembic/versions/d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py#L59-L64)
- **Problema:**
  - `database/schema.sql` define `CONSTRAINT uq_locations_physical_space UNIQUE NULLS NOT DISTINCT (building, floor, sector, room_number)`.
  - Porém, `models.py` e `d4e5f6a7b8c9` criam `Index("uq_locations_physical_space", ..., unique=True)` sem `postgresql_nulls_not_distinct=True`. No PostgreSQL, índices únicos padrão permitem múltiplas linhas duplicadas quando `room_number IS NULL` (violando `FR-003` e `FR-007`).

### 3.3. Cláusulas `ON DELETE` (`CASCADE`, `RESTRICT`, `SET NULL`) ausentes em `src/domain/models.py`
- **Arquivos:**
  - [models.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/domain/models.py#L158-L276)
  - [schema.sql](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/database/schema.sql#L66-L109)
- **Problema:**
  - Em `database/schema.sql`, todas as FKs possuem regras explícitas (`ON DELETE RESTRICT`, `ON DELETE SET NULL`, `ON DELETE CASCADE`).
  - Em `src/domain/models.py`, nenhuma `ForeignKey(...)` define `ondelete=...`. Quando o banco é criado por `uv run db-create` (`Base.metadata.create_all`), todas as FKs ficam sem `ON DELETE CASCADE` ou `ON DELETE SET NULL` no PostgreSQL (confirmado via `\d assets`, `\d asset_movements`, `\d asset_maintenances` e `\d patrimony_history` no container `patrimonio_postgres`).

### 3.4. `CheckConstraint`s e Índices de Performance de `database/schema.sql` ausentes em `models.py` e nas Migrações
- **Arquivos:**
  - [schema.sql](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/database/schema.sql#L53-L54), [linha 71](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/database/schema.sql#L71), [linha 113](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/database/schema.sql#L113), [linhas 119-126](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/database/schema.sql#L119-L126)
  - [models.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/src/domain/models.py#L120-L302)
- **Problema:**
  - `schema.sql` define 4 `CHECK` constraints (`useful_life_months > 0`, `residual_value_rate >= 0.00 AND <= 100.00`, `purchase_cost >= 0.00`, `cost >= 0.00`) e 7 índices (`idx_assets_category_id`, `idx_assets_location_id`, `idx_assets_assigned_user_id`, `idx_assets_status`, `idx_asset_movements_asset_id`, `idx_asset_maintenances_asset_id`, `idx_patrimony_history_asset_id`).
  - Nenhum desses 4 checks ou 7 índices está declarado em `src/domain/models.py` nem na migração `d4e5f6a7b8c9`.

### 3.5. Função PL/pgSQL Órfã `set_updated_at()` no Banco Após Purge
- **Arquivos:**
  - [b2c3d4e5f6a7_refactor_models_catalogs_and_constraints.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/alembic/versions/b2c3d4e5f6a7_refactor_models_catalogs_and_constraints.py#L203-L214)
  - [e5f6a7b8c9d0_purge_legacy_database_tables.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/alembic/versions/e5f6a7b8c9d0_purge_legacy_database_tables.py#L17-L42)
- **Problema:** A migração `b2c3d4e5f6a7` criou a função `set_updated_at()` no PostgreSQL, mas `e5f6a7b8c9d0` removeu apenas as tabelas legadas sem remover a função órfã `set_updated_at()`.

---

## 4. Problemas em Testes, Protótipos e Infraestrutura / Docker

### 4.1. Suíte `tests/e2e/` Quebrada e Ignorada no `pyproject.toml`
- **Arquivos:**
  - [pyproject.toml](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/pyproject.toml#L46)
  - [tests/e2e/conftest.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/tests/e2e/conftest.py#L26-L44)
  - [tests/e2e/test_tier1_feature_coverage.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/tests/e2e/test_tier1_feature_coverage.py#L100-L893)
  - `tests/e2e/test_tier2_boundary_corner.py`, `tests/e2e/test_tier3_cross_feature.py`, `tests/e2e/test_tier4_real_world.py`
- **Problema:** Os testes E2E foram desativados com `--ignore=tests/e2e` no `pyproject.toml` porque ainda instanciam `User(hashed_password=...)` (coluna removida) e chamam `/api/v1/equipments` e `/api/v1/equipments/tags`.

### 4.2. Arquivos de Teste Unitário Descontinuados (Stubs de 1 linha) e Testes do Frontend no Modelo Legado
- **Arquivos no Backend:**
  - [test_equipment_api.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/tests/test_equipment_api.py#L1)
  - [test_equipment_models.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/tests/test_equipment_models.py#L1)
  - [test_equipment_repositories.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/tests/test_equipment_repositories.py#L1)
  - [test_equipment_schemas.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/tests/test_equipment_schemas.py#L1)
  - [test_equipment_use_cases.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/tests/test_equipment_use_cases.py#L1)
  - [test_tags_and_coverage.py](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/tests/test_tags_and_coverage.py#L1)
- **Arquivos no Frontend:**
  - `frontend/src/__tests__/*` (mockam `/api/v1/equipments` e `/api/v1/equipments/tags`, fazendo os testes do Vitest passarem com mocks falsos enquanto a integração real falha com 404).
  - `frontend/src/prototypes/equipment-modal/*` (protótipos baseados no modelo antigo de equipamentos/tags).

### 4.3. Volumes e Nomenclatura nos Arquivos Docker (`docker-compose.yml` e `docker-compose.prod.yml`)
- **Arquivos:**
  - [docker-compose.yml](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/docker-compose.yml#L38-L43)
  - [docker-compose.prod.yml](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/docker-compose.prod.yml#L4-L97)
  - [Dockerfile](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/Dockerfile#L51-L54)
- **Problema:**
  1. `docker-compose.yml` monta `./spec:/app/spec`, mas **não monta `./database:/app/database` nem `./specs:/app/specs`**, e o `Dockerfile` também não copia `database/`. Se `pytest` for executado dentro do container `patrimonio_backend`, `tests/test_seed.py` falha com `FileNotFoundError: database/schema.sql`.
  2. `docker-compose.prod.yml` usa nomes `patrimonio_postgres_prod`, `patrimonio_backend_prod`, `patrimonio_frontend_prod`, `patrimonio_postgres_prod_data`, `patrimonio_net_prod`, divergindo dos identificadores oficiais da Constituição (`GEMINI.md`: `patrimonio_backend`, `patrimonio_frontend`, `patrimonio_postgres`, `patrimonio_net`, `patrimonio_data`).

---

## 5. Plano de Ação Recomendado (Ordem de Execução)

1. **Camada de Banco de Dados e Modelos (`models.py` + Migração Alembic):**
   - Alinhar `src/domain/models.py` e criar/ajustar migração Alembic para garantir que `users.role`, `assets.status` e `asset_maintenances.maintenance_type` usem os tipos ENUM nativos, que `uq_locations_physical_space` tenha `NULLS NOT DISTINCT`, e que todas as FKs (`ondelete`), `CheckConstraint`s e `Index`es de `database/schema.sql` estejam refletidos no ORM e nas migrações.
2. **Camada de Backend (`schemas.py`, `use_cases/`, `api/`):**
   - Validar `AssetStatus` e `MaintenanceTypeEnum` nos schemas Pydantic (`AssetCreate`, `AssetUpdate`, `AssetMaintenanceCreate`).
   - Enriquecer `AssetResponse` / `AssetDetailResponse` (incluindo dados de `category`, `location`, `assigned_user`, `movements`, `maintenances` e `patrimony_history`) para consumo direto pelo Frontend.
   - Expor `GET /api/v1/assets/export` (usando `generate_assets_spreadsheet`), `GET /api/v1/users` (para seleção de custodiante), e `DELETE` em `/api/v1/categories/{id}` e `/api/v1/locations/{id}` (com proteção de integridade referencial).
   - Corrigir `import_routes.py` para usar `require_tecnico_or_admin`, validar `user.is_active` ao atribuir custódia, permitir limpar campos anuláveis em `update_asset` via `model_fields_set` e validar `requires_serial_number` na importação de planilhas.
   - Remover arquivos stubs de 1 linha (`equipment_routes.py`, `catalog_routes.py`, `equipment_use_cases.py`).
3. **Camada de Frontend (`frontend/src/`):**
   - Atualizar `types/`, `api/` (`equipmentApi.ts` / `assetApi.ts`), `App.tsx`, `SideMenu.tsx`, `DashboardPage.tsx`, `EquipmentListPage.tsx`, `EquipmentDetailPage.tsx`, `NewEquipmentModal.tsx`, `ManageTagsModal.tsx` (adaptando para Categorias e Localizações Físicas), `MovementModal.tsx` (com suporte a custodiante e baixa patrimonial) e `MaintenanceModal.tsx` (com `preventiva`/`corretiva`, `service_provider` e `cost`), além de adicionar suporte a renumeração de patrimônio (`POST /api/v1/assets/{id}/renumber`) e aceite de termo (`POST /api/v1/movements/{id}/accept-term`).
   - Liberar acesso completo para o papel `administrador` em todas as rotas e componentes de UI.
4. **Testes e Docker (`tests/`, `frontend/src/__tests__/`, `docker-compose.yml`):**
   - Atualizar os testes do Frontend (`frontend/src/__tests__/`) para os novos contratos de `/api/v1/assets`, `/api/v1/categories` e `/api/v1/locations`.
   - Limpar os arquivos de teste stubs de 1 linha e atualizar `tests/e2e/`.
   - Montar `./database:/app/database` em `docker-compose.yml` e `Dockerfile`.
