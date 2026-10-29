# Bug Verification: Backend Container Startup Crash on Duplicate Table Users

- **Slug**: backend-container
- **Tested**: 2026-10-29T15:53:20-03:00
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

O bug não reproduz mais. O container `patrimonio_backend` reconcilia automaticamente bancos de dados com esquemas pré-existentes sem `alembic_version`, aplica as migrações sem colisão `DuplicateTable`, passa no healthcheck e responde com sucesso na porta 8000. Nenhuma regressão foi introduzida no projeto e a cobertura de testes permanece em 100%.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (post-fix) | `docker compose -p gerenciadordepatrimonio up -d --build backend` | pass | Backend reconciliou `d4e5f6a7b8c9`, aplicou migração de expurgo `e5f6a7b8c9d0`, executou seed e subiu `healthy` |
| New / updated tests | `uv run pytest tests/test_db_readiness.py tests/test_cli.py` | pass | 17 testes passaram cobrindo 100% de linhas e branches |
| Regression suite | `uv run pytest` | pass | 136 testes passaram com 100% de cobertura no código executável `src/` |
| Lint / type-check | `uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/` | pass | Validação do Ruff passou sem violações |

## Output Excerpts

### Testes Unitários e Cobertura (Pytest)
```text
======================= 136 passed, 2 warnings in 11.68s =======================
TOTAL: 1860 stmts, 0 Miss, 358 Branch, 0 BrPart | Coverage: 100%
```

### Linter e Formatação (Ruff)
```text
All checks passed!
76 files already formatted
```

### Inicialização do Container Backend (`docker logs patrimonio_backend`)
```text
==> Verificando prontidão do Banco de Dados e reconciliando versões...
Testando conexão com: postgres:5432/patrimonio_db
==> Conexão com banco de dados estabelecida com sucesso!
==> Executando migrações do Alembic (alembic upgrade head)...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
==> [SEED] Executando seed de dados padrão...
Banco de dados populado com sucesso!
==> Iniciando o servidor...
```

### Verificação de Saúde HTTP (`curl /health`)
```json
{"status":"ok","app":"Gerenciador de Patrimônio"}
```

## Residual Risks

- Ambientes que alterem manualmente nomes de usuários ou senhas no banco após a criação do volume Docker devem garantir que a variável `DATABASE_URL` corresponda às credenciais armazenadas no PostgreSQL.

## Recommendation

Close the bug — verified end-to-end. O comportamento foi testado e verificado tanto no ambiente isolado de testes unitários quanto nos containers Docker reais em execução.
