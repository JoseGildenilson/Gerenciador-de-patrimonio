"""Testes unitários e de validação para schemas de Location (T021)."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from src.domain.schemas import LocationCreate, LocationUpdate, LocationResponse


def test_location_create_valid():
    """Valida criação bem-sucedida de LocationCreate com campos opcionais."""
    loc = LocationCreate(
        building="Prédio Administrativo",
        floor="3º Andar",
        sector="Financeiro",
        room_number="302",
        description="Sala de Contabilidade",
    )
    assert loc.building == "Prédio Administrativo"
    assert loc.room_number == "302"


def test_location_create_validation_failures():
    """Valida rejeição de strings vazias nos campos obrigatórios."""
    with pytest.raises(ValidationError):
        LocationCreate(building="", floor="1", sector="TI")

    with pytest.raises(ValidationError):
        LocationCreate(building="B", floor="", sector="TI")

    with pytest.raises(ValidationError):
        LocationCreate(building="B", floor="1", sector="")


def test_location_update_and_response():
    """Testa LocationUpdate parcial e LocationResponse."""
    up = LocationUpdate(room_number="305-B")
    assert up.room_number == "305-B"
    assert up.building is None

    now = datetime.now(timezone.utc)
    resp = LocationResponse(
        id=5,
        building="Campus Leste",
        floor="Térreo",
        sector="Biblioteca",
        created_at=now,
        updated_at=now,
    )
    assert resp.id == 5
    assert resp.sector == "Biblioteca"
