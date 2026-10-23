# Especificação: Refatoração do Modelo de Banco de Dados e Camada de Domínio

## 1. Visão Geral

Esta especificação define a refatoração estrutural da camada de persistência e modelos de domínio da aplicação de Gestão de Patrimônio. A nova modelagem substitui o armazenamento de tags livres e dados soltos em formato texto (`string`) por catálogos normalizados e extensíveis (`equipment_types`, `sectors`, `equipment_statuses`, `maintenance_types`), introduz controle de *Soft Delete* com regras estritas de unicidade permanente e condicional, reforça tipos nativos do PostgreSQL (`inet`, `macaddr`), formaliza o ciclo de vida de manutenções e o encadeamento cronológico de transferências de setor, e remove artefatos fora do escopo (módulo de tickets e tags não estruturadas), assegurando conformidade estrita com a Constituição do Projeto, `Comunica_Patrimonio.dbml` e `Comunica_Patrimonio_constraints.sql`.

---

## 2. Regras de Negócio &amp; Restrições de Domínio

### 2.1 Controle de Usuários e Perfis (RBAC Simplificado)

- \*\*RN-REF-01 (Perfil Único de Técnico):\*\* Nesta fase do sistema, apenas a role `tecnico` é permitida. A restrição é assegurada tanto na aplicação quanto no banco via restrição `CHECK (role = 'tecnico')`.

- \*\*RN-REF-02 (Unicidade e Soft Delete de Usuários):\*\*

  - O e-mail do usuário possui unicidade *case-insensitive* permanente via índice funcional `LOWER(email)`.

  - A exclusão de usuários é estritamente lógica (`deleted_at`), preservando o histórico de auditoria de manutenções e movimentações realizadas pelo técnico.

  - E-mails de usuários excluídos permanecem reservados no sistema e não podem ser reutilizados.

### 2.2 Auditoria de Acesso e Rate Limiting

- \*\*RN-REF-03 (Auditoria de Tentativas de Login):\*\*

  - Toda tentativa de login registra o endereço IP (`inet`), o e-mail informado (`email_attempted`), o timestamp (`attempted_at`) e o status de sucesso ou falha (`success`).

  - O registro nunca armazena a senha informada.

  - Registros de auditoria são imutáveis e não oferecem exclusão pela interface.

- \*\*RN-REF-04 (Rate Limiting de Autenticação):\*\*

  - O bloqueio de força bruta avalia tentativas de falha por IP (limite de 10 tentativas falhas na janela de 15 minutos), utilizando o campo `email_attempted` para auditoria e rastreamento administrativo.

### 2.3 Catálogos Normalizados Extensíveis

- \*\*RN-REF-05 (Catálogos Estruturais):\*\*

  - O sistema substitui a antiga tabela `equipment_tags` por 4 entidades dedicadas:

    1. `equipment_types` (Tipos de Equipamento: ex. Desktop, Notebook, Monitor, Impressora);

    2. `sectors` (Setores / Localizações: ex. TI, Comunicação, Rádio Produção, Almoxarifado);

    3. `equipment_statuses` (Situações Patrimoniais: Em uso, Em manutenção, Baixado, Ocioso, Aguardando recolhimento, Alienação, Exposição, Acautelado);

    4. `maintenance_types` (Tipos de Manutenção: Preventiva, Corretiva).

- \*\*RN-REF-06 (Unicidade Permanente de Nomes em Catálogos):\*\*

  - Cada catálogo possui índice de unicidade permanente *case-insensitive* sobre o nome padronizado (`LOWER(name)`).

  - Um nome de catálogo não pode ser duplicado mesmo que o registro anterior esteja com exclusão lógica (`deleted_at IS NOT NULL`).

- \*\*RN-REF-07 (Soft Delete e Restauração de Catálogos):\*\*

  - A exclusão de um item de catálogo é puramente lógica (`deleted_at = now()`).

  - Itens desativados são omitidos automaticamente de novas seleções em formulários, mas mantêm integridade referencial com os ativos e históricos existentes.

  - O sistema permite a restauração de itens previamente excluídos via ação administrativa (`deleted_at = NULL`).

