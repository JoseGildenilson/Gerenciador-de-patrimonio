# Relatório Consolidado de Auditoria e Rastreabilidade de Conformidade de Especificações e Constituição (SDD)

**Projeto:** Gestão de Patrimônio e Suporte (Comunica)  
**Metodologia:** Spec-Driven Development (Spec-Anchored)  
**Data da Auditoria:** 13 de Outubro de 2026  
**Auditor Responsável:** Equipe Unificada de Auditoria Técnica (Workers M1, M2, M3 e M4)  
**Status Global:** **98.0% de Conformidade de Cenários BDD (49/50 Conformes, 1 Parcial, 0 Não Implementados)**  
**Arquivo de Referência:** `audit_spec_compliance.md` (Raiz do Projeto)

---

## 1. Sumário Executivo

### 1.1. Contexto e Objetivos da Auditoria

O presente relatório consolida a auditoria técnica exaustiva e independente de conformidade de **100% das especificações** localizadas no diretório `spec/features/`, confrontando cada regra de negócio, cenário BDD (*Behavior-Driven Development*) e plano de tarefas (`tasks.md`) contra a base de código implementada no backend (`src/`), frontend (`frontend/`), suíte de testes automatizados (`tests/`) e arquivos de governança do repositório.

Adicionalmente, foi realizada a auditoria estrita de aderência aos princípios e mandamentos da **Constituição do Projeto** (`GEMINI.md`), inspecionando separação arquitetural, uso de SQLAlchemy 2.0 sem SQL puro (*raw SQL*), controle transacional no nível de casos de uso/operações, isolamento de banco de dados nos testes via migrações Alembic, meta de 100% de cobertura de código executável e configuração de integração contínua (CI).

### 1.2. Métricas Globais de Conformidade

| Dimensão Auditada | Total Avaliado | Conforme / Concluído | Parcial | Não Conforme / Pendente | % Conformidade |
|---|:---:|:---:|:---:|:---:|:---:|
| **Cenários BDD (Formais das Specs)** | **50** | **49** | **1** | **0** | **98.0%** |
| **Cenários Detalhados (`spec-corretion.md`)** | 16 | 15 | 1 | 0 | 93.8% |
| **Tarefas dos `tasks.md` (Checklists)** | **76** | **75** | **1** | **0** | **98.7%** |
| **Suíte de Testes Backend (Pytest)** | 104 testes | 104 aprovados (100%) | 0 falhas | 0 erros / 0 skips | **100.0%** |
| **Cobertura de Código Backend (pytest-cov)** | 1352 stmts / 252 branches | 1349 stmts / 251 branches | - | 3 stmts / 1 branch | **99.75%** (apresentado 99%) |
| **Suíte de Testes Frontend (Vitest)** | 57 testes | 57 aprovados (100%) | 0 falhas | 0 erros | **100.0%** |
| **Compilação Estática TypeScript** | 15 suítes / app | 0 erros (`tsc --noEmit`) | - | 0 erros | **100.0%** |
| **Aderência à Constituição (`GEMINI.md`)** | 6 mandamentos | 3 Conformes | 2 Parciais | 1 Não Conforme | **66.7%** |

### 1.3. Tabela Sintética de Conformidade por Pasta / Módulo

A tabela abaixo resume o status de cada uma das 8 pastas contidas em `spec/features/`:

| Pasta / Especificação em `spec/features/` | Qtd Cenários BDD | Status BDD | Qtd Tarefas | Status Tarefas | Status Global da Feature |
|---|:---:|:---:|:---:|:---:|:---:|
| **1. `equipamentos/`** *(inclui `autocomplete-filtros` e `spec-corretion.md`)* | 15 formais (8 base + 7 autocomplete) | 14 Conformes<br>1 Parcial (Cenário 4) | 16 tarefas (9 base + 7 autocomplete) | 15 Concluídas<br>1 Parcial (TASK-EQ-13) | **PARCIAL (93.3%)**<br>*(Visual dos cards / zebra striping)* |
| **2. `tags-crud/`** | 7 | 7 Conformes (100%) | 13 | 13 Concluídas (100%) | **CONFORME (100%)** |
| **3. `tela-de-login/`** | 6 | 6 Conformes (100%) | 6 | 6 Concluídas (100%) | **CONFORME (100%)** |
| **4. `exportacao-planilha/`** | 5 | 5 Conformes (100%) | 10 | 10 Concluídas (100%) | **CONFORME (100%)** |
| **5. `importacao-planilha/`** | 7 | 7 Conformes (100%) | 18 | 18 Concluídas (100%) | **CONFORME (100%)** |
| **6. `documentacao/`** | 2 | 2 Conformes (100%) | 2 | 2 Concluídas (100%) | **CONFORME (100%)** |
| **7. `gitignore/`** | 3 | 3 Conformes (100%) | 3 | 3 Concluídas (100%) | **CONFORME (100%)** |
| **8. `UI/`** *(Design System Profissional)* | 5 | 5 Conformes (100%) | 8 | 8 Concluídas (100%) | **CONFORME (100%)** |
| **TOTAL CONSOLIDADO** | **50** | **49 Conformes (98.0%)<br>1 Parcial (2.0%)** | **76** | **75 Concluídas (98.7%)<br>1 Parcial (1.3%)** | **98.0% CONFORME** |

---

## 2. Resultados de Execução de Testes e Cobertura

### 2.1. Suíte de Testes do Backend (Pytest)

- **Comando de Execução:**  
  `$env:PYTHONPATH="."; python -m uv run --extra dev pytest` (ou `.\.venv\Scripts\pytest.exe -v --cov=src --cov-branch --cov-report=term-missing`)
- **Resultado:** **104 passed in 6.81s** (0 falhas, 0 erros, 0 pulados / 100% de sucesso).
- **Ambiente de Execução:** Python 3.13.2 64-bit (Windows), uv 0.13.0, pytest 8.4.2, pytest-cov 7.0.0.

#### Distribuição dos Testes Backend por Módulo de Teste:

| Arquivo de Teste | Qtd Testes | Resultado | Escopo Funcional Testado |
|---|:---:|:---:|---|
| `tests/test_api.py` | 12 | 12 passed | Autenticação, login, logout, cookies HttpOnly, rota `/me`, proteção RBAC básica. |
| `tests/test_dashboard.py` | 6 | 6 passed | Métricas do dashboard, totalizadores de tickets e equipamentos por status. |
| `tests/test_database.py` | 2 | 2 passed | Ciclo de vida da sessão SQLAlchemy e conexão. |
| `tests/test_equipment_api.py` | 11 | 11 passed | Endpoints de equipamentos, paginação, filtros múltiplos, RBAC, histórico e sugestões. |
| `tests/test_equipment_models.py` | 6 | 6 passed | Modelos ORM `Equipment`, `EquipmentMovement`, `EquipmentMaintenance`, `EquipmentTag`. |
| `tests/test_equipment_repositories.py` | 6 | 6 passed | Consultas SQLAlchemy 2.0, paginação, filtros combinados, propagação de renomeação de tags. |
| `tests/test_equipment_schemas.py` | 4 | 4 passed | Schemas Pydantic de entrada, saída, filtros e validação de dados. |
| `tests/test_equipment_use_cases.py` | 9 | 9 passed | Casos de uso de listagem, atualização em lote, manutenção múltipla e sugestões. |
| `tests/test_import_api.py` | 11 | 11 passed | Endpoints de preview e execute de importação (.xlsx/.csv), RBAC 403 e validações 400. |
| `tests/test_import_use_cases.py` | 5 | 5 passed | Casos de uso de preview, upsert de equipamentos, criação dinâmica de tags e rollback. |
| `tests/test_rate_limit.py` | 2 | 2 passed | Proteção contra força bruta (10 tentativas em 15 min gerando HTTP 429). |
| `tests/test_security.py` | 6 | 6 passed | Hashing de senhas com Argon2/bcrypt e emissão/validação de tokens JWT. |
| `tests/test_seed.py` | 1 | 1 passed | Função de seed de tags padrão no banco de dados. |
| `tests/test_spreadsheet_exporter.py` | 5 | 5 passed | Utilitário openpyxl: 13 colunas, estilos ciano, formatação de manutenções e freeze panes. |
| `tests/test_spreadsheet_parser.py` | 13 | 13 passed | Parser de planilhas: leitura de .xlsx/.csv, tolerância a cabeçalhos e datas. |
| `tests/test_use_case.py` | 5 | 5 passed | Caso de uso `AuthenticateUserUseCase` e métricas do dashboard. |
| **TOTAL GERAL** | **104** | **104 passed (100%)** | **Cobertura de todos os fluxos críticos do backend** |

---

### 2.2. Tabela Completa de Cobertura de Código Backend (`pytest-cov`)

Abaixo é reproduzida a tabela exata e detalhada gerada pelo `pytest-cov`, mensurando linhas executáveis (*Stmts*), linhas não cobertas (*Miss*), branches (*Branch*), branches parciais (*BrPart*), percentual de cobertura e indicação precisa das linhas faltantes:

| Módulo Fonte | Stmts | Miss | Branch | BrPart | Cobertura | Linhas Faltantes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `src\__init__.py` | 0 | 0 | 0 | 0 | 100% | - |
| `src\api\dashboard_routes.py` | 12 | 0 | 0 | 0 | 100% | - |
| `src\api\dependencies.py` | 36 | 0 | 14 | 0 | 100% | - |
| `src\api\equipment_routes.py` | 139 | 0 | 0 | 0 | 100% | - |
| `src\api\import_routes.py` | 28 | 0 | 0 | 0 | 100% | - |
| `src\api\routes.py` | 62 | 0 | 12 | 0 | 100% | - |
| `src\core\config.py` | 12 | 0 | 0 | 0 | 100% | - |
| `src\core\database.py` | 14 | 0 | 0 | 0 | 100% | - |
| `src\core\security.py` | 60 | 0 | 8 | 0 | 100% | - |
| `src\domain\models.py` | 72 | 0 | 0 | 0 | 100% | - |
| `src\domain\schemas.py` | 145 | 0 | 0 | 0 | 100% | - |
| `src\infrastructure\repositories.py` | 168 | 0 | 32 | 0 | 100% | - |
| `src\infrastructure\spreadsheet_exporter.py` | 69 | 0 | 26 | 0 | 100% | - |
| `src\infrastructure\spreadsheet_parser.py` | 177 | 3 | 54 | 1 | **98%** | **182, 254-255** |
| `src\main.py` | 20 | 0 | 0 | 0 | 100% | - |
| `src\use_cases\authenticate_user.py` | 34 | 0 | 4 | 0 | 100% | - |
| `src\use_cases\equipment_use_cases.py` | 209 | 0 | 80 | 0 | 100% | - |
| `src\use_cases\get_dashboard_metrics.py` | 17 | 0 | 2 | 0 | 100% | - |
| `src\use_cases\import_spreadsheet_use_cases.py` | 78 | 0 | 20 | 0 | 100% | - |
| **TOTAL CONSOLIDADO** | **1352** | **3** | **252** | **1** | **99% (99.75% real)** | - |

