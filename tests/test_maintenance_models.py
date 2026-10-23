"""Testes unitários para os modelos ORM PatrimonyHistory e AssetMaintenance (T036)."""

from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from src.domain.models import Category, Location, Asset, PatrimonyHistory, AssetMaintenance


def test_patrimony_history_and_maintenance_orm(db_session: Session, create_test_user):
    """Valida persistência e integridade referencial de histórico e manutenções."""
    tecnico = create_test_user(email="tecnico_maint@empresa.com", role="tecnico")

    cat = Category(name="Servidores Maint")
    loc = Location(building="DC", floor="Subsolo", sector="Datacenter")
    db_session.add_all([cat, loc])
    db_session.flush()

    asset = Asset(
        patrimony_number="PAT-OLD-01",
        description="Servidor Storage",
        category_id=cat.id,
        location_id=loc.id,
        brand="Supermicro",
    )
    db_session.add(asset)
    db_session.flush()

    # Histórico de renumeração
    hist = PatrimonyHistory(
        asset_id=asset.id,
        old_patrimony_number="PAT-OLD-01",
        new_patrimony_number="PAT-NEW-01",
        reason="Substituição por plaqueta metálica patrimonial",
        changed_by_id=tecnico.id,
        changed_at=datetime.now(timezone.utc),
    )
    db_session.add(hist)
    db_session.flush()

    # Manutenção preventiva
    maint = AssetMaintenance(
        asset_id=asset.id,
        registered_by_id=tecnico.id,
        maintenance_type="preventiva",
        service_provider="Supermicro Suporte",
        description="Atualização de firmware de discos SAS",
        cost=Decimal("450.00"),
        maintenance_date=datetime.now(timezone.utc),
    )
    db_session.add(maint)
    db_session.flush()

    assert hist.id is not None
    assert hist.asset.description == "Servidor Storage"
    assert hist.changed_by.email == "tecnico_maint@empresa.com"

    assert maint.id is not None
    assert maint.asset.patrimony_number == "PAT-OLD-01"
    assert maint.registered_by.email == "tecnico_maint@empresa.com"
    assert len(asset.patrimony_histories) == 1
    assert len(asset.maintenances) == 1