### 2.4 Ativos e Equipamentos de TI

- \*\*RN-REF-08 (Identificadores e Unicidades de Equipamento):\*\*

  - `patrimony_number`: Obrigatório (`NOT NULL`) e único em todo o sistema (\*case-insensitive\* `LOWER(patrimony_number)`), permanecendo reservado mesmo após exclusão lógica do bem (não reutilizável).

  - `serial_number`: Opcional (`NULL`), porém quando preenchido possui unicidade *case-insensitive* permanente no banco (`LOWER(serial_number)`), permanecendo reservado mesmo após exclusão lógica.

  - `hostname`: Opcional (`NULL`), com unicidade *case-insensitive* (`LOWER(hostname)`) restrita a equipamentos ativos (`deleted_at IS NULL`).

  - `ip_address`: Opcional (`NULL`), tipo nativo PostgreSQL `inet`, restrito estritamente a endereços de host (`/32` para IPv4 ou `/128` para IPv6 via `CHECK chk_equipments_ip_host_only`). Único entre equipamentos ativos (`deleted_at IS NULL`).

  - `mac_address`: Opcional (`NULL`), tipo nativo PostgreSQL `macaddr`. Único entre equipamentos ativos (`deleted_at IS NULL`).

  - `printer_identifier`: Opcional (`NULL`), identificador alfanumérico único (\*case-insensitive\* `LOWER(printer_identifier)`) entre equipamentos ativos (`deleted_at IS NULL`).

- \*\*RN-REF-09 (Vínculos de Domínio Obrigatórios):\*\*

  - Todo equipamento deve obrigatoriamente estar associado a:

    - Um tipo de equipamento válido (`equipment_type_id -> equipment_[types.id](http://types.id)`);

    - Um setor atual (`sector_id -> [sectors.id](http://sectors.id)`);

    - Uma situação patrimonial válida (`status_id -> equipment_[statuses.id](http://statuses.id)`).

- \*\*RN-REF-10 (Substituição de Campos Obsoletos):\*\*

  - O antigo campo `product_number` é formalmente substituído por `model` (modelo comercial do fabricante).

  - A coluna `description` torna-se opcional (`NULL`).

- \*\*RN-REF-11 (Criptografia Segura da Chave Windows):\*\*

  - A coluna `windows_key` em texto simples é substituída por `windows_product_key_encrypted` (armazenamento estrito de *ciphertext* encriptado simetricamente via Fernet/AES autenticado no módulo de segurança).

  - As listagens e visualizações comuns retornam o valor mascarado (`••••••••••••••••`), exigindo ação/endpoint autenticado explícito para decriptografia temporária.

- \*\*RN-REF-12 (Soft Delete e Restauração de Equipamentos):\*\*

  - Equipamentos excluídos recebem marcação `deleted_at = now()`.

  - Consultas operacionais regulares (listagens, filtros, contagens do dashboard) filtram estritamente `deleted_at IS NULL`.

  - A exclusão lógica não apaga os históricos associados de movimentações ou manutenções.

  - Equipamentos excluídos podem ser restaurados (`deleted_at = NULL`), devendo o sistema validar (e retornar HTTP 409 Conflict caso ocorra colisão) se algum de seus identificadores únicos parciais (`hostname`, `ip_address`, `mac_address`, `printer_identifier`) tiver sido atribuído a outro equipamento ativo no período em que esteve inativo.

### 2.5 Histórico e Encadeamento de Movimentações (`equipment_movements`)

