# Feature Specification: Gerenciamento de Patrimônio — Modelo de Banco de Dados

**Feature Branch**: `001-gerenciamento-patrimonio`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "Project sispatrimonio com novo modelo de banco de dados para matéria de banco de dados: Enums (user_role, asset_status, maintenance_type), tabelas users, locations, categories, assets, patrimony_history, asset_movements e asset_maintenances."

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

### Edge Cases

- **Exclusão Lógica de Ativos e Usuários**: Ativos e usuários possuem `deleted_at`. Um usuário excluído logicamente não pode receber novas atribuições de custódia de bens (`assigned_user_id`).
- **Categoria exige número de série**: Se `categories.requires_serial_number` for alterado para `true` posteriormente, ativos já existentes sem serial devem manter integridade, mas novas edições e inserções devem exigir o número de série.
- **Transição de Status de Ativo**: Um ativo com status `baixado` não pode ter manutenções abertas nem sofrer transferências para novas localizações ativas sem restauração prévia.
- **Campos Numéricos e Financeiros**: `purchase_cost` e `asset_maintenances.cost` utilizam `numeric(12,2)`, não admitindo valores negativos. `residual_value_rate` deve validar faixa de `0.00` a `100.00`.

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

## Assumptions

- O banco de dados alvo primário é o PostgreSQL 16 (conforme estipulado na Constituição do Projeto e no DBML fornecido).
- As especificações em `specs` (`jsonb`) aceitam qualquer dicionário de pares chave-valor válido em JSON.
- A migração será estruturada de modo a substituir o esquema anterior pelo novo modelo canônico `sispatrimonio`, mantendo compatibilidade de convenções (SQLAlchemy 2.0, Alembic, sem raw SQL).
