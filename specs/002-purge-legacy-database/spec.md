# Feature Specification: Purge Legacy Database and Strict DBML Alignment

**Feature Branch**: `002-purge-legacy-database`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "Quero fazer a mundança para retirar tudo do banco de dados que não esteja no DBML de exemplo, não devemos mudar nada, deve tem exatamente o mesmo modelo, nada a mais"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gestão Patrimonial Estrita pelo Modelo Canônico DBML (Priority: P1)

Como gestor ou técnico de patrimônio, quero operar exclusivamente com os conceitos padronizados de Ativos, Categorias, Localizações Físicas, Movimentações, Histórico de Patrimônio e Manutenções Técnicas, de forma que o sistema reflita unicamente o modelo oficial de dados sem coexistência de estruturas obsoletas ou duplicadas.

**Why this priority**: É o objetivo central do sistema unificar o ciclo de vida dos bens sob o modelo único de dados, eliminando inconsistências e complexidade operacional provenientes de estruturas antigas.

**Independent Test**: Pode ser testado operando o cadastro completo de um ativo (com sua categoria, localização e usuário custodiante), registrando seu histórico de renumeração, movimentação e intervenção de manutenção, comprovando que todas as operações ocorrem nas entidades oficiais sem depender de nenhuma estrutura legada.

**Acceptance Scenarios**:

1. **Given** que o sistema está operando sob o modelo padronizado, **When** o técnico cadastra uma categoria, uma localização física e um ativo com número de patrimônio e especificações técnicas, **Then** o ativo é persistido com sucesso associado à categoria e à localização especificadas.
2. **Given** um ativo existente no sistema, **When** o técnico registra uma manutenção preventiva ou corretiva informando data, custo e prestador, **Then** a manutenção é registrada com sucesso no histórico do ativo com o técnico responsável vinculado.
3. **Given** um ativo em uso em uma localização, **When** o operador transfere o ativo para uma nova localização com custodiante, **Then** a movimentação física é registrada preservando a rastreabilidade completa.

---

### User Story 2 - Descomissionamento Total de Estruturas e Tabelas Fora do DBML (Priority: P1)

Como administrador do sistema e mantenedor de dados, quero que todas as tabelas, colunas, visões e modelos que não constam no modelo DBML oficial sejam completamente removidos do banco de dados e do código, garantindo que o catálogo de dados contenha estritamente e exatamente as 7 entidades padronizadas e nada além.

**Why this priority**: Atende diretamente à determinação do usuário de não manter nada a mais no banco de dados além do DBML especificado, garantindo consistência estrutural, conformidade e redução da dívida técnica.

**Independent Test**: Pode ser testado inspecionando o esquema do banco de dados e a camada de modelos para verificar que apenas as 7 tabelas oficiais existem, e que todas as operações do sistema continuam executando com sucesso e cobertura total de testes.

**Acceptance Scenarios**:

1. **Given** um banco de dados contendo tabelas legadas do protótipo inicial (como estruturas paralelas de equipamentos, setores antigos ou tentativas de acesso), **When** a evolução estrutural de limpeza é aplicada, **Then** todas essas estruturas obsoletas são descartadas e o banco passa a conter exclusivamente as 7 tabelas do DBML.
2. **Given** a tabela de usuários, **When** a limpeza de atributos fora do padrão é executada, **Then** qualquer coluna redundante ou obsoleta (como credenciais antigas em duplicidade) é descartada, preservando unicamente o hash seguro oficial e os campos previstos no DBML.
3. **Given** a aplicação em execução após a limpeza, **When** os fluxos de autenticação, gestão de ativos e relatórios são acionados, **Then** o sistema opera sem falhas de integridade referencial ou dependências fantasmas de tabelas excluídas.

---

### User Story 3 - Integridade Referencial e Proteção de Dados Órfãos (Priority: P2)

Como auditor de conformidade patrimonial, quero que todas as regras de integridade referencial, bloqueios de exclusão indevida e rastreamento de responsabilidade estejam plenamente funcionais após a remoção de resíduos legados, garantindo que não existam registros órfãos ou inconsistências históricas.

**Why this priority**: Garante que o descomissionamento de tabelas legadas não comprometa a higidez dos relacionamentos entre ativos, categorias, localizações e movimentações.

**Independent Test**: Pode ser testado tentando excluir localizações ou categorias que possuam bens vinculados (comprovando o bloqueio), e excluindo bens descartados verificando a limpeza em cascata apenas dos seus próprios históricos dependentes.

**Acceptance Scenarios**:

1. **Given** uma categoria com ativos cadastrados, **When** uma tentativa de exclusão direta dessa categoria for executada, **Then** o sistema rejeita a operação, impedindo a geração de ativos órfãos sem categoria.
2. **Given** um ativo com histórico de movimentações e manutenções, **When** a desincorporação completa ou remoção autorizada do bem ocorre, **Then** as dependências diretas de histórico do bem são removidas em cascata controlada, sem afetar localizações ou usuários envolvidos.

---

### Edge Cases