- \*\*RN-REF-13 (Criação de Movimentação e Restrições Básicas):\*\*

  - O cadastro inicial de um equipamento não gera registro de movimentação; o setor inicial é atribuído diretamente em `equipments.sector_id`.

  - Uma movimentação registra a transferência concluída de um equipamento entre um setor de origem (`origin_sector_id`) e um setor de destino (`destination_sector_id`).

  - Restrição `CHECK`: O setor de origem deve ser obrigatoriamente diferente do setor de destino (`origin_sector_id <> destination_sector_id`).

  - Restrição de Data: A data da movimentação (`movement_date`) não pode ser futura, admitindo margem máxima de 5 minutos no banco (`movement_date <= now() + interval '5 minutes'`) para tolerância a descompasso de relógio (\*clock skew\*).

  - Responsável: Registra obrigatoriamente o técnico autenticado que realizou a operação (`performed_by_user_id -> [users.id](http://users.id)`).

- \*\*RN-REF-14 (Imutabilidade Operacional e Proibição de Exclusão):\*\*

  - Movimentações de equipamentos não oferecem opção de exclusão pela interface, preservando a trilha de auditoria patrimonial.

- \*\*RN-REF-15 (Integridade da Cadeia e Inclusões Retroativas):\*\*

  - Quando uma nova movimentação é inserida ou uma movimentação existente é editada:

    1. O histórico completo de movimentações do equipamento é ordenado cronologicamente por `(movement_date ASC, id ASC)`;

    2. O sistema valida e auto-ajusta a cadeia a partir do índice 1 garantindo que o setor de origem de cada registro coincida com o setor de destino do registro imediatamente anterior (`Origem[n] = Destino[n-1]`);

    3. Caso uma movimentação seja inserida antes da primeira movimentação existente (novo índice 0), seu `destination_sector_id` deve conectar-se ao `origin_sector_id` do antigo primeiro registro (ou atualizar a cadeia de forma consistente);

    4. Valida que nenhum elo resultante da cadeia permaneça com `origin_sector_id == destination_sector_id` (retornando erro de validação HTTP 400/422 e abortando a transação caso ocorra);

    5. O setor atual do bem (`equipments.sector_id`) é recalculado e atualizado na mesma transação para coincidir com o `destination_sector_id` da última movimentação da cadeia ordenada.

### 2.6 Ciclo de Vida de Manutenções (`equipment_maintenances`)

- \*\*RN-REF-16 (Ciclo de Vida: Início e Conclusão):\*\*

  - Toda manutenção possui uma data/hora de início (`started_at`), um tipo obrigatório (`maintenance_type_id -> maintenance_[types.id](http://types.id)`) e a referência ao técnico responsável (`performed_by_user_id -> [users.id](http://users.id)`, obrigatória quando acionada por usuário autenticado via API, porém anulável/`NULL` no banco para permitir cargas legadas e seeds).

  - O campo `completed_at` permanece `NULL` enquanto a manutenção estiver em andamento.

  - Restrição `CHECK`: Quando preenchido, `completed_at >= started_at`.

- \*\*RN-REF-17 (Regra de Exclusividade de Manutenção em Aberto):\*\*

  - É permitido no máximo uma única manutenção em andamento por equipamento simultaneamente, garantido via índice parcial único no banco:

    `CREATE UNIQUE INDEX uq_equipment_maintenances_one_open_per_equipment ON equipment_maintenances (equipment_id) WHERE completed_at IS NULL;`

- \*\*RN-REF-18 (Transição de Situação do Equipamento na Manutenção):\*\*

  - Ao registrar o início de uma manutenção (`completed_at IS NULL`), a situação do equipamento (`equipments.status_id`) é atualizada automaticamente para a situação `"Em manutenção"`.

  - Ao concluir uma manutenção (informando `completed_at`), a interface e o caso de uso exigem que o técnico selecione a nova situação do bem (ex.: `"Em uso"`, `"Ocioso"` ou `"Baixado"`).

  - Manutenções não podem ser excluídas pela interface.

### 2.7 Descontinuação de Artefatos Legados

- \*\*RN-REF-19 (Remoção da Tabela Tickets):\*\*

  - O modelo e tabela `Ticket` / `tickets` são integralmente removidos da base de dados e do código de domínio nesta refatoração. As métricas do Dashboard passam a focar exclusivamente em patrimônio (total de ativos, ativos por situação, ativos por tipo/setor e manutenções em aberto).

