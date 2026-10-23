"""Testes unitários e de validação para schemas de AssetMovement (T029)."""

from datetime import datetime, timezone
from src.domain.schemas import AssetMovementCreate, AssetMovementResponse


def test_asset_movement_create_defaults():
    """Valida AssetMovementCreate com valores padrão e campos opcionais."""
    mov = AssetMovementCreate(
        origin_location_id=1,
        dest_location_id=2,
        notes="Remanejamento de setor",
    )
    assert mov.origin_location_id == 1
    assert mov.dest_location_id == 2
    assert mov.from_user_id is None
    assert mov.to_user_id is None
    assert mov.movement_date is not None


def test_asset_movement_response():
    """Valida AssetMovementResponse from_attributes."""
    now = datetime.now(timezone.utc)
    resp = AssetMovementResponse(
        id=10,
        asset_id=5,
        origin_location_id=1,
        dest_location_id=2,
        from_user_id=None,
        to_user_id=3,
        moved_by_id=1,
        term_accepted_at=now,
        movement_date=now,
        notes="Aceite confirmado",
    )
    assert resp.id == 10
    assert resp.term_accepted_at == now
