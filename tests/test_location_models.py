"""Testes unitários para o modelo ORM Location e unicidade física (T020)."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.domain.models import Location


def test_location_creation_and_fields(db_session: Session):
    """Valida persistência de localização com todos os campos."""
    loc = Location(
        building="Prédio Central",
        floor="2º",
        sector="Engenharia",
        room_number="204",
        description="Laboratório de Circuitos",
    )
    db_session.add(loc)
    db_session.flush()

    assert loc.id is not None
    assert loc.created_at is not None
    assert loc.updated_at is not None


def test_composite_unique_physical_space_rejection(db_session: Session):
    """Valida restrição uq_locations_physical_space contra duplicidade de alocação."""
    loc1 = Location(
        building="Prédio Alfa",
        floor="1",
        sector="Suporte",
        room_number="12",
    )
    db_session.add(loc1)
    db_session.flush()

    # Inserção de combinação idêntica deve falhar
    loc2 = Location(
        building="Prédio Alfa",
        floor="1",
        sector="Suporte",
        room_number="12",
    )
    db_session.add(loc2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
