"""Testes unitários para os scripts de seed de catálogos e banco de dados."""

from sqlalchemy.orm import Session
from src.domain.models import EquipmentType, Sector, EquipmentStatus, MaintenanceType, Equipment
from src.infrastructure.seed import seed_catalogs, seed_database
from src.infrastructure.seed_rich_data import seed_rich_equipments


def test_seed_catalogs_idempotency(db_session: Session):
    """Testa a criação de catálogos padrão e verifica idempotência ao rodar duas vezes."""
    catalogs1 = seed_catalogs(db_session)
    assert len(catalogs1["types"]) == 4
    assert len(catalogs1["sectors"]) == 5
    assert len(catalogs1["statuses"]) == 8
    assert len(catalogs1["maintenance_types"]) == 2

    # Segunda execução não deve gerar erro e deve retornar os mesmos itens
    catalogs2 = seed_catalogs(db_session)
    assert len(catalogs2["types"]) == 4
    assert len(catalogs2["sectors"]) == 5
    assert len(catalogs2["statuses"]) == 8
    assert len(catalogs2["maintenance_types"]) == 2


def test_seed_database_and_rich_data_execution():
    """Testa a execução de seed_database e seed_rich_equipments."""
    seed_database()
    # Executa novamente para verificar idempotência
    seed_database()
    # Executa seed rico
    seed_rich_equipments()
