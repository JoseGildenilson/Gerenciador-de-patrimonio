# Plano de Tarefas: Documentação do Projeto (README.md)

Este documento define o plano detalhado de tarefas para a criação da documentação completa do projeto no `README.md`, atendendo aos requisitos da especificação [`spec.md`](file:///home/gil/code/internal_management/spec/features/documentacao/spec.md) e da [`constituicao.md`](file:///home/gil/code/internal_management/spec/constituicao.md).

---

## Mapeamento de Requisitos da Especificação

| Requisito / Regra | Descrição | Tarefa Correspondente |
|---|---|---|
| **RN-DOC-01** | Visão geral, título e badges de tecnologias e status. | **TASK-DOC-01** |
| **RN-DOC-02** | Apresentação da stack técnica e arquitetura. | **TASK-DOC-01** |
| **RN-DOC-03 / RN-DOC-04** | Instruções de execução com Docker Compose (Dev e Prod). | **TASK-DOC-01** |
| **RN-DOC-05 / RN-DOC-06** | Instruções de execução local (uv, alembic, seed, npm). | **TASK-DOC-01** |
| **RN-DOC-07** | Credenciais padrão de acesso (Técnico e Colaborador). | **TASK-DOC-01** |
| **RN-DOC-08** | Comandos de testes automatizados e cobertura (Pytest / Vitest). | **TASK-DOC-01** |
| **RN-DOC-09** | Explicação sobre CI/CD e Metodologia SDD. | **TASK-DOC-01** |
| **Cenários 1 e 2** | Validação da precisão dos comandos e clareza do guia. | **TASK-DOC-02** |

---

## Lista de Tarefas de Implementação

### Fase 1: Elaboração do README.md
- [x] **TASK-DOC-01: Criação do `README.md` Completo na Raiz**
  - [x] Escrever cabeçalho com badges e resumo do sistema.
  - [x] Detalhar a stack tecnológica de backend, frontend e infra.
  - [x] Detalhar comandos de inicialização via Docker Compose (Dev e Produção).
  - [x] Detalhar comandos de inicialização em ambiente local (Backend + Frontend).
  - [x] Listar usuários padrão de teste e seus perfis (Técnico e Colaborador).
  - [x] Incluir seção de testes automatizados com comandos exatos e metas de cobertura.
  - [x] Documentar a estrutura de diretórios e o pipeline de CI do GitHub Actions.

---

### Fase 2: Validação e Commit
- [x] **TASK-DOC-02: Revisão e Validação da Documentação**
  - [x] Validar links e instruções do README.
  - [x] Commitar as alterações no Git.
