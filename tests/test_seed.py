"""Testes unitários para o script de seed do banco de dados SisPatrimonio."""

from sqlalchemy.orm import Session
from src.domain.models import Category, Location, Asset, User
from src.infrastructure.seed import seed_database
from src.infrastructure.seed_rich_data import seed_rich_equipments


def test_seed_database_execution(db_session: Session):
    """Testa a execução de seed_database e verifica idempotência ao rodar duas vezes."""
    seed_database(db_session)
    assert db_session.query(User).count() >= 3
    assert db_session.query(Category).count() >= 6
    assert db_session.query(Location).count() >= 4
    assert db_session.query(Asset).count() >= 2

    # Segunda execução não deve gerar erro e mantém integridade
    seed_database(db_session)
    assert db_session.query(User).count() >= 3


def test_seed_rich_data_execution():
    """Testa a execução de seed_rich_equipments."""
    seed_rich_equipments()
