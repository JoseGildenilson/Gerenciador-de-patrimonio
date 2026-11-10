# Bug Assessment: Backend Container Startup Crash on Duplicate Table Users

- **Slug**: backend-container
- **Created**: 2026-10-29T15:39:00-03:00
- **Source**: pasted text
- **Verdict**: valid
- **Severity**: critical

## Report (verbatim or summarized)

Ao tentar subir os containers do projeto (`docker compose up`), o container `patrimonio_backend` falha durante a execução do script `entrypoint.sh` ao executar `alembic upgrade head`, gerando o erro:

```text
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_auth, Initial Auth Tables (users & login_attempts)
Traceback (most recent call last):
  File "/app/.venv/lib/python3.13/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
psycopg2.errors.DuplicateTable: relation "users" already exists

sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable) relation "users" already exists
[SQL: 
CREATE TABLE users (
        id SERIAL NOT NULL, 
        email VARCHAR(255) NOT NULL, 
        hashed_password VARCHAR(255) NOT NULL, 
        role VARCHAR(50) DEFAULT 'tecnico' NOT NULL, 
        is_active BOOLEAN DEFAULT 'true' NOT NULL, 
        created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
        PRIMARY KEY (id)
)
]
```

O container encerra com código 1 e entra em reinicialização contínua (`restart: unless-stopped`).

## Symptom

O container `patrimonio_backend` não inicia e entra em crash loop infinito. O comportamento esperado é que as migrações sejam executadas com idempotência ou reconheçam bases pré-existentes, permitindo a inicialização saudável do backend FastAPI e do frontend.

## Reproduction

1. Iniciar o container do PostgreSQL com um volume de dados (`patrimonio_data`) contendo tabelas já criadas (por exemplo, via `database/schema.sql`, execução prévia de `Base.metadata.create_all()` ou volume persistido de versões anteriores sem a tabela `alembic_version`).
2. Executar `docker compose up backend` ou iniciar o container `patrimonio_backend`.
3. Observar a saída de log do container: `entrypoint.sh` executa `alembic upgrade head`, tenta criar a tabela `users` na migração `001_initial_auth` e aborta com `DuplicateTable: relation "users" already exists`.

## Suspected Code Paths

- `entrypoint.sh:35-37` — Executa `alembic upgrade head` diretamente sem verificar se o banco de dados já possui tabelas criadas fora do controle de versões do Alembic (ausência da tabela `alembic_version`).
- `alembic/versions/001_initial_auth_tables.py:17-40` — Migração inicial tenta criar tabela `users` sem verificar se a tabela já existe no banco (`DuplicateTable`).
- `src/cli.py:9-17` — Função `create_db()` cria tabelas via `Base.metadata.create_all(bind=engine)` sem carimbar (`stamp`) a revisão correspondente no Alembic, gerando bancos com tabelas sem `alembic_version`.
- `docker-compose.yml:23-55` — Configuração do serviço backend com política `restart: unless-stopped` que mascara a falha fatal através de um loop de reinicialização ininterrupto.

## Root Cause Hypothesis

O script de inicialização `entrypoint.sh` executa incondicionalmente `alembic upgrade head`. O Alembic determina a revisão inicial consultando a tabela `alembic_version`. Quando o PostgreSQL possui tabelas já criadas (seja por um volume `patrimonio_data` persistido, criação manual via `database/schema.sql` ou execução de `src/cli.py create-db`), mas a tabela `alembic_version` está ausente, o Alembic assume que o banco de dados está vazio (revisão base) e tenta executar a primeira migração `001_initial_auth`. Ao tentar executar `CREATE TABLE users`, o PostgreSQL rejeita a instrução porque a relação já existe. Confiança: alta.

## Proposed Remediation

**Preferred**:
1. No script `entrypoint.sh`, antes de invocar `alembic upgrade head`, executar um script Python de verificação/reconciliação do estado do banco:
   - Inspecionar se `alembic_version` já existe no banco.
   - Caso `alembic_version` não exista:
     - Se a tabela `users` não existir: prosseguir normalmente com `alembic upgrade head` (banco limpo).
     - Se a tabela `users` já existir: detectar o estado do esquema (ex: se `equipments` estiver presente, carimbar a migração `d4e5f6a7b8c9` com `alembic stamp d4e5f6a7b8c9` para que a migração subsequente `e5f6a7b8c9d0` expurgue as tabelas legadas; se apenas as 7 tabelas DBML canônicas existirem, carimbar `head`).
   - Executar `alembic upgrade head`.
2. Em `src/cli.py`, atualizar `create_db()` para carimbar `alembic stamp head` após `Base.metadata.create_all()` para evitar que bancos criados por CLI fiquem sem rastreamento de versão.
3. Para usuários locais que desejam um banco totalmente novo e limpo, documentar a limpeza de volumes antigos via `docker compose down -v`.

**Alternatives**:
- Adicionar blocos `IF NOT EXISTS` / inspeção preventiva dentro das próprias migrações do Alembic (`alembic/versions/`). Ponto contra: adiciona complexidade e desvio do padrão canônico do Alembic em múltiplos scripts de versão.

**Files likely to change**:
- `entrypoint.sh`
- `src/cli.py`
- `tests/test_cli.py`
- `tests/test_migrations.py`

**Tests to add or update**:
- Teste unitário e de integração para validação de `src/cli.py create-db` garantindo que `alembic_version` seja devidamente carimbada.
- Teste para o fluxo de verificação e reconciliação pré-migração no caso de bancos pré-existentes sem registro de versão.

## Risks & Considerations

- O carimbo (`stamp`) automático de versões pré-existentes deve identificar com precisão o estado do esquema para não pular migrações necessárias (como o expurgo de tabelas legadas em `e5f6a7b8c9d0`).
- Manter estrita conformidade com a Constituição do projeto: 100% de cobertura de testes em todo código executável modificado.

## Open Questions

- Nenhum. Causa raiz e comportamento reproduzidos e verificados diretamente no ambiente de containers.
