# Plano de Tarefas: Importação de Planilha (.xlsx / .csv)

## 1. Banco de Dados e Modelos
- [x] 1.1 Atualizar o modelo `Equipment` em `src/domain/models.py` para tornar `serial_number` opcional (`nullable=True`).
- [x] 1.2 Criar migração Alembic para alterar a coluna `serial_number` para `nullable=True` na tabela `equipments`.
- [x] 1.3 Atualizar schemas Pydantic em `src/domain/schemas.py` para aceitar `serial_number: str | None = None` em criação/edição e schemas de importação (`SpreadsheetImportPreviewResponse`, `SpreadsheetImportResultResponse`, etc.).

## 2. Utilitário de Leitura e Sanitização de Planilhas
- [x] 2.1 Criar utilitário `src/infrastructure/spreadsheet_parser.py` para leitura de arquivos `.xlsx` e `.csv`:
  - Leitura da aba `Patrimônio` ou primeira aba com cabeçalhos compatíveis.
  - Normalização e tolerância a variações de nomes de colunas e espaços em branco.
  - Conversão de datas (`ÚLTIMA MANUTENÇÃO`) com tolerância a formatos diversos.
  - Extração limpa dos campos (`equipment_type`, `location`, `status`, `patrimony_number`, `serial_number`, `brand`, `hostname`, `windows_key`, `product_number`, `hist_mov`, `notes`).

## 3. Repositórios e Casos de Uso
- [x] 3.1 Adicionar métodos auxiliares no repositório de equipamentos se necessário (ex: busca por serial ou patrimônio).
- [x] 3.2 Implementar o caso de uso `src/use_cases/import_spreadsheet_use_cases.py`:
  - `preview_spreadsheet(file_bytes, filename)`: retorna estatísticas e primeiras linhas formatadas.
  - `execute_spreadsheet_import(file_bytes, filename, db_session)`: executa o processamento em lote, inserção/atualização de tags, upsert de equipamentos, consolidação de manutenção única e observações dentro da mesma transação.

## 4. Rotas da API e RBAC
- [x] 4.1 Criar rotas em `src/api/import_routes.py`:
  - `POST /api/v1/equipments/import/preview` (Upload de arquivo, RBAC: `tecnico`).
  - `POST /api/v1/equipments/import/execute` (Execução de importação, RBAC: `tecnico`).
- [x] 4.2 Registrar as novas rotas no `src/main.py`.

## 5. Testes Automatizados do Backend (100% de Cobertura)
- [x] 5.1 Criar testes unitários para o parser de planilhas (`tests/test_spreadsheet_parser.py`).
- [x] 5.2 Criar testes unitários para os casos de uso de importação (`tests/test_import_use_cases.py`).
- [x] 5.3 Criar testes de integração/API (`tests/test_import_api.py`) validando:
  - Preview com sucesso (.xlsx e .csv).
  - Execução de importação com criação e atualização (upsert).
  - RBAC (perfil `colaborador` recebendo 403).
  - Tratamento de arquivos vazios, inválidos ou sem colunas esperadas (HTTP 400).
- [x] 5.4 Executar `pytest` com verificação de 100% de cobertura de linhas e branches.

## 6. Frontend: Interface de Importação
- [x] 6.1 Adicionar cliente de API em `frontend/src/api/importApi.ts`.
- [x] 6.2 Criar componente de página `frontend/src/pages/ImportPage.tsx` com:
  - Área de drag-and-drop / seleção de arquivo (.xlsx, .csv).
  - Painel de pré-visualização com total de linhas e preview em tabela.
  - Botão de confirmação de importação com loading state.
  - Relatório/Feedback de conclusão com estatísticas e botão para redirecionar para a lista de equipamentos.
- [x] 6.3 Atualizar o menu lateral `frontend/src/components/SideMenu.tsx` para incluir o item "Importação" (com ícone `FileSpreadsheet` do Lucide), visível apenas para técnicos.
- [x] 6.4 Integrar a rota `/importar` e `/import` no `frontend/src/App.tsx` protegida por autenticação e RBAC.

## 7. Testes Automatizados do Frontend
- [x] 7.1 Criar testes unitários e de integração para `ImportPage` e `importApi` (`frontend/src/__tests__/ImportPage.test.tsx`, `frontend/src/__tests__/importApi.test.ts`).
- [x] 7.2 Atualizar testes do `SideMenu.test.tsx` / `App.test.tsx` para cobrir o novo item de menu.
- [x] 7.3 Executar toda a suíte de testes do frontend com Vitest.

## 8. Validação e Execução
- [x] 8.1 Testar a importação real com o arquivo `PATRIMÔNIO CTM.xlsx`.
- [x] 8.2 Validar que os ~588 equipamentos e suas manutenções e tags foram carregados perfeitamente.
