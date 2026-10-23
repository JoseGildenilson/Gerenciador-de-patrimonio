from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from src.core.security import create_access_token
from src.domain.models import Equipment, EquipmentStatus, EquipmentType, Sector
from src.infrastructure.repositories import DashboardRepository
from src.use_cases.get_dashboard_metrics import GetDashboardMetricsUseCase


@pytest.fixture
def seed_dashboard_data(db_session: Session, test_catalogs, create_test_user):
    """Fixture para criar dados de teste para o dashboard patrimonial."""
    tecnico = create_test_user(email="tecnico_dash@empresa.com", role="tecnico")

    type_nb = test_catalogs["type"]
    sector_ti = test_catalogs["sector_ti"]
    status_em_uso = test_catalogs["status_em_uso"]
    status_manutencao = test_catalogs["status_em_manutencao"]
    status_ocioso = test_catalogs["status_ocioso"]

    equipments = [
        Equipment(
            patrimony_number="PAT-DASH-1",
            serial_number="SN-DASH-1",
            model="Notebook Dell",
            equipment_type_id=type_nb.id,
            sector_id=sector_ti.id,
            status_id=status_em_uso.id,
        ),
        Equipment(
            patrimony_number="PAT-DASH-2",
            serial_number="SN-DASH-2",
            model="Notebook Lenovo",
            equipment_type_id=type_nb.id,
            sector_id=sector_ti.id,
            status_id=status_manutencao.id,
        ),
        Equipment(
            patrimony_number="PAT-DASH-3",
            serial_number="SN-DASH-3",
            model="Notebook HP",
            equipment_type_id=type_nb.id,
            sector_id=sector_ti.id,
            status_id=status_ocioso.id,
        ),
        Equipment(
            patrimony_number="PAT-DASH-DEL",
            serial_number="SN-DASH-DEL",
            model="Notebook Deletado",
            equipment_type_id=type_nb.id,
            sector_id=sector_ti.id,
            status_id=status_em_uso.id,
            deleted_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        ),
    ]
    db_session.add_all(equipments)
    db_session.flush()

    return {"tecnico": tecnico}


def test_dashboard_repository(db_session: Session, seed_dashboard_data):
    repo = DashboardRepository(db_session)
    metrics = repo.get_metrics()

    assert metrics["equipments_total"] == 3
    assert metrics["equipments_in_use"] == 1
    assert metrics["equipments_in_maintenance"] == 1
    assert metrics["equipments_idle"] == 1
    assert "Desktop" in metrics["by_type"]
    assert "TI" in metrics["by_sector"]
    assert metrics["by_status"].get("Em uso") == 1
    assert metrics["by_status"].get("Em manutenção") == 1
    assert metrics["by_status"].get("Ocioso") == 1


def test_dashboard_use_case(db_session: Session, seed_dashboard_data):
    use_case = GetDashboardMetricsUseCase(db_session)
    response = use_case.execute()

    assert response.equipments_total == 3
    assert response.equipments_in_use == 1
    assert response.equipments_in_maintenance == 1
    assert response.equipments_idle == 1
    assert response.by_status.get("Em uso") == 1


@pytest.mark.anyio
async def test_dashboard_api_authenticated(client: AsyncClient, seed_dashboard_data):
    tec = seed_dashboard_data["tecnico"]
    token = create_access_token({"sub": str(tec.id), "email": tec.email, "role": tec.role})

    client.cookies.set("access_token", token)
    response = await client.get("/api/v1/dashboard/metrics")

    assert response.status_code == 200
    data = response.json()
    assert data["equipments_total"] == 3
    assert data["equipments_in_use"] == 1
    assert data["equipments_in_maintenance"] == 1
    assert data["equipments_idle"] == 1
    assert "by_type" in data
    assert "by_sector" in data
    assert "by_status" in data


@pytest.mark.anyio
async def test_dashboard_api_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/metrics")
    assert response.status_code == 401
