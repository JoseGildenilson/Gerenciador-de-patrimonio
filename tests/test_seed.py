"""Testes unitários para o script de seed do banco de dados SisPatrimonio."""

from sqlalchemy.orm import Session
from src.domain.models import (
    Category,
    Location,
    Asset,
    User,
    AssetMovement,
    AssetMaintenance,
    PatrimonyHistory,
)
from src.infrastructure.seed import seed_database
from src.infrastructure.seed_rich_data import seed_rich_equipments


def test_seed_database_execution(db_session: Session):
    """Testa a execução de seed_database e verifica idempotência e paridade com populate.sql."""
    seed_database(db_session)
    assert db_session.query(User).count() >= 5
    assert db_session.query(Category).count() >= 6
    assert db_session.query(Location).count() >= 5
    assert db_session.query(Asset).count() >= 8
    assert db_session.query(PatrimonyHistory).count() >= 1
    assert db_session.query(AssetMovement).count() >= 3
    assert db_session.query(AssetMaintenance).count() >= 3

    # Segunda execução não deve gerar erro e mantém integridade
    seed_database(db_session)
    assert db_session.query(User).count() >= 5
    assert db_session.query(Asset).count() >= 8


def test_seed_rich_data_execution():
    """Testa a execução de seed_rich_equipments."""
    seed_rich_equipments()


def test_populate_sql_valid_argon2_hashes_and_canonical_users():
    """Valida que database/populate.sql contém os e-mails canônicos e hashes Argon2id válidos para senha123."""
    import re
    from pathlib import Path
    from src.core.security import verify_password

    sql_content = Path("database/populate.sql").read_text(encoding="utf-8")
    assert "admin@sispatrimonio.edu.br" in sql_content
    assert "tecnico@sispatrimonio.edu.br" in sql_content
    assert "colaborador@sispatrimonio.edu.br" in sql_content

    hashes = re.findall(r"(\$argon2id\$[^']+)", sql_content)
    assert len(hashes) == 5
    for h in hashes:
        assert not h.endswith("...")
        assert verify_password("senha123", h) is True
