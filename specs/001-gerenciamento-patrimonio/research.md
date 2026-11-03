# Phase 0 Research: Gerenciamento de Patrimônio — Modelo de Banco de Dados

**Feature**: `001-gerenciamento-patrimonio`  
**Date**: 2026-10-22  
**Status**: Completed  

---

## 1. Pesquisa & Decisões Arquiteturais

### 1.1. Tratamento de Enums Nativos do PostgreSQL vs SQLite de Teste
- **Contexto**: O DBML define 3 enums: `user_role` (`administrador`, `tecnico`, `colaborador`), `asset_status` (`disponivel`, `em_uso`, `em_manutencao`, `baixado`) e `maintenance_type` (`preventiva`, `corretiva`).
- **Decisão**: Utilizar `sa.Enum` nativo do SQLAlchemy com classes Python `enum.StrEnum` (ou `enum.Enum` com `values_callable=lambda x: [e.value for e in x]`).
- **Configuração**:
  - Declarar `create_type=True` e `name='user_role'` para PostgreSQL.
  - Para o SQLite in-memory de testes, o SQLAlchemy mapeia automaticamente `Enum` como `VARCHAR` com `CHECK constraint`, garantindo paridade funcional sem quebras no fallback de teste.
- **Alternativas Consideradas**:
  - Tabelas de catálogo separadas (como na versão anterior): Rejeitado porque o modelo fornecido pelo usuário e a matéria de banco de dados exigem expressamente Enums PostgreSQL (`Enum user_role`, `Enum asset_status`, `Enum maintenance_type`).

---

### 1.2. Mapeamento de Coluna `specs` (JSONB)
- **Contexto**: A tabela `assets` possui o campo `specs jsonb [not null, default: '{}']` para armazenar especificações flexíveis de equipamentos de TI e outros bens.
- **Decisão**: Mapear como `sa.JSON().with_variant(postgresql.JSONB, "postgresql")` com `server_default=sa.text("'{}'::jsonb")` no PostgreSQL e `server_default=sa.text("'{}'")` no SQLite. Em Python, tipado como `Mapped[dict[str, Any]] = mapped_column(..., default=dict)`.
- **Alternativas Consideradas**:
  - Colunas normais EAV (Entity-Attribute-Value): Rejeitado por complexidade desnecessária e divergência do DBML fornecido.
  - Coluna `Text` com serialização manual: Rejeitado porque o PostgreSQL oferece operadores indexáveis (`->`, `->>`, `@>`) e validação de sintaxe JSON em runtime com `JSONB`.

---

### 1.3. Estratégia de Unicidade Composta em `locations` com Coluna Nullable
- **Contexto**: `locations` possui a restrição `uq_locations_physical_space` sobre `(building, floor, sector, room_number)`. `room_number` é opcional (`null`).
- **Decisão**:
  - No PostgreSQL 15+, restrições únicas com colunas nulas podem utilizar `UNIQUE NULLS NOT DISTINCT (building, floor, sector, room_number)` ou índice funcional com `COALESCE(room_number, '')`.
  - Para garantir portabilidade transparente com o SQLite de testes (que trata cada `NULL` como distinto no índice único padrão), implementar a constraint formal `Index("uq_locations_physical_space", building, floor, sector, func.coalesce(room_number, ""), unique=True)` ou `UNIQUE NULLS NOT DISTINCT` com fallback de teste.
- **Alternativas Consideradas**:
  - Transformar `room_number` em NOT NULL com valor vazio `""`: Rejeitado para preservar a especificação fiel do DBML (`room_number varchar(50) [null]`).

---

### 1.4. Campos Financeiros e Taxas (`numeric(12,2)` e `numeric(5,2)`)
- **Contexto**: `purchase_cost` e `asset_maintenances.cost` utilizam `numeric(12,2)`. `residual_value_rate` utiliza `numeric(5,2)`.
- **Decisão**: No SQLAlchemy, mapear com `sa.Numeric(precision=12, scale=2)` e `sa.Numeric(precision=5, scale=2)`. No Pydantic v2 e domínio, tipar com `Decimal` do módulo nativo `decimal`, validando `residual_value_rate >= 0.00` e `<= 100.00`.
- **Alternativas Consideradas**:
  - `Float`: Rejeitado sumariamente por causar imprecisão de arredondamento em cálculos fiscais e de depreciação.