- \*\*RN-REF-20 (Remoção de `equipment_tags`):\*\*

  - A tabela `equipment_tags` e os endpoints/componentes de tags livres são descartados e substituídos pelas tabelas normalizadas de catálogos.

---

## 3. Estrutura do Banco de Dados &amp; Definições Técnicas

### 3.1 Modelagem Relacional

\*\*[ users ]\*\*

- `id` (PK, int, serial)

- `email` (varchar 255, NOT NULL, UNIQUE, índice funcional `LOWER(email)`)

- `hashed_password` (varchar 255, NOT NULL)

- `role` (varchar 50, NOT NULL, DEFAULT `'tecnico'`, CHECK `role = 'tecnico'`)

- `is_active` (boolean, NOT NULL, DEFAULT `true`)

- `created_at` (timestamptz, NOT NULL, DEFAULT `now()`)

- `deleted_at` (timestamptz, NULL)

\*\*[ equipment_types ]\*\*

- `id` (PK, int, serial)

- `name` (varchar 100, NOT NULL, UNIQUE, índice funcional `LOWER(name)`)

- `created_at` (timestamptz, NOT NULL, DEFAULT `now()`)

- `deleted_at` (timestamptz, NULL)

\*\*[ sectors ]\*\*

- `id` (PK, int, serial)

- `name` (varchar 100, NOT NULL, UNIQUE, índice funcional `LOWER(name)`)

- `created_at` (timestamptz, NOT NULL, DEFAULT `now()`)

- `deleted_at` (timestamptz, NULL)

\*\*[ equipment_statuses ]\*\*

- `id` (PK, int, serial)

- `name` (varchar 100, NOT NULL, UNIQUE, índice funcional `LOWER(name)`)

- `created_at` (timestamptz, NOT NULL, DEFAULT `now()`)

- `deleted_at` (timestamptz, NULL)

\*\*[ maintenance_types ]\*\*

- `id` (PK, int, serial)

- `name` (varchar 100, NOT NULL, UNIQUE, índice funcional `LOWER(name)`)

- `created_at` (timestamptz, NOT NULL, DEFAULT `now()`)

- `deleted_at` (timestamptz, NULL)

\*\*[ equipments ]\*\*

- `id` (PK, int, serial)

- `patrimony_number` (varchar 255, NOT NULL, UNIQUE, índice funcional `LOWER(patrimony_number)` permanente)

- `description` (text, NULL)

- `serial_number` (varchar 255, NULL, UNIQUE, índice funcional `LOWER(serial_number)` permanente onde `NOT NULL`)

- `hostname` (varchar 255, NULL, UNIQUE parcial `LOWER(hostname)` onde `deleted_at IS NULL`)

- `brand` (varchar 255, NULL)

- `model` (varchar 255, NULL)

- `equipment_type_id` (FK -&gt; `equipment_[types.id](http://types.id)`, NOT NULL)