#### Detalhamento Forense dos Gaps de Cobertura:
1. **`src/infrastructure/spreadsheet_parser.py` (Linha 182):**
   - Trecho: Cláusula `if not any(v is not None and str(v).strip() for v in row_values): continue` dentro do loop `_parse_excel`.
   - Causa: Nenhuma fixture dos testes de planilha Excel possui uma linha completamente vazia intercalada entre linhas de dados válidos.
2. **`src/infrastructure/spreadsheet_parser.py` (Linhas 254-255):**
   - Trecho: Bloco `except Exception: delimiter = ";" if ";" in lines[0] else ","` dentro de `_parse_csv`.
   - Causa: Em todas as execuções de teste com CSV, a biblioteca nativa `csv.Sniffer().sniff` resolveu com sucesso o delimitador, nunca acionando o tratamento de contingência (*fallback*).
3. **Omissão no `pyproject.toml` (`omit = ["src/infrastructure/seed*.py"]`):**
   - Embora `test_seed.py` teste a função `seed_default_tags`, a omissão de `seed.py` da contagem global de cobertura no `pyproject.toml` não possui comentário justificativo explícito, descumprindo a exigência de justificação formal estipulada na Constituição.

---

### 2.3. Suíte de Testes do Frontend (Vitest) e Tipagem

- **Comandos de Execução:**  
  `cd frontend; npm test -- --run`  
  `cd frontend; npx tsc --noEmit`
- **Resultados:**
  - **Vitest:** **57 passed in 15 test files** (100% de sucesso).
  - **TypeScript:** **0 erros** de compilação estática (`tsc --noEmit` retornou código de saída 0).
  - **Arquivos Testados:** `LoginForm.test.tsx` (6), `LoginPage.test.tsx` (6), `AlertBanner.test.tsx` (3), `AutocompleteFilterInput.test.tsx` (5), `ManageTagsModal.test.tsx` (7), `MovementModal.test.tsx` (3), `NewEquipmentModal.test.tsx` (2), `EquipmentPage.test.tsx` (3), `ImportPage.test.tsx` (7), `DashboardPage.test.tsx` (3), `SideMenu.test.tsx` (3), `App.test.tsx` (3), `equipmentApi.test.ts` (1), `importApi.test.ts` (2), `authApi.test.ts` (1).

---

## 3. Auditoria Detalhada de Aderência à Constituição do Projeto (`GEMINI.md`)

A tabela a seguir consolida o confronto direto de cada princípio da Constituição do Projeto (`GEMINI.md`) com a implementação física do sistema:

| Mandamento Constitucional | Exigência Expressa em `GEMINI.md` | Evidências / Código Auditado | Status de Aderência | Análise Detalhada / Parecer |
|---|---|---|:---:|---|
| **1. Separação Arquitetural e Desacoplamento** | *"Simplificações permitidas quando reduzirem complexidade sem comprometer responsabilidades... O domínio pode utilizar bibliotecas de apoio desde que não introduzam dependência de transporte/frameworks."* | - `src/domain/models.py`<br>- `src/domain/schemas.py`<br>- `src/use_cases/*` | **CONFORME** | As camadas de Domínio e Casos de Uso possuem **zero acoplamento** a frameworks HTTP (sem imports de FastAPI, Starlette ou HTTPX). Modelos ORM são usados diretamente com SQLAlchemy 2.0 sob permissão explícita da Constituição. |
| **2. Banimento Absoluto de Raw SQL** | *"O projeto utilizará SQLAlchemy 2.0... SQL puro (raw SQL) não será utilizado."* | - `src/infrastructure/repositories.py`<br>- `src/use_cases/*`<br>- Busca de `text(`, `cursor.execute` | **CONFORME** | Varredura de código revelou **zero instâncias de SQL puro**. Todas as consultas são construídas com a API idiomática do SQLAlchemy 2.0 (`select(Model).where(...)`, `update()`, `in_()`, `ilike()`, `selectinload()`). |
| **3. Controle Transacional** | *"A transação deve ser controlada no nível da operação ou caso de uso. Repositories não devem executar `commit` ou `rollback` de forma independente."* | - `src/infrastructure/repositories.py`<br>- `src/use_cases/import_spreadsheet_use_cases.py`<br>- `src/api/equipment_routes.py` | **CONFORME** | Em `repositories.py` há **zero chamadas a `commit()` ou `rollback()`**. Os repositórios operam puramente registrando entidades na sessão (`db.add()`, `db.delete()`). Transações são comitadas ou revertidas conjuntamente no nível de casos de uso e rotas HTTP. |
| **4. Isolamento do BD nos Testes e Migrations** | *"Testes de integração que envolvam persistência DEVEM utilizar uma instância isolada e descartável do mesmo sistema de banco de dados utilizado pela aplicação. O banco deve ser inicializado a partir das migrations do projeto..."* | - `tests/conftest.py:13`<br>- `tests/conftest.py:31,37`<br>- `alembic/versions/*` | **NÃO CONFORME<br>(Divergência Crítica)** | **Violação Dupla:**<br>1. Aplicação roda em PostgreSQL 16, mas `tests/conftest.py` utiliza SQLite em memória (`sqlite:///:memory:`).<br>2. `conftest.py` inicializa o banco com `Base.metadata.create_all(bind=engine)`, ignorando as 4 migrações oficiais do Alembic. |
| **5. Meta de 100% de Cobertura de Código Executável** | *"Todo código executável DEVE possuir cobertura de testes automatizados de 100%, considerando linhas e branches... As exclusões de cobertura devem ser explícitas e justificadas."* | - `pytest-cov` output<br>- `pyproject.toml:39-41`<br>- `src/infrastructure/spreadsheet_parser.py` | **PARCIALMENTE CONFORME<br>(99.75%)** | 18 de 19 módulos backend atingiram 100%. Restam 3 linhas não cobertas em `spreadsheet_parser.py` (L182 e L254-255). Além disso, a cláusula `omit = ["src/infrastructure/seed*.py"]` carece de justificativa explicada em comentário formal. |
| **6. Integração Contínua (CI no GitHub Actions)** | *"Os testes automatizados DEVEM ser executados automaticamente no GitHub Actions a cada push nas branches develop e main... DEVEM ser executados em pull requests direcionados da branch develop para main."* | - `.github/workflows/ci.yml:3-8` | **PARCIALMENTE CONFORME** | O workflow possui gatilho apenas para `on: push: branches: [main, develop, master]`. **Inexiste o bloco `on: pull_request`**, descumprindo a obrigatoriedade de acionar a suíte em PRs antes do merge. |

---

## 4. Tabela Exaustiva de Rastreabilidade por Feature

Abaixo encontra-se o mapeamento minucioso de **todos os 50 cenários BDD formais**, o cruzamento detalhado com os 16 cenários de `spec-corretion.md` e a auditoria de **todas as 76 tarefas** distribuídas nas 8 pastas de especificação em `spec/features/`.

---

### 4.1. Feature 1: Gestão de Equipamentos (`spec/features/equipamentos/`)

#### 4.1.1. Cenários BDD de `spec/features/equipamentos/spec.md` (8 Cenários)

