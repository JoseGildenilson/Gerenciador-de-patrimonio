# Guia de Tarefas e Correções para o Agente Implementador

Este documento detalha cada uma das tarefas pendentes de correção identificadas pela auditoria de testes e validação do sistema.

Localização canônica das tasks: `specs/001-gerenciamento-patrimonio/tasks.md` (Fase 8: T058 a T069).

---

## 1. Violações Constitucionais e Nomenclatura

### [T058] Remoção de Arquivo Legado
- **Arquivo**: `internal_management.db` (raiz do projeto)
- **Problema**: O arquivo viola a regra de nomenclatura da Constituição em `GEMINI.md`:
  > *"É estritamente proibido o uso de `internal_management`, `internal-management` ou variações em qualquer arquivo, configuração, container, pacote, banco de dados ou documentação."*
- **Ação**: Excluir o arquivo `internal_management.db` da raiz do repositório.

### [T059] Correção do Nome do Volume de Dados
- **Arquivo**: `docker-compose.yml` (linha 107)
- **Problema**: Declarado como `name: patrimonio_postgres_data`. A Constituição estipula:
  > *"Identificadores Oficiais: Rede e Volumes Docker: `patrimonio_net`, `patrimonio_data`"*
- **Ação**: Renomear para `name: patrimonio_data` na seção `volumes.postgres_data`.

---

## 2. Configuração Docker Prod

### [T060] Correção de Host no Docker Compose Prod
- **Arquivo**: `docker-compose.prod.yml` (linha 11)
- **Problema**: A variável de ambiente está definida como:
  ```yaml
  DATABASE_URL: postgresql://postgres:postgres@localhost:5432/patrimonio_db
  ```
  Em ambiente de containers Docker interligados por rede bridge, `localhost` faz o container backend tentar conectar em si próprio em vez de conectar ao container `postgres`.
- **Ação**: Alterar para:
  ```yaml
  DATABASE_URL: postgresql://postgres:postgres@postgres:5432/patrimonio_db
  ```

---

## 3. Linter Backend (Ruff)

Ao executar `uv run ruff check .`, foram encontrados 8 erros na pasta `tests/`:

### [T061] Ajustar Imports em tests/conftest.py
- **Arquivo**: `tests/conftest.py` (linhas 57 e 61)
- **Erro**: `E402 Module level import not at top of file`
- **Causa**: Variáveis de ambiente como `TEST_DATABASE_URL` são setadas antes de importar `settings` e `core_db`.
- **Ação**: Adicionar `# noqa: E402` nas linhas onde a injeção prévia do ambiente for necessária, ou reorganizar mantendo a precedência correta das variáveis de ambiente.

### [T062] Eliminar Imports Redundantes em tests/test_equipment_schemas.py
- **Arquivo**: `tests/test_equipment_schemas.py` (linha 141)
- **Erro**: `F811 Redefinition of unused validate_host_ip / EquipmentUpdate from lines 8/23`
- **Ação**: Na função `test_schema_edge_cases()`, remover as redefinições e importar apenas o que ainda não estiver no escopo global do módulo.

### [T063] Renomear Variável Ambígua em tests/test_spreadsheet_exporter.py
- **Arquivo**: `tests/test_spreadsheet_exporter.py` (linhas 96, 97, 98, 99)
- **Erro**: `E741 Ambiguous variable name: l`
- **Ação**: Alterar a variável de iteração `l` por um nome descritivo (ex: `line`):
  ```python
  assert any("Limpeza básica" in line for line in lines)
  assert any("15/01/2022: Atualização de SO" in line for line in lines)
  assert any("10/05/2024: Troca de SSD (Obs: SSD 500GB)" in line for line in lines)
  assert any("01/03/2025" in line for line in lines)
  ```

---

## 4. Cobertura de Testes Frontend (Meta: 100% Linhas e Branches)

Conforme a Constituição (Princípio 4):
> *"Todo código executável DEVE possuir cobertura de testes automatizados de 100%, considerando linhas e branches."*

### [T064] Testes para ErrorBoundary
- **Arquivo a testar**: `frontend/src/components/ErrorBoundary.tsx`
- **Arquivo de teste**: `frontend/src/__tests__/ErrorBoundary.test.tsx`
- **Cenários requeridos**:
  1. Renderização normal dos componentes filhos (sem erro).
  2. Captura de erro em componente filho (disparo de `componentDidCatch`).
  3. Renderização do fallback UI customizado e do botão "Recarregar página" / reset.
  4. Cobertura dos métodos `getDerivedStateFromError` e `handleReset`.

### [T065] Testes para errorUtils
- **Arquivo a testar**: `frontend/src/utils/errorUtils.ts`
- **Arquivo de teste**: `frontend/src/__tests__/errorUtils.test.ts`
- **Cenários requeridos**:
  1. Resposta de erro padrão da API com `detail` como string.
  2. Resposta de erro 422 com array de validação do FastAPI (`msg`, `loc`).
  3. Erro de rede sem resposta do servidor (`error.request`).
  4. Objeto de erro padrão JS (`Error`) com mensagem genérica.
  5. Valores não-padrão (nulos, indefinidos, strings puras).

### [T066, T067, T068] Cobertura Residual de Páginas
- **EquipmentDetailPage**: Cobrir branches condicionais residuais nas linhas 978, 1050 e 1052 em `frontend/src/__tests__/EquipmentDetailPage.test.tsx`.
- **EquipmentListPage**: Cobrir paginação e botões condicionais nas linhas 502, 518 e 520 em `frontend/src/__tests__/EquipmentPage.test.tsx`.
- **ImportPage**: Cobrir ramificações de upload, feedback de erro e parsing nas linhas 76, 368-378 e 386 em `frontend/src/__tests__/ImportPage.test.tsx`.

---

## 5. Validação Final

### [T069] Execução de Testes e Checagens Globais
O agente implementador deve rodar os seguintes comandos para garantir a conclusão:
1. `uv run ruff check .`
2. `PYTHONPATH=. uv run pytest --cov=src --cov-branch --cov-fail-under=100`
3. `cd frontend && npm run test` (confirmar 100% de cobertura nos componentes ajustados)
4. `cd frontend && npm run build`
