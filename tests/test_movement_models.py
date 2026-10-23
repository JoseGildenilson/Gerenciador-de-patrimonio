"""Testes unitários para o modelo ORM AssetMovement (T028)."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.domain.models import Category, Location, Asset, AssetMovement, User


def test_asset_movement_orm_lifecycle(db_session: Session, create_test_user):
    """Valida persistência e relacionamentos do modelo AssetMovement."""
    tecnico = create_test_user(email="tecnico_mov@empresa.com", role="tecnico")
    colab = create_test_user(email="colab_mov@empresa.com", role="colaborador")

    cat = Category(name="Monitores Mov")
    loc_origem = Location(building="Predio 1", floor="1", sector="TI")
    loc_destino = Location(building="Predio 1", floor="2", sector="RH")
    db_session.add_all([cat, loc_origem, loc_destino])
    db_session.flush()

    asset = Asset(
        patrimony_number="PAT-MOV-01",
        description="Monitor Dell 27",
        category_id=cat.id,
        location_id=loc_origem.id,
        brand="Dell",
    )
    db_session.add(asset)
    db_session.flush()

    mov = AssetMovement(
        asset_id=asset.id,
        origin_location_id=loc_origem.id,
        dest_location_id=loc_destino.id,
        from_user_id=None,
        to_user_id=colab.id,
        moved_by_id=tecnico.id,
        term_accepted_at=datetime.now(timezone.utc),
        notes="Entrega do monitor ao colaborador do RH",
    )
    db_session.add(mov)
    db_session.flush()

    assert mov.id is not None
    assert mov.asset.patrimony_number == "PAT-MOV-01"
    assert mov.origin_location.sector == "TI"
    assert mov.dest_location.sector == "RH"
    assert mov.to_user.email == "colab_mov@empresa.com"
    assert mov.moved_by.email == "tecnico_mov@empresa.com"
    assert len(asset.movements) == 1