- **Tentativa de consulta a identificadores ou rotas de entidades legadas**: O sistema deve retornar respostas claras de recurso não existente (404) ou descontinuado, orientando os clientes a utilizar a API canônica de Ativos.
- **Usuários com papéis ou estados legados**: Todos os usuários devem estar mapeados com exatidão para um dos três papéis do catálogo oficial (`administrador`, `tecnico`, `colaborador`).
- **Remoção de colunas com dados históricos**: Qualquer dado essencial de ativos presente em estruturas legadas deve ser migrado previamente para os campos correspondentes do modelo canônico antes do descarte das colunas obsoletas.
- **Localizações físicas sem numeração de sala**: A unicidade do espaço físico (prédio, andar, setor) deve ser preservada rigorosamente mesmo quando o campo de sala não for preenchido (nulo).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE conter estritamente e exatamente as 7 entidades no banco de dados correspondentes ao DBML: `users`, `locations`, `categories`, `assets`, `patrimony_history`, `asset_movements` e `asset_maintenances`.
- **FR-002**: O sistema NÃO DEVE conter nenhuma tabela adicional no banco de dados além das 7 especificadas no DBML oficial (devem ser expurgadas quaisquer tabelas de protótipos anteriores como `equipments`, `sectors`, `equipment_types`, `equipment_statuses`, `maintenance_types`, `equipment_movements`, `equipment_maintenances` e `login_attempts`).
- **FR-003**: A entidade `users` DEVE conter estritamente os campos: `id`, `name`, `email`, `password_hash`, `role`, `is_active`, `deleted_at`, `created_at` e `updated_at`, eliminando qualquer coluna redundante herdada de versões anteriores.
- **FR-004**: O sistema DEVE restringir os papéis de usuários aos três valores do enumerador `user_role`: `administrador`, `tecnico` e `colaborador`.
- **FR-005**: O sistema DEVE restringir as situações patrimoniais dos ativos aos quatro valores do enumerador `asset_status`: `disponivel`, `em_uso`, `em_manutencao` e `baixado`.
- **FR-006**: O sistema DEVE restringir as intervenções de manutenção aos dois valores do enumerador `maintenance_type`: `preventiva` e `corretiva`.
- **FR-007**: A entidade `locations` DEVE manter a restrição de unicidade para a combinação de prédio, andar, setor e sala, garantindo que não existam duplicidades espaciais mesmo com campos opcionais nulos.
- **FR-008**: A entidade `categories` DEVE registrar o nome único, meses de vida útil estimada, taxa percentual de depreciação residual e a flag indicativa de obrigatoriedade de número de série.
- **FR-009**: A entidade `assets` DEVE garantir a unicidade de número de patrimônio e de número de série (quando preenchido), suportando atributos técnicos flexíveis no campo de especificações estruturadas.
- **FR-010**: A entidade `patrimony_history` DEVE auditar todas as renumerações de patrimônio, gravando o número anterior, o novo número, o motivo formal e o usuário responsável pela alteração.
- **FR-011**: A entidade `asset_movements` DEVE registrar cada movimentação física de ativo, armazenando localização de origem, localização de destino, usuário de origem, usuário destinatário, responsável pela movimentação, data do aceite e observações.
- **FR-012**: A entidade `asset_maintenances` DEVE registrar intervenções de manutenção vinculadas ao ativo, com data, tipo, prestador de serviço, descrição detalhada, custo financeiro e o técnico responsável.
- **FR-013**: Toda a camada de código do sistema (modelos de dados, repositórios, casos de uso e rotas) DEVE ser purificada, removendo definições e dependências vinculadas às entidades descartadas.

### Key Entities

- **User (`users`)**: Representa os usuários do sistema com controle de acesso baseado em três perfis (`administrador`, `tecnico`, `colaborador`), credencial criptografada (`password_hash`), identificação e ciclo de vida.
- **Location (`locations`)**: Espaço físico hierárquico com prédio, andar, setor, sala e descrição, garantindo unicidade espacial do local de instalação dos bens.
- **Category (`categories`)**: Classificação patrimonial dos ativos com parâmetros de vida útil, taxa residual para depreciação e exigência de número de série.
- **Asset (`assets`)**: Bem patrimonial individualizado por número de patrimônio e número de série, com categoria, localização, custodiante opcional, dados de aquisição, status e especificações.
- **Patrimony History (`patrimony_history`)**: Histórico imutável de renumeração ou troca de plaqueta patrimonial de um ativo.
- **Asset Movement (`asset_movements`)**: Registro histórico de transferência física de localização e/ou custodiante de um bem.
- **Asset Maintenance (`asset_maintenances`)**: Registro técnico e financeiro de intervenções preventivas ou corretivas executadas em um bem.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O catálogo de tabelas do banco de dados reflete exatamente 7 tabelas com 0% de tabelas órfãs ou legadas residuais.
- **SC-002**: 100% das consultas, comandos e cadastros do sistema operam exclusivamente sobre as 7 entidades oficiais do DBML.
- **SC-003**: 100% da suíte de testes automatizados passa com sucesso após o descarte das tabelas legadas.
- **SC-004**: A cobertura de testes automatizados em linhas e ramificações (branches) permanece em 100% para todo o código executável.
- **SC-005**: Tempo de migração e limpeza estrutural em ambiente de homologação inferior a 30 segundos, sem perda de dados válidos de patrimônio.

## Assumptions

- O banco de dados alvo é o PostgreSQL 16+, com suporte nativo a tipos enumerados (`ENUM`) e `JSONB`.
- Todos os dados históricos válidos já foram consolidados nas tabelas `assets`, `locations`, `categories`, `asset_movements` e `asset_maintenances` durante a evolução do sistema.
- Clientes que consomem a API de equipamentos legada migrarão para os endpoints canônicos de `/api/v1/assets`, `/api/v1/locations` e `/api/v1/categories`.
