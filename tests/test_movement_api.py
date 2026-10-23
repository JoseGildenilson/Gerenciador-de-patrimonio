"""Testes de integração para a API de Asset Movements e Termos de Custódia (T035)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from src.core.security import create_access_token
from src.domain.models import Category, Location, Asset


@pytest.fixture
def auth_headers(create_test_user):
    tecnico = create_test_user(email="tecnico_mov_api@empresa.com", role="tecnico")
    token = create_access_token(
        {"sub": str(tecnico.id), "email": tecnico.email, "role": tecnico.role}
    )
    return {"token": token, "user": tecnico}


@pytest.mark.anyio
async def test_movement_api_transfer_and_custody_acceptance(
    client: AsyncClient, db_session: Session, auth_headers, create_test_user
):
    client.cookies.set("access_token", auth_headers["token"])
    colab1 = create_test_user(email="colab_origem@empresa.com", role="colaborador")
    colab2 = create_test_user(email="colab_destino@empresa.com", role="colaborador")

    cat = Category(name="Equipamentos Mov API")
    loc_ti = Location(building="Predio A", floor="1", sector="TI")
    loc_eng = Location(building="Predio B", floor="2", sector="Engenharia")
    db_session.add_all([cat, loc_ti, loc_eng])
    db_session.flush()

    asset = Asset(
        patrimony_number="PAT-MOV-API-01",
        description="Notebook Lenovo ThinkPad",
        category_id=cat.id,
        location_id=loc_ti.id,
        assigned_user_id=colab1.id,
        brand="Lenovo",
    )
    db_session.add(asset)
    db_session.flush()

    # 1. Listar inicialmente vazio
    resp_empty = await client.get(f"/api/v1/assets/{asset.id}/movements")
    assert resp_empty.status_code == 200
    assert resp_empty.json() == []

    # 404 para ativo inexistente
    assert (await client.get("/api/v1/assets/99999/movements")).status_code == 404

    # 2. Registrar transferência TI -> Engenharia e Colab1 -> Colab2
    mov_payload = {
        "origin_location_id": loc_ti.id,
        "dest_location_id": loc_eng.id,
        "from_user_id": colab1.id,
        "to_user_id": colab2.id,
        "notes": "Transferência para novo projeto de engenharia",
    }
    resp_mov = await client.post(f"/api/v1/assets/{asset.id}/movements", json=mov_payload)
    assert resp_mov.status_code == 201
    mov_data = resp_mov.json()
    assert mov_data["id"] is not None
    assert mov_data["term_accepted_at"] is None
    mov_id = mov_data["id"]

    # Validar que a localização e custodiante do ativo foram atualizados
    db_session.refresh(asset)
    assert asset.location_id == loc_eng.id
    assert asset.assigned_user_id == colab2.id

    # 3. Aceite eletrônico do termo de custódia
    resp_term = await client.post(f"/api/v1/movements/{mov_id}/accept-term")
    assert resp_term.status_code == 200
    assert resp_term.json()["term_accepted_at"] is not None

    # Aceite de termo inexistente (404)
    assert (await client.post("/api/v1/movements/99999/accept-term")).status_code == 404

    # 4. Registrar baixa patrimonial (dest_location_id = None)
    mov_baixa_payload = {
        "origin_location_id": loc_eng.id,
        "dest_location_id": None,
        "from_user_id": colab2.id,
        "to_user_id": None,
        "notes": "Descarte / baixa do bem por obsolescência",
    }
    resp_baixa = await client.post(f"/api/v1/assets/{asset.id}/movements", json=mov_baixa_payload)
    assert resp_baixa.status_code == 201
    db_session.refresh(asset)
    assert asset.status == "baixado"
    assert asset.assigned_user_id is None

    # 5. Erros de validação (HTTP 404)
    assert (
        await client.post(
            f"/api/v1/assets/{asset.id}/movements",
            json={**mov_payload, "origin_location_id": 99999},
        )
    ).status_code == 404
    assert (
        await client.post(
            f"/api/v1/assets/{asset.id}/movements", json={**mov_payload, "dest_location_id": 99999}
        )
    ).status_code == 404
    assert (
        await client.post(
            f"/api/v1/assets/{asset.id}/movements", json={**mov_payload, "from_user_id": 99999}
        )
    ).status_code == 404
    assert (
        await client.post(
            f"/api/v1/assets/{asset.id}/movements", json={**mov_payload, "to_user_id": 99999}
        )
    ).status_code == 404
    assert (
        await client.post("/api/v1/assets/99999/movements", json=mov_payload)
    ).status_code == 404
