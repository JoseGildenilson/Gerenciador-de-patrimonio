from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from src.core.security import create_access_token
from src.domain.models import Asset, Category, Location
from src.infrastructure.repositories import DashboardRepository
from src.use_cases.get_dashboard_metrics import GetDashboardMetricsUseCase


@pytest.fixture
def seed_dashboard_data(db_session: Session, test_catalogs, create_test_user):
    """Fixture para criar dados de teste para o dashboard patrimonial com o modelo canônico."""
    tecnico = create_test_user(email="tecnico_dash@empresa.com", role="tecnico")

    cat_nb = test_catalogs["cat_notebook"]
    loc_ti = test_catalogs["loc_ti"]

    assets = [
        Asset(
            patrimony_number="PAT-DASH-1",
            serial_number="SN-DASH-1",
            description="Notebook Dell",
            brand="Dell",
            model="Latitude 5430",
            category_id=cat_nb.id,
            location_id=loc_ti.id,
            status="em_uso",
        ),
        Asset(
            patrimony_number="PAT-DASH-2",
            serial_number="SN-DASH-2",
            description="Notebook Lenovo",
            brand="Lenovo",
            model="ThinkPad T14",
            category_id=cat_nb.id,
            location_id=loc_ti.id,
            status="em_manutencao",
        ),
        Asset(
            patrimony_number="PAT-DASH-3",
            serial_number="SN-DASH-3",
            description="Notebook HP",
            brand="HP",
            model="EliteBook",
            category_id=cat_nb.id,
            location_id=loc_ti.id,
            status="disponivel",
        ),
        Asset(
            patrimony_number="PAT-DASH-DEL",
            serial_number="SN-DASH-DEL",
            description="Notebook Deletado",
            brand="Dell",
            model="Vostro",
            category_id=cat_nb.id,
            location_id=loc_ti.id,
            status="em_uso",
            deleted_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        ),
    ]
    db_session.add_all(assets)
    db_session.flush()

    return {"tecnico": tecnico}


def test_dashboard_repository(db_session: Session, seed_dashboard_data):
    repo = DashboardRepository(db_session)
    metrics = repo.get_metrics()

    assert metrics["assets_total"] == 3
    assert metrics["assets_in_use"] == 1
    assert metrics["assets_in_maintenance"] == 1
    assert metrics["assets_available"] == 1
    assert "Notebook" in metrics["by_type"]
    assert "TI" in metrics["by_sector"]
    assert metrics["by_status"].get("em_uso") == 1
    assert metrics["by_status"].get("em_manutencao") == 1
    assert metrics["by_status"].get("disponivel") == 1


def test_dashboard_use_case(db_session: Session, seed_dashboard_data):
    use_case = GetDashboardMetricsUseCase(db_session)
    response = use_case.execute()

    assert response.assets_total == 3
    assert response.assets_in_use == 1
    assert response.assets_in_maintenance == 1
    assert response.assets_available == 1
    assert response.by_status.get("em_uso") == 1


@pytest.mark.anyio
async def test_dashboard_api_authenticated(client: AsyncClient, seed_dashboard_data):
    tec = seed_dashboard_data["tecnico"]
    token = create_access_token({"sub": str(tec.id), "email": tec.email, "role": tec.role})

    client.cookies.set("access_token", token)
    response = await client.get("/api/v1/dashboard/metrics")

    assert response.status_code == 200
    data = response.json()
    assert data["assets_total"] == 3
    assert data["assets_in_use"] == 1
    assert data["assets_in_maintenance"] == 1
    assert data["assets_available"] == 1
    assert "by_type" in data
    assert "by_sector" in data
    assert "by_status" in data


@pytest.mark.anyio
async def test_dashboard_api_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/metrics")
    assert response.status_code == 401
