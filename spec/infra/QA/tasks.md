# Plano de Tarefas de QA: Execução da Auditoria e Blindagem da Suíte

Este documento detalha o plano operacional de tarefas para implementar as melhorias, correções de segurança, fechamento de lacunas de cobertura e garantia da conformidade com a [Constituição do Projeto](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/spec/constituicao.md), conforme estruturado no plano de ação [`plan.md`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/spec/infra/QA/plan.md).

---

## 1. Matriz de Rastreabilidade (Auditoria x Tarefas)

| Item da Auditoria | Severidade | Descrição Resumida | Tarefa de Implementação |
|---|:---:|---|---|
| **CRIT-01** | [CRÍTICO] | Violação constitucional de persistência (SQLite vs PostgreSQL e Migrations não testadas) | **TASK-QA-13**, **TASK-QA-14** |
| **CRIT-02** | [CRÍTICO] | Bypass de rate limit por spoofing de cabeçalho `X-Forwarded-For` | **TASK-QA-03** |
| **CRIT-03** | [CRÍTICO] | Entropia criptográfica não testada e vulnerabilidade de salt estático no fallback | **TASK-QA-02** |
| **ALTO-01** | [ALTO] | Cobertura superficial na tela de detalhes (`EquipmentDetailPage`) sem testar edições/exclusão | **TASK-QA-08** |
| **ALTO-02** | [ALTO] | Ausência de testes para `MultiSelectFilterDropdown` (RN-EQ-03/04 e Cenários BDD 1-3) | **TASK-QA-06** |
| **ALTO-03** | [ALTO] | Ausência de testes para modais `MaintenanceModal` e `EditMaintenanceModal` | **TASK-QA-07** |
| **MED-01** | [MÉDIO] | Asserção inócua de exportação Excel no teste de API (`len(content) > 0`) | **TASK-QA-09** |
| **MED-02** | [MÉDIO] | Erro assíncrono no JSDOM durante teste de download (`navigation not implemented`) | **TASK-QA-11** |
| **MED-03** | [MÉDIO] | Lacuna de cobertura no backend (L182 e L254-255 de `spreadsheet_parser.py`) | **TASK-QA-01** |
| **MED-04** | [MÉDIO] | Warnings de `act(...)` no frontend em `AuthProvider` | **TASK-QA-12** |
| **BAIX-01** | [BAIXO] | Protótipos e componentes mortos inflando a métrica de cobertura do frontend | **TASK-QA-10** |
| **BAIX-02** | [BAIXO] | Ausência de `pythonpath = ["."]` no `pyproject.toml` | **TASK-QA-05** |
| **CR-BUG-01**| [ALTO] | Impossibilidade de limpar `patrimony_number` e `hostname` na atualização de Equipamento | **TASK-QA-04** |

---

## 2. Lista de Tarefas de Implementação

### 🚀 Fase 1: Segurança, 100% Backend e Correções Críticas (Prioridade Máxima)

