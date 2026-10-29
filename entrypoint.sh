#!/bin/sh
set -e

echo "==> Verificando prontidão do Banco de Dados e reconciliando versões..."
python -m src.infrastructure.db_readiness

echo "==> Executando migrações do Alembic (alembic upgrade head)..."
alembic upgrade head

if [ "$RUN_SEED" = "true" ]; then
    echo "==> [SEED] Executando seed de dados padrão..."
    python -m src.infrastructure.seed
else
    echo "==> [SEED] Pulando seed de dados (RUN_SEED != true)."
fi

echo "==> Iniciando o servidor..."
exec "$@"
