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
        except Exception as e:
            pytest.skip(f"PostgreSQL offline ({e}); skipping Alembic PostgreSQL lifecycle test")
    elif test_db_url and "sqlite" in test_db_url:
        pytest.skip(
            "Alembic migrations contain PostgreSQL-specific DDL (e.g. DROP TABLE CASCADE, triggers, INET); requires PostgreSQL"
        )
    else:
        db_file = tmp_path / "test_migration.db"
        db_url = f"sqlite:///{db_file}"
        pytest.skip("Alembic migrations contain PostgreSQL-specific DDL; requires PostgreSQL")

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)

    try:
        # 1. Aplica todas as migrações (upgrade head)
        command.upgrade(cfg, "head")

        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "users" in tables
        assert "equipments" in tables
        assert "equipment_types" in tables
        assert "sectors" in tables
        assert "equipment_statuses" in tables
        assert "maintenance_types" in tables
        assert "equipment_movements" in tables
        assert "equipment_maintenances" in tables
        assert "locations" in tables
        assert "categories" in tables
        assert "assets" in tables
        assert "patrimony_history" in tables
        assert "asset_movements" in tables
        assert "asset_maintenances" in tables
        assert "alembic_version" in tables

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
        assert "equipments" in reapplied_tables
        assert "equipment_types" in reapplied_tables
        assert "sectors" in reapplied_tables
        assert "equipment_statuses" in reapplied_tables
        assert "maintenance_types" in reapplied_tables
        assert "equipment_movements" in reapplied_tables
        assert "equipment_maintenances" in reapplied_tables
        engine.dispose()
    finally:
        if admin_engine:
            from sqlalchemy import text

            with admin_engine.connect() as conn:
                conn.execute(
                    text("DROP DATABASE IF EXISTS test_migrations_lifecycle WITH (FORCE);")
                )
            admin_engine.dispose()
