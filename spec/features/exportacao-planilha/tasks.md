# Plano de Tarefas: Exportação de Equipamentos em Planilha (.xlsx)

Este documento define o plano detalhado de implementação para a funcionalidade de **Exportação de Equipamentos em Planilha Excel**, mapeando cada requisito da especificação [`spec.md`](file:///home/gil/code/internal_management/spec/features/exportacao-planilha/spec.md) e garantindo conformidade com a [`constituicao.md`](file:///home/gil/code/internal_management/spec/constituicao.md).

---

## Mapeamento de Requisitos da Especificação

| Requisito / Regra | Descrição | Tarefa Correspondente |
|---|---|---|
| **RN-EXP-01** | Controle de Acesso: Endpoint restrito a `tecnico` (`HTTP 403` para colaborador). | **TASK-EXP-05**, **TASK-EXP-06** |
| **RN-EXP-02 / RN-EXP-03** | Escopo dos Dados: Respeitar filtros ativos na tela ou exportar todos. | **TASK-EXP-02**, **TASK-EXP-03**, **TASK-EXP-05**, **TASK-EXP-08** |
| **RN-EXP-04 / RN-EXP-05** | Formato `.xlsx`, aba "Patrimônio" e nome dinâmico com timestamp. | **TASK-EXP-01**, **TASK-EXP-03**, **TASK-EXP-05** |
| **RN-EXP-06** | 13 Colunas canônicas na ordem exata do modelo `PATRIMÔNIO CTM.xlsx`. | **TASK-EXP-01**, **TASK-EXP-03** |
| **RN-EXP-07** | Formatação cronológica de manutenções com quebras de linha na célula. | **TASK-EXP-01**, **TASK-EXP-03** |
| **RN-EXP-08 a RN-EXP-11** | Estilização fiel (Cabeçalho Ciano `#4DD0E1`, Freeze Panes, larguras de coluna e Wrap Text). | **TASK-EXP-01** |
| **RN-EXP-12 / RN-EXP-13** | Botão "Exportar Planilha" no cabeçalho de equipamentos com loading state e download. | **TASK-EXP-07**, **TASK-EXP-08**, **TASK-EXP-09** |
| **Cenários 1 a 5** | Validação BDD completa e cobertura 100%. | **TASK-EXP-04**, **TASK-EXP-06**, **TASK-EXP-09**, **TASK-EXP-10** |

---

## Lista de Tarefas de Implementação

### Fase 1: Backend — Utilitário de Exportação e Repositório
- [x] **TASK-EXP-01: Utilitário Gerador de Planilha Excel (`src/infrastructure/spreadsheet_exporter.py`)**
  - [x] Implementar a função `generate_equipments_excel(equipments: list[Equipment]) -> bytes` usando `openpyxl`.
  - [x] Criar aba "Patrimônio".
  - [x] Inserir os 13 cabeçalhos canônicos com cor de fundo `#4DD0E1`, fonte Arial/Calibri, alinhamento central e altura ajustada.
  - [x] Aplicar congelamento de painel na linha 1 (`ws.freeze_panes = "A2"`).
  - [x] Definir larguras proporcionais para cada coluna.
  - [x] Preencher as linhas de dados mapeando cada campo e formatando datas (`last_maintenance_at`) e manutenções cronológicas com quebras de linha (`\n`).
  - [x] Habilitar quebra automática de texto (`wrap_text=True`) e linhas de grade (`ws.views.sheetView[0].showGridLines = True`).
  - [x] Retornar os bytes binários do arquivo Excel via `io.BytesIO`.

- [x] **TASK-EXP-02: Método de Consulta Não-Paginada no Repositório (`EquipmentRepository.list_all_filtered`)**
  - [x] Criar método `list_all_filtered` em `src/infrastructure/repositories.py` com suporte aos mesmos filtros da listagem paginada.
  - [x] Aplicar *eager loading* em `Equipment.maintenances` (`selectinload(Equipment.maintenances)`) para evitar problema de N+1 queries.

- [x] **TASK-EXP-03: Caso de Uso de Exportação (`ExportEquipmentsUseCase`)**
  - [x] Criar o caso de uso `ExportEquipmentsUseCase` em `src/use_cases/equipment_use_cases.py`.
  - [x] Receber os parâmetros de filtro, consultar o repositório e invocar `generate_equipments_excel`.
  - [x] Retornar os bytes gerados e o nome sugerido do arquivo formatado (`PATRIMONIO_YYYY-MM-DD_HHMM.xlsx`).

- [x] **TASK-EXP-04: Testes Unitários do Gerador e Use Case (100% Cobertura)**
  - [x] Criar `tests/test_spreadsheet_exporter.py` validando estrutura das colunas, dados preenchidos, formatação de manutenções e estilos da planilha.
  - [x] Adicionar testes para `ExportEquipmentsUseCase` em `tests/test_equipment_use_cases.py`.

---

### Fase 2: Backend — Endpoint HTTP e RBAC
- [x] **TASK-EXP-05: Rota HTTP `GET /api/v1/equipments/export`**
  - [x] Adicionar rota em `src/api/equipment_routes.py` protegida por `require_tecnico_role`.
  - [x] Receber query params: `types`, `locations`, `statuses`, `patrimony_numbers`, `serial_numbers`, `product_numbers`, `search`, `sort_by`, `sort_order`.
  - [x] Retornar `Response(content=file_bytes, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="{filename}"'})`.

- [x] **TASK-EXP-06: Testes de API HTTP para Exportação**
  - [x] Criar testes em `tests/test_equipment_api.py` cobrindo:
    - Download de todos os equipamentos (Cenário 1).
    - Download filtrado (Cenário 2).
    - Formatação do histórico de manutenções (Cenário 3).
    - Bloqueio para usuário colaborador com status HTTP 403 (Cenário 4).
    - Acesso negado para usuário desautenticado (HTTP 401).

---

### Fase 3: Frontend — Integração e Download
- [x] **TASK-EXP-07: Função de API no Frontend (`equipmentApi.exportEquipments`)**
  - [x] Adicionar método `exportEquipments` em `frontend/src/api/equipmentApi.ts` configurado para `responseType: 'blob'`.

- [x] **TASK-EXP-08: Botão "Exportar Planilha" na Página de Equipamentos (`EquipmentListPage.tsx`)**
  - [x] Adicionar botão "Exportar Planilha" com ícone `FileSpreadsheet` no cabeçalho ao lado de "Gerenciar Tags".
  - [x] Implementar estado `isExporting` com feedback visual (spinner) durante o download.
  - [x] Coletar os filtros atualmente selecionados e acionar a chamada da API, disparando o download do arquivo via URL de objeto temporário (`window.URL.createObjectURL(blob)`).

- [x] **TASK-EXP-09: Testes Automatizados no Frontend (Vitest)**
  - [x] Adicionar testes em `frontend/src/__tests__/equipmentApi.test.ts` para a rota de exportação.
  - [x] Adicionar testes em `frontend/src/__tests__/EquipmentPage.test.tsx` testando clique no botão de exportação e estado de loading.

---

### Fase 4: Validação Geral e Verificação de 100% de Cobertura
- [x] **TASK-EXP-10: Auditoria Completa da Suíte de Testes**
  - [x] Executar `pytest --cov=src --cov-branch` garantindo 100% de cobertura no backend.
  - [x] Executar `npx tsc --noEmit` garantindo zero erros de tipagem.
  - [x] Executar `npm test -- --run` garantindo aprovação de todos os testes no frontend.
