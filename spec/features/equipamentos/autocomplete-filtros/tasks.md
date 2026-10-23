# Plano de Tarefas: Autocomplete nos Filtros de Patrimônio, Série e Produto

---

## FASE 1: Backend — Endpoint de Sugestões

### [x] TASK-AC-01: Método de sugestões no EquipmentRepository
- **Objetivo:** Adicionar método `get_distinct_values_by_prefix` ao `EquipmentRepository` que retorna valores distintos de um campo filtrados por prefixo.
- **Detalhamento:**
  - Método recebe `field` (nome da coluna), `prefix` (texto digitado) e `limit` (máximo de resultados, padrão 10).
  - Realiza `SELECT DISTINCT <campo>` com `WHERE <campo> ILIKE '<prefix>%'` e `LIMIT`.
  - Campos válidos: `patrimony_number`, `serial_number`, `product_number`.
  - Filtra valores `NULL` (não retorna nulos).
  - Ordena os resultados em ordem alfabética.
- **[x] TASK-AC-01-TEST:**
  - Testes de integração validando: busca por prefixo, case-insensitive, limite de resultados, exclusão de nulos, ordenação (`tests/test_equipment_repositories.py`).

### [x] TASK-AC-02: Use Case GetSuggestionsUseCase
- **Objetivo:** Criar caso de uso `GetSuggestionsUseCase` que valida os parâmetros e delega ao repositório.
- **Detalhamento:**
  - Valida que `field` é um dos campos permitidos (`patrimony_number`, `serial_number`, `product_number`).
  - Valida que `prefix` tem pelo menos 2 caracteres.
  - Lança `ValueError` com mensagem descritiva em caso de parâmetros inválidos.
  - Retorna lista de strings distintas.
- **[x] TASK-AC-02-TEST:**
  - Testes unitários validando: campo válido, campo inválido (ValueError), prefixo curto (ValueError), delegação ao repositório (`tests/test_equipment_use_cases.py`).

### [x] TASK-AC-03: Endpoint GET /api/v1/equipments/suggestions
- **Objetivo:** Criar rota HTTP que expõe as sugestões de autocomplete.
- **Detalhamento:**
  - `GET /api/v1/equipments/suggestions` com parâmetros `field`, `prefix`, `limit` (padrão 10, máximo 50).
  - Protegido por `require_tecnico_role`.
  - Retorna `list[str]` com os valores sugeridos.
  - Retorna HTTP 400 para campo inválido ou prefixo insuficiente.
  - **Posição no roteador:** Rota registrada antes da rota `/{id}`.
- **[x] TASK-AC-03-TEST:**
  - Testes de API validando: resposta bem-sucedida, campo inválido (400), prefixo curto (400), autenticação (403), limite de resultados (`tests/test_equipment_api.py`).

---

## FASE 2: Frontend — Componente de Autocomplete e Integração

### [x] TASK-AC-04: Método getSuggestions no equipmentApi
- **Objetivo:** Adicionar função `getSuggestions` ao client HTTP do frontend.
- **Detalhamento:**
  - `getSuggestions(field: string, prefix: string, limit?: number): Promise<string[]>`
  - Chama `GET /api/v1/equipments/suggestions` com os parâmetros.
- **[x] TASK-AC-04-TEST:**
  - Teste unitário validando a chamada HTTP correta (`frontend/src/__tests__/equipmentApi.test.ts`).

### [x] TASK-AC-05: Componente AutocompleteFilterInput
- **Objetivo:** Criar componente React reutilizável `AutocompleteFilterInput` que substitui os `<input>` atuais.
- **Detalhamento:**
  - Props: `field`, `placeholder`, `selectedValues`, `onAddValue`, `testId`.
  - Exibe dropdown de sugestões posicionado abaixo do input.
  - Debounce de 300ms antes de consultar a API.
  - Mínimo de 2 caracteres para disparar consulta.
  - Filtra valores já presentes em `selectedValues` das sugestões exibidas.
  - Ao clicar numa sugestão, chama `onAddValue(valor)` e limpa o input.
  - Mantém o `onKeyDown` com Enter para adicionar valor livre.
  - Fecha o dropdown ao clicar fora (click outside) ou pressionar Escape.
  - Exibe badge de contagem quando há valores selecionados (igual ao comportamento atual).
  - Estilo visual consistente com o design system escuro existente.
- **[x] TASK-AC-05-TEST:**
  - Testes com Vitest + RTL: exibição de sugestões, seleção por clique, entrada livre via Enter, ocultação de selecionados, fechamento do dropdown (`frontend/src/__tests__/AutocompleteFilterInput.test.tsx`).

### [x] TASK-AC-06: Integração na EquipmentListPage
- **Objetivo:** Substituir os 3 `<input>` atuais de Patrimônio, Série e Produto pelo componente `AutocompleteFilterInput`.
- **Detalhamento:**
  - Substituição dos blocos de input no `EquipmentListPage.tsx`.
  - Conectar cada instância ao `equipmentApi.getSuggestions` com o `field` correspondente.
  - Manter toda a lógica existente de chips, limpeza e filtros.
- **[x] TASK-AC-06-TEST:**
  - Testes de integração no `EquipmentListPage` validando o fluxo completo de autocomplete (`frontend/src/__tests__/EquipmentPage.test.tsx`).

---

## FASE 3: Verificação Geral

### [x] TASK-AC-07: Execução da Suíte Completa de Testes
- **Objetivo:** Validar que todos os testes passam e a cobertura permanece em 100%.
- **Verificações Realizadas:**
  - `PYTHONPATH=. ./.venv/bin/pytest tests/ --cov=src --cov-branch` (**66/66 testes aprovados com 100% de cobertura no backend**).
  - `npx tsc --noEmit` (**0 erros de compilação**).
  - `npm test -- --run` (**46/46 testes aprovados em 13 arquivos no frontend**).