---

### 1.5. Estratégia de Migração no Alembic
- **Contexto**: A aplicação possui tabelas existentes (`equipments`, `sectors`, `equipment_types`, `equipment_statuses`, etc.). A nova especificação substitui a estrutura pelo projeto `sispatrimonio`.
- **Decisão**: Criar nova migração formal `d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py`:
  1. Cria os novos enums (`user_role`, `asset_status`, `maintenance_type`).
  2. Ajusta `users` para suportar `name`, renomear `hashed_password` para `password_hash` e incluir `administrador` na role.
  3. Cria as novas tabelas: `categories`, `locations`, `assets`, `patrimony_history`, `asset_movements`, `asset_maintenances`.
  4. Migra dados existentes de compatibilidade onde aplicável (ou substitui tabelas legadas garantindo idempotência com `downgrade()`).
- **Alternativas Consideradas**:
  - Alterar migrações antigas retroativamente: Rejeitado pela Constituição do Projeto (migrações passadas são imutáveis e já estão commitadas).

---

### 1.6. Observabilidade e Logging Descritivo de Operações de Banco de Dados
- **Contexto**: Necessidade de demonstrar com clareza em aula e apresentações acadêmicas as operações SQL e transações em tempo real no terminal, sem poluição visual.
- **Decisão**: Implementar listeners de eventos do SQLAlchemy (`event.listens_for(engine, "before_cursor_execute")` e `after_cursor_execute`) em `src/core/database.py`:
  1. **Filtro de Ruído**: Ignorar comandos de healthcheck automáticos (`SELECT 1`).
  2. **Formatação Limpa**: Imprimir prefixo `[SQL QUERY]`, a query formatada, parâmetros e a duração em milissegundos.
  3. **Segurança de Credenciais**: Higienizar parâmetros sensíveis (`password_hash`, senhas, tokens), substituindo seus valores por `[REDACTED]`.
  4. **Ativação Segura**: Controlar o listener através da variável de ambiente `LOG_SQL_STATEMENTS` (ativa por padrão em desenvolvimento e desativada em produção).
- **Alternativas Consideradas**:
  - `echo=True` global no SQLAlchemy: Descartado por gerar poluição excessiva com checkouts de pool de conexão, rollbacks automáticos de leitura e ausência de mascaramento de senhas.
  - Log nativo do PostgreSQL (`log_statement = 'all'`): Descartado porque os healthchecks do Docker (`pg_isready` e `SELECT 1` a cada 5 segundos) inundam o console.

---

### 1.7. Convergência Estrita de Schema entre Alembic, `models.py` e `database/schema.sql`
- **Contexto**: A auditoria completa identificou que a migração `d4e5f6a7b8c9` criou os tipos `ENUM` no PostgreSQL mas declarou `assets.status` e `asset_maintenances.maintenance_type` como `sa.String(length=50)` e manteve `users.role` como `VARCHAR(50)`. Além disso, `uq_locations_physical_space` estava sem `postgresql_nulls_not_distinct=True`, `src/domain/models.py` não declarava `ondelete` (`CASCADE`, `RESTRICT`, `SET NULL`) nas `ForeignKey`s, faltavam os 4 `CheckConstraint`s e os 7 `Index`es de performance de `database/schema.sql`, e a função legada `set_updated_at()` permanecia órfã após o purge.
- **Decisão**:
  - Atualizar `src/domain/models.py` e as migrações Alembic `alembic/versions/d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py` e `alembic/versions/e5f6a7b8c9d0_purge_legacy_database_tables.py` para:
    1. Converter e tipar `users.role` (`user_role`, default `'colaborador'`), `assets.status` (`asset_status`, default `'disponivel'`) e `asset_maintenances.maintenance_type` (`maintenance_type`) com os tipos ENUM nativos no PostgreSQL.
    2. Configurar `postgresql_nulls_not_distinct=True` em `uq_locations_physical_space` (e fallback de validação na camada de aplicação/repositório para SQLite in-memory).
    3. Definir explicitamente `ondelete="RESTRICT"`, `ondelete="SET NULL"` e `ondelete="CASCADE"` em todas as `ForeignKey`s de `src/domain/models.py` e nas migrações, espelhando `database/schema.sql`.
    4. Adicionar os 4 `CheckConstraint`s (`useful_life_months > 0`, `residual_value_rate >= 0.00 AND residual_value_rate <= 100.00`, `purchase_cost >= 0.00`, `cost >= 0.00`) e os 7 índices (`idx_assets_category_id`, `idx_assets_location_id`, `idx_assets_assigned_user_id`, `idx_assets_status`, `idx_asset_movements_asset_id`, `idx_asset_maintenances_asset_id`, `idx_patrimony_history_asset_id`).
    5. Remover a função PL/pgSQL órfã `DROP FUNCTION IF EXISTS set_updated_at() CASCADE` na migração de purge.