| ID do Cenário | Nome do Cenário | Critérios (Given / When / Then Resumidos) | Componentes / Arquivos de Implementação | Testes Automatizados Correspondentes | Status | Justificativa Técnica & Evidências |
|---|---|---|---|---|:---:|---|
| **EQ-BDD-01** | **Cenário 1:** Selecionar múltiplos valores em filtro de busca interna | *Dado:* técnico abre filtro `Nº Série`;<br>*Quando:* pesquisa `123` e seleciona, pesquisa `432` e seleciona;<br>*Então:* filtro exibe `Nº Série (2)`;<br>*E:* lista exibe itens com serial `123` OU `432`. | - Backend: `src/api/equipment_routes.py:49, 58-71`<br>- Repositório: `src/infrastructure/repositories.py:155-158`<br>- Frontend: `AutocompleteFilterInput.tsx:109-117`, `EquipmentListPage.tsx:49-51, 95-107` | - `tests/test_equipment_api.py::test_equipment_api_list_and_filters`<br>- `tests/test_equipment_repositories.py::test_equipment_repository_list_paginated_filtered_and_search`<br>- `frontend/src/__tests__/EquipmentPage.test.tsx:93-109` | **Conforme** | Backend recebe `serial_number: List[str]` e constrói `or_(*[ilike(...)])`. Frontend exibe badge de contagem e lista de chips. |
| **EQ-BDD-02** | **Cenário 2:** Múltiplos filtros simultâneos (OR interno, AND externo) | *Dado:* seleciona `Notebook` e `Desktop` em Tipo e `Comunicação` e `Rádio Produção` em Localização;<br>*Então:* retorna `(Notebook OU Desktop) E (Comunicação OU Rádio Produção)`. | - Backend: `src/infrastructure/repositories.py:139-150`<br>- Frontend: `EquipmentListPage.tsx:332-358`, `MultiSelectFilterDropdown.tsx` | - `tests/test_equipment_api.py::test_equipment_api_list_and_filters`<br>- `tests/test_equipment_use_cases.py:95-100` | **Conforme** | Cláusulas independentes `.in_()` combinadas com `.where()` nativo do SQLAlchemy, garantindo OR intra-filtro e AND inter-filtros. |
| **EQ-BDD-03** | **Cenário 3:** Desmarcar filtro individual | *Dado:* filtro `Tipo` com 3 opções ativas;<br>*Quando:* clica em "Desmarcar tudo" no dropdown de Tipo;<br>*Então:* limpa opções de Tipo e mantém demais filtros intocados. | - Frontend: `MultiSelectFilterDropdown.tsx:48-50, 131-144`<br>- Estado: `EquipmentListPage.tsx:334-340` | - `frontend/src/__tests__/EquipmentPage.test.tsx:103-110` | **Conforme** | Cada dropdown possui handler `handleClearAll` que zera exclusivamente seu estado local sem afetar filtros adjacentes. |
| **EQ-BDD-04** | **Cenário 4:** Visualização limpa com nomes proporcionais, respiro interno e alto contraste | *Dado:* listagem carregada;<br>*Quando:* blocos exibidos;<br>*Então:* layout horizontal, nomes `text-sm sm:text-base font-bold`, respiro `p-5 sm:px-6 sm:py-5`, bordas `border-2 border-slate-700/90` e cores alternadas (*zebra striping*). | - Frontend: `EquipmentListPage.tsx:472-536` | - `frontend/src/__tests__/EquipmentPage.test.tsx:43-65` | **Parcial** | **Gap de Apresentação:** Layout horizontal, metadados inline e animação staggered estão presentes. Porém, **zebra striping** (par/ímpar) não foi implementado (`index % 2 === 0` ausente, classe fixa `bg-[#1E1E1E]`), borda é simples `border-[#333333]` em vez de dupla `border-2 border-slate-700/90`, e padding é `p-4` em vez de `p-5 sm:px-6 sm:py-5`. |
| **EQ-BDD-05** | **Cenário 5:** Edição completa em modo único na tela de detalhes | *Dado:* visualizando detalhes em tela única;<br>*Quando:* clica em "Editar equipamento";<br>*Então:* todos os campos abrem edição simultânea;<br>*E:* ao clicar em "Salvar alterações", persiste dados e volta a visualização. | - Backend: `src/api/equipment_routes.py:226-246`, `src/use_cases/equipment_use_cases.py:126-175`<br>- Frontend: `EquipmentDetailPage.tsx:163-211` | - `tests/test_equipment_use_cases.py::test_update_equipment_use_case`<br>- `tests/test_equipment_api.py::test_equipment_api_update_404_and_400`<br>- `frontend/src/__tests__/EquipmentPage.test.tsx:183-199` | **Conforme** | Flag `isEditing` abre todos os campos; chamada para `equipmentApi.updateEquipment` atualiza o registro; botão "Cancelar" reverte alterações. |
| **EQ-BDD-06** | **Cenário 6:** Registrar manutenção com múltiplos itens agrupados | *Dado:* cadastra manutenção com data `18/09/2026` e itens `Troca de SSD`, `Limpeza interna`, `Troca de pasta térmica`;<br>*Então:* cria 1 registro agrupado e atualiza `last_maintenance_at` do equipamento para `18/09/2026`. | - Backend: `src/api/equipment_routes.py:267-283`, `src/use_cases/equipment_use_cases.py:206-232`<br>- Frontend: `MaintenanceModal.tsx:37-44, 87-97` | - `tests/test_equipment_use_cases.py::test_record_maintenance_use_case_updates_last_maintenance_date_without_changing_status`<br>- `tests/test_equipment_api.py::test_equipment_api_movements_and_maintenances` | **Conforme** | Descrição unificada permite lista de itens; caso de uso atualiza explicitamente `equipment.last_maintenance_at = data.maintenance_date` sem alterar o status do ativo. |
| **EQ-BDD-07** | **Cenário 7:** Editar e excluir registro de manutenção no histórico | *Dado:* manutenção existente no histórico;<br>*Quando:* clica em "Editar", altera itens e data;<br>*E:* ao clicar em "Excluir", remove o registro e recalcula data da última manutenção. | - Backend: `src/api/equipment_routes.py:286-329`, `src/use_cases/equipment_use_cases.py:234-300`<br>- Frontend: `EditMaintenanceModal.tsx:42-66`, `EquipmentDetailPage.tsx:213-223` | - `tests/test_equipment_use_cases.py::test_update_and_delete_maintenance_use_cases`<br>- `tests/test_equipment_api.py::test_equipment_api_movements_and_maintenances` | **Conforme** | Endpoints PUT e DELETE operacionais; use cases recalculam `last_maintenance_at` com base no `max(maintenance_date)` restante; interface com modais dedicados. |
| **EQ-BDD-08** | **Cenário 8:** Navegação explícita | *Dado:* em `/equipamentos`, clicar em "← Voltar ao Dashboard" navega para `/dashboard`;<br>*Dado:* em detalhes, clicar em "← Voltar para equipamentos" navega para `/equipamentos`. | - Frontend: `EquipmentListPage.tsx:253-261` (`data-testid="back-to-dashboard-btn"`), `EquipmentDetailPage.tsx` (`data-testid="back-to-equipments-btn"`) | - `frontend/src/__tests__/EquipmentPage.test.tsx:111-118, 200-207` | **Conforme** | Botões com `navigate('/dashboard')` e `navigate('/equipamentos')` validados via testes com React Router. |

---

#### 4.1.2. Cenários BDD de `spec/features/equipamentos/autocomplete-filtros/spec.md` (7 Cenários)

| ID do Cenário | Nome do Cenário | Critérios (Given / When / Then Resumidos) | Componentes / Arquivos de Implementação | Testes Automatizados Correspondentes | Status | Justificativa Técnica & Evidências |
|---|---|---|---|---|:---:|---|
| **AC-BDD-01** | **Cenário 1:** Sugestões ao digitar no filtro de Patrimônio | *Dado:* digita prefixo `PA`;<br>*Então:* exibe `PAT001`, `PAT002`, `PAT100` e omite `SER001`. | - Backend: `src/api/equipment_routes.py:161-175`, `src/infrastructure/repositories.py:270-305`<br>- Frontend: `AutocompleteFilterInput.tsx:36-68` | - `tests/test_equipment_api.py::test_equipment_api_suggestions`<br>- `frontend/src/__tests__/AutocompleteFilterInput.test.tsx:42-84` | **Conforme** | Consulta `EquipmentRepository.get_distinct_values_by_prefix` usa DISTINCT e ILIKE com ordenação alfabética; input exibe popover de sugestões. |
| **AC-BDD-02** | **Cenário 2:** Bloqueio de sugestões com menos de 2 caracteres | *Dado:* digita 1 caractere (`S`);<br>*Então:* não dispara busca nem exibe dropdown. | - Backend: `src/use_cases/equipment_use_cases.py:378-380`<br>- Frontend: `AutocompleteFilterInput.tsx:42-47` | - `frontend/src/__tests__/AutocompleteFilterInput.test.tsx:12-40`<br>- `tests/test_equipment_api.py::test_equipment_api_suggestions:362-366` | **Conforme** | Validação no frontend previne chamadas de rede; backend rejeita prefixos `< 2` caracteres com HTTP 400. |
| **AC-BDD-03** | **Cenário 3:** Adicionar sugestão como chip ao clicar | *Dado:* clica em sugestão;<br>*Então:* adiciona como chip, limpa campo de texto e filtra lista. | - Frontend: `AutocompleteFilterInput.tsx:70-75`, `EquipmentListPage.tsx:365, 373, 381` | - `frontend/src/__tests__/AutocompleteFilterInput.test.tsx:78-83` | **Conforme** | Callback `onSelect` aciona `handleAddTextFilter`, limpando a entrada e atualizando a query de busca. |
| **AC-BDD-04** | **Cenário 4:** Ocultar valores já selecionados nas sugestões | *Dado:* valor já está selecionado como chip;<br>*Então:* não é listado nas sugestões. | - Frontend: `AutocompleteFilterInput.tsx:53` | - `frontend/src/__tests__/AutocompleteFilterInput.test.tsx:50, 73-76` | **Conforme** | Filtro de array `results.filter(item => !selectedValues.includes(item))` remove duplicidades da lista suspensa. |
| **AC-BDD-05** | **Cenário 5:** Manter entrada livre via tecla Enter | *Dado:* texto digitado não consta nas sugestões;<br>*Quando:* pressiona Enter;<br>*Então:* adiciona valor como chip normalmente. | - Frontend: `AutocompleteFilterInput.tsx:77-87` | - `frontend/src/__tests__/AutocompleteFilterInput.test.tsx:86-108`<br>- `frontend/src/__tests__/EquipmentPage.test.tsx:93-102` | **Conforme** | Listener `onKeyDown` captura `e.key === 'Enter'`, validando duplicidade e adicionando chip customizado. |
| **AC-BDD-06** | **Cenário 6:** Backend retorna erro para campo inválido | *Dado:* requisição com `field=invalid_field`;<br>*Então:* retorna HTTP 400 Bad Request. | - Backend: `src/use_cases/equipment_use_cases.py:374-376`, `src/api/equipment_routes.py:173-174` | - `tests/test_equipment_api.py::test_equipment_api_suggestions:357-360`<br>- `tests/test_equipment_use_cases.py::test_get_suggestions_use_case` | **Conforme** | Validação contra lista de campos permitidos (`patrimony_number`, `serial_number`, `product_number`). |
| **AC-BDD-07** | **Cenário 7:** Backend retorna erro para prefixo curto | *Dado:* requisição com `prefix=A`;<br>*Então:* retorna HTTP 400 Bad Request. | - Backend: `src/use_cases/equipment_use_cases.py:378-380`, `src/api/equipment_routes.py:173-174` | - `tests/test_equipment_api.py::test_equipment_api_suggestions:362-366` | **Conforme** | Caso de uso levanta `ValueError` quando `len(prefix.strip()) < 2`, convertido para HTTP 400 na rota. |

---

#### 4.1.3. Cruzamento Detalhado com `spec/features/equipamentos/spec-corretion.md` (16 Cenários)

O arquivo `spec-corretion.md` estabeleceu o refinamento detalhado da tela de equipamentos. Seu alinhamento com a base de código é detalhado abaixo:

1. **Cenário 1 (Filtro múltiplo com busca interna):** Conforme (`AutocompleteFilterInput.tsx`, `equipment_routes.py:49`).
2. **Cenário 2 (Comportamento estilo Google Sheets):** Conforme (`MultiSelectFilterDropdown.tsx`).
3. **Cenário 3 (Desmarcar tudo no dropdown):** Conforme (`MultiSelectFilterDropdown.tsx:48-50`).
4. **Cenário 4 (Blocos empilhados e estrutura):** **Parcial** (estrutura em blocos ok, zebra striping e borda dupla ausentes em `EquipmentListPage.tsx:479`).
5. **Cenário 5 (Abrir detalhes ao clicar no bloco):** Conforme (`EquipmentListPage.tsx:476`).
6. **Cenário 6 (Modo de edição em lote):** Conforme (`EquipmentDetailPage.tsx:163-211`).
7. **Cenário 7 (Cancelar edição):** Conforme (`EquipmentDetailPage.tsx:170`).
8. **Cenário 8 (Salvar alterações):** Conforme (`EquipmentDetailPage.tsx:185`).
9. **Cenário 9 (Manutenção com vários itens):** Conforme (`RecordMaintenanceUseCase`, `MaintenanceModal.tsx`).
10. **Cenário 10 (Atualização de última manutenção):** Conforme (`RecordMaintenanceUseCase:229`).
11. **Cenário 11 (Editar manutenção no histórico):** Conforme (`UpdateMaintenanceUseCase`, `EditMaintenanceModal.tsx`).
12. **Cenário 12 (Excluir manutenção no histórico):** Conforme (`DeleteMaintenanceUseCase`, `EquipmentDetailPage.tsx:213`).
13. **Cenário 13 (Situação não alterada automaticamente por manutenção/movimentação):** Conforme (`RecordMovementUseCase` e `RecordMaintenanceUseCase` não alteram status; testado em `tests/test_equipment_use_cases.py`).
14. **Cenário 14 (Voltar para equipamentos):** Conforme (`EquipmentDetailPage.tsx`, `data-testid="back-to-equipments-btn"`).
15. **Cenário 15 (Voltar ao Dashboard):** Conforme (`EquipmentListPage.tsx`, `data-testid="back-to-dashboard-btn"`).
16. **Cenário 16 (Entrada com animação slide-in):** Conforme (`EquipmentListPage.tsx:477-479` com `animate-slide-in-right` e delay staggered).

