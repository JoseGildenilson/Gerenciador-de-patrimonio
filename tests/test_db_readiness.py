"""Testes unitários e de integração para verificação de prontidão e reconciliação do banco de dados."""

from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from alembic.config import Config
from src.infrastructure import db_readiness


def test_wait_for_database_success_with_credentials():
    """Testa conexão bem-sucedida com URL contendo credenciais (@)."""
    with patch("src.infrastructure.db_readiness.create_engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

        result = db_readiness.wait_for_database(
            "postgresql://user:pass@localhost:5432/test_db",
            max_retries=1,
            retry_interval=0.01,
        )

        assert result is True
        mock_conn.execute.assert_called_once()


def test_wait_for_database_sqlite_success():
    """Testa conexão com SQLite e validação de connect_args."""
    with patch("src.infrastructure.db_readiness.create_engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

        result = db_readiness.wait_for_database(
            "sqlite:///./test.db",
            max_retries=1,
            retry_interval=0.01,
        )

        assert result is True
        mock_engine.assert_called_with(
            "sqlite:///./test.db", connect_args={"check_same_thread": False}
        )


def test_wait_for_database_retry_and_timeout():
    """Testa falhas repetidas e tempo limite excedido."""
    with (
        patch("src.infrastructure.db_readiness.create_engine") as mock_engine,
        patch("time.sleep") as mock_sleep,
    ):
        mock_engine.side_effect = Exception("Falha de conexão")

        result = db_readiness.wait_for_database(
            "postgresql://localhost:5432/test_db",
            max_retries=3,
            retry_interval=0.05,
        )

        assert result is False
        assert mock_sleep.call_count == 3


def test_reconcile_alembic_schema_already_managed(tmp_path):
    """Testa banco que já possui tabela alembic_version (não altera nada)."""
    db_file = tmp_path / "managed.db"
    engine = create_engine(f"sqlite:///{db_file}")

    metadata = MetaData()
    Table("alembic_version", metadata, Column("version_num", String(32), primary_key=True))
    Table("users", metadata, Column("id", Integer, primary_key=True))
    metadata.create_all(engine)

    result = db_readiness.reconcile_alembic_schema(engine)
    assert result is None
    engine.dispose()


def test_reconcile_alembic_schema_fresh_database(tmp_path):
    """Testa banco limpo sem tabelas (não requer reconciliação)."""
    db_file = tmp_path / "fresh.db"
    engine = create_engine(f"sqlite:///{db_file}")

    result = db_readiness.reconcile_alembic_schema(engine)
    assert result is None
    engine.dispose()


def test_reconcile_alembic_schema_legacy_equipments_table(tmp_path):
    """Testa banco existente contendo tabela legada equipments (carimba d4e5f6a7b8c9)."""
    db_file = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{db_file}")

    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True))
    Table("equipments", metadata, Column("id", Integer, primary_key=True))
    metadata.create_all(engine)

    with patch("alembic.command.stamp") as mock_stamp:
        result = db_readiness.reconcile_alembic_schema(engine)
        assert result == "d4e5f6a7b8c9"
        mock_stamp.assert_called_once()
        assert mock_stamp.call_args[0][1] == "d4e5f6a7b8c9"

    engine.dispose()


def test_reconcile_alembic_schema_canonical_assets_table(tmp_path):
    """Testa banco existente contendo tabela assets (carimba head)."""
    db_file = tmp_path / "canonical.db"
    engine = create_engine(f"sqlite:///{db_file}")

    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True))
    Table("assets", metadata, Column("id", Integer, primary_key=True))
    metadata.create_all(engine)

    custom_cfg = Config("alembic.ini")
    with patch("alembic.command.stamp") as mock_stamp:
        result = db_readiness.reconcile_alembic_schema(engine, alembic_cfg=custom_cfg)
        assert result == "head"
        mock_stamp.assert_called_once()
        assert mock_stamp.call_args[0][1] == "head"

    engine.dispose()


def test_reconcile_alembic_schema_only_users_table(tmp_path):
    """Testa banco existente contendo apenas tabela users (carimba 001_initial_auth)."""
    db_file = tmp_path / "users_only.db"
    engine = create_engine(f"sqlite:///{db_file}")

    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True))
    metadata.create_all(engine)

    with patch("alembic.command.stamp") as mock_stamp:
        result = db_readiness.reconcile_alembic_schema(engine)
        assert result == "001_initial_auth"
        mock_stamp.assert_called_once()
        assert mock_stamp.call_args[0][1] == "001_initial_auth"

    engine.dispose()


def test_main_success_sqlite(tmp_path):
    """Testa execução principal com sucesso em banco SQLite."""
    db_file = tmp_path / "main.db"
    sqlite_url = f"sqlite:///{db_file}"

    with (
        patch.dict("os.environ", {"DATABASE_URL": sqlite_url}),
        patch("src.infrastructure.db_readiness.wait_for_database", return_value=True) as mock_wait,
        patch("src.infrastructure.db_readiness.reconcile_alembic_schema") as mock_reconcile,
    ):
        exit_code = db_readiness.main()
        assert exit_code == 0
        mock_wait.assert_called_once_with(sqlite_url)
        mock_reconcile.assert_called_once()


def test_main_failure_timeout():
    """Testa retorno 1 quando wait_for_database falha."""
    with patch("src.infrastructure.db_readiness.wait_for_database", return_value=False):
        exit_code = db_readiness.main()
        assert exit_code == 1


def test_main_fallback_settings_database_url():
    """Testa uso de settings.DATABASE_URL quando DATABASE_URL não está no os.environ."""
    with (
        patch.dict("os.environ", {}, clear=True),
        patch("src.infrastructure.db_readiness.settings") as mock_settings,
        patch("src.infrastructure.db_readiness.wait_for_database", return_value=True) as mock_wait,
        patch("src.infrastructure.db_readiness.reconcile_alembic_schema"),
    ):
        mock_settings.DATABASE_URL = "postgresql://localhost:5432/fallback_db"
        exit_code = db_readiness.main()
        assert exit_code == 0
        mock_wait.assert_called_once_with("postgresql://localhost:5432/fallback_db")
