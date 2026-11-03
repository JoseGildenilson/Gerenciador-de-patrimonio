# Bug Assessment: Backend Container Startup Crash: Missing db_readiness Module

- **Slug**: bug-backend
- **Created**: 2026-11-01T01:55:00-03:00
- **Source**: pasted text
- **Verdict**: valid
- **Severity**: critical

## Report (verbatim or summarized)

Ao executar `docker compose up -d`, o container `patrimonio_backend` falha na inicialização e se torna `unhealthy`:

```text
[+] up 5/5
 ✔ Network patrimonio_net        Created
 ✔ Volume patrimonio_data        Created
 ✔ Container patrimonio_postgres Healthy
 ✘ Container patrimonio_backend  Error dependency backend failed to start
 ✔ Container patrimonio_frontend Created
dependency failed to start: container patrimonio_backend is unhealthy
```

Nos logs de `docker logs -f patrimonio_backend`:
```text
==> Verificando prontidão do Banco de Dados e reconciliando versões...
/app/.venv/bin/python: No module named src.infrastructure.db_readiness
```

## Symptom

O container `patrimonio_backend` entra em falha imediata na inicialização porque o script de entrypoint tenta executar o módulo `src.infrastructure.db_readiness`, que não existe no diretório montado `/app/src`. Como consequência, o backend é marcado como `unhealthy` e o frontend não inicializa devido à dependência.

## Reproduction

1. Ter uma imagem Docker local previamente construída contendo o `/entrypoint.sh` da branch `fix/BackEndContainer` (que invoca `python -m src.infrastructure.db_readiness`).
2. Estar na branch `develop` (onde `src/infrastructure/db_readiness.py` não está presente no diretório `src/`).
3. Executar `docker compose up -d` com o bind mount `- ./src:/app/src`.
4. Observar a falha imediata com `No module named src.infrastructure.db_readiness`.

## Suspected Code Paths

- `entrypoint.sh:4` — Versão da imagem Docker invoca `python -m src.infrastructure.db_readiness`, enquanto a versão da branch local `develop` ainda possui script inline.
- `docker-compose.yml:39` — Realiza bind mount `- ./src:/app/src`, sobrescrevendo o código empacotado na imagem pelo código da branch atual.
- `origin/fix/BackEndContainer` (commit `c00a367d64d67e5ccce7fb8461f14113eac60972`) — Criou `src/infrastructure/db_readiness.py` e ajustou `entrypoint.sh`, porém o commit ainda não foi mesclado na branch `develop`.

## Root Cause Hypothesis

A imagem Docker `patrimonio_backend` presente no host foi compilada a partir da branch `origin/fix/BackEndContainer` (ou manteve o `/entrypoint.sh` dessa revisão). O `docker-compose.yml` monta o diretório do host `./src` em `/app/src`. Como a branch ativa é a `develop`, onde o módulo `src/infrastructure/db_readiness.py` ainda não existe, o `/entrypoint.sh` do container tenta executar um módulo ausente no volume montado, quebrando a inicialização com código de erro 1. Confiança: alta.

## Proposed Remediation

**Preferred**:
1. Incorporar as melhorias de reconciliação de schema e prontidão de banco presentes na branch `origin/fix/BackEndContainer` na branch `develop`:
   - Adicionar `src/infrastructure/db_readiness.py`.
   - Atualizar `entrypoint.sh` para utilizar `python -m src.infrastructure.db_readiness`.
   - Atualizar `src/cli.py` para carimbar `head` via `command.stamp(cfg, "head")` após `Base.metadata.create_all()`.
   - Adicionar a suíte de testes `tests/test_db_readiness.py`.
2. Reconstruir os containers Docker com `docker compose build backend` ou `docker compose up -d --build`.
3. Validar se o backend sobe saudável (`healthy`) e se os testes automatizados mantêm 100% de cobertura de código.

**Alternatives**:
- Reconstruir a imagem backend com o `entrypoint.sh` legado da branch `develop` via `docker compose build --no-cache backend`. *Desvantagem*: Reintroduz a falha crítica de `DuplicateTable: relation "users" already exists` quando o volume de banco já possui tabelas criadas fora do Alembic.

**Files likely to change**:
- `entrypoint.sh`
- `src/infrastructure/db_readiness.py`
- `src/cli.py`
- `tests/test_db_readiness.py`

**Tests to add or update**:
- `tests/test_db_readiness.py` (testes de verificação de conexão, timeout, e reconciliação automática de revisões do Alembic com 100% de cobertura).

## Risks & Considerations

- O novo módulo `src/infrastructure/db_readiness.py` DEVE possuir 100% de cobertura de testes em linhas e branches para cumprir o princípio inegociável da Constituição do Projeto.
- A reconstrução da imagem (`--build`) deve ser executada após o alinhamento dos arquivos para garantir que `/entrypoint.sh` dentro e fora do container fiquem perfeitamente sincronizados.

## Open Questions

- Nenhum. Causa raiz comprovada pelo histórico do git e logs do Docker.