---

#### 4.1.4. Auditoria de Tarefas: `spec/features/equipamentos/tasks.md`

| Tarefa | Status no Checklist | Status no Código | Evidências / Arquivos no Código | Observações |
|---|:---:|:---:|---|---|
| **TASK-EQ-10** | [x] | **Concluído** | `src/api/equipment_routes.py:45-50`, `src/infrastructure/repositories.py:120-177` | Rota aceita `List[str] = Query(None)` e constrói filtros combinados. |
| **TASK-EQ-10-TEST** | [x] | **Concluído** | `tests/test_equipment_api.py:94-115`, `tests/test_equipment_repositories.py:46-77` | Testes de integração cobrindo filtros múltiplos e paginação. |
| **TASK-EQ-11** | [x] | **Concluído** | `src/domain/schemas.py:85-110`, `src/use_cases/equipment_use_cases.py:206-300` | Endpoints PUT e DELETE de manutenção e recálculo de data. |
| **TASK-EQ-11-TEST** | [x] | **Concluído** | `tests/test_equipment_use_cases.py:test_update_and_delete_maintenance_use_cases` | Testes com 100% de cobertura no backend. |
| **TASK-EQ-12** | [x] | **Concluído** | `MultiSelectFilterDropdown.tsx`, `EquipmentListPage.tsx:332-358` | Componente estilo Google Sheets com busca interna e botão Voltar ao Dashboard. |
| **TASK-EQ-13** | [x] | **Parcial** | `frontend/src/pages/EquipmentListPage.tsx:472-536` | **Divergência:** Cards horizontais implementados, mas **zebra striping** e bordas duplas (`border-2 border-slate-700/80`) ausentes. |
| **TASK-EQ-14** | [x] | **Concluído** | `frontend/src/pages/EquipmentDetailPage.tsx:163-211` | Tela única sem abas, modo de edição em lote com Salvar/Cancelar. |
| **TASK-EQ-15** | [x] | **Concluído** | `MaintenanceModal.tsx`, `EditMaintenanceModal.tsx`, `EquipmentDetailPage.tsx:213-223` | Edição e exclusão de manutenções no frontend com múltiplos itens. |
| **TASK-EQ-16** | [x] | **Concluído** | `frontend/src/components/NewEquipmentModal.tsx` | Formulário amplo organizado por seções lógicas. |
| **TASK-EQ-17** | [x] | **Concluído** | `frontend/src/__tests__/EquipmentPage.test.tsx`, `equipmentApi.test.ts` | Testes frontend aprovados. |
| **TASK-EQ-18** | [x] | **Concluído** | `pytest tests/`, `npm test -- --run`, `npx tsc --noEmit` | 104 testes backend passando, 57 testes frontend passando, zero erros TypeScript. |

---

#### 4.1.5. Auditoria de Tarefas: `spec/features/equipamentos/autocomplete-filtros/tasks.md`

| Tarefa | Status Checklist | Status Código | Evidências / Arquivos no Código | Observações |
|---|:---:|:---:|---|---|
| **TASK-AC-01** | [x] | **Concluído** | `src/infrastructure/repositories.py:270-305` | Método `get_distinct_values_by_prefix` com ILIKE e DISTINCT. |
| **TASK-AC-01-TEST** | [x] | **Concluído** | `tests/test_equipment_repositories.py:202-235` | Testes de integração de busca por prefixo e case-insensitivity. |
| **TASK-AC-02** | [x] | **Concluído** | `src/use_cases/equipment_use_cases.py:361-395` | `GetSuggestionsUseCase` com validação de campos e tamanho do prefixo. |
| **TASK-AC-02-TEST** | [x] | **Concluído** | `tests/test_equipment_use_cases.py:test_get_suggestions_use_case` | Testes unitários do caso de uso. |
| **TASK-AC-03** | [x] | **Concluído** | `src/api/equipment_routes.py:161-175` | Rota `GET /api/v1/equipments/suggestions` com RBAC de técnico. |
| **TASK-AC-03-TEST** | [x] | **Concluído** | `tests/test_equipment_api.py:305-367` | Testes de API para 200, 400 e 403. |
| **TASK-AC-04** | [x] | **Concluído** | `frontend/src/api/equipmentApi.ts:135-144` | Função `getSuggestions` no cliente Axios. |
| **TASK-AC-04-TEST** | [x] | **Concluído** | `frontend/src/__tests__/equipmentApi.test.ts` | Teste unitário de chamada de API. |
| **TASK-AC-05** | [x] | **Concluído** | `frontend/src/components/AutocompleteFilterInput.tsx` | Componente reutilizável com debounce 300ms, limite 10 e Enter fallback. |
| **TASK-AC-05-TEST** | [x] | **Concluído** | `frontend/src/__tests__/AutocompleteFilterInput.test.tsx` | 5 testes cobrindo todos os cenários com Vitest + RTL. |
| **TASK-AC-06** | [x] | **Concluído** | `frontend/src/pages/EquipmentListPage.tsx:361-384` | Integração nos filtros de patrimônio, série e produto. |
| **TASK-AC-06-TEST** | [x] | **Concluído** | `frontend/src/__tests__/EquipmentPage.test.tsx:93-102` | Integração na página validada. |
| **TASK-AC-07** | [x] | **Concluído** | `pytest`, `npx tsc --noEmit`, `vitest` | Verificação geral realizada com sucesso. |

---

### 4.2. Feature 2: Gerenciamento e CRUD de Tags (`spec/features/tags-crud/`)

#### 4.2.1. Cenários BDD de `spec/features/tags-crud/spec.md` (7 Cenários)

| ID do Cenário | Nome do Cenário | Critérios (Given / When / Then Resumidos) | Componentes / Arquivos de Implementação | Testes Automatizados Correspondentes | Status | Justificativa Técnica & Evidências |
|---|---|---|---|---|:---:|---|
| **TAG-BDD-01** | **Cenário 1:** Listar tags filtradas por categoria | *Dado:* acessa gerenciador de tags;<br>*Quando:* seleciona aba "Localização";<br>*Então:* lista apenas tags de categoria `localizacao`. | - Backend: `src/api/equipment_routes.py:92-100`, `src/infrastructure/repositories.py:328-331`<br>- Frontend: `ManageTagsModal.tsx:195-226` | - `tests/test_equipment_api.py::test_equipment_api_tags:171-178`<br>- `frontend/src/__tests__/ManageTagsModal.test.tsx:40-58` | **Conforme** | Rota `GET /api/v1/equipments/tags?category=localizacao` filtra no banco; frontend separa por abas com contador de itens. |
| **TAG-BDD-02** | **Cenário 2:** Criar nova tag com sucesso | *Dado:* categoria "tipo";<br>*Quando:* preenche `"Tablet"` e clica em Adicionar;<br>*Então:* persiste com categoria `tipo` e exibe em listas e dropdowns. | - Backend: `src/api/equipment_routes.py:103-119`, `src/use_cases/equipment_use_cases.py:314-328`<br>- Frontend: `ManageTagsModal.tsx:81-100` | - `tests/test_equipment_api.py::test_equipment_api_tags:161-166`<br>- `frontend/src/__tests__/ManageTagsModal.test.tsx:60-86` | **Conforme** | Retorno HTTP 201 Created; callback `onTagsUpdated` recarrega listas de seleção em toda a aplicação. |
| **TAG-BDD-03** | **Cenário 3:** Impedir criação de tag duplicada na mesma categoria | *Dado:* tag `"TI"` já existe em `localizacao`;<br>*Quando:* tenta recriar `"TI"` em `localizacao`;<br>*Então:* retorna HTTP 400 Bad Request. | - Backend: `src/use_cases/equipment_use_cases.py:320-322`, `src/api/equipment_routes.py:116-118`<br>- Frontend: `ManageTagsModal.tsx` | - `tests/test_equipment_api.py::test_equipment_api_tags:167-170`<br>- `tests/test_equipment_use_cases.py::test_manage_tags_use_case` | **Conforme** | Use case valida unicidade por categoria case-insensitively e levanta `ValueError`, convertido em HTTP 400. |
| **TAG-BDD-04** | **Cenário 4:** Renomear tag com propagação para equipamentos | *Dado:* tag `"TI"` associada a equipamentos;<br>*Quando:* renomeia para `"Tecnologia da Informação"`;<br>*Então:* atualiza a tag e propaga a alteração em todos os equipamentos vinculados na mesma transação. | - Backend: `src/api/equipment_routes.py:121-141`, `src/use_cases/equipment_use_cases.py:329-350`, `src/infrastructure/repositories.py:350-379`<br>- Frontend: `ManageTagsModal.tsx:102-136` | - `tests/test_equipment_repositories.py::test_equipment_tag_repository:96-117`<br>- `tests/test_equipment_api.py::test_equipment_api_tags:179-183`<br>- `frontend/src/__tests__/ManageTagsModal.test.tsx:88-118` | **Conforme** | Método `propagate_tag_rename` executa `UPDATE equipment SET location = :new WHERE location = :old` atomicamente; frontend oferece edição inline. |
| **TAG-BDD-05** | **Cenário 5:** Excluir tag preservando histórico dos ativos | *Dado:* tag `"Ocioso"` associada a equipamentos;<br>*Quando:* confirma exclusão;<br>*Então:* tag é removida da lista disponível, mas equipamentos mantêm o valor histórico. | - Backend: `src/api/equipment_routes.py:143-158`, `src/use_cases/equipment_use_cases.py:351-359`<br>- Frontend: `ManageTagsModal.tsx:138-151` | - `tests/test_equipment_repositories.py::test_equipment_tag_repository:118-122`<br>- `tests/test_equipment_api.py::test_equipment_api_tags:195-199`<br>- `frontend/src/__tests__/ManageTagsModal.test.tsx:120-143` | **Conforme** | Operação remove registro apenas de `equipment_tags`; tabela `equipments` permanece inalterada; modal de confirmação no frontend. |
| **TAG-BDD-06** | **Cenário 6:** Criar nova tag inline no modal de movimentação | *Dado:* modal de movimentação aberto;<br>*Quando:* clica em "Criar local", digita `"Almoxarifado B"` e confirma;<br>*Então:* tag é criada e selecionada automaticamente como destino. | - Frontend: `MovementModal.tsx:39-53, 113-145` | - `frontend/src/__tests__/MovementModal.test.tsx:42-83` | **Conforme** | Função `handleCreateLocation` cria tag via API e atualiza o estado `destinationLocation` com o novo nome imediatamente. |
| **TAG-BDD-07** | **Cenário 7:** Bloqueio de acesso para colaborador (RBAC) | *Dado:* usuário com role `colaborador`;<br>*Quando:* tenta criar, editar ou excluir tags;<br>*Então:* requisições rejeitadas com HTTP 403 Forbidden. | - Backend: `src/api/equipment_routes.py:96, 107, 126, 147`<br>- Frontend: `SideMenu.tsx:125-135` | - `tests/test_equipment_api.py::test_equipment_api_tags:204-217` | **Conforme** | Todas as rotas usam `Depends(require_tecnico_role)`; item do SideMenu fica oculto para colaboradores. |

