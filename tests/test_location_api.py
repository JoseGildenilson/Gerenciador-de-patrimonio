"""Testes de integração para a API de Location (T027)."""

import pytest
from httpx import AsyncClient
from src.core.security import create_access_token


@pytest.fixture
def auth_headers(create_test_user):
    tecnico = create_test_user(email="tecnico_loc_api@empresa.com", role="tecnico")
    token = create_access_token(
        {"sub": str(tecnico.id), "email": tecnico.email, "role": tecnico.role}
    )
    return {"token": token, "user": tecnico}


@pytest.mark.anyio
async def test_location_api_crud_and_uniqueness(client: AsyncClient, auth_headers):
    client.cookies.set("access_token", auth_headers["token"])

    # 1. Cadastrar localização inicial
    payload1 = {
        "building": "Prédio Administrativo",
        "floor": "1º Andar",
        "sector": "Recursos Humanos",
        "room_number": "105",
        "description": "Sala de Seleção",
    }
    resp1 = await client.post("/api/v1/locations", json=payload1)
    assert resp1.status_code == 201
    loc1_id = resp1.json()["id"]

    # 2. Conflito por espaço físico idêntico (HTTP 409)
    resp_dup = await client.post("/api/v1/locations", json=payload1)
    assert resp_dup.status_code == 409

    # 3. Cadastrar segunda localização com sala nula
    payload2 = {
        "building": "Galpão Logística",
        "floor": "Térreo",
        "sector": "Almoxarifado",
        "room_number": None,
    }
    resp2 = await client.post("/api/v1/locations", json=payload2)
    assert resp2.status_code == 201
    loc2_id = resp2.json()["id"]

    # 4. Listagem e filtros
    resp_all = await client.get("/api/v1/locations")
    assert resp_all.status_code == 200
    assert len(resp_all.json()) == 2

    resp_filter_b = await client.get("/api/v1/locations?building=Galpão Logística")
    assert len(resp_filter_b.json()) == 1

    resp_filter_s = await client.get("/api/v1/locations?sector=Recursos Humanos")
    assert len(resp_filter_s.json()) == 1

    # 5. Obter por ID (200 e 404)
    resp_get = await client.get(f"/api/v1/locations/{loc1_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["room_number"] == "105"

    assert (await client.get("/api/v1/locations/99999")).status_code == 404

    # 6. Atualizar localização
    resp_up = await client.put(f"/api/v1/locations/{loc1_id}", json={"room_number": "106"})
    assert resp_up.status_code == 200
    assert resp_up.json()["room_number"] == "106"

    # 7. Atualizar provocando conflito com outra localização (HTTP 409)
    resp_up_dup = await client.put(
        f"/api/v1/locations/{loc2_id}",
        json={
            "building": "Prédio Administrativo",
            "floor": "1º Andar",
            "sector": "Recursos Humanos",
            "room_number": "106",
        },
    )
    assert resp_up_dup.status_code == 409

    # 8. Atualizar localização inexistente (HTTP 404)
    assert (await client.put("/api/v1/locations/99999", json={"building": "X"})).status_code == 404
