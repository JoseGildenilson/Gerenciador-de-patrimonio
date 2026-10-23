"""Testes de integração para as APIs de Renumeração e Manutenção (T045)."""

from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from src.core.security import create_access_token
from src.domain.models import Category, Location, Asset


@pytest.fixture
def auth_headers(create_test_user):
    tecnico = create_test_user(email="tecnico_maint_api@empresa.com", role="tecnico")
    token = create_access_token(
        {"sub": str(tecnico.id), "email": tecnico.email, "role": tecnico.role}
    )
    return {"token": token, "user": tecnico}


@pytest.mark.anyio
async def test_renumbering_api_lifecycle_and_constraints(
    client: AsyncClient, db_session: Session, auth_headers
):
    client.cookies.set("access_token", auth_headers["token"])

    cat = Category(name="Equipamentos Renumber")
    loc = Location(building="Predio Central", floor="1", sector="TI")
    db_session.add_all([cat, loc])
    db_session.flush()

    a1 = Asset(
        patrimony_number="PAT-ORIG-01",
        description="Switch Cisco Catalyst",
        category_id=cat.id,
        location_id=loc.id,
        brand="Cisco",
    )
    a2 = Asset(
        patrimony_number="PAT-EXISTING-02",
        description="Roteador MikroTik",
        category_id=cat.id,
        location_id=loc.id,
        brand="MikroTik",
    )
    db_session.add_all([a1, a2])
    db_session.flush()

    # 1. Renumeração com sucesso
    renumber_payload = {
        "new_patrimony_number": "PAT-RENUM-01",
        "reason": "Substituição de plaqueta de código de barras avariada",
    }
    resp = await client.post(f"/api/v1/assets/{a1.id}/renumber", json=renumber_payload)
    assert resp.status_code == 200
    hist = resp.json()
    assert hist["old_patrimony_number"] == "PAT-ORIG-01"
    assert hist["new_patrimony_number"] == "PAT-RENUM-01"
    assert hist["reason"] == "Substituição de plaqueta de código de barras avariada"

    # Validar que o patrimônio no ativo foi atualizado
    db_session.refresh(a1)
    assert a1.patrimony_number == "PAT-RENUM-01"

    # Verificar que o histórico aparece no GET /assets/{id}
    resp_detail = await client.get(f"/api/v1/assets/{a1.id}")
    assert resp_detail.status_code == 200
    assert len(resp_detail.json()["patrimony_history"]) == 1
    assert resp_detail.json()["patrimony_history"][0]["new_patrimony_number"] == "PAT-RENUM-01"

    # 2. Conflito ao tentar renomear para o mesmo número (HTTP 409)
    resp_same = await client.post(
        f"/api/v1/assets/{a1.id}/renumber",
        json={"new_patrimony_number": "PAT-RENUM-01", "reason": "Mesmo número"},
    )
    assert resp_same.status_code == 409

    # 3. Conflito ao tentar renomear para número já usado por outro ativo (HTTP 409)
    resp_dup = await client.post(
        f"/api/v1/assets/{a1.id}/renumber",
        json={"new_patrimony_number": "PAT-EXISTING-02", "reason": "Colisão"},
    )
    assert resp_dup.status_code == 409

    # 4. Renumeração em ativo inexistente (HTTP 404)
    resp_404 = await client.post("/api/v1/assets/99999/renumber", json=renumber_payload)
    assert resp_404.status_code == 404


@pytest.mark.anyio
async def test_asset_maintenance_api_lifecycle(
    client: AsyncClient, db_session: Session, auth_headers
):
    client.cookies.set("access_token", auth_headers["token"])

    cat = Category(name="Impressoras Maint")
    loc = Location(building="Prédio Sul", floor="Térreo", sector="Operações")
    db_session.add_all([cat, loc])
    db_session.flush()

    asset = Asset(
        patrimony_number="PAT-PRINT-01",
        description="Impressora Térmica Zebra",
        category_id=cat.id,
        location_id=loc.id,
        brand="Zebra",
    )
    db_session.add(asset)
    db_session.flush()

    # 1. Listar inicialmente vazio
    resp_list_empty = await client.get(f"/api/v1/assets/{asset.id}/maintenances")
    assert resp_list_empty.status_code == 200
    assert resp_list_empty.json() == []

    # 404 para ativo inexistente
    assert (await client.get("/api/v1/assets/99999/maintenances")).status_code == 404

    # 2. Cadastrar manutenção preventiva
    maint_payload = {
        "maintenance_type": "preventiva",
        "service_provider": "Assistência Técnica Zebra",
        "description": "Limpeza da cabeça térmica e calibração de sensores",
        "cost": 320.50,
    }
    resp_create = await client.post(f"/api/v1/assets/{asset.id}/maintenances", json=maint_payload)
    assert resp_create.status_code == 201
    created_data = resp_create.json()
    assert created_data["id"] is not None
    assert created_data["maintenance_type"] == "preventiva"
    assert float(created_data["cost"]) == 320.50

    # 3. Listar manutenções do ativo
    resp_list = await client.get(f"/api/v1/assets/{asset.id}/maintenances")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) == 1

    # 4. Criar manutenção em ativo inexistente (HTTP 404)
    assert (
        await client.post("/api/v1/assets/99999/maintenances", json=maint_payload)
    ).status_code == 404