- [x] **TASK-QA-01: Atingir 100% de Cobertura de Linhas e Branches no Backend (Art. 2.4 da Constituição)**
  - [x] Criar caso de teste em [`tests/test_spreadsheet_parser.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_spreadsheet_parser.py) processando uma planilha Excel contendo linhas em branco intercaladas entre registros válidos (cobrindo a linha 182 de `spreadsheet_parser.py`).
  - [x] Criar caso de teste em [`tests/test_spreadsheet_parser.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_spreadsheet_parser.py) processando arquivo CSV cujo conteúdo faça `csv.Sniffer().sniff()` lançar exceção, exercitando o fallback manual de delimitador (cobrindo linhas 254-255).
  - [x] *Arquivos Afetados:* [`tests/test_spreadsheet_parser.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_spreadsheet_parser.py).
  - *Critério de Aceite:* `pytest --cov=src --cov-branch` atinge rigorosamente **100% de cobertura** sem exclusões indevidas.

- [x] **TASK-QA-02: Teste de Entropia Criptográfica e Correção de Salt Dinâmico (CRIT-03)**
  - [x] Criar teste unitário em [`tests/test_security.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_security.py) garantindo que chamadas sucessivas de `hash_password` para a mesma senha gerem hashes distintos (`assert hash_password("senha") != hash_password("senha")`).
  - [x] Refatorar a função de fallback em [`src/core/security.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/src/core/security.py#L24-L46) para gerar salt criptograficamente aleatório e único via `os.urandom(16)` e extraí-lo na verificação.
  - [x] *Arquivos Afetados:* [`tests/test_security.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_security.py), [`src/core/security.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/src/core/security.py).
  - *Critério de Aceite:* Testes validam unicidade de salts para senhas idênticas tanto no caminho padrão Argon2id quanto no fallback.

- [x] **TASK-QA-03: Testes de Penetração contra IP Spoofing e Blindagem de Rate Limiting (CRIT-02)**
  - [x] Criar casos de teste em [`tests/test_rate_limit.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_rate_limit.py) e [`tests/test_api.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_api.py) simulando ataques de força bruta com cabeçalhos `X-Forwarded-For` forjados/rotativos originados do mesmo host.
  - [x] Ajustar a função `_extract_client_ip` em [`src/api/routes.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/src/api/routes.py#L20-L30) para validar se o cliente remoto é um proxy confiável homologado antes de aceitar cabeçalhos de proxy.
  - [x] *Arquivos Afetados:* [`tests/test_rate_limit.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_rate_limit.py), [`tests/test_api.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_api.py), [`src/api/routes.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/src/api/routes.py).
  - *Critério de Aceite:* Ataques com IP forjado no cabeçalho não burlam o bloqueio de 10 tentativas.

- [x] **TASK-QA-04: Teste e Correção da Limpeza de Campos Opcionais na Atualização de Ativos (CR-BUG-01)**
  - [x] Criar teste em [`tests/test_equipment_use_cases.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_equipment_use_cases.py) verificando se o envio de `patrimony_number=None` (ou `""`) e `hostname=None` (ou `""`) limpa os campos no banco sem disparar falsos erros de validação de duplicidade.
  - [x] Corrigir `UpdateEquipmentUseCase.execute` em [`src/use_cases/equipment_use_cases.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/src/use_cases/equipment_use_cases.py#L143-L151) para tratar explicitamente campos opcionais quando informados como nulos ou vazios.
  - [x] *Arquivos Afetados:* [`tests/test_equipment_use_cases.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_equipment_use_cases.py), [`src/use_cases/equipment_use_cases.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/src/use_cases/equipment_use_cases.py).
  - *Critério de Aceite:* Testes confirmam que o técnico consegue remover números de patrimônio e hostname previamente salvos.

- [x] **TASK-QA-05: Configuração de Execução Direta do Pytest no pyproject.toml (BAIX-02)**
  - [x] Adicionar `pythonpath = ["."]` na seção `[tool.pytest.ini_options]` de [`pyproject.toml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/pyproject.toml#L29-L34).
  - [x] *Arquivos Afetados:* [`pyproject.toml`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/pyproject.toml).
  - *Critério de Aceite:* Executar `pytest` diretamente a partir da raiz sem necessidade de configurar `PYTHONPATH=.` manualmente.

---

### 🛡️ Fase 2: Blindagem e Cobertura do Frontend (Eliminação de Pontos Cegos)

- [x] **TASK-QA-06: Suíte de Testes para o Componente de Filtro Múltiplo (ALTO-02)**
  - [x] Criar `frontend/src/__tests__/MultiSelectFilterDropdown.test.tsx` cobrindo:
    - [x] Renderização fechada e abertura/fechamento ao clicar no gatilho.
    - [x] Filtragem de opções pelo campo de pesquisa interna.
    - [x] Seleção e desmarcação múltipla via checkboxes (validação do callback `onChange`).
    - [x] Clique no botão "Desmarcar tudo" zerando as opções selecionadas.
    - [x] Fechamento automático ao clicar fora do elemento (`mousedown` externo).
  - [x] *Arquivos Criados:* `frontend/src/__tests__/MultiSelectFilterDropdown.test.tsx`.
  - *Critério de Aceite:* Cobertura de linhas do componente salta de 38% para > 95%.

- [x] **TASK-QA-07: Suíte de Testes para Modais de Registro e Edição de Manutenção (ALTO-03)**
  - [x] Criar `frontend/src/__tests__/MaintenanceModal.test.tsx` cobrindo:
    - [x] Validação de campo obrigatório (descrição vazia bloqueia o envio).
    - [x] Preenchimento e envio com sucesso chamando `equipmentApi.recordMaintenance`.
    - [x] Estado de desabilitado/loading no botão de salvar.
    - [x] Exibição de mensagem de erro ao receber rejeição da API (HTTP 400/500).
    - [x] Acionamento dos callbacks `onSuccess` e `onClose`.
  - [x] Criar `frontend/src/__tests__/EditMaintenanceModal.test.tsx` cobrindo:
    - [x] Preenchimento automático com os dados da manutenção selecionada.
    - [x] Alteração de dados e submissão com sucesso chamando `equipmentApi.updateMaintenance`.
    - [x] Tratamento de falhas e fechamento do modal.
  - [x] *Arquivos Criados:* `frontend/src/__tests__/MaintenanceModal.test.tsx`, `frontend/src/__tests__/EditMaintenanceModal.test.tsx`.
  - *Critério de Aceite:* Cobertura de funções de ambos os modais sobe de 20% para > 90%.

- [x] **TASK-QA-08: Testes Aprofundados da Tela de Detalhes do Equipamento (ALTO-01)**
  - [x] Criar `frontend/src/__tests__/EquipmentDetailPage.test.tsx` (desmembrando o teste cosmético de `EquipmentPage.test.tsx`):
    - [x] Carregamento inicial em tela única com todas as seções (sem abas - RN-EQ-07).
    - [x] Ativação do modo de edição em lote, alteração de múltiplos campos e clique em "Salvar alterações".
    - [x] Verificação da chamada a `equipmentApi.updateEquipment` com os dados editados.
    - [x] Simulação de erro da API na atualização com exibição de alerta de falha.
    - [x] Alternância de exibição da Chave Windows mascarada (`••••••••`) para revelada via botão Mostrar/Ocultar (RN-EQ-14).
    - [x] Fluxo de exclusão de manutenção do histórico com chamada a `equipmentApi.deleteMaintenance` (Cenário BDD 7).
    - [x] Abertura dos modais de movimentação e manutenção a partir dos botões da tela.
  - [x] *Arquivos Criados/Afetados:* `frontend/src/__tests__/EquipmentDetailPage.test.tsx`, [`frontend/src/__tests__/EquipmentPage.test.tsx`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/src/__tests__/EquipmentPage.test.tsx).
  - *Critério de Aceite:* Cobertura de funções de `EquipmentDetailPage.tsx` sobe de 18% para > 80%.

- [x] **TASK-QA-09: Suíte de Testes para o Menu Lateral Retrátil (SideMenu)**
  - [x] Criar `frontend/src/__tests__/SideMenu.test.tsx` cobrindo:
    - [x] Estado recolhido por padrão ao carregar (RN-01 do Dashboard).
    - [x] Abertura e fechamento ao clicar no botão de alternância.
    - [x] Fechamento ao pressionar tecla `Escape` e ao clicar fora do menu.
    - [x] Exibição exclusiva do item "Patrimônio" para o perfil `tecnico` e ocultação para `colaborador` (RN-02 / RN-04).
    - [x] Abertura do modal de gerenciamento de tags a partir do botão no menu lateral.
  - [x] *Arquivos Criados:* `frontend/src/__tests__/SideMenu.test.tsx`.
  - *Critério de Aceite:* Cobertura de funções do `SideMenu.tsx` sobe de 41% para > 85%.

---

### 🧹 Fase 3: Higienização de Métricas e Estabilização dos Testes

- [x] **TASK-QA-10: Isolamento de Protótipos e Código Morto no vite.config.ts (BAIX-01)**
  - [x] Adicionar `'src/prototypes/**'`, `'src/components/AnimatedCounter.tsx'` e `'src/api/dashboardApi.ts'` no array `coverage.exclude` de [`frontend/vite.config.ts`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/vite.config.ts#L26-L33).
  - [x] Avaliar a remoção definitiva dos arquivos mortos não referenciados pela aplicação.
  - [x] *Arquivos Afetados:* [`frontend/vite.config.ts`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/vite.config.ts).
  - *Critério de Aceite:* O relatório de cobertura do frontend reflete fidedignamente o código de produção ativo.

- [x] **TASK-QA-11: Correção do Mock de Download no JSDOM (MED-02)**
  - [x] Em [`frontend/src/__tests__/EquipmentPage.test.tsx`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/src/__tests__/EquipmentPage.test.tsx#L231-L236) ou no setup global `setup.ts`, interceptar `HTMLAnchorElement.prototype.click = vi.fn()`.
  - [x] *Arquivos Afetados:* [`frontend/src/__tests__/EquipmentPage.test.tsx`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/src/__tests__/EquipmentPage.test.tsx).
  - *Critério de Aceite:* Eliminação definitiva do erro `Error: Not implemented: navigation (except hash changes)` nos logs de execução do Vitest.

- [x] **TASK-QA-12: Estabilização de Ciclos Assíncronos e Eliminação de Warnings de act(...) (MED-04)**
  - [x] Ajustar testes em [`frontend/src/__tests__/ImportPage.test.tsx`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/src/__tests__/ImportPage.test.tsx) e `DashboardPage.test.tsx` para aguardar resoluções assíncronas do `AuthProvider` via `await waitFor(() => ...)` antes de desmontar o componente.
  - [x] *Arquivos Afetados:* [`frontend/src/__tests__/ImportPage.test.tsx`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/frontend/src/__tests__/ImportPage.test.tsx).
  - *Critério de Aceite:* Execução limpa do Vitest sem warnings de `act(...)`.

- [x] **TASK-QA-13: Inspeção Estrutural Binária no Teste de Exportação Excel (MED-01)**
  - [x] Atualizar [`tests/test_equipment_api.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_equipment_api.py#L369-L416) carregando o binário via `openpyxl.load_workbook(io.BytesIO(resp_filtered.content))`.
  - [x] Validar a presença da aba "Patrimônio", as 13 colunas na ordem correta e a exata quantidade de linhas filtradas.
  - [x] *Arquivos Afetados:* [`tests/test_equipment_api.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/test_equipment_api.py).
  - *Critério de Aceite:* Teste valida o conteúdo binário real gerado pela rota de exportação.

---

### 🏛️ Fase 4: Persistência Real e Migrations Alembic (Conformidade Constitucional)

- [x] **TASK-QA-14: Teste Automatizado das Migrations do Alembic (CRIT-01)**
  - [x] Criar teste unitário em `tests/test_migrations.py` executando o ciclo completo de migrações: `alembic upgrade head` seguido de `alembic downgrade base` e novo `upgrade head`.
  - [x] *Arquivos Criados:* `tests/test_migrations.py`.
  - *Critério de Aceite:* Validação automatizada de integridade de todas as migrations presentes em `alembic/versions/`.

- [x] **TASK-QA-15: Transição para PostgreSQL Isolado em Ambiente de Teste/CI (Art. 3.3 da Constituição)**
  - [x] Configurar fixture no `tests/conftest.py` para permitir conexão com banco PostgreSQL real descartável quando a variável `TEST_DATABASE_URL` for fornecida.
  - [x] Atualizar pipeline do GitHub Actions para instanciar serviço PostgreSQL dedicado para a execução da suíte de testes.
  - [x] *Arquivos Afetados:* [`tests/conftest.py`](file:///C:/Users/70486375447/orca/workspaces/comunica-projeto/conch/tests/conftest.py), `.github/workflows/ci.yml`.
  - *Critério de Aceite:* Suíte de integração executando sobre PostgreSQL idêntico ao ambiente produtivo, em estrita conformidade com o Artigo 3 da Constituição.

---

## 3. Critérios de Conclusão e Definição de Pronto (DoD)

Para que o plano de QA seja considerado concluído, as seguintes condições devem ser satisfeitas:

1. **Backend:** 100% de cobertura em linhas e branches no Pytest (`--cov-fail-under=100`), sem falhas em nenhum teste.
2. **Frontend:** Cobertura de linhas superior a 85% em componentes e páginas de produção, com 100% dos fluxos de modais e tela de detalhes testados.
3. **Logs Limpos:** Zero warnings de `act(...)` e zero erros não tratados no JSDOM.
4. **Segurança:** Testes de invasão validando proteção de brute-force contra IP spoofing e salts criptograficamente aleatórios.
5. **Constituição:** Testes rodando sobre migrations e aderentes à política de transações e persistência.