- `sector_id` (FK -&gt; [`sectors.id`](http://sectors.id), NOT NULL)

- `status_id` (FK -&gt; `equipment_[statuses.id](http://statuses.id)`, NOT NULL)

- `ip_address` (inet, NULL, CHECK host-only `/32` ou `/128`, UNIQUE parcial onde `deleted_at IS NULL`)

- `mac_address` (macaddr, NULL, UNIQUE parcial onde `deleted_at IS NULL`)

- `printer_identifier` (varchar 255, NULL, UNIQUE parcial `LOWER(printer_identifier)` onde `deleted_at IS NULL`)

- `windows_product_key_encrypted` (text, NULL)

- `notes` (text, NULL)

- `created_at` (timestamptz, NOT NULL, DEFAULT `now()`)

- `updated_at` (timestamptz, NOT NULL, DEFAULT `now()`, trigger)

- `deleted_at` (timestamptz, NULL)

\*\*[ equipment_movements ]\*\*

- `id` (PK, int, serial)

- `equipment_id` (FK -&gt; [`equipments.id`](http://equipments.id), NOT NULL)

- `origin_sector_id` (FK -&gt; [`sectors.id`](http://sectors.id), NOT NULL)

- `destination_sector_id` (FK -&gt; [`sectors.id`](http://sectors.id), NOT NULL)

- `movement_date` (timestamptz, NOT NULL, DEFAULT `now()`, CHECK `<= now() + interval '5 minutes'`)

- `performed_by_user_id` (FK -&gt; [`users.id`](http://users.id), NOT NULL)

- `notes` (text, NULL)

- `created_at` (timestamptz, NOT NULL, DEFAULT `now()`)

- `updated_at` (timestamptz, NOT NULL, DEFAULT `now()`, trigger)

\*\*[ equipment_maintenances ]\*\*

- `id` (PK, int, serial)

- `equipment_id` (FK -&gt; [`equipments.id`](http://equipments.id), NOT NULL)

- `started_at` (timestamptz, NOT NULL, DEFAULT `now()`)

- `completed_at` (timestamptz, NULL, CHECK `completed_at IS NULL OR completed_at >= started_at`)

- `maintenance_type_id` (FK -&gt; `maintenance_[types.id](http://types.id)`, NOT NULL)

- `performed_by_user_id` (FK -&gt; [`users.id`](http://users.id), NULL)

- `description` (text, NULL)

- `notes` (text, NULL)

- `created_at` (timestamptz, NOT NULL, DEFAULT `now()`)

- `updated_at` (timestamptz, NOT NULL, DEFAULT `now()`, trigger)

\*\*[ login_attempts ]\*\*

- `id` (PK, int, serial)

- `email_attempted` (varchar 255, NOT NULL)

- `ip_address` (inet, NOT NULL)

- `attempted_at` (timestamptz, NOT NULL, DEFAULT `now()`)

- `success` (boolean, NOT NULL, DEFAULT `false`)

### 3.2 Triggers e Funções PL/pgSQL

- Função genérica `set_updated_at()` aplicada via triggers `BEFORE UPDATE` nas tabelas:

  - `equipments` (`trg_equipments_updated_at`)

  - `equipment_movements` (`trg_equipment_movements_updated_at`)

  - `equipment_maintenances` (`trg_equipment_maintenances_updated_at`)

### 3.3 Seeds Iniciais de Catálogos

- `equipment_statuses`: `Em uso`, `Em manutenção`, `Baixado`, `Ocioso`, `Aguardando recolhimento`, `Alienação`, `Exposição`, `Acautelado`.

- `maintenance_types`: `Preventiva`, `Corretiva`.

---

## 4. Adaptação das Camadas de Domínio, Repositórios e Schemas

### 4.1 Schemas Pydantic (`src/domain/[schemas.py](http://schemas.py)`)

- Criação de schemas dedicados para cada catálogo (`EquipmentTypeResponse`, `EquipmentTypeCreate`, `SectorResponse`, `SectorCreate`, `EquipmentStatusResponse`, `EquipmentStatusCreate`, `MaintenanceTypeResponse`, `MaintenanceTypeCreate`).

- Atualização do schema de Equipamento:

  - Substituição de `product_number` por `model`.

  - Substituição de strings simples por referências a IDs na entrada (`equipment_type_id`, `sector_id`, `status_id`) e objetos aninhados na resposta (`equipment_type`, `sector`, `status`).

  - Adição e validação dos campos `ip_address` (host-only), `mac_address` e `printer_identifier`.

  - Tratamento de `windows_product_key`: entrada recebe valor em texto puro para criptografia na camada de aplicação; saída comum retorna indicador/valor mascarado; endpoint/schema específico permite revelação se solicitado pelo técnico autenticado.

- Atualização do schema de Movimentação:

  - `origin_sector_id`, `destination_sector_id`, `movement_date`, `performed_by_user_id`, `notes`.

- Atualização do schema de Manutenção:

  - `started_at`, `completed_at`, `maintenance_type_id`, `performed_by_user_id`, `description`, `notes` (incluindo `new_status_id` no payload de conclusão da manutenção).

- Atualização do schema do Dashboard:

  - Remoção de contagens de tickets; foco em métricas de equipamentos (`equipments_total`, `equipments_in_maintenance`, contagens agrupadas por status, tipos e setores).

### 4.2 Repositórios e Casos de Uso (`src/infrastructure/` e `src/use_cases/`)

- `CatalogsRepository`: Operações de CRUD com suporte a `deleted_at`, busca *case-insensitive* (`LOWER`) e listagem de ativos/inativos.

- `EquipmentRepository`:

  - Aplicação padrão de filtro `deleted_at IS NULL` nas listagens operacionais.

  - Carregamento de relacionamentos (`equipment_type`, `sector`, `status`, históricos) via `selectinload` / `joinedload` para evitar consultas N+1.

  - Ordenação e filtros por múltiplos IDs de tipo, setor e status.

- `MovementsUseCase`:

  - Lógica de ordenação `(movement_date ASC, id ASC)`, auto-ajuste do encadeamento retroativo (`Origem[n] = Destino[n-1]`), validação `origin_sector_id <> destination_sector_id` e recálculo transacional de `equipments.sector_id`.

- `MaintenancesUseCase`:

  - Validação de exclusividade de manutenção aberta e transições automáticas de situação patrimonial (`Em manutenção` na abertura e nova situação selecionada na conclusão).

### 4.3 Impacto em Migrações, Seeds, Planilhas e Testes

- \*\*Alembic (`alembic/versions/`):\*\* Consolidar ou criar a migração refletindo fielmente `Comunica_Patrimonio.dbml` e todas as constraints/índices/triggers de `Comunica_Patrimonio_constraints.sql`, removendo a tabela `tickets` e `equipment_tags`.

- \*\*Seeds e Importação/Exportação ([`seed.py`](http://seed.py), `seed_rich_[data.py](http://data.py)`, `spreadsheet_[parser.py](http://parser.py)`, `spreadsheet_[exporter.py](http://exporter.py)`):\*\* Atualizar para resolver ou criar os registros nos catálogos (`equipment_types`, `sectors`, `equipment_statuses`, `maintenance_types`) via busca *case-insensitive*, mapear `model` no lugar de `product_number` e criptografar chaves do Windows quando presentes.

---

## 5. Cenários de Aceitação (BDD)

### Cenário 1: Cadastro de equipamento com chaves estrangeiras e validação de host IP

- \*\*Dado\*\* que existam os catálogos cadastrados: Tipo "Desktop", Setor "TI" e Situação "Em uso"

- \*\*Quando\*\* o técnico cadastrar um novo equipamento com patrimônio "PAT-001", IP "192.168.1.50", tipo, setor e situação válidos

- \*\*Então\*\* o equipamento deve ser persistido com sucesso vinculado às respectivas chaves estrangeiras

- \*\*E\*\* o endereço IP deve ser validado e salvo como endereço de host válido (`/32`).

### Cenário 2: Rejeição de IP com máscara de sub-rede

- \*\*Dado\*\* que o técnico tente cadastrar um equipamento com o endereço IP "192.168.1.0/24"

- \*\*Quando\*\* a requisição for processada

- \*\*Então\*\* o sistema deve rejeitar a gravação com erro de validação/constraint indicando que apenas endereços de host são permitidos.

### Cenário 3: Unicidade permanente de patrimônio mesmo após exclusão lógica

- \*\*Dado\*\* que o equipamento "PAT-100" tenha sido excluído logicamente (`deleted_at IS NOT NULL`)

- \*\*Quando\*\* o técnico tentar cadastrar um novo equipamento com patrimônio "pat-100" ou "PAT-100"

- \*\*Então\*\* o sistema deve recusar o cadastro acusando violação de unicidade de número de patrimônio.

### Cenário 4: Liberação de hostname após exclusão lógica de equipamento anterior

- \*\*Dado\*\* que o equipamento ativo "SRV-01" possua o hostname "srv-app.local"

- \*\*Quando\*\* o equipamento "SRV-01" for excluído logicamente (`deleted_at = now()`)

- \*\*Então\*\* um novo equipamento deve poder ser cadastrado utilizando o hostname "srv-app.local" sem conflito.

### Cenário 5: Início de manutenção altera situação para 'Em manutenção'

- \*\*Dado\*\* que um equipamento esteja na situação "Em uso" e não possua manutenção em andamento

- \*\*Quando\*\* o técnico registrar o início de uma manutenção corretiva

- \*\*Então\*\* o registro de manutenção deve ser criado com `completed_at = NULL` e `performed_by_user_id` preenchido com o ID do técnico

- \*\*E\*\* a situação do equipamento deve ser alterada automaticamente para "Em manutenção".

### Cenário 6: Impedir abertura de segunda manutenção concorrente no mesmo equipamento

- \*\*Dado\*\* que o equipamento possua uma manutenção aberta (`completed_at IS NULL`)

- \*\*Quando\*\* o técnico tentar abrir uma nova manutenção para o mesmo equipamento

- \*\*Então\*\* o sistema deve rejeitar a operação informando que já existe uma manutenção em andamento.

### Cenário 7: Conclusão de manutenção exige nova situação patrimonial

- \*\*Dado\*\* que o equipamento esteja com manutenção em andamento

- \*\*Quando\*\* o técnico concluir a manutenção informando a data/hora de conclusão e definindo a nova situação como "Em uso"

- \*\*Então\*\* o registro de manutenção deve ter `completed_at` atualizado

- \*\*E\*\* a situação do equipamento deve ser atualizada para "Em uso".

### Cenário 8: Registro de movimentação retroativa intermediária e auto-ajuste da cadeia de setores

- \*\*Dado\*\* que um equipamento tenha sido criado no setor "Almoxarifado"

- \*\*E\*\* possua uma movimentação em 01/10 de "Almoxarifado" para "TI"

- \*\*E\*\* possua uma movimentação em 10/10 de "TI" para "Diretoria" (sendo "Diretoria" o setor atual)

- \*\*Quando\*\* o técnico registrar uma movimentação retroativa com data 05/10 transferindo o equipamento de "TI" para "Comunicação"

- \*\*Então\*\* o sistema deve reordenar a cadeia cronológica (`01/10 -> 05/10 -> 10/10`)

- \*\*E\*\* a movimentação de 10/10 deve ter seu `origin_sector_id` atualizado automaticamente de "TI" para "Comunicação" na mesma transação

- \*\*E\*\* o setor atual do equipamento em `equipments.sector_id` deve permanecer "Diretoria" (destino da movimentação mais recente).

### Cenário 9: Proibição de movimentação para o mesmo setor de origem

- \*\*Dado\*\* que um equipamento esteja localizado no setor "TI"

- \*\*Quando\*\* o técnico tentar registrar uma movimentação com destino também ao setor "TI"

- \*\*Então\*\* a operação deve ser rejeitada com erro indicando que a origem e o destino devem ser setores diferentes.

### Cenário 10: Auditoria de tentativa de login gravando e-mail e IP

- \*\*Dado\*\* que uma tentativa de autenticação ocorra a partir do IP "10.0.0.15" para o e-mail "[tecnico@empresa.com](mailto:tecnico@empresa.com)"

- \*\*Quando\*\* a tentativa for processada (com sucesso ou com senha incorreta)

- \*\*Então\*\* uma linha deve ser persistida na tabela `login_attempts` contendo `email_attempted = "[tecnico@empresa.com](mailto:tecnico@empresa.com)"`, `ip_address = "10.0.0.15"` e o indicador de sucesso correspondente

- \*\*E\*\* a senha informada não deve constar em nenhum campo do banco de dados.