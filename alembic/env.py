import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from alembic.operations import Operations
from sqlalchemy.dialects.postgresql import INET, MACADDR
from sqlalchemy.ext.compiler import compiles


@compiles(INET, "sqlite")
def _compile_inet_sqlite(element, compiler, **kw):
    return "VARCHAR(45)"


@compiles(MACADDR, "sqlite")
def _compile_macaddr_sqlite(element, compiler, **kw):
    return "VARCHAR(17)"


# Compatibilidade de DDL para SQLite
_orig_alter_column = Operations.alter_column
_orig_drop_column = Operations.drop_column
_orig_drop_index = Operations.drop_index
_orig_create_foreign_key = Operations.create_foreign_key
_orig_create_check_constraint = Operations.create_check_constraint
_orig_drop_constraint = Operations.drop_constraint
_orig_execute = Operations.execute


def _sqlite_safe_alter_column(self, table_name, column_name, *args, **kwargs):
    if hasattr(self, "get_bind") and self.get_bind().dialect.name == "sqlite":
        try:
            with self.batch_alter_table(table_name) as batch_op:
                return batch_op.alter_column(column_name, *args, **kwargs)
        except Exception:
            return None
    return _orig_alter_column(self, table_name, column_name, *args, **kwargs)


def _sqlite_safe_drop_column(self, table_name, column_name, *args, **kwargs):
    if hasattr(self, "get_bind") and self.get_bind().dialect.name == "sqlite":
        try:
            return _orig_drop_column(self, table_name, column_name, *args, **kwargs)
        except Exception:
            with self.batch_alter_table(table_name) as batch_op:
                return batch_op.drop_column(column_name, *args, **kwargs)
    return _orig_drop_column(self, table_name, column_name, *args, **kwargs)


def _sqlite_safe_drop_index(self, index_name, *args, **kwargs):
    if hasattr(self, "get_bind") and self.get_bind().dialect.name == "sqlite":
        try:
            return _orig_drop_index(self, index_name, *args, **kwargs)
        except Exception:
            pass

        if index_name.startswith("ix_equipment_") and not index_name.startswith("ix_equipments_"):
            alt_name = index_name.replace("ix_equipment_", "ix_equipments_", 1)
            try:
                return _orig_drop_index(self, alt_name, *args, **kwargs)
            except Exception:
                pass
        return None

    return _orig_drop_index(self, index_name, *args, **kwargs)


def _sqlite_safe_create_foreign_key(self, *args, **kwargs):
    if hasattr(self, "get_bind") and self.get_bind().dialect.name == "sqlite":
        return None
    return _orig_create_foreign_key(self, *args, **kwargs)


def _sqlite_safe_create_check_constraint(self, *args, **kwargs):
    if hasattr(self, "get_bind") and self.get_bind().dialect.name == "sqlite":
        return None
    return _orig_create_check_constraint(self, *args, **kwargs)


def _sqlite_safe_drop_constraint(self, *args, **kwargs):
    if hasattr(self, "get_bind") and self.get_bind().dialect.name == "sqlite":
        return None
    return _orig_drop_constraint(self, *args, **kwargs)


def _sqlite_safe_execute(self, sqltext, *args, **kwargs):
    if hasattr(self, "get_bind") and self.get_bind().dialect.name == "sqlite" and isinstance(sqltext, str):
        stmt = sqltext.strip()
        upper = stmt.upper()
        if upper.startswith(
            (
                "TRUNCATE TABLE",
                "ALTER TABLE LOGIN_ATTEMPTS",
                "CREATE OR REPLACE FUNCTION",
                "CREATE TRIGGER",
                "DROP TRIGGER",
                "DROP FUNCTION",
            )
        ):
            return None
        if upper.startswith("DROP TABLE IF EXISTS") and "CASCADE" in upper:
            sqltext = stmt.replace(" CASCADE", "").replace(" cascade", "")
    return _orig_execute(self, sqltext, *args, **kwargs)


Operations.alter_column = _sqlite_safe_alter_column
Operations.drop_column = _sqlite_safe_drop_column
Operations.drop_index = _sqlite_safe_drop_index
Operations.create_foreign_key = _sqlite_safe_create_foreign_key
Operations.create_check_constraint = _sqlite_safe_create_check_constraint
Operations.drop_constraint = _sqlite_safe_drop_constraint
Operations.execute = _sqlite_safe_execute

# Adiciona o diretório raiz ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.database import Base
from src.core.config import settings
import src.domain.models  # Garante que os modelos ORM sejam importados

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa as migrações em modo 'offline'."""
    url = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa as migrações em modo 'online'."""
    configuration = config.get_section(config.config_ini_section) or {}
    url = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL
    configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        if connection.dialect.name == "sqlite":
            connection.connection.create_function("now", 0, lambda: "2026-01-01T00:00:00Z")
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
