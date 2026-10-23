# Plano de Tarefas: Padronização do .gitignore e Limpeza de Dependências

Este documento define o plano detalhado de tarefas para a padronização do arquivo `.gitignore` e a limpeza de dependências versionadas indevidamente, em conformidade com a especificação [`spec.md`](file:///home/gil/code/internal_management/spec/features/gitignore/spec.md) e com a [`constituicao.md`](file:///home/gil/code/internal_management/spec/constituicao.md).

---

## Mapeamento de Requisitos da Especificação

| Requisito / Regra | Descrição | Tarefa Correspondente |
|---|---|---|
| **RN-IGN-01** | Desindexação de `frontend/node_modules/` do Git sem remover do disco. | **TASK-IGN-01** |
| **RN-IGN-02 a RN-IGN-08** | Estruturação e preenchimento completo do arquivo `.gitignore`. | **TASK-IGN-02** |
| **Cenários 1 a 3** | Validação com `git status` e verificação de integridade do workspace. | **TASK-IGN-03** |

---

## Lista de Tarefas de Implementação

### Fase 1: Limpeza do Índice do Git
- [x] **TASK-IGN-01: Desindexar `frontend/node_modules/`**
  - [x] Executar `git rm -r --cached frontend/node_modules` para remover os ~12.000 arquivos do índice de rastreamento do Git.
  - [x] Garantir que os arquivos permaneçam intactos no disco local.

---

### Fase 2: Configuração Estruturada do `.gitignore`
- [x] **TASK-IGN-02: Atualização do `.gitignore`**
  - [x] Adicionar seções para Python & venv (`__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `*.egg-info/`, etc.).
  - [x] Adicionar seções para Testes & Cobertura (`.pytest_cache/`, `.coverage`, `htmlcov/`, `coverage/`, `frontend/coverage/`).
  - [x] Adicionar seções para Node.js & Frontend (`node_modules/`, `frontend/node_modules/`, `dist/`, `frontend/dist/`, `frontend/build/`, `.vite/`).
  - [x] Adicionar seções para Variáveis de Ambiente (`.env`, `.env.*`, com exceção `!.env.example`).
  - [x] Adicionar seções para Bancos de Dados & Planilhas (`*.db`, `*.sqlite`, `*.sqlite3`, `internal_management.db`, `*.xlsx`, `*.xls`).
  - [x] Adicionar seções para Logs & Temporários (`*.log`, `tmp/`).
  - [x] Adicionar seções para IDEs & OS (`.vscode/`, `.idea/`, `.DS_Store`, `Thumbs.db`).

---

### Fase 3: Validação
- [x] **TASK-IGN-03: Auditoria do Estado do Git**
  - [x] Executar `git status` e verificar que `node_modules`, `.env`, `.coverage`, `.db` e `.xlsx` não são exibidos como não rastreados.
  - [x] Executar testes para garantir que nada foi afetado no funcionamento do sistema.
