"""Testes de integridade das migrações do Alembic (TASK-QA-14 / CRIT-01)."""

import os
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_migrations_lifecycle(tmp_path):
    """Testa o ciclo de vida completo das migrações: upgrade head -> downgrade base -> upgrade head."""
    test_db_url = os.environ.get("TEST_DATABASE_URL")
    admin_engine = None
    if test_db_url and "postgresql" in test_db_url:
        from sqlalchemy import text

        admin_url = test_db_url.rsplit("/", 1)[0] + "/postgres"
        try:
            admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
            with admin_engine.connect() as conn:
                conn.execute(text("DROP DATABASE IF EXISTS test_migrations_lifecycle;"))
                conn.execute(text("CREATE DATABASE test_migrations_lifecycle;"))
            db_url = test_db_url.rsplit("/", 1)[0] + "/test_migrations_lifecycle"
        except Exception:
            admin_engine = None
            db_file = tmp_path / "test_migration.db"
            db_url = f"sqlite:///{db_file}"
    else:
        db_file = tmp_path / "test_migration.db"
        db_url = f"sqlite:///{db_file}"

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)

    try:
        # 1. Aplica todas as migrações (upgrade head)
        command.upgrade(cfg, "head")

        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        # Tabelas canônicas DBML estritamente presentes
        assert "users" in tables
        assert "locations" in tables
        assert "categories" in tables
        assert "assets" in tables
        assert "patrimony_history" in tables
        assert "asset_movements" in tables
        assert "asset_maintenances" in tables
        assert "alembic_version" in tables
        # Tabelas legadas estritamente expurgadas
        assert "equipments" not in tables
        assert "equipment_types" not in tables
        assert "sectors" not in tables
        assert "equipment_statuses" not in tables
        assert "maintenance_types" not in tables
        assert "equipment_movements" not in tables
        assert "equipment_maintenances" not in tables
        assert "login_attempts" not in tables

        # 2. Reverte todas as migrações (downgrade base)
        command.downgrade(cfg, "base")

        inspector = inspect(engine)
        remaining_tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
        assert len(remaining_tables) == 0

        # 3. Reaplica todas as migrações (upgrade head)
        command.upgrade(cfg, "head")

        inspector = inspect(engine)
        reapplied_tables = inspector.get_table_names()
        assert "users" in reapplied_tables
        assert "locations" in reapplied_tables
        assert "categories" in reapplied_tables
        assert "assets" in reapplied_tables
        assert "patrimony_history" in reapplied_tables
        assert "asset_movements" in reapplied_tables
        assert "asset_maintenances" in reapplied_tables
        assert "equipments" not in reapplied_tables
        assert "equipment_types" not in reapplied_tables
        assert "sectors" not in reapplied_tables
        assert "equipment_statuses" not in reapplied_tables
        assert "maintenance_types" not in reapplied_tables
        assert "equipment_movements" not in reapplied_tables
        assert "equipment_maintenances" not in reapplied_tables
        assert "login_attempts" not in reapplied_tables
        engine.dispose()
    finally:
        if admin_engine:
            from sqlalchemy import text

            with admin_engine.connect() as conn:
                conn.execute(
                    text("DROP DATABASE IF EXISTS test_migrations_lifecycle WITH (FORCE);")
                )
            admin_engine.dispose()
