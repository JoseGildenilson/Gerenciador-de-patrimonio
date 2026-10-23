# Plano de Tarefas: Refatoração do Modelo de Banco de Dados e Camada de Domínio

## FASE 1: Persistência, Modelos ORM, Migração Alembic &amp; Triggers (PostgreSQL)

- [x] \*\*TASK-REF-01: Atualização dos Modelos ORM no SQLAlchemy 2.0\*\*

  - \*\*Objetivo:\*\* Refatorar os modelos em `src/domain/[models.py](http://models.py)` refletindo fielmente a especificação, `Comunica_Patrimonio.dbml` e as constraints PostgreSQL.

  - \*\*Detalhamento:\*\*

    - Criar novos modelos de catálogo:

      - `EquipmentType` (`equipment_types`): `id`, `name` (unique, índice funcional lower), `created_at`, `deleted_at`.

      - `Sector` (`sectors`): `id`, `name` (unique, índice funcional lower), `created_at`, `deleted_at`.

      - `EquipmentStatus` (`equipment_statuses`): `id`, `name` (unique, índice funcional lower), `created_at`, `deleted_at`.

      - `MaintenanceType` (`maintenance_types`): `id`, `name` (unique, índice funcional lower), `created_at`, `deleted_at`.

    - Atualizar `User` (`users`):

      - Adicionar `deleted_at: Mapped[datetime | None]`.

      - Reforçar `CHECK` constraint `chk_users_role_tecnico` (`role = 'tecnico'`).

      - Configurar índice funcional de unicidade `LOWER(email)`.

    - Atualizar `LoginAttempt` (`login_attempts`):

      - Adicionar `email_attempted: Mapped[str] = mapped_column(String(255), nullable=False)`.

      - Atualizar `ip_address` para tipo nativo `INET` do PostgreSQL (`sqlalchemy.dialects.postgresql.INET`).

    - Atualizar `Equipment` (`equipments`):

      - Substituir strings soltas por chaves estrangeiras obrigatórias (`NOT NULL`): `equipment_type_id` (`equipment_[types.id](http://types.id)`), `sector_id` ([`sectors.id`](http://sectors.id)), `status_id` (`equipment_[statuses.id](http://statuses.id)`).

      - Substituir `product_number` por `model: Mapped[str | None]`.

      - Tornar `description` opcional (`Mapped[str | None]`).

      - Substituir `windows_key` por `windows_product_key_encrypted: Mapped[str | None]`.

      - Adicionar campos de rede e impressão: `ip_address` (`INET`), `mac_address` (`MACADDR`), `printer_identifier` (`String(255)`).

      - Adicionar `updated_at` e `deleted_at` (\*soft delete\*).

      - Configurar relacionamentos ORM com `selectinload` para os catálogos e históricos.

    - Atualizar `EquipmentMovement` (`equipment_movements`):

      - Atualizar FKs obrigatórias (`NOT NULL`): `origin_sector_id` ([`sectors.id`](http://sectors.id)), `destination_sector_id` ([`sectors.id`](http://sectors.id)), `performed_by_user_id` ([`users.id`](http://users.id)).

      - Adicionar `updated_at`.

    - Atualizar `EquipmentMaintenance` (`equipment_maintenances`):

      - Substituir `maintenance_date` por `started_at: Mapped[datetime]` e `completed_at: Mapped[datetime | None]`.

      - Substituir string de tipo por FK obrigatória `maintenance_type_id` (`maintenance_[types.id](http://types.id)`).

      - Adicionar `performed_by_user_id: Mapped[int | None]` ([`users.id`](http://users.id), anulável no banco para cargas legadas/seeds).

      - Adicionar `updated_at`.

    - Remover do arquivo `src/domain/[models.py](http://models.py)`:

      - Remover classe `Ticket` e tabela `tickets`.

      - Remover classe `EquipmentTag` e tabela `equipment_tags`.

- [x] \*\*TASK-REF-02: Migração Incremental no Alembic\*\*

  - \*\*Objetivo:\*\* Criar nova revisão no Alembic encadeada em `a1b2c3d4e5f6` contendo todos os DDLs, constraints, triggers, seeds de catálogo e remoção de tabelas legadas.

  - \*\*Detalhamento:\*\*

    - Criar script de migração em `alembic/versions/` com `down_revision = 'a1b2c3d4e5f6'`.

    - Remover as tabelas legadas `tickets` e `equipment_tags`.

    - Criar as tabelas de catálogos (`equipment_types`, `sectors`, `equipment_statuses`, `maintenance_types`).

    - Antes de aplicar as novas colunas/FKs `NOT NULL` em `equipments`, `equipment_movements`, `equipment_maintenances` e `login_attempts`, executar `TRUNCATE` / `DELETE` nos registros legados incompatíveis para evitar violação de integridade durante a migração.

    - Implementar alterações estruturais em `users`, `equipments`, `equipment_movements`, `equipment_maintenances` e `login_attempts`.

    - Criar constraints `CHECK`:

      - `chk_users_role_tecnico`: `role = 'tecnico'`.

      - `chk_equipments_ip_host_only`: `ip_address IS NULL OR (family(ip_address) = 4 AND masklen(ip_address) = 32) OR (family(ip_address) = 6 AND masklen(ip_address) = 128)`.

      - `chk_movement_different_sectors`: `origin_sector_id <> destination_sector_id`.

      - `chk_movement_date_not_future`: `movement_date <= (now() + interval '5 minutes')`.

      - `chk_maintenance_completion_after_start`: `completed_at IS NULL OR completed_at >= started_at`.

    - Criar índices compostos, únicos funcionais e parciais no PostgreSQL:

      - Índice composto em `equipment_movements (equipment_id, movement_date, id)`.

      - `uq_equipment_maintenances_one_open_per_equipment ON equipment_maintenances (equipment_id) WHERE completed_at IS NULL`.

      - `uq_users_email_lower ON users (LOWER(email))`.

      - `uq_equipment_types_name_lower`, `uq_sectors_name_lower`, `uq_equipment_statuses_name_lower`, `uq_maintenance_types_name_lower` sobre `(LOWER(name))`.

      - `uq_equipments_patrimony_number_lower ON equipments (LOWER(patrimony_number))`.

      - `uq_equipments_serial_number_lower ON equipments (LOWER(serial_number)) WHERE serial_number IS NOT NULL`.

      - `uq_equipments_hostname_active ON equipments (LOWER(hostname)) WHERE deleted_at IS NULL AND hostname IS NOT NULL`.

      - `uq_equipments_ip_address_active ON equipments (ip_address) WHERE deleted_at IS NULL AND ip_address IS NOT NULL`.

      - `uq_equipments_mac_address_active ON equipments (mac_address) WHERE deleted_at IS NULL AND mac_address IS NOT NULL`.

      - `uq_equipments_printer_identifier_active ON equipments (LOWER(printer_identifier)) WHERE deleted_at IS NULL AND printer_identifier IS NOT NULL`.

    - Criar função PL/pgSQL `set_updated_at()` e registrar triggers `BEFORE UPDATE` (`trg_equipments_updated_at`, `trg_equipment_movements_updated_at`, `trg_equipment_maintenances_updated_at`).

    - Inserir carga inicial (`INSERT ... ON CONFLICT (name) DO NOTHING`) para `equipment_statuses` (`Em uso`, `Em manutenção`, `Baixado`, `Ocioso`, `Aguardando recolhimento`, `Alienação`, `Exposição`, `Acautelado`) e `maintenance_types` (`Preventiva`, `Corretiva`).

---

## FASE 2: Segurança, Criptografia &amp; Schemas Pydantic

- [x] \*\*TASK-REF-03: Módulo de Criptografia e Mascaramento de Chaves Windows\*\*

  - \*\*Objetivo:\*\* Implementar em `src/core/[security.py](http://security.py)` as rotinas criptográficas simétricas autenticadas e mascaramento de exibição para `windows_product_key`.

  - \*\*Detalhamento:\*\*

    - Adicionar suporte a criptografia simétrica usando `cryptography.fernet.Fernet`, derivando deterministicamente uma chave válida de 32 bytes em Base64 URL-safe a partir de `settings.SECRET_KEY` via `base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest())`.

    - Implementar `encrypt_windows_product_key(plain_key: str | None) -> str | None`.

    - Implementar `decrypt_windows_product_key(encrypted_key: str | None) -> str | None`.

    - Implementar `mask_windows_product_key(encrypted_or_plain_key: str | None) -> str | None` retornando `"••••••••••••••••"` quando houver chave cadastrada e `None` quando vazia.

- [x] \*\*TASK-REF-04: Atualização dos Schemas Pydantic (`src/domain/[schemas.py](http://schemas.py)`)\*\*

  - \*\*Objetivo:\*\* Ajustar DTOs de entrada e resposta para refletir a nova estrutura de dados, catálogos e novos campos de rede/licença.

  - \*\*Detalhamento:\*\*

    - Criar schemas para os catálogos estruturais:

      - `CatalogItemResponse`: `id`, `name`, `created_at`, `deleted_at`.

      - `CatalogItemCreate`: `name` (validação `min_length=1`, `strip`).

      - `CatalogItemUpdate`: `name` (validação `min_length=1`, `strip`).

      - Schemas tipados derivados para `EquipmentType`, `Sector`, `EquipmentStatus` e `MaintenanceType`.

    - Atualizar schemas de Equipamento:

      - `EquipmentCreate`: `patrimony_number` (obrigatório), `equipment_type_id`, `sector_id`, `status_id`, `description`, `serial_number`, `hostname`, `brand`, `model`, `ip_address` (validação de host-only sem máscara de sub-rede), `mac_address`, `printer_identifier`, `windows_product_key` (texto puro para encriptação), `notes`.

      - `EquipmentUpdate`: campos opcionais permitindo edição e limpeza (`None`) de atributos opcionais.

      - `EquipmentResponse`: inclui objetos aninhados de catálogo (`equipment_type`, `sector`, `status`), `windows_product_key` mascarado por padrão, `created_at`, `updated_at`, `deleted_at`.

      - `EquipmentListItemResponse`: DTO enxuto sem históricos detalhados para performance da listagem paginada.

      - `EquipmentSecretKeyResponse`: DTO específico para retorno da chave de produto decriptografada quando solicitada por técnico autenticado.

    - Atualizar schemas de Movimentação:

      - `EquipmentMovementCreate`: `origin_sector_id`, `destination_sector_id`, `movement_date`, `notes`.

      - `EquipmentMovementUpdate`: `origin_sector_id`, `destination_sector_id`, `movement_date`, `notes`.

      - `EquipmentMovementResponse`: inclui dados dos setores de origem/destino, `performed_by_user_id` e timestamps (`movement_date`, `created_at`, `updated_at`).

    - Atualizar schemas de Manutenção:

      - `EquipmentMaintenanceStart`: `maintenance_type_id`, `started_at` (opcional, default `now()`), `description`, `notes`.

      - `EquipmentMaintenanceComplete`: `completed_at`, `new_status_id` (obrigatório), `description`, `notes`.

      - `EquipmentMaintenanceUpdate`: edição de `maintenance_type_id`, `started_at`, `completed_at`, `description`, `notes`.

      - `EquipmentMaintenanceResponse`: inclui `maintenance_type`, `performed_by_user_id`, datas e notas.

    - Atualizar schemas de Autenticação &amp; Auditoria:

      - `LoginAttemptResponse`: `id`, `email_attempted`, `ip_address`, `attempted_at`, `success`.

    - Atualizar schema do Dashboard:

      - `DashboardMetricsResponse`: remover métricas de tickets; focar em patrimônio (`equipments_total`, `equipments_in_maintenance`, `equipments_in_use`, `equipments_idle`, contagens agrupadas por situação, tipo e setor).

---

## FASE 3: Repositórios de Dados com Suporte a Soft Delete &amp; Catálogos

- [x] \*\*TASK-REF-05: Repositório de Catálogos (`CatalogsRepository`)\*\*

  - \*\*Objetivo:\*\* Implementar operações de persistência para `EquipmentType`, `Sector`, `EquipmentStatus` e `MaintenanceType` em `src/infrastructure/[repositories.py](http://repositories.py)`.

  - \*\*Detalhamento:\*\*

    - Implementar métodos de consulta:

      - `list_active(model_class)`: filtra `deleted_at IS NULL` ordenado por `name`.

      - `list_all(model_class)`: inclui itens excluídos logicamente.

      - `get_by_id(model_class, item_id)`: busca por ID.

      - `get_by_name_lower(model_class, name)`: busca *case-insensitive* por `func.lower(model_[class.name](http://class.name)) == name.lower()`.

    - Implementar métodos de escrita:

      - `create(item)`: persiste novo registro de catálogo.

      - `update(item, new_name)`: atualiza nome do catálogo.

      - `soft_delete(item)`: atribui `deleted_at = now()`.

      - `restore(item)`: restaura item logicamente excluído (`deleted_at = None`).

- [x] \*\*TASK-REF-06: Refatoração do `EquipmentRepository`\*\*

  - \*\*Objetivo:\*\* Atualizar as consultas de equipamentos para suportar o novo modelo, *soft delete* e joins otimizados.

  - \*\*Detalhamento:\*\*

    - Garantir filtro padrão `deleted_at IS NULL` em todas as consultas operacionais (listagens, buscas e contagens).

    - Suportar parâmetro `include_deleted: bool = False` para consultas administrativas/restauração.

    - Configurar carregamento otimizado de relacionamentos (`selectinload([Equipment.equipment](http://Equipment.equipment)_type)`, `selectinload(Equipment.sector)`, `selectinload(Equipment.status)`).

    - Atualizar filtragem múltipla para listas de IDs de catálogos (`equipment_type_ids`, `sector_ids`, `status_ids`) e busca textual.

    - Implementar verificações de unicidade permanente (`patrimony_number`, `serial_number` — *case-insensitive* em toda a tabela) e de unicidade ativa (`hostname`, `ip_address`, `mac_address`, `printer_identifier` — apenas onde `deleted_at IS NULL`).

    - Implementar métodos `soft_delete(equipment)` e `restore(equipment)`.

- [x] \*\*TASK-REF-07: Repositório de Movimentações e Manutenções\*\*

  - \*\*Objetivo:\*\* Adequar operações de persistência e consulta dos históricos de movimentação e manutenção.

  - \*\*Detalhamento:\*\*

    - Movimentações:

      - Método `get_ordered_movements(equipment_id)` retornando todos os registros do equipamento ordenados estritamente por `(EquipmentMovement.movement_date.asc(), [EquipmentMovement.id](http://EquipmentMovement.id).asc())`.

      - Métodos de criação e atualização dentro da mesma transação da sessão.

    - Manutenções:

      - Método `get_open_maintenance(equipment_id)` retornando a manutenção com `completed_at IS NULL`.

      - Método `get_maintenances_by_equipment(equipment_id)` com ordenação decrescente por `started_at`.

- [x] \*\*TASK-REF-08: Atualização do `LoginAttemptRepository`\*\*

  - \*\*Objetivo:\*\* Persistir e auditar tentativas com `email_attempted` e `ip_address` (`INET`).

  - \*\*Detalhamento:\*\*

    - Atualizar método `record_attempt(ip_address: str, email_attempted: str, success: bool)`.

    - Manter método `count_recent_failures(ip_address: str, window_minutes: int)` para verificação de *rate limiting*.

- [x] \*\*TASK-REF-09: Atualização do `DashboardRepository`\*\*

  - \*\*Objetivo:\*\* Substituir métricas de tickets por consolidações patrimoniais (filtrando equipamentos com `deleted_at IS NULL`).

  - \*\*Detalhamento:\*\*

    - Remover todas as consultas à tabela `tickets`.

    - Implementar contagens agregadas de equipamentos ativos por situação (`status`), tipo (`equipment_type`) e setor (`sector`).

    - Implementar contagem de manutenções em aberto (`completed_at IS NULL` em equipamentos ativos).

---

## FASE 4: Casos de Uso de Domínio &amp; Rotas FastAPI

- [x] \*\*TASK-REF-10: Casos de Uso de Equipamentos e Catálogos (`src/use_cases/equipment_use_[cases.py](http://cases.py)`)\*\*

  - \*\*Objetivo:\*\* Atualizar criação, edição, *soft delete*, restauração, gerenciamento de catálogos e revelação de chave Windows.

  - \*\*Detalhamento:\*\*

    - Casos de uso de Catálogos: criar, listar ativos/todos, editar nome (validando unicidade *case-insensitive* permanente), excluir logicamente e restaurar.

    - `CreateEquipmentUseCase`:

      - Validar existência e estado ativo (`deleted_at IS NULL`) de `equipment_type_id`, `sector_id` e `status_id`.

      - Validar formato de IP host-only (`/32` ou `/128`) se informado.

      - Validar unicidades permanentes e ativas.

      - Criptografar `windows_product_key` antes de salvar em `windows_product_key_encrypted`.

    - `UpdateEquipmentUseCase`:

      - Tratar campos opcionais permitindo limpeza (`None`).

      - Validar unicidades caso identificadores sejam alterados.

      - Criptografar nova chave do Windows se fornecida.

    - `DeleteEquipmentUseCase`:

      - Executar *soft delete* (`deleted_at = now()`), preservando históricos.

    - `RestoreEquipmentUseCase`:

      - Restaurar equipamento excluído validando antes se algum identificador único parcial ativo (`hostname`, `ip_address`, `mac_address`, `printer_identifier`) foi ocupado por outro equipamento ativo no período; lançar erro de conflito (HTTP 409 Conflict) caso haja colisão.

    - `GetDecryptedWindowsKeyUseCase`:

      - Decriptografar e retornar a chave do Windows para o técnico autenticado.

- [x] \*\*TASK-REF-11: Caso de Uso de Encadeamento de Movimentações (`MovementsUseCase`)\*\*

  - \*\*Objetivo:\*\* Implementar regras estritas de encadeamento cronológico e recálculo transacional do setor atual.

  - \*\*Detalhamento:\*\*

    - Validar que `origin_sector_id <> destination_sector_id`.

    - Validar que `movement_date` não seja futura (respeitando margem máxima de tolerância).

    - Ao inserir nova movimentação ou editar movimentação existente:

      1. Persistir/atualizar o registro na sessão e buscar todas as movimentações do equipamento ordenadas por `(movement_date ASC, id ASC)`.

      2. A partir do índice `1`, auto-ajustar  `movimento[n].origin_sector_id = movimento[n-1].destination_sector_id`.

      3. Se uma movimentação foi inserida no índice `0` antes de movimentações já existentes, garantir continuidade com o registro seguinte.

      4. Verificar se algum elo da cadeia resultante ficou com `origin_sector_id == destination_sector_id`; caso positivo, abortar a transação e lançar erro de validação (HTTP 400/422).

      5. Atualizar `equipment.sector_id` na mesma transação com o `destination_sector_id` do último elemento da cadeia ordenada.

- [x] \*\*TASK-REF-12: Caso de Uso do Ciclo de Manutenção (`MaintenancesUseCase`)\*\*

  - \*\*Objetivo:\*\* Implementar ciclo de vida com início, conclusão, validação de unicidade e transições de situação.

  - \*\*Detalhamento:\*\*

    - `StartMaintenanceUseCase`:

      - Verificar se já existe manutenção em aberto (`completed_at IS NULL`) para o equipamento; se existir, lançar erro de conflito/regra de negócio (HTTP 400/409).

      - Criar manutenção com `started_at`, `maintenance_type_id` e `performed_by_user_id` do técnico autenticado.

      - Buscar a situação `"Em manutenção"` em `equipment_statuses` e atualizar `equipment.status_id` na mesma transação.

    - `CompleteMaintenanceUseCase`:

      - Validar que a manutenção existe e está em aberto (`completed_at IS NULL`).

      - Validar que `completed_at >= started_at`.

      - Exigir e validar `new_status_id` (garantindo que exista, esteja ativo e não seja `"Em manutenção"`).

      - Atualizar `maintenance.completed_at` e `equipment.status_id = new_status_id` na mesma transação.

    - `UpdateMaintenanceUseCase`:

      - Permitir atualização de `description`, `notes`, `maintenance_type_id` e datas (respeitando `completed_at >= started_at`).

- [x] \*\*TASK-REF-13: Atualização da Autenticação e Rate Limiting (`src/use_cases/authenticate_[user.py](http://user.py)`)\*\*

  - \*\*Objetivo:\*\* Registrar `email_attempted`, validar `deleted_at IS NULL` / `is_active` do usuário e aplicar *rate limit* por IP.

  - \*\*Detalhamento:\*\*

    - Bloquear tentativas vindas de IPs com 10 ou mais falhas nos últimos 15 minutos.

    - Buscar usuário de forma *case-insensitive* (`LOWER(email)`) garantindo `deleted_at IS NULL` e `is_active == True`.

    - Gravar `email_attempted` e `ip_address` em `login_attempts` tanto no sucesso quanto na falha, jamais registrando a senha.

- [x] \*\*TASK-REF-14: Atualização do Caso de Uso de Dashboard (`src/use_cases/get_dashboard_[metrics.py](http://metrics.py)`)\*\*

  - \*\*Objetivo:\*\* Refletir métricas focadas exclusivamente em inventário de patrimônio.

  - \*\*Detalhamento:\*\*

    - Remover cálculos e campos de tickets.

    - Retornar total de ativos, ativos em manutenção, ativos em uso, ativos ociosos e distribuições por tipo e setor.

- [x] \*\*TASK-REF-15: Refatoração das Rotas FastAPI (`src/api/`)\*\*

  - \*\*Objetivo:\*\* Atualizar `src/api/equipment_[routes.py](http://routes.py)`, `src/api/dashboard_[routes.py](http://routes.py)`, `src/api/import_[routes.py](http://routes.py)`, `src/api/[routes.py](http://routes.py)` e `src/api/[dependencies.py](http://dependencies.py)` para expor os novos contratos HTTP.

  - \*\*Detalhamento:\*\*

    - Remover rotas legadas de tags (`/tags`) e qualquer menção a tickets.

    - Criar rotas para os 4 catálogos (`equipment-types`, `sectors`, `equipment-statuses`, `maintenance-types`) permitindo listagem, criação, edição, *soft delete* e restauração.

    - Atualizar rotas de equipamentos para receber/retornar os novos schemas, suportar filtros por múltiplos IDs de catálogos, *soft delete* (`DELETE /equipments/{id}`), restauração (`POST /equipments/{id}/restore` retornando 409 em caso de conflito) e revelação de chave Windows (`GET /equipments/{id}/windows-key`).

    - Atualizar rotas de movimentações (criação e edição com recálculo da cadeia; sem endpoint `DELETE`) e manutenções (início, conclusão com `new_status_id` e edição; sem endpoint `DELETE`).

    - Atualizar rota de login em `src/api/[routes.py](http://routes.py)` para extrair o IP do cliente e repassar `email_attempted` e `ip_address` ao caso de uso.

---

## FASE 5: Cargas de Dados, Seeds &amp; Integração com Planilhas

- [x] \*\*TASK-REF-16: Refatoração dos Seeds da Aplicação (`src/infrastructure/[seed.py](http://seed.py)` e `seed_rich_[data.py](http://data.py)`)\*\*

  - \*\*Objetivo:\*\* Adequar os scripts de inicialização e dados ricos ao novo modelo relacional.

  - \*\*Detalhamento:\*\*

    - Remover qualquer criação de `Ticket` ou `EquipmentTag`.

    - Garantir a carga idempotente dos 4 catálogos (`equipment_types`, `sectors`, `equipment_statuses`, `maintenance_types`).

    - Criar equipamentos de demonstração vinculados às FKs dos catálogos, com `model`, `ip_address` (`/32`), `mac_address` e `windows_product_key_encrypted`.

    - Criar históricos consistentes de movimentações (respeitando `Origem[n] = Destino[n-1]` e `sector_id` final) e manutenções.

- [x] \*\*TASK-REF-17: Atualização dos Utilitários de Planilha (`spreadsheet_[parser.py](http://parser.py)`, `spreadsheet_[exporter.py](http://exporter.py)` e `import_spreadsheet_use_[cases.py](http://cases.py)`)\*\*

  - \*\*Objetivo:\*\* Adaptar a importação e exportação de planilhas Excel/CSV para os catálogos normalizados e novos campos.

  - \*\*Detalhamento:\*\*

    - Importador:

      - Resolver tipo, setor e situação nos catálogos via busca *case-insensitive* (criando automaticamente o item no catálogo caso não exista, ou reativando se aplicável).

      - Mapear modelo comercial para `model` (substituindo `product_number`).

      - Validar e converter `ip_address` (garantindo formato host-only), `mac_address` e `printer_identifier`.

      - Criptografar chaves do Windows presentes na planilha antes de persistir em `windows_product_key_encrypted`.

    - Exportador:

      - Exportar os nomes legíveis de `equipment_[type.name](http://type.name)`, [`sector.name`](http://sector.name) e [`status.name`](http://status.name).

      - Exportar `model`, `ip_address`, `mac_address`, `printer_identifier` e chave Windows mascarada.

---

## FASE 6: Suíte de Testes Automatizados no PostgreSQL (100% de Cobertura)

- [x] \*\*TASK-REF-18: Configuração do Ambiente de Testes para PostgreSQL (`tests/[conftest.py](http://conftest.py)` e CI)\*\*

  - \*\*Objetivo:\*\* Configurar a suíte de testes para rodar sobre PostgreSQL real com isolamento transacional rápido.

  - \*\*Detalhamento:\*\*

    - Configurar engine de testes em `tests/[conftest.py](http://conftest.py)` apontando para banco PostgreSQL de teste (suportando tipos `INET`, `MACADDR`, funções `family()`/`masklen()` e triggers PL/pgSQL).

    - Executar as migrações (`alembic upgrade head`) na preparação do banco de testes.

    - Implementar isolamento entre testes via transações aninhadas (`SAVEPOINT` / `connection.begin_nested()` com `rollback` ao final de cada teste), preservando intactos os seeds iniciais de `equipment_statuses` e `maintenance_types` criados pela migration.

    - Verificar e ajustar `.github/workflows/ci.yml` para garantir serviço `postgres` ativo no job de testes do backend.

- [x] \*\*TASK-REF-19: Testes de Modelos, Constraints, Triggers e Repositórios\*\*

  - \*\*Objetivo:\*\* Validar regras físicas do PostgreSQL e métodos dos repositórios (`tests/test_equipment_[models.py](http://models.py)`, `tests/test_equipment_[repositories.py](http://repositories.py)`, `tests/test_[database.py](http://database.py)`).

  - \*\*Detalhamento:\*\*

    - Testar constraints `CHECK`: IP com máscara `/24` rejeitado (`chk_equipments_ip_host_only`), `origin_sector_id == destination_sector_id` rejeitado, `movement_date` futura além de 5 minutos rejeitada, `completed_at < started_at` rejeitado, `role <> 'tecnico'` rejeitada.

    - Testar triggers de atualização automática de `updated_at` em `equipments`, `equipment_movements` e `equipment_maintenances`.

    - Testar índices únicos permanentes *case-insensitive* (`patrimony_number`, `serial_number`, [`users.email`](http://users.email), nomes de catálogos) mesmo após `deleted_at IS NOT NULL`.

    - Testar índices únicos parciais ativos (`hostname`, `ip_address`, `mac_address`, `printer_identifier`) confirmando liberação após *soft delete*.

    - Testar índice parcial `uq_equipment_maintenances_one_open_per_equipment`.

- [x] \*\*TASK-REF-20: Testes dos Casos de Uso de Domínio e Segurança\*\*

  - \*\*Objetivo:\*\* Validar regras de negócio, criptografia, planilhas e encadeamentos (`tests/test_[security.py](http://security.py)`, `tests/test_equipment_use_[cases.py](http://cases.py)`, `tests/test_import_use_[cases.py](http://cases.py)`, `tests/test_spreadsheet_[parser.py](http://parser.py)`, `tests/test_spreadsheet_[exporter.py](http://exporter.py)`).

  - \*\*Detalhamento:\*\*

    - Testar encriptação, decriptação e mascaramento de `windows_product_key`.

    - Testar criação, edição, *soft delete* e restauração de equipamentos (incluindo erro HTTP 409 quando IP/hostname já estiver em uso por outro ativo).

    - Testar Cenário 8 (movimentação retroativa intermediária): inserção de transferência em `05/10` entre `01/10` e `10/10`, validando reordenação `(movement_date ASC, id ASC)`, auto-ajuste do `origin_sector_id` da movimentação de `10/10` e manutenção do `equipments.sector_id`.

    - Testar ciclo completo de manutenção: abertura mudando status para `"Em manutenção"`, bloqueio de segunda manutenção aberta e conclusão exigindo nova situação patrimonial.

    - Testar parser, importador e exportador de planilhas com os novos catálogos e campos.

- [x] \*\*TASK-REF-21: Testes de Rotas da API, Auditoria de Login e Dashboard\*\*

  - \*\*Objetivo:\*\* Validar contratos HTTP (`tests/test_[api.py](http://api.py)`, `tests/test_equipment_[api.py](http://api.py)`, `tests/test_import_[api.py](http://api.py)`, `tests/test_[dashboard.py](http://dashboard.py)`, `tests/test_rate_[limit.py](http://limit.py)`).

  - \*\*Detalhamento:\*\*

    - Testar endpoints CRUD e restauração dos 4 catálogos.

    - Testar endpoints de equipamentos, movimentações, manutenções e revelação autenticada da chave Windows.

    - Testar gravação de `email_attempted` e `ip_address` em `login_attempts` e bloqueio de *rate limit* após 10 falhas.

    - Testar endpoint do dashboard validando as métricas patrimoniais.

- [x] \*\*TASK-REF-22: Verificação Final de Cobertura e Conformidade Constitucional\*\*

  - \*\*Objetivo:\*\* Assegurar 100% de cobertura de testes e ausência de código morto.

  - \*\*Detalhamento:\*\*

    - Executar a suíte completa com checagem estrita de cobertura de linhas e branches:

      `uv run pytest --cov=src --cov-branch --cov-report=term-missing`

    - Confirmar 100% de cobertura e conformidade integral com a Constituição do Projeto.