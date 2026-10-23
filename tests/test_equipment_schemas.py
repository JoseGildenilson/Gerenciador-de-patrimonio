"""Testes unitários para validação dos schemas Pydantic de Equipamentos, Catálogos e Redes."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from src.domain.schemas import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    EquipmentListItemResponse,
    EquipmentListResponse,
    EquipmentSecretKeyResponse,
    EquipmentMovementCreate,
    EquipmentMovementResponse,
    EquipmentMaintenanceStart,
    EquipmentMaintenanceComplete,
    EquipmentMaintenanceResponse,
    EquipmentTypeCreate,
    EquipmentTypeResponse,
    SectorResponse,
    EquipmentStatusResponse,
    DashboardMetricsResponse,
    validate_host_ip,
)


def test_equipment_create_schema_valid():
    """Testa criação válida do schema EquipmentCreate com identificadores e IP de host."""
    data = EquipmentCreate(
        patrimony_number="PAT-001",
        equipment_type_id=1,
        sector_id=2,
        status_id=3,
        description="OptiPlex 7090",
        model="7090-MT",
        ip_address="192.168.1.50/32",
        mac_address="00:1A:2B:3C:4D:5E",
        printer_identifier="PRN-01",
        windows_product_key="VK9X2-N8Y4R-W3M2T-K7P1Q-L9Z0A",
    )
    assert data.patrimony_number == "PAT-001"
    assert data.ip_address == "192.168.1.50"
    assert data.model == "7090-MT"


def test_equipment_create_schema_ip_validation_rejections():
    """Testa validação e rejeição de IPs inválidos e sub-redes (Cenário 2)."""
    # Rejeição de máscara de sub-rede /24
    with pytest.raises(ValidationError, match="host único"):
        EquipmentCreate(
            patrimony_number="PAT-002",
            equipment_type_id=1,
            sector_id=1,
            status_id=1,
            ip_address="192.168.1.0/24",
        )

    # Rejeição de IP malformado
    with pytest.raises(ValidationError, match="inválido"):
        EquipmentCreate(
            patrimony_number="PAT-003",
            equipment_type_id=1,
            sector_id=1,
            status_id=1,
            ip_address="999.999.999.999",
        )


def test_equipment_create_schema_missing_required():
    """Testa falha de validação ao omitir campos obrigatórios (patrimony_number, fks)."""
    with pytest.raises(ValidationError):
        EquipmentCreate(description="Faltando patrimônio e FKs")


def test_catalog_schemas_validation():
    """Testa criação de catálogo e validação de nome não vazio."""
    cat = EquipmentTypeCreate(name="  Notebook  ")
    assert cat.name == "Notebook"

    with pytest.raises(ValidationError):
        EquipmentTypeCreate(name="   ")


def test_movement_and_maintenance_schemas():
    """Testa schemas de movimentação e ciclo de vida de manutenção."""
    mov = EquipmentMovementCreate(
        origin_sector_id=1,
        destination_sector_id=2,
    )
    assert mov.destination_sector_id == 2

    start_maint = EquipmentMaintenanceStart(
        maintenance_type_id=1,
        description="Troca de ventoinha",
    )
    assert start_maint.maintenance_type_id == 1

    comp_maint = EquipmentMaintenanceComplete(
        new_status_id=3,
        description="Concluído",
    )
    assert comp_maint.new_status_id == 3


def test_equipment_response_and_dashboard_schemas():
    """Testa schemas completos de resposta e dashboard."""
    now = datetime.now(timezone.utc)
    type_resp = EquipmentTypeResponse(id=1, name="Desktop", created_at=now)
    sector_resp = SectorResponse(id=1, name="TI", created_at=now)
    status_resp = EquipmentStatusResponse(id=1, name="Em uso", created_at=now)

    item = EquipmentListItemResponse(
        id=1,
        patrimony_number="PAT-001",
        equipment_type_id=1,
        equipment_type=type_resp,
        sector_id=1,
        sector=sector_resp,
        status_id=1,
        status=status_resp,
        windows_product_key="••••••••••••••••",
        created_at=now,
        updated_at=now,
    )
    assert item.windows_product_key == "••••••••••••••••"

    dash = DashboardMetricsResponse(
        equipments_total=10,
        equipments_in_maintenance=2,
        equipments_in_use=7,
        equipments_idle=1,
        by_status={"Em uso": 7, "Em manutenção": 2, "Ocioso": 1},
        by_type={"Desktop": 6, "Notebook": 4},
        by_sector={"TI": 10},
    )
    assert dash.equipments_total == 10
    assert dash.equipments_in_maintenance == 2


def test_schema_edge_cases():
    from src.domain.schemas import validate_host_ip, CatalogItemUpdate, EquipmentUpdate

    assert validate_host_ip("") is None
    assert validate_host_ip(None) is None
    assert validate_host_ip("   ") is None

    with pytest.raises(ValueError, match="Endereço IP inválido"):
        validate_host_ip("invalid_host/24")

    with pytest.raises(ValueError, match="não pode ser vazio"):
        CatalogItemUpdate(name="   ")

    item_upd = CatalogItemUpdate(name="  Novo Nome  ")
    assert item_upd.name == "Novo Nome"

    assert validate_host_ip("192.168.1.1") == "192.168.1.1"

    upd = EquipmentUpdate(ip_address="192.168.1.1/32")
    assert upd.ip_address == "192.168.1.1"
