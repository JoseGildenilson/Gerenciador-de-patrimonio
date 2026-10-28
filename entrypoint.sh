#!/bin/sh
set -e

echo "==> Verificando prontidão do Banco de Dados..."
python - <<'EOF'
import sys
import time
import os
from sqlalchemy import create_engine, text

db_url = os.getenv("DATABASE_URL", "sqlite:///./patrimonio.db")
print(f"Testando conexão com: {db_url.split('@')[-1] if '@' in db_url else db_url}")

max_retries = 30
retry_interval = 2

for i in range(max_retries):
    try:
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        engine = create_engine(db_url, connect_args=connect_args)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("==> Conexão com banco de dados estabelecida com sucesso!")
        sys.exit(0)
    except Exception as exc:
        print(f"Tentativa {i+1}/{max_retries} falhou: {exc}. Aguardando {retry_interval}s...")
        time.sleep(retry_interval)

print("==> ERRO: Tempo limite excedido para conectar ao banco de dados.")
sys.exit(1)
EOF

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
