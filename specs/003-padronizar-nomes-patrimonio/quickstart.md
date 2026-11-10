# Quickstart: Validação da Padronização de Nomenclatura

Este guia descreve os passos práticos para verificar e validar a conformidade de todas as nomenclaturas no projeto **Gerenciador de Patrimônio**.

---

## 1. Pré-requisitos

- Git instalado
- Python 3.13 com uv / virtualenv ativo
- Node.js 20+ com npm
- Docker e Docker Compose instalados

---

## 2. Cenário 1: Auditoria Textual de Nomes Legados

Verificar se não existem ocorrências ativas dos termos proibidos em código executável ou configurações:

```bash
# Executar busca por termos proibidos em arquivos de código e infraestrutura
git grep -i "internal_management" -- "src/" "alembic/" "frontend/src/" "docker-compose*" ".env*"
git grep -i "internal-management" -- "src/" "alembic/" "frontend/src/" "docker-compose*" ".env*"
```

**Resultado Esperado**:
- Saída vazia (código de saída 1 do grep = nenhuma correspondência encontrada).

---

## 3. Cenário 2: Validação de Nomenclatura Docker Compose

Verificar se os arquivos compose atendem aos contratos de rede e volume:

```bash
# Validar sintaxe e configuração do Docker Compose
docker compose config --quiet
docker compose -f docker-compose.prod.yml config --quiet
```

Inspecionar as seções de redes e volumes geradas:

```bash
docker compose config | grep -E "(patrimonio_net|patrimonio_data)"
```

**Resultado Esperado**:
- Todos os serviços vinculados à rede `patrimonio_net`.
- Volume de dados do PostgreSQL configurado com a chave e nome `patrimonio_data`.
- Nenhuma referência a `patrimonio-net` (com hífen) ou `postgres_data`.

---

## 4. Cenário 3: Validação da Suíte Completa de Testes

Garantir que os ajustes não quebraram a execução dos testes e que os quality gates constitucionais permanecem atendidos:

### Backend:
```bash
uv run pytest --cov=src --cov-branch --cov-fail-under=100
```
**Resultado Esperado**:
- 100% dos testes passam.
- 100% de cobertura de linhas e branches mantida.

### Frontend:
```bash
cd frontend
npm test
npx tsc --noEmit
```
**Resultado Esperado**:
- Suíte Vitest aprovada com sucesso.
- Compilação TypeScript sem nenhum erro de tipo.
