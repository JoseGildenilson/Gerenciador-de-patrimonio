# Tasks: Padronização de Nomenclatura e Conformidade Constitucional

**Input**: Design documents from `/specs/003-padronizar-nomes-patrimonio/`
**Prerequisites**: [plan.md](file:///C:/Users/70486375447/orca/workspaces/Gerenciador-de-patrimonio/Fix-names/specs/003-padronizar-nomes-patrimonio/plan.md), [spec.md](file:///C:/Users/70486375447/orca/workspaces/Gerenciador-de-patrimonio/Fix-names/specs/003-padronizar-nomes-patrimonio/spec.md), [research.md](file:///C:/Users/70486375447/orca/workspaces/Gerenciador-de-patrimonio/Fix-names/specs/003-padronizar-nomes-patrimonio/research.md), [data-model.md](file:///C:/Users/70486375447/orca/workspaces/Gerenciador-de-patrimonio/Fix-names/specs/003-padronizar-nomes-patrimonio/data-model.md), [contracts/](file:///C:/Users/70486375447/orca/workspaces/Gerenciador-de-patrimonio/Fix-names/specs/003-padronizar-nomes-patrimonio/contracts/)

## Format: `- [ ] [ID] [P?] [Story] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verificação do ambiente e estado inicial do repositório

- [X] T001 Verify baseline repository status and ensure git working tree is clean in .
- [X] T002 [P] Review existing Docker Compose configurations in docker-compose.yml and docker-compose.prod.yml against contracts/docker-compose-contract.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Verificação prévia da suíte de testes antes de aplicar alterações

**⚠️ CRITICAL**: Confirmar que a suíte base está verde antes de iniciar as modificações das histórias de usuário

- [X] T003 Verify baseline test execution passes before changes in tests/
- [X] T004 [P] Verify baseline frontend test execution passes with npm test in frontend/

**Checkpoint**: Linha de base validada e verde — a implementação das histórias de usuário pode iniciar

---

## Phase 3: User Story 1 - Conformidade e Padronização de Identificadores Docker e Configuração (Priority: P1) 🎯 MVP

**Goal**: Padronizar identificadores de rede (`patrimonio_net`) e volume (`patrimonio_data`) nos arquivos Docker Compose e arquivos de configuração de ambiente.

**Independent Test**: Executar `docker compose config` e inspecionar a saída gerada confirmando que redes e volumes seguem estritamente `patrimonio_net` e `patrimonio_data`.

### Implementation for User Story 1

- [X] T005 [US1] Update network declarations and service references from `patrimonio-net` to `patrimonio_net` in docker-compose.yml
- [X] T006 [US1] Update volume declarations and postgres service mount from `postgres_data` to `patrimonio_data` in docker-compose.yml
- [X] T007 [US1] Update network declarations and service references from `patrimonio-net` to `patrimonio_net` in docker-compose.prod.yml
- [X] T008 [US1] Update volume declarations and postgres service mount to canonical `patrimonio_data` in docker-compose.prod.yml
- [X] T009 [P] [US1] Verify and align environment variables with canonical database and network identifiers in .env.example
- [X] T010 [US1] Validate syntax and configuration output of Docker Compose files via docker compose config in docker-compose.yml

**Checkpoint**: Neste ponto, a User Story 1 está completa e testável de forma independente (MVP alcançado)

---

## Phase 4: User Story 2 - Purga Estrita de Menções a Nomes Legados em Todo o Repositório (Priority: P1)

**Goal**: Eliminar quaisquer resquícios textuais de nomes legados ou termos proibidos em docstrings, scripts e documentações secundárias.

**Independent Test**: Executar varredura automatizada com `git grep` em todo o repositório confirmando ausência de termos proibidos fora das definições constitucionais.

### Implementation for User Story 2

- [X] T011 [P] [US2] Update docstring in alembic/versions/97cfe449ece9_add_equipment_management_models.py to Gerenciador de Patrimonio context
- [X] T012 [P] [US2] Update legacy network and volume references (`patrimonio-net` and `postgres_data`) in spec/features/docker-compose/spec.md
- [X] T013 [P] [US2] Update legacy network and volume references in spec/features/docker-compose/tasks.md
- [X] T014 [P] [US2] Update legacy network references in spec/infra/DEVOPS/plan.md, spec/infra/DEVOPS/task.md, and spec/infra/DEVOPS/tasks.md
- [X] T015 [US2] Execute automated repository audit verifying zero forbidden terms (`internal_management` / `internal-management`) outside constitutional definitions in .

**Checkpoint**: Neste ponto, as histórias US1 e US2 estão completamente atendidas

---

## Phase 5: User Story 3 - Preservação da Integridade Funcional e Suíte de Testes (Priority: P2)

**Goal**: Garantir que as alterações de infraestrutura e documentação preservem a integridade dos testes e a cobertura constitucional de 100%.

**Independent Test**: Executar a suíte de testes com 100% de aprovação e conferir passagem limpa no CI.

### Implementation for User Story 3

- [X] T016 [US3] Verify .github/workflows/ci.yml alignment with canonical database test variables
- [X] T017 [US3] Execute full backend test suite with 100% code coverage requirement in tests/
- [X] T018 [P] [US3] Execute frontend test suite and strict TypeScript type check in frontend/

**Checkpoint**: Todas as histórias de usuário funcionais e de qualidade validadas com sucesso

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validação final de ponta a ponta e atualização do status dos artefatos

- [X] T019 Execute end-to-end scenarios described in specs/003-padronizar-nomes-patrimonio/quickstart.md
- [X] T020 [P] Update specification status in specs/003-padronizar-nomes-patrimonio/spec.md to Ready for Implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências — execução imediata
- **Foundational (Phase 2)**: Depende do Setup — bloqueia as histórias de usuário para assegurar baseline limpo
- **User Stories (Phases 3 to 5)**: Dependem da conclusão da Phase 2
  - US1 (P1 - Docker & Configurações): Pode ser executada primeiro (MVP)
  - US2 (P1 - Purga de Nomes Legados): Pode ser executada em paralelo ou após US1
  - US3 (P2 - Validação de Testes e CI): Depende da conclusão de US1 e US2
- **Polish (Phase 6)**: Depende da conclusão das histórias US1, US2 e US3

### Parallel Opportunities

- **T001 e T002**: Revisão de arquivos compose em paralelo
- **T003 e T004**: Execução dos testes baseline de backend e frontend em paralelo
- **T009**: Atualização de `.env.example` em paralelo com ajustes no Compose
- **T011, T012, T013 e T014**: Atualizações textuais em migração e documentações em paralelo
- **T017 e T018**: Testes finais de backend e frontend em paralelo

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Completar Setup (T001, T002) + Foundational (T003, T004)
2. Implementar User Story 1 (T005 a T010)
3. Validar sintaxe e configuração do Docker Compose com `docker compose config`
4. Entrega do MVP de infraestrutura padronizada

### Incremental Delivery
1. Foundation estabelecida
2. MVP entregue (US1)
3. Purga textual executada e auditada (US2)
4. Quality gate e validação de cobertura 100% executados (US3)
5. Validação final rápida do quickstart e encerramento (Phase 6)
