"""Testes de modelos ORM para Category e Asset (T009)."""

from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.domain.models import Category, Location, Asset, User


def test_category_and_asset_creation(db_session: Session, create_test_user):
    """Testa criação e relacionamentos entre Category, Location, User e Asset."""
    user = create_test_user(email="custodiante@empresa.com", role="colaborador")

    category = Category(
        name="Laptops Executivos",
        useful_life_months=48,
        residual_value_rate=Decimal("10.00"),
        requires_serial_number=True,
    )
    db_session.add(category)
    db_session.flush()

    location = Location(
        building="Prédio A",
        floor="1",
        sector="Diretoria",
        room_number="101",
    )
    db_session.add(location)
    db_session.flush()

    asset = Asset(
        patrimony_number="PAT-EXEC-01",
        serial_number="SN-EXEC-01",
        description="ThinkPad X1 Carbon",
        category_id=category.id,
        location_id=location.id,
        assigned_user_id=user.id,
        brand="Lenovo",
        model="X1 Carbon Gen 10",
        purchase_cost=Decimal("12000.00"),
        purchase_date=date(2026, 2, 10),
        status="em_uso",
        specs={"screen": "14 inch 4K", "ram": "32GB"},
    )
    db_session.add(asset)
    db_session.flush()

    assert asset.id is not None
    assert asset.category.name == "Laptops Executivos"
    assert asset.location.building == "Prédio A"
    assert asset.assigned_user.email == "custodiante@empresa.com"
    assert len(category.assets) == 1


def test_unique_category_name_constraint(db_session: Session):
    """Valida rejeição de categorias com nomes duplicados."""
    c1 = Category(name="Monitores")
    db_session.add(c1)
    db_session.flush()

    c2 = Category(name="Monitores")
    db_session.add(c2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_unique_asset_patrimony_and_serial_constraints(db_session: Session):
    """Valida unicidade de número de patrimônio e número de série em ativos."""
    cat = Category(name="Periféricos")
    loc = Location(building="B", floor="2", sector="TI")
    db_session.add_all([cat, loc])
    db_session.flush()

    a1 = Asset(
        patrimony_number="PAT-DUP",
        serial_number="SN-DUP",
        description="Mouse sem fio",
        category_id=cat.id,
        location_id=loc.id,
        brand="Logitech",
    )
    db_session.add(a1)
    db_session.flush()

    # Tentativa de duplicar patrimony_number
    a2 = Asset(
        patrimony_number="PAT-DUP",
        serial_number="SN-OUTRO",
        description="Outro mouse",
        category_id=cat.id,
        location_id=loc.id,
        brand="Logitech",
    )
    db_session.add(a2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Tentativa de duplicar serial_number
    cat = Category(name="Periféricos 2")
    loc = Location(building="B2", floor="2", sector="TI")
    db_session.add_all([cat, loc])
    db_session.flush()

    a3 = Asset(
        patrimony_number="PAT-A",
        serial_number="SN-SERIAL-DUP",
        description="Teclado",
        category_id=cat.id,
        location_id=loc.id,
        brand="Dell",
    )
    db_session.add(a3)
    db_session.flush()

    a4 = Asset(
        patrimony_number="PAT-B",
        serial_number="SN-SERIAL-DUP",
        description="Outro teclado",
        category_id=cat.id,
        location_id=loc.id,
        brand="Dell",
    )
    db_session.add(a4)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
