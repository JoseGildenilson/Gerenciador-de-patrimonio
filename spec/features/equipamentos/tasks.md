# Plano de Tarefas: Ajustes & Melhorias na Gestão de Equipamentos (Patrimônio)

---

## FASE 1: Ajustes no Backend & Suporte a Filtros Múltiplos e Manutenções

### [x] TASK-EQ-10: Suporte a Filtros Múltiplos no Repositório e Endpoints
- **Objetivo:** Permitir passar múltiplos valores para os filtros (`type`, `location`, `status`, `patrimony_number`, `serial_number`, `product_number`) no backend.
- **Detalhamento:**
  - Atualizados os schemas Pydantic e os parâmetros da rota GET em `src/api/equipment_routes.py` para aceitar `List[str] = Query(None)`.
  - Atualizado `EquipmentRepository.list_paginated_and_filtered` em `src/infrastructure/repositories.py` para construir cláusulas SQL `in_` ou múltiplas cláusulas `LIKE` (lógica OR interna para o mesmo filtro, AND entre filtros diferentes).
- **[x] TASK-EQ-10-TEST (Testes Pytest):**
  - Adicionados testes de repositório e de integração API validando consultas combinadas com múltiplos tipos, localizações e números de série (`tests/test_equipment_api.py` e `tests/test_equipment_use_cases.py`).

### [x] TASK-EQ-11: Refatoração do Modelo/DTO de Manutenção & Edição/Exclusão
- **Objetivo:** Suportar múltiplos itens por manutenção, remover obrigatoriedade de "tipo de manutenção", e criar endpoints de atualização e exclusão de manutenções.
- **Detalhamento:**
  - Atualizados os schemas `EquipmentMaintenanceCreate`, `EquipmentMaintenanceUpdate` e `EquipmentMaintenanceResponse` em `src/domain/schemas.py`.
  - Criados casos de uso `UpdateMaintenanceUseCase` e `DeleteMaintenanceUseCase` em `src/use_cases/equipment_use_cases.py`.
  - Implementados endpoints em `src/api/equipment_routes.py`:
    - `PUT /api/v1/equipments/{equipment_id}/maintenances/{maintenance_id}`
    - `DELETE /api/v1/equipments/{equipment_id}/maintenances/{maintenance_id}`
  - Garantido que a criação, edição ou exclusão de manutenção atualize a data de `last_maintenance_at` no equipamento.
- **[x] TASK-EQ-11-TEST (Testes Pytest):**
  - Adicionados testes unitários para os novos casos de uso e testes de API para edição e exclusão de manutenções com 100% de cobertura no Pytest.

---

## FASE 2: Frontend — Componentes, Filtros Google Sheets & Cards com Respiro e Zebra Striping

### [x] TASK-EQ-12: Componente de Filtro com Busca Interna e Seleção Múltipla (Google Sheets)
- **Objetivo:** Criar o componente `MultiSelectFilterDropdown` e integrá-lo à barra de filtros de `EquipmentListPage.tsx`.
- **Detalhamento:**
  - Criado o componente `MultiSelectFilterDropdown.tsx` contendo:
    - Campo de busca textual interna.
    - Lista de opções com *checkboxes*.
    - Ação "Desmarcar tudo" específica para aquele filtro.
    - Exibição de estado visual no botão principal (ex.: `Tipo (2)`).
  - Atualizado `EquipmentListPage.tsx` para gerenciar os estados de lista em cada filtro e o botão global "Limpar filtros".
  - Adicionado botão **"← Voltar ao Dashboard"** direcionando para `/dashboard` (RN-EQ-06).

### [x] TASK-EQ-13: Refatoração dos Cards de Equipamento (Layout Horizontal Limpo, Respiro & Zebra Striping)
- **Objetivo:** Garantir visualização limpa com espaçamento generoso e bordas destacadas para diferenciação dos blocos.
- **Detalhamento:**
  - Layout horizontal limpo restaurado (Ícone + Descrição + Marca + Tipo + Metadados Inline + Data da Última Manutenção no canto direito).
  - Adicionado respiro generoso (`space-y-4` entre itens e `p-5.5` de padding interno).
  - Aplicadas **bordas duplas bem destacadas (`border-2`)** e **cores intercaladas (*zebra striping*)** entre itens pares (`bg-slate-900 border-2 border-slate-700/80 shadow-md`) e ímpares (`bg-slate-950/80 border-2 border-slate-800/80 shadow-md`).

---

## FASE 3: Frontend — Tela de Detalhes Única, Edição em Lote & Gestão de Manutenção

### [x] TASK-EQ-14: Refatoração da Tela de Detalhes (Tela Única, Botão Voltar & Edição em Lote)
- **Objetivo:** Transformar a tela de detalhes em uma visualização única (sem abas de navegação para a info do equipamento), com navegação de retorno e edição de todos os campos.
- **Detalhamento:**
  - Adicionado botão **"← Voltar para equipamentos"** direcionando para `/equipamentos`.
  - Implementado o botão **"Editar equipamento"** que alterna toda a tela para o modo de edição simultânea dos campos cadastrais.
  - Exibidos botões **"Salvar alterações"** e **"Cancelar"** durante o modo de edição.

### [x] TASK-EQ-15: Gestão de Manutenções no Histórico (Múltiplos Itens, Edição e Exclusão)
- **Objetivo:** Permitir adicionar manutenções com múltiplos itens, editar registros existentes e excluir registros diretamente no histórico.
- **Detalhamento:**
  - Atualizado `MaintenanceModal.tsx` para permitir registrar múltiplos itens por manutenção.
  - Adicionados botões **"Editar"** e **"Excluir"** em cada card de manutenção no histórico de `EquipmentDetailPage.tsx`.
  - Criado o modal `EditMaintenanceModal.tsx` para edição de manutenções existentes.
  - Atualizado `equipmentApi.ts` com funções `updateMaintenance` e `deleteMaintenance`.

### [x] TASK-EQ-16: Refatoração da Tela/Modal de Cadastro de Equipamento
- **Objetivo:** Ampliar a área útil do formulário de novo equipamento (`NewEquipmentModal.tsx`).
- **Detalhamento:**
  - Aumentado padding, tamanhos de fonte de *labels* e *inputs*, distribuindo melhor as seções (Identificação, Localização/Situação, Rede, Licenciamento, Manutenção e Observações).

---

## FASE 4: Testes Frontend & Verificação Geral

### [x] TASK-EQ-17: Testes Automatizados no Frontend (Vitest & RTL)
- **Objetivo:** Garantir 100% de cobertura e passagem de todos os testes no frontend.
- **[x] TASK-EQ-17-TEST (Vitest):**
  - Atualizado `equipmentApi.test.ts` testando os métodos `updateMaintenance`, `deleteMaintenance` e filtros múltiplos.
  - Atualizado `EquipmentPage.test.tsx` testando a seleção múltipla nos dropdowns de filtro, edição em lote na tela de detalhes, e adição/edição/exclusão de manutenções (28/28 testes passando).

### [x] TASK-EQ-18: Verificação de Compilação & Suíte Integrada
- **Objetivo:** Validar execução de toda a suíte de testes no backend (Pytest) e frontend (Vitest + TSC).
- **Verificações Realizadas:**
  - `PYTHONPATH=. ./.venv/bin/pytest tests/ --cov=src --cov-branch` (**63/63 testes aprovados com 100% de cobertura nos arquivos do módulo**).
  - `npx tsc --noEmit` (**0 erros de compilação**).
  - `npx vitest run` (**28/28 testes frontend aprovados**).