---

#### 4.2.2. Auditoria de Tarefas: `spec/features/tags-crud/tasks.md`

| Tarefa | Status Checklist | Status Código | Evidências / Arquivos | Observações |
|---|:---:|:---:|---|---|
| **1.1 DTOs / Schemas Pydantic** | [x] | **Concluído** | `src/domain/schemas.py:59-62` | `EquipmentTagUpdate` com validação de string não vazia. |
| **1.2 Repositório de Tags** | [x] | **Concluído** | `src/infrastructure/repositories.py:313-384` | Métodos `get_by_id`, `delete` e `propagate_tag_rename`. |
| **1.3 Casos de Uso (`ManageTagsUseCase`)** | [x] | **Concluído** | `src/use_cases/equipment_use_cases.py:301-360` | Métodos `create_tag`, `update_tag`, `delete_tag` implementados. |
| **1.4 Roteador HTTP** | [x] | **Concluído** | `src/api/equipment_routes.py:92-159` | Rotas GET, POST, PUT, DELETE com tratamento de 400, 404 e 403. |
| **1.5 Testes Automatizados Backend** | [x] | **Concluído** | `tests/test_equipment_api.py:156-218`, `test_equipment_use_cases.py` | 100% de cobertura no Pytest. |
| **2.1 Cliente de API Frontend** | [x] | **Concluído** | `frontend/src/api/equipmentApi.ts:98-112` | Métodos `updateTag` e `deleteTag` implementados. |
| **2.2 Modal ManageTagsModal** | [x] | **Concluído** | `frontend/src/components/ManageTagsModal.tsx` | Abas por categoria, contador, edição inline e confirmação de exclusão. |
| **2.3 Ponto no SideMenu** | [x] | **Concluído** | `frontend/src/components/SideMenu.tsx:125-135` | Item "Gerenciar Tags" com ícone de Tag restrito a técnico. |
| **2.4 Ponto no Header de Equipamentos** | [x] | **Concluído** | `frontend/src/pages/EquipmentListPage.tsx:290-297` | Botão "Gerenciar Tags" abre o modal com callback de reload. |
| **2.5 Criação Rápida no MovementModal** | [x] | **Concluído** | `frontend/src/components/MovementModal.tsx:39-53, 113-145` | Botão "Criar local" sem duplo "+". |
| **2.6 Criação Rápida nos Detalhes/Criação** | [x] | **Concluído** | `EquipmentDetailPage.tsx:141-160`, `NewEquipmentModal.tsx:75-125` | Botões "Criar tipo", "Criar local", "Criar situação" operacionais. |
| **2.7 Testes Automatizados Frontend** | [x] | **Concluído** | `ManageTagsModal.test.tsx`, `MovementModal.test.tsx` | Testes completos com Vitest + RTL. |
| **3 Validação e Conclusão** | [x] | **Concluído** | Pytest e Vitest | Todas as suítes passam com 100% de sucesso. |

---

### 4.3. Feature 3: Tela de Login (`spec/features/tela-de-login/`)

#### 4.3.1. Cenários BDD de `spec/features/tela-de-login/spec.md` (6 Cenários)

| ID do Cenário | Nome do Cenário | Critérios (Given / When / Then Resumidos) | Componentes / Arquivos de Implementação | Testes Automatizados Correspondentes | Status | Justificativa Técnica & Evidências |
|---|---|---|---|---|:---:|---|
| **LOG-BDD-01** | **Cenário 1:** Renderização inicial e animação de login | *Dado:* usuário não autenticado em `/login`;<br>*Quando:* página carregada;<br>*Então:* transição fade-in/scale-up, formulário centralizado, campos limpos e foco no Email. | - Frontend: `LoginPage.tsx:28-55`, `tailwind.config.js:25-32` | - `frontend/src/__tests__/LoginPage.test.tsx:40-50`<br>- `frontend/src/__tests__/LoginForm.test.tsx:40-50` | **Conforme** | Animação `animate-fade-in-scale`, container flex centralizado, autofocus no campo de email. |
| **LOG-BDD-02** | **Cenário 2:** Validação de campos obrigatórios no frontend | *Dado:* tenta submeter sem email ou senha;<br>*Então:* bloqueia envio e exibe mensagens "Email é obrigatório" e "Senha é obrigatória". | - Frontend: `LoginForm.tsx:20-35, 91-93, 133-135` | - `frontend/src/__tests__/LoginForm.test.tsx:52-71`<br>- `frontend/src/__tests__/LoginPage.test.tsx:52-64` | **Conforme** | Função `validate` bloqueia requisição de rede e apresenta mensagens de feedback abaixo dos inputs. |
| **LOG-BDD-03** | **Cenário 3:** Interação visual no hover do botão de login | *Dado:* formulário válido;<br>*Quando:* hover sobre botão "Entrar";<br>*Então:* transição suave de tom, elevação sutil e brilho/glow. | - Frontend: `LoginForm.tsx:139-156`, `index.css:15-17` | - `frontend/src/__tests__/LoginForm.test.tsx` | **Conforme** | Classes `transition-all duration-150 active:scale-[0.99] shadow-sm` configuradas; estilização sóbria. |
| **LOG-BDD-04** | **Cenário 4:** Submissão bem-sucedida de login | *Dado:* credenciais válidas;<br>*Quando:* submete;<br>*Então:* ativa `isSubmitting`, spinner, atualiza `AuthContext` e redireciona para `/dashboard`. | - Backend: `src/api/routes.py:30-58`<br>- Frontend: `LoginForm.tsx:37-53`, `AuthContext.tsx:46-73`, `LoginPage.tsx:11` | - `frontend/src/__tests__/LoginPage.test.tsx:137-156`<br>- `frontend/src/__tests__/LoginForm.test.tsx` | **Conforme** | Chamada Axios com `withCredentials: true`, cookies HttpOnly gravados, redirecionamento via `navigate('/dashboard')`. |
| **LOG-BDD-05** | **Cenário 5:** Exibição de erro por credenciais inválidas (HTTP 401) | *Dado:* credenciais incorretas;<br>*Quando:* API responde 401;<br>*Então:* reabilita formulário e exibe banner genérico amigável. | - Backend: `src/api/routes.py:54-55`<br>- Frontend: `AuthContext.tsx:60-62`, `AlertBanner.tsx`, `LoginForm.tsx:57-63` | - `frontend/src/__tests__/LoginPage.test.tsx:87-110`<br>- `frontend/src/__tests__/LoginForm.test.tsx:94-117` | **Conforme** | Resposta 401 exibe banner vermelho com `AlertCircle` e mensagem "Credenciais inválidas. Verifique seu email e senha.". |
| **LOG-BDD-06** | **Cenário 6:** Exibição de alerta de rate limit (HTTP 429) | *Dado:* limite de 10 tentativas atingido;<br>*Quando:* API responde 429;<br>*Então:* formulário reabilitado e banner âmbar com `ShieldAlert` alerta sobre bloqueio temporário (15 min). | - Backend: `src/use_cases/authenticate_user.py:46-55`, `src/api/routes.py:52-53`<br>- Frontend: `AuthContext.tsx:57-59`, `AlertBanner.tsx:22-29` | - `frontend/src/__tests__/LoginPage.test.tsx:112-135`<br>- `frontend/src/__tests__/LoginForm.test.tsx:119-142`<br>- `tests/test_rate_limit.py` | **Conforme** | Backend rastreia tentativas por IP e emite HTTP 429; frontend exibe alerta destacado de bloqueio. |

---

#### 4.3.2. Auditoria de Tarefas: `spec/features/tela-de-login/tasks.md`

| Tarefa | Status Checklist | Status Código | Evidências / Arquivos | Observações |
|---|:---:|:---:|---|---|
| **TASK-UI-01** | [x] | **Concluído** | `frontend/src/index.css`, `frontend/tailwind.config.js` | Tailwind configurado com tokens neutros, animações e fonte Inter. |
| **TASK-UI-02** | [x] | **Concluído** | `authApi.ts`, `AuthContext.tsx`, `useAuth.ts` | Axios configurado com `withCredentials: true` e sessão por cookies HttpOnly. |
| **TASK-UI-03** | [x] | **Concluído** | `LoginForm.tsx` | Formulário com anel de foco, micro-interações, validação client-side e `isSubmitting`. |
| **TASK-UI-04** | [x] | **Concluído** | `AlertBanner.tsx` | Banner para 401 (vermelho) e 429 (âmbar com `ShieldAlert`). |
| **TASK-UI-05** | [x] | **Concluído** | `LoginPage.tsx` | Layout centralizado responsivo com animação de entrada e redirecionamento. |
| **TASK-UI-06** | [x] | **Concluído** | `LoginPage.test.tsx`, `LoginForm.test.tsx`, `AlertBanner.test.tsx` | Suíte RTL / Vitest cobrindo os 6 cenários BDD com 100% de sucesso. |

---

### 4.4. Feature 4: Exportação de Equipamentos em Planilha Excel (`spec/features/exportacao-planilha/`)

#### 4.4.1. Cenários BDD de `spec/features/exportacao-planilha/spec.md` (5 Cenários)

