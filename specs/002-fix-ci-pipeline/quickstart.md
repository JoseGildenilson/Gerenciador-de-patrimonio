# Quickstart & Validation Guide: CI Pipeline Stabilization

**Feature**: `002-fix-ci-pipeline`  
**Date**: 2026-10-28  

Este guia detalha o procedimento de validação local e remota para assegurar que as correções do pipeline de Integração Contínua funcionam de ponta a ponta.

---

## 1. Pré-Requisitos Locais

Para simular e verificar as etapas localmente antes do envio:
- Python 3.13 instalado e gerenciador `uv`.
- Node.js 20+ e `npm`.
- Docker Desktop ativo (para validação dos builds de imagem e container PostgreSQL).
- GitHub CLI (`gh`) autenticado para validação remota no GitHub Actions.

---

## 2. Roteiro de Validação Local

### Etapa 2.1: Validação de Formatação e Linter do Backend
Executar no terminal na raiz do projeto:

```bash
# Verificar e formatar arquivos com discrepância
uv run ruff format src/

# Validar que a checagem não reporta nenhuma divergência
uv run ruff format --check src/

# Validar regras de linting
uv run ruff check src/
```
**Resultado Esperado:** Mensagem `33 files already formatted` e `All checks passed!`.

### Etapa 2.2: Validação de Migrações e Testes de Backend com Cobertura
Com uma instância do PostgreSQL rodando localmente (ou banco de teste configurado):

```bash
# Executar migrações do Alembic
uv run alembic upgrade head

# Executar suíte completa de testes com gate de 100% de cobertura
PYTHONPATH=. uv run pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=100
```
**Resultado Esperado:** 100% dos testes aprovados com cobertura total de linhas e ramos (`Required test coverage of 100% reached`).

### Etapa 2.3: Validação do Frontend
No diretório `frontend`:

```bash
cd frontend
npm ci
npx tsc --noEmit
npm run lint
npm run build
npm test -- --run
cd ..
```
**Resultado Esperado:** Tipos compilados sem erro, build do Vite gerado em `frontend/dist` e todos os testes Vitest aprovados.

---

## 3. Roteiro de Validação Remota (GitHub Actions)

### Etapa 3.1: Envio da Branch e Acionamento Manual
Após comitar as correções em branch de trabalho:

```bash
# Disparar execução manual na branch de correção
gh workflow run "CI Pipeline" --ref JoseGildenilson/CI-Fix

# Acompanhar o status em tempo real
gh run watch
```

### Etapa 3.2: Verificação do Resultado
Confirmar que todos os 3 jobs concluem com sucesso:
- `Backend Tests & Migrations` (incluindo inicialização sem erros da role `root` e passo de formatação aprovado)
- `Frontend Tests & TypeScript Check`
- `Validate Docker Builds`

```bash
gh run list -L 1
```
**Resultado Esperado:** Status `completed` com conclusão `success` (✓ verde).
