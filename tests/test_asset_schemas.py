"""Testes unitários e de validação para schemas de Category e Asset (T008)."""

from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError
from src.domain.schemas import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    AssetDetailResponse,
    AssetListResponse,
    PatrimonyRenumberRequest,
    PatrimonyHistoryResponse,
)


def test_category_create_valid():
    """Valida criação bem-sucedida de schema CategoryCreate com valores padrão."""
    cat = CategoryCreate(name="Notebooks")
    assert cat.name == "Notebooks"
    assert cat.residual_value_rate == Decimal("0.00")
    assert cat.requires_serial_number is False
    assert cat.useful_life_months is None


def test_category_residual_value_rate_bounds():
    """Valida restrições de limites de residual_value_rate (0.00 a 100.00)."""
    # Válido no limite inferior
    c1 = CategoryCreate(name="Item Min", residual_value_rate=Decimal("0.00"))
    assert c1.residual_value_rate == Decimal("0.00")

    # Válido no limite superior
    c2 = CategoryCreate(name="Item Max", residual_value_rate=Decimal("100.00"))
    assert c2.residual_value_rate == Decimal("100.00")

    # Inválido abaixo de zero
    with pytest.raises(ValidationError):
        CategoryCreate(name="Item Negativo", residual_value_rate=Decimal("-0.01"))

    # Inválido acima de 100
    with pytest.raises(ValidationError):
        CategoryCreate(name="Item Superior", residual_value_rate=Decimal("100.01"))


def test_category_update_and_response():
    """Testa CategoryUpdate com campos parciais e CategoryResponse from_attributes."""
    up = CategoryUpdate(useful_life_months=36, requires_serial_number=True)
    assert up.useful_life_months == 36
    assert up.requires_serial_number is True
    assert up.name is None

    now = datetime.now(timezone.utc)
    resp = CategoryResponse(
        id=1,
        name="Cadeiras",
        useful_life_months=60,
        residual_value_rate=Decimal("5.00"),
        requires_serial_number=False,
        created_at=now,
        updated_at=now,
    )
    assert resp.id == 1
    assert resp.name == "Cadeiras"


def test_asset_create_valid_and_specs():
    """Valida AssetCreate com especificações dinâmicas e valores válidos."""
    asset = AssetCreate(
        patrimony_number="PAT-100",
        serial_number="SN-XYZ",
        description="Servidor Dell PowerEdge",
        category_id=1,
        location_id=2,
        brand="Dell",
        model="R740",
        purchase_cost=Decimal("15000.50"),
        purchase_date=date(2026, 1, 15),
        specs={"cores": 32, "ram_gb": 128},
    )
    assert asset.patrimony_number == "PAT-100"
    assert asset.specs["cores"] == 32
    assert asset.status == "disponivel"


def test_asset_update_and_detail_response():
    """Valida AssetUpdate e AssetDetailResponse contendo histórico de renumeração."""
    up = AssetUpdate(description="Servidor atualizado", specs={"ram_gb": 256})
    assert up.description == "Servidor atualizado"
    assert up.specs == {"ram_gb": 256}

    now = datetime.now(timezone.utc)
    hist = PatrimonyHistoryResponse(
        id=10,
        asset_id=1,
        old_patrimony_number="PAT-001",
        new_patrimony_number="PAT-002",
        reason="Plaqueta danificada",
        changed_by_id=1,
        changed_at=now,
    )
    detail = AssetDetailResponse(
        id=1,
        patrimony_number="PAT-002",
        description="Item",
        category_id=1,
        location_id=1,
        brand="HP",
        status="disponivel",
        patrimony_history=[hist],
    )
    assert len(detail.patrimony_history) == 1
    assert detail.patrimony_history[0].new_patrimony_number == "PAT-002"


def test_patrimony_renumber_request_validation():
    """Valida campos obrigatórios da requisição de renumeração."""
    req = PatrimonyRenumberRequest(new_patrimony_number="PAT-NOVO", reason="Troca de etiqueta")
    assert req.new_patrimony_number == "PAT-NOVO"
    assert req.reason == "Troca de etiqueta"

    with pytest.raises(ValidationError):
        PatrimonyRenumberRequest(new_patrimony_number="", reason="")
