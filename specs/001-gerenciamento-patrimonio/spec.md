# Feature Specification: Gerenciamento de Patrimônio — Modelo de Banco de Dados

**Feature Branch**: `001-gerenciamento-patrimonio`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "Project sispatrimonio com novo modelo de banco de dados para matéria de banco de dados: Enums (user_role, asset_status, maintenance_type), tabelas users, locations, categories, assets, patrimony_history, asset_movements e asset_maintenances."

## Clarifications

### Session 2026-10-31

- Q: Como o sistema deve registrar e exibir as operações de banco de dados nos logs durante a execução da aplicação para a apresentação acadêmica? → A: Listener customizado no SQLAlchemy que exibe SQL limpo, parâmetros e tempo em ms no terminal do backend, filtrando ruídos de healthcheck (`SELECT 1`).
- Q: Como deve ser controlado o acionamento desse log detalhado de operações SQL no sistema? (FR-012) → A: Variável de ambiente configurável (`LOG_SQL_STATEMENTS=true`), ativada por padrão em ambiente de desenvolvimento e desativada em produção.
- Q: Como os valores de parâmetros sensíveis (como hashes de senhas e chaves criptográficas) devem ser tratados na exibição dos logs de SQL? (FR-012) → A: Mascaramento de dados sensíveis (parâmetros como senhas e credenciais são substituídos por `[REDACTED]`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastro e Gestão de Ativos com Categorias e Depreciação (Priority: P1)

Como Administrador ou Técnico de Patrimônio, quero cadastrar e gerenciar ativos vinculados a categorias estruturadas (com regras de vida útil e taxa residual de depreciação) e especificações flexíveis em JSON, para manter o inventário contábil e operacional fiel ao modelo acadêmico do SisPatrimonio.

**Why this priority**: É a espinha dorsal do sistema de patrimônio; sem os ativos e categorias normalizadas, nenhuma movimentação ou manutenção pode ocorrer.

**Independent Test**: Pode ser validado criando categorias com taxa de depreciação e exigência de número de série, cadastrando ativos com dados fiscais (custo e data de aquisição) e especificações técnicas dinâmicas em JSON.

**Acceptance Scenarios**:

1. **Given** que existe a categoria "Notebooks" com `requires_serial_number = true`, **When** um técnico tentar cadastrar um ativo dessa categoria sem informar `serial_number`, **Then** o sistema deve rejeitar o cadastro com erro de validação.
2. **Given** um ativo cadastrado com `patrimony_number = "PAT-2026-001"`, **When** outro cadastro tentar usar o mesmo número de patrimônio, **Then** a operação deve ser rejeitada por violação de unicidade.
3. **Given** um ativo cadastrado com `specs = {"ram": "16GB", "storage": "512GB SSD"}`, **When** o ativo for consultado, **Then** as especificações devem ser recuperadas com integridade semântica em formato estruturado.

---

### User Story 2 - Localização Física Estruturada e Espaço Físico Único (Priority: P2)

Como Técnico ou Administrador, quero organizar os locais físicos por Prédio, Andar, Setor e Sala opcional, garantindo a unicidade do espaço físico para posicionar ativos com exatidão no campus/edifício.

**Why this priority**: Substitui a antiga localização simples/solta por uma hierarquia física consistente que impede duplicação de salas e setores no mesmo edifício.

**Independent Test**: Pode ser validado criando localizações com prédio, andar e setor, e confirmando que repetições exatas da mesma combinação física disparam violação da restrição de unicidade composta.

**Acceptance Scenarios**:

1. **Given** uma localização cadastrada com `building = "Bloco A"`, `floor = "2"`, `sector = "Engenharia"` e `room_number = "204"`, **When** for submetido um novo cadastro com exatamente os mesmos valores, **Then** o sistema deve rejeitar a criação por violação da restrição `uq_locations_physical_space`.
2. **Given** uma localização válida, **When** um ativo for associado a ela, **Then** o ativo deve refletir sua alocação geográfica estruturada.

---

### User Story 3 - Movimentação Física, Transferência de Custódia e Aceite de Termo (Priority: P3)

Como Administrador, Técnico ou Colaborador, quero registrar movimentações de ativos entre locais e transferências de custódia entre colaboradores, com registro do aceite do termo de responsabilidade, para assegurar rastreabilidade jurídica e física dos bens.

**Why this priority**: Garante governança patrimonial, responsabilização do custodiante e controle de baixas patrimoniais.

**Independent Test**: Pode ser testado registrando a transferência de um ativo da localização A para a B, mudando o custodiante de João para Maria e registrando o timestamp do aceite do termo de responsabilidade.

**Acceptance Scenarios**:

1. **Given** um ativo alocado no "Bloco A", **When** o técnico registrar uma movimentação para o "Bloco B" definindo `to_user_id` e data de movimentação, **Then** o histórico de movimentação deve ser persistido e o ativo deve atualizar sua localização atual e seu custodiante atribuído.
2. **Given** um processo de desincorporação/baixa de um bem, **When** a movimentação for registrada com `dest_location_id = null`, **Then** o sistema deve aceitar a baixa e atualizar o status do ativo para `baixado`.
3. **Given** uma movimentação pendente de assinatura, **When** o custodiante confirmar o recebimento do equipamento, **Then** o campo `term_accepted_at` deve ser carimbado com o timestamp atual.

---

### User Story 4 - Rastreabilidade de Renumeração de Patrimônio e Manutenções Técnicas (Priority: P4)

Como Técnico, quero registrar substituições de plaquetas de patrimônio com justificativa formal e documentar manutenções preventivas ou corretivas (com custo e prestador de serviço), para manter o histórico de vida útil e financeiro do bem.

**Why this priority**: Essencial para conformidade com a matéria de banco de dados e auditoria de inventário físico.

**Independent Test**: Pode ser testado alterando a plaqueta de um ativo (registrando o valor antigo, novo e motivo) e inserindo manutenções preventivas com custos associados.

**Acceptance Scenarios**:

1. **Given** um ativo com patrimônio "PAT-001", **When** a placa física for danificada e o técnico registrar a troca para "PAT-002" com o motivo "Plaqueta danificada", **Then** um registro imutável em `patrimony_history` deve ser gravado e o ativo deve passar a ter o patrimônio "PAT-002".
2. **Given** um ativo em uso, **When** for registrada uma manutenção do tipo `corretiva` com `cost = 450.00` e `service_provider = "TechFix Ltda"`, **Then** o registro deve ser associado ao ativo e computado no histórico de intervenções.

---

### User Story 5 - Comandos e Scripts de Criação e Povoamento do Banco de Dados (Priority: P2)

Como Professor avaliador da disciplina de Banco de Dados ou Desenvolvedor do sistema, quero dispor de comandos automatizados na CLI (`uv run db-create` e `uv run db-seed`) e scripts SQL nativos (`database/schema.sql` e `database/populate.sql`), para criar e popular o banco de dados de maneira rápida, reprodutível e independente da ferramenta de execução (psql, DBeaver, pgAdmin ou terminal).

**Why this priority**: Requisito acadêmico obrigatório para entrega e avaliação prática do modelo relacional da disciplina de Banco de Dados.

**Independent Test**: Executar `database/schema.sql` e `database/populate.sql` via psql ou executar `uv run db-create` seguido de `uv run db-seed`, confirmando criação íntegra das tabelas, enums e dados iniciais no PostgreSQL.

**Acceptance Scenarios**:

1. **Given** um banco de dados PostgreSQL vazio, **When** o comando `uv run db-create` for executado, **Then** todos os enums e tabelas do modelo de patrimônio devem ser criados com suas chaves e índices.
2. **Given** um banco criado, **When** o comando `uv run db-seed` for executado, **Then** o sistema deve inserir dados de teste para usuários (admin, técnico, colaborador), categorias, localizações, ativos com JSONB, movimentações e manutenções com sucesso.
3. **Given** os arquivos `database/schema.sql` e `database/populate.sql`, **When** inspecionados ou executados em um cliente SQL padrão (psql / DBeaver), **Then** devem conter a sintaxe DDL e DML pura válida para PostgreSQL 16.

---

### User Story 6 - Observabilidade e Visualização de Operações de Banco nos Logs (Priority: P2)

Como Professor avaliador da disciplina de Banco de Dados ou Desenvolvedor do sistema, quero visualizar nos logs da aplicação as queries SQL executadas a cada requisição (SELECT ao listar, INSERT ao cadastrar, UPDATE/DELETE em alterações) com parâmetros e tempo em ms, de forma limpa e sem poluição de healthcheck, para demonstrar e auditar o funcionamento do banco em tempo real.

**Why this priority**: Requisito essencial para demonstração prática e defesa do projeto na disciplina de Banco de Dados.

**Independent Test**: Executar uma requisição de listagem (`GET /api/v1/assets`) e de cadastro (`POST /api/v1/assets`), confirmando nos logs do terminal a emissão de `[SQL QUERY]` com o SQL executado, duração em ms, sem ocorrência de `SELECT 1` e com campos confidenciais mascarados como `[REDACTED]`.

**Acceptance Scenarios**:

1. **Given** a aplicação executando com `LOG_SQL_STATEMENTS = true`, **When** uma listagem de ativos for solicitada, **Then** o comando `SELECT` gerado deve ser exibido no log formatado com seus parâmetros e tempo de resposta em milissegundos.
2. **Given** um cadastro de usuário ou autenticação com dados de senha, **When** a query for registrada nos logs, **Then** os campos sensíveis (`password_hash`) devem ser automaticamente mascarados como `[REDACTED]`.
3. **Given** o container executando o healthcheck periódico (`SELECT 1`), **When** o comando for executado pelo SGBD, **Then** o listener de log da aplicação deve ignorar essa consulta, evitando poluição visual no terminal.

---

### User Story 7 - Integração Ponta a Ponta do Frontend React e Contratos de API com o Modelo Canônico (Priority: P1)

Como Administrador, Técnico ou Colaborador utilizando a aplicação web React, quero visualizar métricas reais no Dashboard, listar, filtrar, cadastrar, editar, exportar e importar ativos, gerenciar categorias e localizações físicas, registrar movimentações com custodiante e termo de aceite, renumerar plaquetas de patrimônio e lançar manutenções (`preventiva` ou `corretiva`) consumindo exclusivamente os endpoints canônicos (`/api/v1/assets`, `/api/v1/categories`, `/api/v1/locations`, `/api/v1/movements`, `/api/v1/users`, `/api/v1/dashboard/metrics`), sem chamadas legadas a `/api/v1/equipments` ou bloqueio indevido do perfil `administrador`.

**Why this priority**: A interface web precisa refletir integralmente as 7 tabelas e 3 enums do banco de dados para que o sistema opere ponta a ponta sem erros `404 Not Found` ou `403 Forbidden`.

**Independent Test**: Acessar o sistema com `admin@sispatrimonio.edu.br` e `tecnico@sispatrimonio.edu.br`, navegar pelo Dashboard, Inventário de Ativos, Detalhes do Ativo, Modais de Cadastro, Categorias/Localizações, Movimentação, Renumeração, Manutenção e Importação/Exportação de Planilhas, validando que todas as operações persistem no PostgreSQL 16 sem erros HTTP.

**Acceptance Scenarios**:

1. **Given** um usuário autenticado com `role = "administrador"` ou `role = "tecnico"`, **When** acessar o Dashboard, a listagem de ativos (`/equipamentos`), detalhes (`/equipamentos/:id`) ou importação (`/importar`), **Then** o acesso deve ser permitido e os dados das 7 tabelas canônicas devem ser carregados das rotas `/api/v1/assets`, `/api/v1/categories`, `/api/v1/locations` e `/api/v1/dashboard/metrics`.
2. **Given** a listagem de ativos ou página de detalhes, **When** os ativos forem exibidos, **Then** o payload deve incluir os dados expandidos de categoria (`CategoryResponse`), localização física (`LocationResponse`) e custodiante (`UserSummaryResponse`), permitindo visualização imediata de prédio/andar/setor/sala, depreciação e responsável.
3. **Given** a necessidade de gerenciar catálogos no frontend, **When** o técnico ou administrador abrir o gerenciador de Categorias e Localizações, **Then** poderá criar, editar e excluir categorias (`/api/v1/categories`) e localizações físicas (`/api/v1/locations`), recebendo `409 Conflict` caso tente excluir um registro que possua ativos vinculados.
4. **Given** a página de detalhes de um ativo, **When** o técnico ou administrador alterar o número de patrimônio com justificativa, registrar movimentação de local/custodiante (ou baixa patrimonial), aceitar termo de responsabilidade ou lançar/editar/excluir manutenção, **Then** a interface deve invocar os endpoints canônicos correspondentes e atualizar o histórico em tela.

---

### Edge Cases

- **Exclusão Lógica de Ativos e Usuários**: Ativos e usuários possuem `deleted_at`. Um usuário excluído logicamente não pode receber novas atribuições de custódia de bens (`assigned_user_id`).
- **Categoria exige número de série**: Se `categories.requires_serial_number` for alterado para `true` posteriormente, ativos já existentes sem serial devem manter integridade, mas novas edições e inserções devem exigir o número de série.
- **Transição de Status de Ativo**: Um ativo com status `baixado` não pode ter manutenções abertas nem sofrer transferências para novas localizações ativas sem restauração prévia.
- **Campos Numéricos e Financeiros**: `purchase_cost` e `asset_maintenances.cost` utilizam `numeric(12,2)`, não admitindo valores negativos. `residual_value_rate` deve validar faixa de `0.00` a `100.00`.
- **Parâmetros Sensíveis em Logs de Banco**: Na persistência, leitura ou falha de execução envolvendo usuários e credenciais, a higienização de parâmetros (`sanitize_sql_params`) deve substituir valores de colunas e parâmetros protegidos (`password`, `password_hash`, `hash`, `token`, `secret`, `key`) por `[REDACTED]`, tanto em execuções unitárias quanto em lotes (`executemany` no `db-seed` e importação de planilhas).
- **Escopo de Eventos, Transações, Migrações e Fallback de Testes no Log SQL**: O listener é acoplado exclusivamente à `engine` da aplicação (`before_cursor_execute` e `after_cursor_execute`), operando de forma idêntica no PostgreSQL 16 e no fallback SQLite de testes unitários. Comandos implícitos de controle de transação (`BEGIN`, `COMMIT`, `ROLLBACK`), consultas de healthcheck (`SELECT 1`) e execuções externas de DDL via CLI do Alembic não emitem linhas `[SQL QUERY]`, mantendo o log limpo e estritamente focado nas consultas DML/DQL da aplicação.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE adotar PostgreSQL como SGBD com suporte aos Enums nativos: `user_role` (`administrador`, `tecnico`, `colaborador`), `asset_status` (`disponivel`, `em_uso`, `em_manutencao`, `baixado`) e `maintenance_type` (`preventiva`, `corretiva`).
- **FR-002**: O sistema DEVE gerenciar a tabela `users` contendo `name`, `email` único, `password_hash`, `role` (default: `colaborador`), `is_active` e controle de soft delete (`deleted_at`).
- **FR-003**: O sistema DEVE gerenciar a tabela `locations` com restrição de unicidade composta `uq_locations_physical_space` cobrindo `(building, floor, sector, room_number)`.
- **FR-004**: O sistema DEVE gerenciar a tabela `categories` contendo nome único, `useful_life_months`, `residual_value_rate` (0 a 100) e flag booleana `requires_serial_number`.
- **FR-005**: O sistema DEVE validar a obrigatoriedade de `serial_number` no cadastro/edição de ativos caso a categoria associada possua `requires_serial_number = true`.
- **FR-006**: O sistema DEVE armazenar em `assets` o número de patrimônio único, número de série único (se preenchido), descrição, marca, modelo, custo de aquisição, data de aquisição, status do ativo, chave estrangeira para categoria, chave estrangeira para localização, chave estrangeira opcional para usuário atribuído (custodiante), especificações flexíveis em `specs` (`jsonb`) e controle de soft delete.
- **FR-007**: Toda alteração no número de patrimônio de um ativo DEVE gerar atomicamente um registro em `patrimony_history` contendo `asset_id`, `old_patrimony_number`, `new_patrimony_number`, `reason`, `changed_by_id` e timestamp.
- **FR-008**: Toda movimentação de ativo DEVE ser registrada em `asset_movements` contendo `origin_location_id`, `dest_location_id` (anulável para baixa patrimonial), `from_user_id` e `to_user_id` opcionais, `moved_by_id`, `movement_date`, observações e `term_accepted_at` opcional.
- **FR-009**: O sistema DEVE registrar manutenções em `asset_maintenances` contendo `asset_id`, `registered_by_id`, `maintenance_type`, `service_provider` opcional, descrição textual, custo monetário e data da manutenção.
- **FR-010**: O sistema DEVE fornecer comandos CLI (`uv run db-create` e `uv run db-seed`) registrados como entrypoints em `pyproject.toml` para criar tabelas/migrações e popular dados completos do SisPatrimonio.
- **FR-011**: O sistema DEVE fornecer arquivos SQL nativos (`database/schema.sql` e `database/populate.sql`) contendo DDL e DML prontos para execução em clientes SQL padrão para PostgreSQL 16.
- **FR-012**: O sistema DEVE disponibilizar um listener de eventos de execução na `engine` do SQLAlchemy (`before_cursor_execute` e `after_cursor_execute`, compatível com PostgreSQL 16 e SQLite em testes) controlado pela variável de ambiente `LOG_SQL_STATEMENTS` (habilitada por padrão em desenvolvimento `True` e desabilitada em produção `False`) para exibir nos logs do backend todas as queries DML/DQL (`SELECT` em listagens/consultas, `INSERT` em cadastros/movimentações/manutenções e `UPDATE` em edições/renumerações/soft-delete) no formato padronizado `[SQL QUERY] (<duração>ms) SQL: <statement> | PARAMS: <params>`, com parâmetros higienizados (mascaramento automático de `password`, `hash`, `token`, `secret`, `key` via `[REDACTED]` em execuções simples ou em lote) e filtragem estrita de consultas de healthcheck (`SELECT 1`) e ruídos de controle transacional (`BEGIN`/`COMMIT`/`ROLLBACK`).
- **FR-013**: As migrações Alembic (`alembic/versions/`) e os modelos ORM (`src/domain/models.py`) DEVEM refletir com paridade exata o DDL de `database/schema.sql`, incluindo tipos `ENUM` nativos nas colunas (`users.role`, `assets.status`, `asset_maintenances.maintenance_type`), unicidade física `uq_locations_physical_space` com `NULLS NOT DISTINCT`, políticas `ON DELETE` (`RESTRICT`, `SET NULL`, `CASCADE`) nas chaves estrangeiras, `CheckConstraint`s de valores positivos/faixas e índices de performance.
- **FR-014**: Os schemas de entrada da API (`AssetCreate`, `AssetUpdate`, `AssetMaintenanceCreate`, `AssetMaintenanceUpdate`) DEVEM validar estritamente os enums `AssetStatus` e `MaintenanceTypeEnum` via Pydantic v2 (retornando HTTP 422 em valores inválidos), permitir limpeza explícita de campos anuláveis via `model_fields_set` em `PUT /api/v1/assets/{id}` e validar que usuários custodiantes (`assigned_user_id`, `to_user_id`) estejam ativos (`is_active = true` e `deleted_at IS NULL`).
- **FR-015**: O backend DEVE disponibilizar os endpoints de suporte operacional: `GET /api/v1/assets/export` (exportação `.xlsx`), `GET /api/v1/assets/suggestions` (autocomplete de filtros), `GET /api/v1/users` (listagem de usuários ativos para custódia), `DELETE /api/v1/categories/{id}` e `DELETE /api/v1/locations/{id}` (bloqueando exclusão com `409 Conflict` se houver ativos ou movimentações vinculadas), além de `PUT /api/v1/assets/{id}/maintenances/{maintenance_id}` e `DELETE /api/v1/assets/{id}/maintenances/{maintenance_id}`.
- **FR-016**: O controle de acesso RBAC no Backend (incluindo `import_routes.py`) e no Frontend (`App.tsx`, `SideMenu.tsx`, `DashboardPage.tsx`, páginas e modais) DEVE conceder ao papel `administrador` todas as permissões operacionais concedidas ao `tecnico`.
- **FR-017**: A aplicação Frontend React (`frontend/src/`) DEVE consumir exclusivamente os contratos canônicos (`/api/v1/assets`, `/api/v1/categories`, `/api/v1/locations`, `/api/v1/movements`, `/api/v1/users`, `/api/v1/dashboard/metrics`), eliminando chamadas às rotas descontinuadas `/api/v1/equipments` e `/api/v1/equipments/tags`.

### Key Entities *(include if feature involves data)*

- **User**: Usuário do sistema com papéis de `administrador`, `tecnico` ou `colaborador`. Pode ser custodiante de ativos ou responsável por movimentações e manutenções.
- **Location**: Espaço físico do campus identificado por prédio, andar, setor e sala opcional, com unicidade física composta.
- **Category**: Classificação patrimonial com diretrizes contábeis de depreciação e obrigatoriedade de serial.
- **Asset**: Bem patrimonial monitorado com especificações técnicas dinâmicas em JSONB e dados contábeis/fiscais.
- **PatrimonyHistory**: Registro imutável de auditoria de renumerações de patrimônio.
- **AssetMovement**: Registro de transferência de local, custodiante e aceite de termo de responsabilidade.
- **AssetMaintenance**: Registro de intervenção preventiva ou corretiva com prestador e custo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das 7 tabelas e 3 enums do modelo `sispatrimonio` modelados com fidelidade relacional e validados por migração Alembic idempotente (`upgrade` e `downgrade`).
- **SC-002**: Tempo de execução de consultas de ativos filtradas por categoria, localização ou status inferior a 100ms para bases de até 10.000 ativos.
- **SC-003**: 100% das operações de renumeração de patrimônio registradas atomicamente sem perda de rastreabilidade do identificador anterior.
- **SC-004**: Zero violações das restrições de integridade referencial e unicidade física composta em toda a suíte de testes automatizados.
- **SC-005**: Comandos `uv run db-create` e `uv run db-seed` executam sem erros, populando com sucesso todas as entidades do modelo e mantendo cobertura de código em 100%.
- **SC-006**: 100% das operações SQL (`SELECT`, `INSERT`, `UPDATE`/soft-delete) geradas pelas rotas da API (`/api/v1/*`) e comandos são visualizáveis no formato `[SQL QUERY] (<ms>ms) SQL: ...` e verificadas por testes de integração automatizados, com zero vazamento de queries automáticas de healthcheck (`SELECT 1`) ou credenciais em texto claro.
- **SC-007**: 100% das telas, modais e fluxos do Frontend React (`DashboardPage`, `EquipmentListPage`, `EquipmentDetailPage`, `ImportPage`, `NewEquipmentModal`, `ManageTagsModal`, `MovementModal`, `MaintenanceModal`, `EditMaintenanceModal`) operam ponta a ponta sobre os endpoints das 7 tabelas canônicas, com suíte backend (`pytest --cov=src --cov-branch --cov-fail-under=100`), suíte E2E (`tests/e2e/`) e suíte frontend (`npx tsc --noEmit` e `vitest run`) aprovadas sem erros.

## Assumptions

- O banco de dados alvo primário é o PostgreSQL 16 (conforme estipulado na Constituição do Projeto e no DBML fornecido).
- As especificações em `specs` (`jsonb`) aceitam qualquer dicionário de pares chave-valor válido em JSON.
- A migração será estruturada de modo a substituir o esquema anterior pelo novo modelo canônico `sispatrimonio`, mantendo compatibilidade de convenções (SQLAlchemy 2.0, Alembic, sem raw SQL).