- **Rationale**: Garante que bancos criados via `alembic upgrade head`, `uv run db-create` ou `database/schema.sql` produzam exatamente a mesma estrutura relacional no PostgreSQL 16.
- **Alternativas Consideradas**:
  - Manter `VARCHAR(50)` nas migrações e validar apenas no Python: Rejeitado por violar `FR-001` e `SC-001` (exigência acadêmica de tipos ENUM nativos e constraints no SGBD).

---

### 1.8. Completude dos Contratos Backend, RBAC `administrador` e DTOs Enriquecidos
- **Contexto**: O Frontend precisa exibir nomes de categorias, localizações físicas (`building`, `floor`, `sector`, `room_number`), custodiantes (`assigned_user`), data da última manutenção (`last_maintenance_at`), exportar planilha (`.xlsx`), sugerir autocompletes, listar usuários ativos para custódia, excluir categorias/localizações sem uso e editar/excluir registros de manutenção. Adicionalmente, `import_routes.py` bloqueava `administrador` (`403 Forbidden`), `schemas.py` usava `str` em vez de `AssetStatus`/`MaintenanceTypeEnum` (causando erro 500 no PostgreSQL), `update_asset` ignorava `None` explícito e a importação de planilhas ignorava `requires_serial_number`, `purchase_cost`, `purchase_date` e `specs`.
- **Decisão**:
  1. **Validação Estrita de Enums**: Tipar `AssetCreate.status`, `AssetUpdate.status`, `AssetMaintenanceCreate.maintenance_type` e `AssetMaintenanceUpdate.maintenance_type` com `AssetStatus` e `MaintenanceTypeEnum` em `src/domain/schemas.py`.
  2. **DTOs Enriquecidos e Retrocompatíveis**: Incluir objetos aninhados opcionais (`category: CategoryResponse | None`, `location: LocationResponse | None`, `assigned_user: UserSummaryResponse | None`, `last_maintenance_at: datetime | None`) em `AssetResponse`, e `movements: list[AssetMovementResponse]` + `maintenances: list[AssetMaintenanceResponse]` em `AssetDetailResponse` via `selectinload`/`joinedload` no repositório.
  3. **Novos Endpoints Canônicos**:
     - `GET /api/v1/assets/export` (streaming `.xlsx` via `generate_assets_spreadsheet`).
     - `GET /api/v1/assets/suggestions` (valores distintos para autocomplete de busca/filtros).
     - `GET /api/v1/users` (lista usuários com `is_active=True` e `deleted_at IS NULL`).
     - `DELETE /api/v1/categories/{id}` e `DELETE /api/v1/locations/{id}` (retornando `204 No Content` ou `409 Conflict` se houver ativos/movimentações vinculadas).
     - `PUT /api/v1/assets/{id}/maintenances/{maintenance_id}` e `DELETE /api/v1/assets/{id}/maintenances/{maintenance_id}`.
  4. **RBAC e Regras de Negócio**: Substituir `require_tecnico_role` por `require_tecnico_or_admin` em `import_routes.py`; validar `user.is_active` ao atribuir custódia; usar `data.model_fields_set` em `AssetUseCases.update_asset`; validar `requires_serial_number` e mapear `CUSTO AQUISIÇÃO`, `DATA AQUISIÇÃO` e `ESPECIFICAÇÕES` na importação de planilhas.
- **Rationale**: Elimina erros 404/403/500 e permite que o Frontend renderize listagens e detalhes completos sem múltiplas requisições N+1.
- **Alternativas Consideradas**:
  - Recriar a rota antiga `/api/v1/equipments` como proxy: Rejeitado porque a especificação `002-purge-legacy-database` determina o descomissionamento total do modelo legado e o uso exclusivo das 7 entidades do DBML (`assets`, `categories`, `locations`, `patrimony_history`, `asset_movements`, `asset_maintenances`, `users`).

