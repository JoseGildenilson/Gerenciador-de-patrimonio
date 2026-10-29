# Feature Specification: Padronização de Nomenclatura e Conformidade Constitucional

**Feature Branch**: `fix/names-project`

**Created**: 2026-10-29

**Status**: Implemented

**Input**: User description: "Verificar e padronizar toda a nomenclatura do projeto para Gerenciador de Patrimônio, garantindo conformidade com a Constituição em todos os arquivos Docker, configurações, documentações e código, purgando qualquer resquício de nomes legados ou divergentes"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conformidade e Padronização de Identificadores Docker e Configuração (Priority: P1)

Como desenvolvedor, operador DevOps ou avaliador do projeto, quero que todos os arquivos de configuração de contêineres (`docker-compose.yml`, `docker-compose.prod.yml`, `Dockerfile`) e arquivos de ambiente reflitam estritamente os identificadores canônicos oficiais estipulados na Constituição do Projeto (`patrimonio_backend`, `patrimonio_frontend`, `patrimonio_postgres`, rede `patrimonio_net`, volume `patrimonio_data`), eliminando discrepâncias como o uso de hífen (`patrimonio-net`) ou nomes genéricos (`postgres_data`), de forma que o ambiente execute de maneira uniforme e auditável.

**Why this priority**: É requisito constitucional direto e garante a consistência técnica dos ambientes de desenvolvimento, testes e produção do sistema.

**Independent Test**: Pode ser testado inspecionando os arquivos Docker Compose e arquivos de configuração de ambiente, validando que todas as declarações de serviços, redes internas e volumes persistentes utilizam exatamente os nomes oficiais estabelecidos.

**Acceptance Scenarios**:

1. **Given** os arquivos de orquestração Docker Compose (`docker-compose.yml` e `docker-compose.prod.yml`), **When** as definições de rede são inspecionadas, **Then** tanto a chave do serviço quanto a rede externa/driver referenciam univocamente `patrimonio_net`.
2. **Given** as definições de persistência de dados nos arquivos Docker Compose, **When** inspecionada a declaração de volumes, **Then** o volume persistente do banco de dados é configurado uniformemente como `patrimonio_data`.
3. **Given** as variáveis e arquivos de exemplo de ambiente (`.env.example`), **When** verificadas as configurações de banco e rede, **Then** todos os identificadores apontam para `patrimonio_db`, `patrimonio_net` e portas padronizadas.

---

### User Story 2 - Purga Estrita de Menções a Nomes Legados em Todo o Repositório (Priority: P1)

Como mantenedor e auditor do projeto, quero que qualquer menção residual ativa ao nome legado (`internal_management`, `internal-management` ou termos anteriores à adaptação para Gerenciador de Patrimônio) seja purgada de todos os arquivos de documentação, scripts, comentários de código e migrações do banco de dados, excetuando-se estritamente as cláusulas que documentam a proibição de uso na Constituição.

**Why this priority**: Atende à regra constitucional expressa que proíbe o uso de `internal_management`, `internal-management` ou variações em qualquer arquivo, configuração, container, pacote, banco de dados ou documentação.

**Independent Test**: Pode ser testado executando uma varredura automatizada de busca textual em todo o repositório, comprovando que não existem referências residuais ativas em nenhum arquivo do projeto fora do texto das próprias cláusulas proibitivas da Constituição.

**Acceptance Scenarios**:

1. **Given** o repositório de código, documentações, scripts e migrações, **When** uma busca textual por `internal_management` e `internal-management` é executada, **Then** nenhuma ocorrência é encontrada fora dos documentos regulatórios onde a proibição é formalmente enunciada.
2. **Given** docstrings e comentários de migrações e módulos (como em `alembic/versions/`), **When** inspecionados, **Then** referências genéricas antigas são substituídas pelo contexto oficial do Gerenciador de Patrimônio.

---

### User Story 3 - Preservação da Integridade Funcional e Suíte de Testes (Priority: P2)

Como time de engenharia e garantia de qualidade, quero assegurar que todos os ajustes e padronizações de nomenclatura preservem a integridade dos contratos públicos, rotas e regras de negócio do sistema, mantendo 100% de aprovação e cobertura na suíte de testes automatizados.

