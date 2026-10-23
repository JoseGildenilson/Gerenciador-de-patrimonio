"""Testes de integração para as APIs de Category e Asset (T019)."""

from datetime import date
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from src.core.security import create_access_token
from src.domain.models import Category, Location, Asset


@pytest.fixture
def auth_headers(create_test_user):
    tecnico = create_test_user(email="tecnico_asset_api@empresa.com", role="tecnico")
    token = create_access_token(
        {"sub": str(tecnico.id), "email": tecnico.email, "role": tecnico.role}
    )
    return {"token": token, "user": tecnico}


@pytest.mark.anyio
async def test_category_api_lifecycle_and_conflicts(client: AsyncClient, auth_headers):
    client.cookies.set("access_token", auth_headers["token"])

    # 1. Listar inicialmente vazio
    resp = await client.get("/api/v1/categories")
    assert resp.status_code == 200
    assert resp.json() == []

    # 2. Cadastrar categoria com sucesso
    payload = {
        "name": "Notebooks Empresariais",
        "useful_life_months": 36,
        "residual_value_rate": 10.0,
        "requires_serial_number": True,
    }
    resp = await client.post("/api/v1/categories", json=payload)
    assert resp.status_code == 201
    cat_data = resp.json()
    assert cat_data["id"] is not None
    assert cat_data["requires_serial_number"] is True
    cat_id = cat_data["id"]

    # 3. Rejeição por duplicidade (HTTP 409)
    resp_dup = await client.post("/api/v1/categories", json=payload)
    assert resp_dup.status_code == 409

    # 4. Obter por ID
    resp_get = await client.get(f"/api/v1/categories/{cat_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["name"] == "Notebooks Empresariais"

    # 5. Obter ID inexistente (HTTP 404)
    resp_404 = await client.get("/api/v1/categories/99999")
    assert resp_404.status_code == 404

    # 6. Atualizar categoria
    resp_put = await client.put(
        f"/api/v1/categories/{cat_id}", json={"name": "Laptops Corporativos"}
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["name"] == "Laptops Corporativos"

    # 7. Atualizar categoria com nome duplicado (HTTP 409)
    await client.post("/api/v1/categories", json={"name": "Outra Categoria"})
    resp_put_dup = await client.put(
        f"/api/v1/categories/{cat_id}", json={"name": "Outra Categoria"}
    )
    assert resp_put_dup.status_code == 409

    # 8. Atualizar categoria inexistente (HTTP 404)
    resp_put_404 = await client.put("/api/v1/categories/99999", json={"name": "Nao Existe"})
    assert resp_put_404.status_code == 404


@pytest.mark.anyio
async def test_asset_api_lifecycle_validation_and_filters(
    client: AsyncClient, db_session: Session, auth_headers, create_test_user
):
    client.cookies.set("access_token", auth_headers["token"])
    colab = create_test_user(email="colab_asset@empresa.com", role="colaborador")

    # Setup de categoria e localização
    cat_req_serial = Category(name="Notebooks", requires_serial_number=True)
    cat_opt_serial = Category(name="Mobiliário", requires_serial_number=False)
    loc1 = Location(building="Predio Central", floor="1", sector="TI", room_number="10")
    loc2 = Location(building="Predio Central", floor="2", sector="RH", room_number="20")
    db_session.add_all([cat_req_serial, cat_opt_serial, loc1, loc2])
    db_session.flush()

    # 1. Falha ao cadastrar ativo sem serial quando categoria exige (HTTP 400)
    asset_fail_payload = {
        "patrimony_number": "PAT-FAIL-01",
        "serial_number": None,
        "description": "Notebook Dell sem serial",
        "category_id": cat_req_serial.id,
        "location_id": loc1.id,
        "brand": "Dell",
    }
    resp_fail = await client.post("/api/v1/assets", json=asset_fail_payload)
    assert resp_fail.status_code == 400

    # 2. Falhas com relacionamentos inexistentes (HTTP 404)
    p_bad_cat = {**asset_fail_payload, "serial_number": "SN-1", "category_id": 99999}
    assert (await client.post("/api/v1/assets", json=p_bad_cat)).status_code == 404

    p_bad_loc = {**asset_fail_payload, "serial_number": "SN-1", "location_id": 99999}
    assert (await client.post("/api/v1/assets", json=p_bad_loc)).status_code == 404

    p_bad_user = {**asset_fail_payload, "serial_number": "SN-1", "assigned_user_id": 99999}
    assert (await client.post("/api/v1/assets", json=p_bad_user)).status_code == 404

    # 3. Sucesso ao cadastrar com serial quando categoria exige
    asset_ok_payload = {
        "patrimony_number": "PAT-OK-01",
        "serial_number": "SN-OK-01",
        "description": "Notebook Dell Latitude",
        "category_id": cat_req_serial.id,
        "location_id": loc1.id,
        "assigned_user_id": colab.id,
        "brand": "Dell",
        "model": "Latitude 5420",
        "purchase_cost": 4500.00,
        "purchase_date": "2026-03-01",
        "status": "em_uso",
        "specs": {"cpu": "Core i5", "ram": "16GB"},
    }
    resp_ok = await client.post("/api/v1/assets", json=asset_ok_payload)
    assert resp_ok.status_code == 201
    asset_id = resp_ok.json()["id"]

    # 4. Sucesso ao cadastrar item sem serial quando categoria NÃO exige
    asset_mob_payload = {
        "patrimony_number": "PAT-MOB-01",
        "serial_number": None,
        "description": "Mesa em L",
        "category_id": cat_opt_serial.id,
        "location_id": loc2.id,
        "brand": "Kappesberg",
    }
    resp_mob = await client.post("/api/v1/assets", json=asset_mob_payload)
    assert resp_mob.status_code == 201

    # 5. Conflito por patrimônio duplicado (HTTP 409)
    resp_dup_pat = await client.post(
        "/api/v1/assets", json={**asset_ok_payload, "serial_number": "SN-OTHER"}
    )
    assert resp_dup_pat.status_code == 409

    # 6. Conflito por serial duplicado (HTTP 409)
    resp_dup_ser = await client.post(
        "/api/v1/assets", json={**asset_ok_payload, "patrimony_number": "PAT-OTHER"}
    )
    assert resp_dup_ser.status_code == 409

    # 7. Listagem com filtros e busca
    resp_list = await client.get("/api/v1/assets?search=Latitude")
    assert resp_list.status_code == 200
    assert resp_list.json()["total"] == 1
    assert resp_list.json()["items"][0]["brand"] == "Dell"

    # Filtro por category_id
    resp_cat_filter = await client.get(f"/api/v1/assets?category_id={cat_opt_serial.id}")
    assert resp_cat_filter.json()["total"] == 1
    assert resp_cat_filter.json()["items"][0]["description"] == "Mesa em L"

    # Filtro por location_id e status
    resp_loc_filter = await client.get(f"/api/v1/assets?location_id={loc1.id}&status=em_uso")
    assert resp_loc_filter.json()["total"] == 1

    # 8. Obter detalhes do ativo por ID (200 e 404)
    resp_detail = await client.get(f"/api/v1/assets/{asset_id}")
    assert resp_detail.status_code == 200
    assert resp_detail.json()["patrimony_history"] == []

    assert (await client.get("/api/v1/assets/99999")).status_code == 404

    # 9. Atualizar ativo (sucesso, erros 404 e 409)
    resp_update = await client.put(
        f"/api/v1/assets/{asset_id}", json={"description": "Notebook Dell Latitude Atualizado"}
    )
    assert resp_update.status_code == 200
    assert resp_update.json()["description"] == "Notebook Dell Latitude Atualizado"

    # Conflito ao atualizar para serial já existente
    resp_update_dup_serial = await client.put(
        f"/api/v1/assets/{resp_mob.json()['id']}", json={"serial_number": "SN-OK-01"}
    )
    assert resp_update_dup_serial.status_code == 409

    # 404 nos relacionamentos de update
    assert (
        await client.put(f"/api/v1/assets/{asset_id}", json={"category_id": 99999})
    ).status_code == 404
    assert (
        await client.put(f"/api/v1/assets/{asset_id}", json={"location_id": 99999})
    ).status_code == 404
    assert (
        await client.put(f"/api/v1/assets/{asset_id}", json={"assigned_user_id": 99999})
    ).status_code == 404
    assert (await client.put("/api/v1/assets/99999", json={"description": "X"})).status_code == 404

    # 10. Soft delete do ativo
    resp_del = await client.delete(f"/api/v1/assets/{asset_id}")
    assert resp_del.status_code == 204

    # Ativo deletado não deve mais aparecer na listagem
    resp_list_after_del = await client.get("/api/v1/assets")
    assert resp_list_after_del.json()["total"] == 1

    # Deletar ID inexistente (HTTP 404)
    assert (await client.delete("/api/v1/assets/99999")).status_code == 404