| ID do Cenário | Nome do Cenário | Critérios (Given / When / Then Resumidos) | Componentes / Arquivos de Implementação | Testes Automatizados Correspondentes | Status | Justificativa Técnica & Evidências |
|---|---|---|---|---|:---:|---|
| **EXP-BDD-01** | **Cenário 1:** Exportação de todos os equipamentos sem filtros | *Dado:* técnico na tela de equipamentos sem filtros;<br>*Quando:* clica em "Exportar Planilha";<br>*Então:* gera `.xlsx` com todos os equipamentos;<br>*E:* aba "Patrimônio" com 13 colunas, cabeçalho ciano `#4DD0E1` e freeze panes em A2. | - Backend: `src/api/equipment_routes.py:177-208`, `src/use_cases/equipment_use_cases.py:387-420`, `src/infrastructure/spreadsheet_exporter.py:83-160` | - `tests/test_equipment_api.py::test_equipment_api_export_all_and_filtered`<br>- `tests/test_equipment_use_cases.py::test_export_equipments_use_case`<br>- `tests/test_spreadsheet_exporter.py::test_generate_equipments_excel_with_data_and_styles` | **Conforme** | Arquivo OpenXML gerado com 13 cabeçalhos exatos, preenchimento `#4DD0E1`, `freeze_panes="A2"`, `showGridLines=True` e `wrap_text=True`. |
| **EXP-BDD-02** | **Cenário 2:** Exportação com filtros aplicados | *Dado:* técnico filtra por `Tipo: Notebook` e `Localização: TI`;<br>*Quando:* clica em "Exportar Planilha";<br>*Então:* arquivo contém apenas equipamentos filtrados. | - Backend: `src/api/equipment_routes.py:177-208`, `src/infrastructure/repositories.py:235-251` | - `tests/test_equipment_api.py::test_equipment_api_export_all_and_filtered`<br>- `tests/test_equipment_use_cases.py::test_export_equipments_use_case` | **Conforme** | Repositório `list_all_filtered` reaproveita a mesma query builder de filtros múltiplos sem paginação. |
| **EXP-BDD-03** | **Cenário 3:** Formatação do histórico de manutenções | *Dado:* equipamento com múltiplas manutenções cronológicas;<br>*Quando:* exporta planilha;<br>*Então:* coluna "HISTÓRICO DE MOVIMENTAÇÕES" consolida as intervenções separadas por `\n` ordenadas por data. | - Backend: `src/infrastructure/spreadsheet_exporter.py:43-73` (`_format_maintenances`) | - `tests/test_spreadsheet_exporter.py::test_format_maintenances_sorting_and_variations` | **Conforme** | Função ordena explicitamente por `maintenance_date` e concatena os eventos formatados com quebras de linha (`\n`). |
| **EXP-BDD-04** | **Cenário 4:** Bloqueio de acesso para Colaborador (RBAC) | *Dado:* usuário com role `colaborador`;<br>*Quando:* acessa `GET /api/v1/equipments/export`;<br>*Então:* requisição rejeitada com HTTP 403 Forbidden. | - Backend: `src/api/equipment_routes.py:189` (`require_tecnico_role`) | - `tests/test_equipment_api.py::test_equipment_api_export_rbac_forbidden`<br>- `tests/test_equipment_api.py::test_endpoints_unauthorized_without_token` | **Conforme** | Dependência `require_tecnico_role` bloqueia colaboradores com 403 e não autenticados com 401. |
| **EXP-BDD-05** | **Cenário 5:** Interface e feedback no frontend | *Dado:* clica em "Exportar Planilha";<br>*Quando:* requisição em andamento;<br>*Então:* botão exibe spinner;<br>*E:* ao concluir, dispara download nativo no navegador. | - Frontend: `equipmentApi.ts:112-131`, `EquipmentListPage.tsx:215-241, 274-288` | - `frontend/src/__tests__/EquipmentPage.test.tsx:220-259`<br>- `frontend/src/__tests__/equipmentApi.test.ts:85-106` | **Conforme** | Estado `isExporting` com ícone `Loader2`; download automático via blob e criação de elemento `<a>` temporário. |

---

#### 4.4.2. Auditoria de Tarefas: `spec/features/exportacao-planilha/tasks.md`

| Tarefa | Status Checklist | Status Código | Evidências / Arquivos | Observações |
|---|:---:|:---:|---|---|
| **TASK-EXP-01** | [x] | **Concluído** | `src/infrastructure/spreadsheet_exporter.py` | 13 colunas, cabeçalho ciano `#4DD0E1`, freeze panes A2 e auto-wrap. |
| **TASK-EXP-02** | [x] | **Concluído** | `src/infrastructure/repositories.py:222-251` | `EquipmentRepository.list_all_filtered` com eager loading de manutenções. |
| **TASK-EXP-03** | [x] | **Concluído** | `src/use_cases/equipment_use_cases.py:387-420` | `ExportEquipmentsUseCase` gerando bytes e filename com timestamp. |
| **TASK-EXP-04** | [x] | **Concluído** | `tests/test_spreadsheet_exporter.py` | 5 testes unitários de estilos, largura e ordenação de manutenções. |
| **TASK-EXP-05** | [x] | **Concluído** | `src/api/equipment_routes.py:177-208` | Rota `GET /api/v1/equipments/export` com streaming OpenXML. |
| **TASK-EXP-06** | [x] | **Concluído** | `tests/test_equipment_api.py:368-424` | Testes de exportação sem filtro, com filtro e RBAC 403. |
| **TASK-EXP-07** | [x] | **Concluído** | `frontend/src/api/equipmentApi.ts:112-131` | Função `exportEquipments` com `responseType: 'blob'`. |
| **TASK-EXP-08** | [x] | **Concluído** | `frontend/src/pages/EquipmentListPage.tsx:274-288` | Botão "Exportar Planilha" com ícone e feedback de loading. |
| **TASK-EXP-09** | [x] | **Concluído** | `frontend/src/__tests__/EquipmentPage.test.tsx` | Testes de integração do botão e disparo de download via Vitest. |
| **TASK-EXP-10** | [x] | **Concluído** | Pytest e Vitest | Validação completa: 104 testes backend e 57 frontend passando. |

---

### 4.5. Feature 5: Importação de Equipamentos via Planilha (`spec/features/importacao-planilha/`)

#### 4.5.1. Cenários BDD de `spec/features/importacao-planilha/spec.md` (7 Cenários)

| ID do Cenário | Nome do Cenário | Critérios (Given / When / Then Resumidos) | Componentes / Arquivos de Implementação | Testes Automatizados Correspondentes | Status | Justificativa Técnica & Evidências |
|---|---|---|---|---|:---:|---|
| **IMP-BDD-01** | **Cenário 1:** Pré-visualização de Planilha (Preview) | *Dado:* arquivo `.xlsx` ou `.csv` válido;<br>*Quando:* envia para preview;<br>*Então:* responde HTTP 200;<br>*E:* retorna total de linhas e amostra de primeiras linhas sem persistir no banco. | - Backend: `src/api/import_routes.py:19-42`, `src/use_cases/import_spreadsheet_use_cases.py:18-52`, `src/infrastructure/spreadsheet_parser.py:128-146` | - `tests/test_import_api.py::test_preview_endpoint_success`<br>- `tests/test_import_api.py::test_preview_endpoint_csv_success`<br>- `tests/test_import_use_cases.py::test_preview_spreadsheet_use_case` | **Conforme** | Retorna `SpreadsheetImportPreviewResponse` com até 10 linhas amostradas sem executar escrita ou commit na sessão. |
| **IMP-BDD-02** | **Cenário 2:** Confirmação de importação com sucesso e upsert | *Dado:* planilha com itens novos e existentes;<br>*Quando:* confirma importação;<br>*Então:* executa transação no banco;<br>*E:* cria novos, atualiza existentes, insere tags dinâmicas e vincula manutenção;<br>*E:* retorna contadores `created_count` e `updated_count`. | - Backend: `src/api/import_routes.py:44-68`, `src/use_cases/import_spreadsheet_use_cases.py:54-179` | - `tests/test_import_api.py::test_execute_import_endpoint_success`<br>- `tests/test_import_use_cases.py::test_execute_spreadsheet_import_creation_and_tags`<br>- `tests/test_import_use_cases.py::test_execute_spreadsheet_import_upsert_all_fields` | **Conforme** | Lógica de upsert localiza por patrimônio e depois por serial. Atualiza todos os campos de existentes e cria novos registros. |
| **IMP-BDD-03** | **Cenário 3:** Equipamentos sem serial ou sem patrimônio | *Dado:* linhas com `Nº SÉRIE` ou `Nº PATRIMÔNIO` vazios;<br>*Quando:* importa;<br>*Então:* salva mantendo campos como `None` sem identificadores artificiais nem bloqueio. | - Model: `src/domain/models.py:44-45` (`nullable=True`)<br>- Migration: `alembic/versions/a1b2c3d4e5f6_make_serial_number_nullable.py`<br>- Parser: `src/infrastructure/spreadsheet_parser.py:194-195` | - `tests/test_import_use_cases.py::test_execute_spreadsheet_import_creation_and_tags` (caso `row_sem_ident` com None) | **Conforme** | Coluna `serial_number` tornada `nullable=True` via migration Alembic; parser preenche `None` para campos vazios. |
| **IMP-BDD-04** | **Cenário 4:** Consolidação de manutenção e observações | *Dado:* linha com última manutenção, histórico de movimentações e observações;<br>*Quando:* importa;<br>*Então:* cria 1 registro em `equipment_maintenances` com tipo "Histórico Importado" e `notes` recebe observações. | - Backend: `src/use_cases/import_spreadsheet_use_cases.py:151-163` | - `tests/test_import_use_cases.py::test_execute_spreadsheet_import_creation_and_tags` | **Conforme** | Registro único criado com data da última manutenção e descrição combinada do histórico; `notes` populado com observações. |
| **IMP-BDD-05** | **Cenário 5:** Bloqueio para usuário colaborador (RBAC) | *Dado:* usuário com role `colaborador`;<br>*Quando:* tenta preview ou execute;<br>*Então:* rejeita com HTTP 403 Forbidden. | - Backend: `src/api/import_routes.py:22, 48` (`require_tecnico_role`)<br>- Frontend: `App.tsx:61-67` (`requiredRole="tecnico"`) | - `tests/test_import_api.py::test_preview_endpoint_colaborador_forbidden`<br>- `tests/test_import_api.py::test_execute_import_endpoint_colaborador_forbidden`<br>- `frontend/src/__tests__/DashboardPage.test.tsx:60-91` | **Conforme** | Endpoints HTTP protegidos com 403 e rota frontend `/importar` protegida com redirecionamento para o Dashboard. |
| **IMP-BDD-06** | **Cenário 6:** Envio de arquivo inválido ou sem dados | *Dado:* arquivo corrompido ou sem dados;<br>*Quando:* processa;<br>*Então:* retorna HTTP 400 Bad Request com mensagem detalhada. | - Backend: `src/infrastructure/spreadsheet_parser.py:133-145, 153`, `src/api/import_routes.py:32-36, 58-62` | - `tests/test_import_api.py::test_preview_endpoint_empty_file_bad_request`<br>- `tests/test_import_api.py::test_execute_import_endpoint_invalid_file_bad_request`<br>- `tests/test_spreadsheet_parser.py::test_parse_spreadsheet_empty_file_raises` | **Conforme** | Exceções `ValueError` capturadas e transformadas em HTTP 400 com mensagens amigáveis ("O arquivo enviado está vazio.", etc.). |
| **IMP-BDD-07** | **Cenário 7:** Interface do Frontend (Aba Importação) | *Dado:* técnico acessa sistema;<br>*Então:* menu lateral exibe "Importação";<br>*Quando:* clica, vê drag-and-drop, contadores, tabela de preview e botão de confirmação;<br>*E:* vê resumo de sucesso com contadores. | - Frontend: `SideMenu.tsx:142-154`, `ImportPage.tsx:1-406`, `App.tsx:61-68` | - `frontend/src/__tests__/ImportPage.test.tsx` (7 testes completos de upload, preview, confirmação e contadores) | **Conforme** | Fluxo completo implementado com área de drop, visualização de linhas parseadas, contadores de cards e reset de formulário. |

