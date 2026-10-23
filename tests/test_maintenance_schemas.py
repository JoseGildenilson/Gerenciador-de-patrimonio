"""Testes unitários e de validação para schemas de Manutenção e Histórico (T037)."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError
from src.domain.schemas import (
    AssetMaintenanceCreate,
    AssetMaintenanceResponse,
    PatrimonyHistoryResponse,
)


def test_asset_maintenance_create_valid():
    """Valida AssetMaintenanceCreate com dados de manutenção preventiva."""
    m = AssetMaintenanceCreate(
        maintenance_type="preventiva",
        service_provider="Oficina Autorizada Dell",
        description="Limpeza e troca de pasta térmica",
        cost=Decimal("250.00"),
    )
    assert m.maintenance_type == "preventiva"
    assert m.cost == Decimal("250.00")
    assert m.maintenance_date is not None


def test_asset_maintenance_create_validation():
    """Valida rejeição de custo negativo ou descrição vazia."""
    with pytest.raises(ValidationError):
        AssetMaintenanceCreate(
            maintenance_type="corretiva",
            description="",
        )

    with pytest.raises(ValidationError):
        AssetMaintenanceCreate(
            maintenance_type="corretiva",
            description="Reparo",
            cost=Decimal("-10.00"),
        )


def test_asset_maintenance_response():
    """Valida AssetMaintenanceResponse from_attributes."""
    now = datetime.now(timezone.utc)
    resp = AssetMaintenanceResponse(
        id=1,
        asset_id=10,
        registered_by_id=2,
        maintenance_type="corretiva",
        service_provider="Assoc TI",
        description="Troca de placa-mãe",
        cost=Decimal("1200.00"),
        maintenance_date=now,
        created_at=now,
        updated_at=now,
    )
    assert resp.id == 1
    assert resp.cost == Decimal("1200.00")
