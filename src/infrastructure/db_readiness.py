"""Verificação de prontidão e reconciliação automática de versões do banco de dados."""

import os
import sys
import time
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.dialects import postgresql
from alembic.config import Config
from alembic import command
from src.core.config import settings


def wait_for_database(db_url: str, max_retries: int = 30, retry_interval: float = 2.0) -> bool:
    """Aguarda a disponibilidade de conexão com o banco de dados especificado."""
    display_url = db_url.split("@")[-1] if "@" in db_url else db_url
    print(f"Testando conexão com: {display_url}")

    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    for i in range(max_retries):
        try:
            temp_engine = create_engine(db_url, connect_args=connect_args)
            with temp_engine.connect() as conn:
                conn.execute(select(1))
            temp_engine.dispose()
            print("==> Conexão com banco de dados estabelecida com sucesso!")
            return True
        except Exception as exc:
            print(f"Tentativa {i + 1}/{max_retries} falhou: {exc}. Aguardando {retry_interval}s...")
            time.sleep(retry_interval)

    print("==> ERRO: Tempo limite excedido para conectar ao banco de dados.")
    return False


def reconcile_alembic_schema(engine, alembic_cfg: Config | None = None) -> str | None:
    """Reconcilia bancos com esquemas pré-existentes que não possuem tabela alembic_version."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "alembic_version" in tables:
        return None

    if "users" not in tables:
        return None

    if "equipments" in tables:
        target_revision = "d4e5f6a7b8c9"
    elif "assets" in tables:
        target_revision = "head"
    else:
        target_revision = "001_initial_auth"

    cfg = alembic_cfg or Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False))

    print(
        f"==> Base existente sem alembic_version detectada. "
        f"Carimbando revisão '{target_revision}'..."
    )
    command.stamp(cfg, target_revision)
    return target_revision


def ensure_pg_enums(engine) -> None:
    """Garante a existência dos tipos ENUM no PostgreSQL se o dialeto for postgresql."""
    if engine.dialect.name != "postgresql":
        return

    enums = (
        postgresql.ENUM("administrador", "tecnico", "colaborador", name="user_role"),
        postgresql.ENUM("disponivel", "em_uso", "em_manutencao", "baixado", name="asset_status"),
        postgresql.ENUM("preventiva", "corretiva", name="maintenance_type"),
    )
    for pg_enum in enums:
        pg_enum.create(engine, checkfirst=True)


def main() -> int:
    """Ponto de entrada para validação de prontidão e reconciliação via CLI."""
    db_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL
    if not wait_for_database(db_url):
        return 1

    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    ready_engine = create_engine(db_url, connect_args=connect_args)
    try:
        ensure_pg_enums(ready_engine)
        reconcile_alembic_schema(ready_engine)
    finally:
        ready_engine.dispose()

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