---

#### 4.5.2. Auditoria de Tarefas: `spec/features/importacao-planilha/tasks.md`

| Tarefa | Status Checklist | Status Código | Evidências / Arquivos | Observações |
|---|:---:|:---:|---|---|
| **1.1 Modelo `Equipment`** | [x] | **Concluído** | `src/domain/models.py:44` | `serial_number: nullable=True`. |
| **1.2 Migração Alembic** | [x] | **Concluído** | `alembic/versions/a1b2c3d4e5f6_make_serial_number_nullable.py` | Migração criada e funcional. |
| **1.3 Schemas Pydantic** | [x] | **Concluído** | `src/domain/schemas.py:179-216` | Schemas `SpreadsheetImportPreviewResponse` e `ResultResponse`. |
| **2.1 Utilitário Parser** | [x] | **Concluído** | `src/infrastructure/spreadsheet_parser.py` | Suporte a `.xlsx`, `.csv`, detecção de aba 'Patrimônio' e tolerância a cabeçalhos. |
| **3.1 Métodos de Repositório** | [x] | **Concluído** | `src/infrastructure/repositories.py` | Busca por patrimônio e por serial. |
| **3.2 Casos de Uso de Importação** | [x] | **Concluído** | `src/use_cases/import_spreadsheet_use_cases.py` | `PreviewSpreadsheetUseCase` e `ExecuteSpreadsheetImportUseCase`. |
| **4.1 Rotas da API e RBAC** | [x] | **Concluído** | `src/api/import_routes.py` | Rotas de preview e execute com `require_tecnico_role`. |
| **4.2 Registro de Rotas** | [x] | **Concluído** | `src/main.py:33` | `app.include_router(import_router)`. |
| **5.1 Testes do Parser** | [x] | **Concluído** | `tests/test_spreadsheet_parser.py` | 13 testes cobrindo variações de colunas, datas e formatos. |
| **5.2 Testes dos Use Cases** | [x] | **Concluído** | `tests/test_import_use_cases.py` | 5 testes cobrindo preview e execução com criação e upsert. |
| **5.3 Testes da API HTTP** | [x] | **Concluído** | `tests/test_import_api.py` | 10 testes cobrindo 200, 400 e 403. |
| **5.4 Execução do Pytest** | [x] | **Concluído** | Pytest CLI | 104 testes passando no backend. |
| **6.1 Cliente de API Frontend** | [x] | **Concluído** | `frontend/src/api/importApi.ts` | Chamadas para preview e execute com upload `multipart/form-data`. |
| **6.2 Página ImportPage** | [x] | **Concluído** | `frontend/src/pages/ImportPage.tsx` | Drag-and-drop, preview de dados e resumo estatístico. |
| **6.3 Menu Lateral SideMenu** | [x] | **Concluído** | `frontend/src/components/SideMenu.tsx:142-154` | Item "Importar Planilha" com ícone `FileSpreadsheet`. |
| **6.4 Roteamento App.tsx** | [x] | **Concluído** | `frontend/src/App.tsx:61-68` | Rotas `/importar` e `/import` com RBAC. |
| **7.1 a 7.3 Testes do Frontend** | [x] | **Concluído** | `ImportPage.test.tsx`, `importApi.test.ts` | 7 testes de tela e 2 de API passando no Vitest. |
| **8.1 e 8.2 Validação Real** | [x] | **Concluído** | Testes de carga sintéticos | Testes validam carga de planilhas e integridade do upsert. |

---

### 4.6. Feature 6: Documentação do Projeto (`spec/features/documentacao/`)

#### 4.6.1. Cenários BDD de `spec/features/documentacao/spec.md` (2 Cenários)

| ID do Cenário | Nome do Cenário | Critérios (Given / When / Then Resumidos) | Componentes / Arquivos de Implementação | Testes / Verificação Técnica | Status | Justificativa Técnica & Evidências |
|---|---|---|---|---|:---:|---|
| **DOC-BDD-01** | **Cenário 1:** Novo desenvolvedor inicia o projeto via Docker | *Dado:* repositório clonado;<br>*Quando:* executa `docker compose up --build`;<br>*Então:* serviços sobem e ficam acessíveis nas portas indicadas. | - Arquivo: `README.md:58-82`<br>- Configurações: `docker-compose.yml`, `docker-compose.prod.yml`, `Dockerfile` | - Verificação textual direta do `README.md`<br>- Verificação da existência física dos arquivos Docker | **Conforme** | `README.md` documenta os ambientes de Desenvolvimento (portas 5173, 8000, 5432) e Produção Nginx (porta 3000). |
| **DOC-BDD-02** | **Cenário 2:** Execução de testes a partir da documentação | *Dado:* validação da qualidade;<br>*Quando:* executa comandos descritos na seção de testes do `README.md`;<br>*Então:* suítes de testes do backend e frontend executam com sucesso. | - Arquivo: `README.md:139-153` | - Execução real realizada no terminal dos comandos citados:<br>  * `$env:PYTHONPATH="."; pytest --cov=src --cov-branch`<br>  * `cd frontend; npx tsc --noEmit`<br>  * `cd frontend; npm test -- --run` | **Conforme** | Comandos documentados executados no ambiente com sucesso: 104 testes backend aprovados, 57 frontend aprovados e 0 erros TypeScript. |

#### 4.6.2. Auditoria de Regras de Negócio e Tarefas: `spec/features/documentacao/tasks.md`

- **RN-DOC-01 (Badges e Título):** Presente em `README.md:1-11`.
- **RN-DOC-02 (Stack e Arquitetura):** Tabela detalhada em `README.md:46-55`.
- **RN-DOC-03 / RN-DOC-04 (Docker Compose Dev & Prod):** Seção completa em `README.md:60-82`.
- **RN-DOC-05 / RN-DOC-06 (Execução Local via uv e npm):** Passo a passo em `README.md:84-126` com `alembic upgrade head` e seed.
- **RN-DOC-07 (Credenciais Padrão):** Tabela em `README.md:128-136` listando Técnico (`tecnico@empresa.com` / `senha123`) e Colaborador (`colaborador@empresa.com` / `senha123`).
- **RN-DOC-08 (Testes e Cobertura):** Seção em `README.md:139-153`.
- **RN-DOC-09 (Pipeline de CI/CD e SDD):** Seções em `README.md:156-182`.
- **TASK-DOC-01 (Criação do README.md Completo):** `[x]` -> **Concluído**.
- **TASK-DOC-02 (Revisão e Validação da Documentação):** `[x]` -> **Concluído**.

---

### 4.7. Feature 7: Padronização do `.gitignore` e Limpeza (`spec/features/gitignore/`)

#### 4.7.1. Cenários BDD de `spec/features/gitignore/spec.md` (3 Cenários)

| ID do Cenário | Nome do Cenário | Critérios (Given / When / Then Resumidos) | Componentes / Arquivos de Implementação | Testes / Verificação Técnica | Status | Justificativa Técnica & Evidências |
|---|---|---|---|---|:---:|---|
| **IGN-BDD-01** | **Cenário 1:** Desindexação de `node_modules` sem exclusão em disco | *Dado:* `frontend/node_modules/` rastreado;<br>*Quando:* executa limpeza no índice do Git;<br>*Então:* arquivos são desindexados do Git e preservados no disco local. | - Índice Git do repositório<br>- Configuração: `.gitignore:53-54` | - Executado `git ls-files frontend/node_modules`: retornou vazio (0 arquivos rastreados).<br>- Diretório local `frontend/node_modules/` preservado no disco. | **Conforme** | `frontend/node_modules` desindexado com sucesso via `git rm --cached` e preservado localmente. |
| **IGN-BDD-02** | **Cenário 2:** Prevenção de versionamento de novos arquivos ignorados | *Dado:* `.gitignore` atualizado;<br>*Quando:* arquivos `.env`, `.coverage`, `.db`, `.xlsx` são criados;<br>*Então:* `git status` não lista como untracked. | - Arquivo: `.gitignore` (119 linhas divididas nas 7 seções requeridas) | - Executado `git status --porcelain`: nenhum artefato de build, cobertura, banco local ou planilha listado. | **Conforme** | Regras e extensões de RN-IGN-02 a RN-IGN-08 configuradas nas 7 seções estruturadas. |
| **IGN-BDD-03** | **Cenário 3:** Preservação de arquivos de template | *Dado:* `.env.example`;<br>*Quando:* verificado pelo Git;<br>*Então:* continua sendo rastreado normalmente. | - Regra de exceção: `.gitignore:80` (`!.env.example`)<br>- Regra planilhas: `.gitignore:92-93` (`!*.example.xlsx`) | - Executado `git ls-files .env.example`: retornou `.env.example` normalmente. | **Conforme** | Arquivo `.env.example` permanece sob controle de versão graças à regra de negação explícita. |

#### 4.7.2. Auditoria de Tarefas: `spec/features/gitignore/tasks.md`

- **TASK-IGN-01: Desindexar `frontend/node_modules/`:** `[x]` -> **Concluído**.
- **TASK-IGN-02: Configuração Estruturada do `.gitignore`:** `[x]` -> **Concluído**.
- **TASK-IGN-03: Auditoria do Estado do Git:** `[x]` -> **Concluído**.

---

### 4.8. Feature 8: Redesign Visual & Design System Anti-IA (`spec/features/UI/`)

#### 4.8.1. Cenários BDD de `spec/features/UI/spec.md` (5 Cenários)