**Why this priority**: Evita regressões funcionais durante as atividades de conformidade e garante que as verificações de qualidade contínua (CI) permaneçam verdes.

**Independent Test**: Pode ser testado executando a suíte completa de testes no backend (`pytest`) e frontend (`vitest` e `tsc --noEmit`), confirmando 100% de sucesso e cobertura de testes intacta.

**Acceptance Scenarios**:

1. **Given** que todas as correções de nomenclatura foram aplicadas em arquivos de configuração e código, **When** os testes automatizados são executados, **Then** todos os testes passam com 100% de cobertura de código (linhas e branches).
2. **Given** os workflows de Integração Contínua (`.github/workflows/ci.yml`), **When** avaliados, **Then** permanecem alinhados com os nomes e variáveis canônicas do banco (`test_patrimonio_db`) e passam sem inconsistências.

---

### Edge Cases

- **Exceção Constitucional**: A regra constitucional em `GEMINI.md` e `spec/constituicao.md` menciona literalmente o termo legado para fins de proibição explícita. Essa menção normativa NÃO deve ser apagada da regra de governança, mas sim preservada para garantir a rastreabilidade do padrão proibido.
- **Divergência de Hífen vs. Sublinhado no Docker Compose**: O Docker Compose aceita tanto `patrimonio-net` quanto `patrimonio_net`, mas para estrita conformidade com a Constituição (`patrimonio_net`), a chave de declaração e o nome da rede devem ser unificados em `patrimonio_net`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE utilizar o identificador canônico `patrimonio_net` para as redes Docker em todos os arquivos de composição (`docker-compose.yml`, `docker-compose.prod.yml`).
- **FR-002**: O sistema DEVE utilizar o identificador canônico `patrimonio_data` para os volumes persistentes de banco de dados nos arquivos Docker Compose.
- **FR-003**: O sistema DEVE remover quaisquer referências descritivas residuais a `internal_management` ou `internal-management` em docstrings de migrações do banco de dados (ex.: `alembic/versions/`), documentações secundárias e scripts.
- **FR-004**: O sistema DEVE assegurar que as definições de pacote backend (`gerenciador_patrimonio` em `pyproject.toml`) e frontend (`patrimonio-frontend` em `frontend/package.json`) permaneçam estritamente em conformidade com a Constituição.
- **FR-005**: O sistema DEVE assegurar que as variáveis de ambiente em `.env.example` e documentações de inicialização utilizem os identificadores oficiais (`patrimonio_db`, `patrimonio_net`, `patrimonio_backend`, etc.).
- **FR-006**: O sistema DEVE garantir que a suíte completa de testes unitários, testes de integração e verificações estáticas de tipo execute com 100% de sucesso após as alterações.

### Key Entities *(include if feature involves data)*

- **Identificadores Canônicos do Sistema**: Conjunto normativo de nomes oficiais estipulados pela Constituição:
  - Nome Canônico do Projeto: `Gerenciador de Patrimônio`
  - Backend / Pacote Python: `gerenciador_patrimonio`
  - Frontend: `patrimonio-frontend`
  - Banco de Dados: `patrimonio_db` (testes: `test_patrimonio_db`)
  - Containers Docker: `patrimonio_backend`, `patrimonio_frontend`, `patrimonio_postgres`
  - Rede e Volumes Docker: `patrimonio_net`, `patrimonio_data`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% de conformidade com a Constituição em todos os arquivos Docker Compose, com `patrimonio_net` e `patrimonio_data` devidamente padronizados.
- **SC-002**: Zero ocorrências residuais de nomes legados em código funcional, scripts e documentações (salvo onde citado como regra de proibição na Constituição).
- **SC-003**: 100% dos testes automatizados passando com cobertura de 100% mantida no backend e compilação limpa no frontend.
- **SC-004**: Validação completa do pipeline de CI sem incompatibilidades de nomenclatura.

## Assumptions

- A padronização não introduz nenhuma nova entidade ou alteração em colunas do banco de dados relacional (o modelo DBML já foi estabilizado em specs anteriores).
- A menção do nome proibido na seção de governança da Constituição (`GEMINI.md` e `spec/constituicao.md`) é necessária e legítima para documentar formalmente a regra de veto.
- Nenhuma rota pública de API (`/api/v1/`) terá sua URI alterada, mantendo total retrocompatibilidade com o frontend.