---

### 1.9. Migração Completa do Frontend React para o Modelo Canônico SisPatrimonio
- **Contexto**: Todo o diretório `frontend/src/` ainda consumia `/api/v1/equipments` e `/api/v1/equipments/tags` e bloqueava usuários com `role === 'administrador'`.
- **Decisão**:
  1. Atualizar `frontend/src/types/{auth,dashboard,equipment}.ts` e `frontend/src/api/equipmentApi.ts` para consumir `/api/v1/assets`, `/api/v1/categories`, `/api/v1/locations`, `/api/v1/movements` e `/api/v1/users`.
  2. Liberar o perfil `administrador` em `App.tsx`, `SideMenu.tsx` e `DashboardPage.tsx` (`user?.role === 'tecnico' || user?.role === 'administrador'`).
  3. Conectar `DashboardPage.tsx` a `dashboardApi.getMetrics()` exibindo os indicadores reais do banco (`assets_total`, `assets_in_use`, `assets_in_maintenance`, `assets_available`, `assets_decommissioned`, distribuição por categoria e localização).
  4. Adaptar `EquipmentListPage.tsx`, `NewEquipmentModal.tsx`, `ManageTagsModal.tsx` (gerenciamento estruturado de Categorias com depreciação/serial obrigatório e Localizações com prédio/andar/setor/sala), `EquipmentDetailPage.tsx` (incluindo `specs` JSONB, dados contábeis, renumeração de patrimônio com histórico e aceite de termo de responsabilidade), `MovementModal.tsx` (com `origin_location_id`, `dest_location_id`, `from_user_id`, `to_user_id` e opção de baixa patrimonial) e `MaintenanceModal.tsx` / `EditMaintenanceModal.tsx` (`preventiva`/`corretiva`, `service_provider`, `cost`, `description`, `maintenance_date`).
- **Rationale**: Restaura o funcionamento integral de todas as telas da SPA React em conformidade com o banco de dados PostgreSQL 16.
- **Alternativas Consideradas**:
  - Manter o conceito de "tags" genéricas no frontend e converter para categorias/localizações com valores fictícios de prédio/andar: Rejeitado porque impediria o usuário de informar `useful_life_months`, `residual_value_rate`, `requires_serial_number`, `building`, `floor`, `sector` e `room_number` exigidos pelas User Stories 1 e 2.

---

## 2. Resumo de Decisões Prontas para Fase 1

| Componente | Decisão Final | Rationale |
|---|---|---|
| **Enums** | `sa.Enum(..., native_enum=True)` em `models.py` e nas colunas da migração Alembic | Fidelidade estrita ao DBML `sispatrimonio` e paridade com `database/schema.sql`. |
| **JSONB** | `sa.JSON().with_variant(postgresql.JSONB, "postgresql")` | Compatibilidade híbrida PG 16 e SQLite de testes. |
| **Índice de Localização** | `uq_locations_physical_space` com `postgresql_nulls_not_distinct=True` | Unicidade de espaço físico mesmo quando `room_number IS NULL`. |
| **Integridade & Checks** | `ondelete` (`RESTRICT`, `SET NULL`, `CASCADE`), 4 `CheckConstraint`s e 7 `Index`es no ORM/Alembic | Paridade de 100% entre `alembic upgrade head`, `db-create` e `database/schema.sql`. |
| **Depreciação** | `Decimal` com `Numeric(5,2)` | Precisão contábil para vida útil e valor residual. |
| **Renumeração** | Transação atômica em `patrimony_history` + modal/ação no Frontend | Rastreabilidade total exigida na auditoria patrimonial. |
| **SQL Logging** | Listener SQLAlchemy filtrando `SELECT 1` | Visibilidade clara com métrica de tempo em ms e mascaramento de senhas. |
| **Frontend & RBAC** | Consumo exclusivo de `/api/v1/assets`, `/categories`, `/locations`, `/movements`, `/users` + suporte a `administrador` | Elimina erros 404/403 e integra toda a SPA React às 7 tabelas canônicas. |