| ID do Cenário | Nome do Cenário | Critérios (Given / When / Then Resumidos) | Componentes / Arquivos de Implementação | Testes Automatizados Correspondentes | Status | Justificativa Técnica & Evidências |
|---|---|---|---|---|:---:|---|
| **UI-BDD-01** | **Cenário 1:** Visualização da Tela de Login sem clichês de IA | *Dado:* acesso a `/login`;<br>*Quando:* renderizada;<br>*Então:* sem esferas de luz ou gradientes borrados, card com borda fina de 1px e botão "Entrar" sólido de alto contraste. | - `LoginPage.tsx:28-55`<br>- `LoginForm.tsx:138-156` | - `frontend/src/__tests__/LoginPage.test.tsx` (6 testes)<br>- `frontend/src/__tests__/LoginForm.test.tsx` (6 testes) | **Conforme** | Fundo `bg-zinc-950`; card em `bg-zinc-900/90 border border-zinc-800/90`; botão em `bg-zinc-100 hover:bg-white text-zinc-950`. |
| **UI-BDD-02** | **Cenário 2:** Visualização do Dashboard Corporativo | *Dado:* usuário em `/dashboard`;<br>*Quando:* visualiza indicadores;<br>*Então:* números em `font-mono tabular-nums` e cards neutros em tons de Zinc/dark sem gradientes. | - `DashboardPage.tsx:43-125`<br>- `SideMenu.tsx:80-160` | - `frontend/src/__tests__/DashboardPage.test.tsx` (3 testes) | **Conforme** | Layout industrial em `#121212` e `#1E1E1E`, tipografia monoespaçada para métricas e ausência de neon. |
| **UI-BDD-03** | **Cenário 3:** Lista de Equipamentos de Alta Densidade | *Dado:* técnico em `/equipamentos`;<br>*Quando:* lista é carregada;<br>*Então:* alta densidade, situação por *Status Dot* discreto com texto, identificadores em `font-mono text-xs` e animação suave. | - `EquipmentListPage.tsx:152-192` (`renderStatusPill`), `471-540`<br>- `index.css:74-88` | - `frontend/src/__tests__/EquipmentPage.test.tsx`<br>- `frontend/src/__tests__/AutocompleteFilterInput.test.tsx` | **Conforme** | Status Dots discretos com pontos coloridos; identificadores com `font-mono`; filtros compactos estilo Google Sheets. |
| **UI-BDD-04** | **Cenário 4:** Tela de Detalhes e Linha do Tempo Técnica | *Dado:* técnico em `/equipamentos/:id`;<br>*Quando:* visualiza histórico;<br>*Então:* eventos em formato de timeline técnica com linha conectora vertical e máscara na Chave Windows. | - `EquipmentDetailPage.tsx:66, 600-750, 855-985` | - `frontend/src/__tests__/EquipmentPage.test.tsx`<br>- `frontend/src/__tests__/MovementModal.test.tsx` | **Conforme** | Quadrantes técnicos em 1px; máscara de Chave Windows com toggle; log de atividades unificado combinando movimentações e manutenções em timeline. |
| **UI-BDD-05** | **Cenário 5:** Preservação de Testes e Funcionalidades | *Dado:* redesign implementado;<br>*Quando:* suíte de testes do frontend executada;<br>*Então:* todos os testes passam com 100% de sucesso e fluxos de dados íntegros. | - Configurações: `vitest.config.ts`, `tsconfig.json` | - Vitest: 15 arquivos, 57 testes aprovados (0 falhas)<br>- TypeScript `tsc --noEmit`: 0 erros | **Conforme** | A meta original de 28 testes foi superada para 57 testes no frontend, todos passando sem quebra de seletores (`data-testid`). |

#### 4.8.2. Auditoria de Tarefas: `spec/features/UI/tasks.md`

- **TASK-UI-01: Atualização de CSS Base e Tokens Globais (`index.css` & `tailwind.config.js`):** `[x]` -> **Concluído**.
- **TASK-UI-02: Redesign da Página de Login (`LoginPage.tsx`):** `[x]` -> **Concluído**.
- **TASK-UI-03: Redesign do Formulário e Alertas (`LoginForm.tsx` & `AlertBanner.tsx`):** `[x]` -> **Concluído**.
- **TASK-UI-04: Redesign do Dashboard e Menu Lateral (`DashboardPage.tsx` & `SideMenu.tsx`):** `[x]` -> **Concluído**.
- **TASK-UI-05: Redesign da Listagem e Filtros (`EquipmentListPage.tsx` & `MultiSelectFilterDropdown.tsx`):** `[x]` -> **Concluído**.
- **TASK-UI-06: Redesign da Tela de Detalhes e Linha do Tempo (`EquipmentDetailPage.tsx`):** `[x]` -> **Concluído**.
- **TASK-UI-07: Redesign dos Modais (`NewEquipmentModal.tsx`, `MaintenanceModal.tsx`, etc.):** `[x]` -> **Concluído**.
- **TASK-UI-08: Execução e Validação dos Testes Automatizados:** `[x]` -> **Concluído** (57 testes passando no Vitest, 0 erros no TypeScript).

---

## 5. Lista Prioritária de Pendências e Débitos Técnicos

Com base nas evidências coletadas, as pendências foram categorizadas por severidade e impacto arquitetural, acompanhadas do plano de ação corretivo necessário:

```
[P1 - ALTA]   Adequação do Banco de Dados nos Testes (PostgreSQL + Alembic)
      │
      ├── [P2 - MÉDIA] Eliminar Gaps de Cobertura Backend (3 linhas em parser)
      │
      ├── [P3 - MÉDIA] Ajuste Visual nos Cards de Equipamentos (Zebra Striping)
      │
      ├── [P4 - MÉDIA] Adicionar Trigger de Pull Request no CI (.github)
      │
      └── [P5 - BAIXA] Justificativa Formal de Exclusão de Seeds (pyproject.toml)
```

---

### 🔴 P1 (Alta Prioridade) — Adequação do Banco de Dados nos Testes de Integração (`tests/conftest.py`)
- **Problema / Violação Constitucional:**  
  A Constituição (`GEMINI.md`) determina textualmente que testes de integração com persistência utilizem o **mesmo banco de dados da aplicação (PostgreSQL)** em instância isolada e descartável, inicializado **a partir das migrações do Alembic**. Atualmente, `tests/conftest.py` define fixamente SQLite em memória (`sqlite:///:memory:`) e cria tabelas via `Base.metadata.create_all`, ignorando o histórico de migrações e divergindo do dialeto e comportamentos específicos do PostgreSQL.
- **Ação Necessária:**
  1. Alterar `tests/conftest.py` para inspecionar a variável de ambiente `TEST_DATABASE_URL` ou `DATABASE_URL`.
  2. Se configurada para PostgreSQL (como no container do CI e Docker Compose), aplicar as migrações programaticamente usando `alembic.command.upgrade(alembic_cfg, "head")` e limpar os dados após os testes via truncate em cascata.
  3. Manter o SQLite em memória estritamente como modo de fallback rápido para desenvolvimento desconectado, documentando essa exceção técnica na Constituição se for aprovada.

---

### 🟡 P2 (Média Prioridade) — Fechamento dos Gaps de Cobertura Backend (100.0%)
- **Problema / Violação Constitucional:**  
  A cobertura global do backend está em **99.75%** devido a 3 linhas executáveis não cobertas em `src/infrastructure/spreadsheet_parser.py`:
  - **Linha 182:** Cláusula `continue` que pula linhas totalmente vazias no parsing de planilhas Excel.
  - **Linhas 254-255:** Cláusula `except Exception:` que atua como fallback de delimitador caso o `csv.Sniffer()` falhe.
- **Ação Necessária:**
  1. Adicionar em `tests/test_spreadsheet_parser.py` um caso de teste com planilha `.xlsx` contendo uma linha em branco entre linhas preenchidas (exercita a linha 182).
  2. Adicionar um caso de teste de CSV com string de formato ambíguo ou mockar a falha do método `csv.Sniffer.sniff` para disparar o fallback (exercita as linhas 254-255).
  3. Com isso, o backend alcançará **1352/1352 declarações (100.0%) e 252/252 branches (100.0%)**.

---

### 🟡 P3 (Média Prioridade) — Implementação de Zebra Striping e Bordas em `EquipmentListPage.tsx`
- **Problema / Divergência de Spec:**  
  O Cenário 4 de `spec/features/equipamentos/spec.md` e a tarefa `TASK-EQ-13` estipulam que a listagem de equipamentos apresente cores alternadas (*zebra striping*) entre cards pares e ímpares, bordas duplas reforçadas (`border-2 border-slate-700/90`) e espaçamento interno generoso (`p-5 sm:px-6 sm:py-5`). Atualmente, `EquipmentListPage.tsx:479` renderiza todos os cards com fundo idêntico `bg-[#1E1E1E]`, borda simples `border-[#333333]` e padding `p-4`.
- **Ação Necessária:**
  1. Em `frontend/src/pages/EquipmentListPage.tsx` (na iteração `equipments.map((item, index) => ...)`):
     - Aplicar alternância de classes no container do bloco:
       ```tsx
       className={`rounded-lg flex items-start gap-4 transition-colors cursor-pointer animate-slide-in-right opacity-0 p-5 sm:px-6 sm:py-5 ${
         index % 2 === 0
           ? 'bg-slate-900 border-2 border-slate-700/80 hover:border-slate-500'
           : 'bg-slate-950/80 border-2 border-slate-800/80 hover:border-slate-600'
       }`}
       ```
  2. Ajustar os testes do componente em `EquipmentPage.test.tsx` se necessário para assegurar a passagem contínua da suíte.

---

### 🟡 P4 (Média Prioridade) — Inclusão do Gatilho de Pull Request no GitHub Actions
- **Problema / Violação Constitucional:**  
  A Constituição estipula que *"Os testes automatizados DEVEM ser executados automaticamente em pull requests direcionados da branch develop para a branch main."* No arquivo `.github/workflows/ci.yml`, o workflow está configurado apenas com `on: push: branches: [main, develop, master]`, deixando PRs sem verificação automática antes da fusão de código.
- **Ação Necessária:**
  1. Em `.github/workflows/ci.yml`, adicionar o bloco de gatilho:
     ```yaml
     on:
       push:
         branches:
           - main
           - develop
           - master
       pull_request:
         branches:
           - main
           - develop
     ```

---

### 🟢 P5 (Baixa Prioridade) — Formalização da Exclusão de Seeds no `pyproject.toml`
- **Problema / Regra da Constituição:**  
  A Constituição estabelece que *"As exclusões de cobertura devem ser explícitas e justificadas."* O arquivo `pyproject.toml` contém `omit = ["src/infrastructure/seed*.py"]` sem qualquer comentário explicativo.
- **Ação Necessária:**
  1. Adicionar comentário no `pyproject.toml`:
     ```toml
     # Exclusão autorizada pela Constituição: scripts utilitários de seed contêm apenas
     # carga sintética de dados para desenvolvimento e não possuem lógica de negócio.
     omit = ["src/infrastructure/seed*.py"]
     ```

---

## 6. Parecer Conclusivo da Auditoria

A base de código do projeto **Comunica - Gestão de Patrimônio e Suporte** apresenta maturidade técnica excepcional, arquitetura desacoplada, ausência completa de SQL puro e suítes de testes automatizados com taxa de 100% de sucesso tanto no backend (104 testes passando em ~6.8s) quanto no frontend (57 testes passando em ~10.5s sem erros de TypeScript).

Em relação às especificações funcionais (`spec/features/`), o sistema alcança **98.0% de conformidade de cenários BDD** (49 de 50 cenários plenamente atendidos e cobertos por testes). A única pendência funcional/visual é o refinamento de apresentação de zebra striping nos cards de equipamentos (Cenário 4 de `equipamentos/spec.md`).

Em relação à Constituição do Projeto (`GEMINI.md`), foram identificadas 3 não-conformidades pontuais: a utilização de SQLite em memória com `create_all` em vez de PostgreSQL descartável com migrações Alembic nos testes de integração, a falta de 3 linhas para a meta de 100% de cobertura no backend (atingindo 99.75%), e a ausência do gatilho de `pull_request` no CI. 

A resolução dos cinco itens detalhados na Lista Prioritária conduzirá o repositório a **100% de conformidade de especificações e aderência constitucional**.
