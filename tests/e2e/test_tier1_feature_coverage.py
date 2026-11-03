"""E2E Test Suite - Tier 1: Feature Coverage (Normative & Happy Paths - Canonical SisPatrimonio).

Covers all core system features with genuine, opaque-box HTTP API tests:
- F1: Authentication & Session Lifecycle (RN-01 to RN-07)
- F2: Asset Management CRUD, Renumbering & Multi-Filters (`/api/v1/assets`)
- F3: Maintenance History & Physical/Custody Movements (`/api/v1/assets/{id}/maintenances`, `/movements`)
- F4: Categories & Physical Locations CRUD (`/api/v1/categories`, `/api/v1/locations`)
- F5: Spreadsheet Import & Export (`/api/v1/equipments/import/*`, `/api/v1/assets/export`)
- F6: Dashboard & Operational Health (`/api/v1/dashboard/metrics`, `/health`)
"""

import io

import openpyxl
import pytest
from httpx import AsyncClient

# ==============================================================================
# F1: Authentication & Session Lifecycle
# ==============================================================================


@pytest.mark.anyio
async def test_tier1_auth_login_success(client: AsyncClient, e2e_users):
    """Testa login com credenciais válidas, recepção de cookies HttpOnly e dados do usuário."""
    login_payload = {
        "email": e2e_users["tecnico"].email,
        "password": e2e_users["raw_password"],
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == e2e_users["tecnico"].email
    assert data["user"]["role"] == "tecnico"

    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.anyio
async def test_tier1_auth_me_protected_endpoint(client: AsyncClient, tecnico_tokens):
    """Testa consulta ao perfil protegido /auth/me autenticado via Cookie HttpOnly."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == tecnico_tokens["user"].email
    assert data["role"] == "tecnico"
    assert data["is_active"] is True


@pytest.mark.anyio
async def test_tier1_auth_bearer_token(client: AsyncClient, tecnico_tokens):
    """Testa acesso a rota protegida utilizando cabeçalho Authorization: Bearer."""
    headers = {"Authorization": f"Bearer {tecnico_tokens['access_token']}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == tecnico_tokens["user"].email


@pytest.mark.anyio
async def test_tier1_auth_refresh_lifecycle(client: AsyncClient, tecnico_tokens):
    """Testa renovação de sessão via refresh_token enviado por cookie."""
    client.cookies.set("refresh_token", tecnico_tokens["refresh_token"])
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == tecnico_tokens["user"].email
    assert "access_token" in response.cookies


@pytest.mark.anyio
async def test_tier1_auth_logout_clears_cookies(client: AsyncClient, tecnico_tokens):
    """Testa encerramento de sessão via logout limpando os cookies."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    client.cookies.set("refresh_token", tecnico_tokens["refresh_token"])

    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert "Logout realizado" in response.json()["message"]


@pytest.mark.anyio
async def test_tier1_auth_inactive_user_rejected(client: AsyncClient, e2e_users):
    """Testa que usuário inativo tem autenticação recusada com HTTP 401."""
    login_payload = {
        "email": e2e_users["inativo"].email,
        "password": e2e_users["raw_password"],
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "inválid" in response.json()["detail"].lower()


# ==============================================================================
# F2: Asset Management CRUD & Multi-Filters
# ==============================================================================


@pytest.mark.anyio
async def test_tier1_equipment_create_success(client: AsyncClient, tecnico_tokens):
    """Testa cadastro completo de ativo com identificadores, JSONB specs e FK canônicas."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    payload = {
        "serial_number": "SN-T1-001",
        "patrimony_number": "PAT-T1-001",
        "description": "Dell Latitude 5420 i7 16GB",
        "brand": "Dell",
        "model": "Latitude 5420",
        "category_id": tecnico_tokens["category_id"],
        "location_id": tecnico_tokens["location_id"],
        "status": "em_uso",
        "purchase_cost": 4500.00,
        "purchase_date": "2026-01-15",
        "specs": {
            "hostname": "HOST-T1-01",
            "product_number": "PRD-9988",
            "windows_key": "VK7JG-NPHTM-C97JM-9MPGT-3V66T",
            "notes": "Equipamento principal de desenvolvimento",
        },
    }
    response = await client.post("/api/v1/assets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["serial_number"] == "SN-T1-001"
    assert data["patrimony_number"] == "PAT-T1-001"
    assert data["description"] == "Dell Latitude 5420 i7 16GB"
    assert data["category"]["name"] == "Notebook Padrao"
    assert data["specs"]["hostname"] == "HOST-T1-01"


@pytest.mark.anyio
async def test_tier1_equipment_get_detail(client: AsyncClient, tecnico_tokens):
    """Testa recuperação detalhada de ativo por ID com relacionamentos."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    payload = {
        "serial_number": "SN-T1-DETAIL",
        "patrimony_number": "PAT-T1-DETAIL",
        "description": "Monitor LG 24 Polegadas",
        "brand": "LG",
        "model": "Monitor 24",
        "category_id": tecnico_tokens["category_id"],
        "location_id": tecnico_tokens["location_id"],
        "status": "em_uso",
    }
    create_resp = await client.post("/api/v1/assets", json=payload)
    assert create_resp.status_code == 201
    eq_id = create_resp.json()["id"]

    detail_resp = await client.get(f"/api/v1/assets/{eq_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == eq_id
    assert detail["description"] == "Monitor LG 24 Polegadas"
    assert detail["category_id"] == tecnico_tokens["category_id"]
    assert detail["location_id"] == tecnico_tokens["location_id"]
    assert detail["movements"] == []
    assert detail["maintenances"] == []
    assert detail["patrimony_history"] == []


@pytest.mark.anyio
async def test_tier1_equipment_pagination_and_sorting(client: AsyncClient, tecnico_tokens):
    """Testa listagem paginada com total e páginas calculadas."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    for i in range(3):
        await client.post(
            "/api/v1/assets",
            json={
                "serial_number": f"SN-PAGE-{i}",
                "patrimony_number": f"PAT-PAGE-{i}",
                "description": f"Equipamento Paginado {i}",
                "brand": "HP",
                "model": f"ProDesk {i}",
                "category_id": tecnico_tokens["category_id"],
                "location_id": tecnico_tokens["location_id"],
                "status": "em_uso",
            },
        )

    response = await client.get("/api/v1/assets?page=1&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert data["page"] == 1
    assert data["limit"] == 2
    assert len(data["items"]) == 2


@pytest.mark.anyio
async def test_tier1_equipment_filter_multiple_types_or_logic(client: AsyncClient, tecnico_tokens):
    """Testa que múltiplos valores para o mesmo filtro utilizam lógica OR."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    cat1 = (
        await client.post(
            "/api/v1/categories",
            json={"name": "Cat OR Notebook", "requires_serial_number": False},
        )
    ).json()
    cat2 = (
        await client.post(
            "/api/v1/categories",
            json={"name": "Cat OR Desktop", "requires_serial_number": False},
        )
    ).json()
    cat3 = (
        await client.post(
            "/api/v1/categories",
            json={"name": "Cat OR Impressora", "requires_serial_number": False},
        )
    ).json()

    await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-OR-1",
            "description": "Item OR 1",
            "brand": "Dell",
            "category_id": cat1["id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )
    await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-OR-2",
            "description": "Item OR 2",
            "brand": "HP",
            "category_id": cat2["id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )
    await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-OR-3",
            "description": "Item OR 3",
            "brand": "Epson",
            "category_id": cat3["id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )

    resp = await client.get(f"/api/v1/assets?category_id={cat1['id']}")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(item["patrimony_number"] == "PAT-OR-1" for item in items)


@pytest.mark.anyio
async def test_tier1_equipment_filter_multiple_fields_and_logic(
    client: AsyncClient, tecnico_tokens
):
    """Testa que filtros em campos distintos combinam com lógica AND."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    cat_nb = (
        await client.post(
            "/api/v1/categories",
            json={"name": "Cat AND Notebook", "requires_serial_number": False},
        )
    ).json()
    cat_dk = (
        await client.post(
            "/api/v1/categories",
            json={"name": "Cat AND Desktop", "requires_serial_number": False},
        )
    ).json()
    loc_ti = (
        await client.post(
            "/api/v1/locations",
            json={"building": "Bloco AND", "floor": "1", "sector": "TI"},
        )
    ).json()
    loc_rh = (
        await client.post(
            "/api/v1/locations",
            json={"building": "Bloco AND", "floor": "1", "sector": "RH"},
        )
    ).json()

    await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-AND-1",
            "description": "Notebook TI",
            "brand": "Dell",
            "model": "Notebook TI",
            "category_id": cat_nb["id"],
            "location_id": loc_ti["id"],
        },
    )
    await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-AND-2",
            "description": "Notebook RH",
            "brand": "Dell",
            "model": "Notebook RH",
            "category_id": cat_nb["id"],
            "location_id": loc_rh["id"],
        },
    )
    await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-AND-3",
            "description": "Desktop TI",
            "brand": "HP",
            "model": "Desktop TI",
            "category_id": cat_dk["id"],
            "location_id": loc_ti["id"],
        },
    )

    resp = await client.get(
        f"/api/v1/assets?category_id={cat_nb['id']}&location_id={loc_ti['id']}"
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["description"] == "Notebook TI"


@pytest.mark.anyio
async def test_tier1_equipment_update_batch_mode(client: AsyncClient, tecnico_tokens):
    """Testa edição completa e renumeração via PUT /api/v1/assets/{id} e POST /renumber."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-UPD-001",
            "description": "Nome Antigo",
            "brand": "Dell",
            "model": "Nome Antigo",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )
    eq_id = created.json()["id"]

    update_payload = {
        "description": "Nome Atualizado ThinkPad",
        "brand": "Lenovo",
        "model": "ThinkPad",
        "status": "disponivel",
        "specs": {"notes": "Revisado pela equipe"},
    }
    update_resp = await client.put(f"/api/v1/assets/{eq_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["brand"] == "Lenovo"
    assert updated["description"] == "Nome Atualizado ThinkPad"
    assert updated["status"] == "disponivel"

    ren_resp = await client.post(
        f"/api/v1/assets/{eq_id}/renumber",
        json={"new_patrimony_number": "PAT-UPD-002", "reason": "Reetiquetagem oficial"},
    )
    assert ren_resp.status_code == 200
    assert ren_resp.json()["old_patrimony_number"] == "PAT-UPD-001"
    assert ren_resp.json()["new_patrimony_number"] == "PAT-UPD-002"


# ==============================================================================
# F3: Maintenance History & Location Movements
# ==============================================================================


@pytest.mark.anyio
async def test_tier1_maintenance_record_grouped_items(client: AsyncClient, tecnico_tokens):
    """Testa registro de manutenção com atualização automática de last_maintenance_at."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-MAINT-001",
            "description": "Server Dell R740",
            "brand": "Dell",
            "model": "Server Dell R740",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
            "status": "em_uso",
        },
    )
    eq_id = created.json()["id"]

    maint_payload = {
        "maintenance_date": "2026-09-18T10:00:00Z",
        "maintenance_type": "preventiva",
        "service_provider": "Dell ProSupport",
        "description": "Troca de SSD, Limpeza interna, Troca de pasta térmica",
        "cost": 350.00,
    }
    maint_resp = await client.post(f"/api/v1/assets/{eq_id}/maintenances", json=maint_payload)
    assert maint_resp.status_code == 201
    maint_data = maint_resp.json()
    assert maint_data["asset_id"] == eq_id
    assert "Troca de SSD" in maint_data["description"]

    detail_resp = await client.get(f"/api/v1/assets/{eq_id}")
    eq_detail = detail_resp.json()
    assert eq_detail["last_maintenance_at"] is not None
    assert "2026-09-18" in eq_detail["last_maintenance_at"]
    assert len(eq_detail["maintenances"]) == 1


@pytest.mark.anyio
async def test_tier1_maintenance_preserves_equipment_status(client: AsyncClient, tecnico_tokens):
    """Testa que registrar manutenção não altera a situação/status do ativo."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-MAINT-002",
            "description": "Workstation Dell",
            "brand": "Dell",
            "model": "Workstation",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
            "status": "em_uso",
        },
    )
    eq_id = created.json()["id"]

    await client.post(
        f"/api/v1/assets/{eq_id}/maintenances",
        json={
            "maintenance_date": "2026-09-20T12:00:00Z",
            "maintenance_type": "corretiva",
            "description": "Formatação do SO",
        },
    )

    detail_resp = await client.get(f"/api/v1/assets/{eq_id}")
    assert detail_resp.json()["status"] == "em_uso"


@pytest.mark.anyio
async def test_tier1_maintenance_update_fields(client: AsyncClient, tecnico_tokens):
    """Testa edição de registro de manutenção existente no histórico."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-MAINT-003",
            "description": "MacBook Pro M2",
            "brand": "Apple",
            "model": "MacBook",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )
    eq_id = created.json()["id"]

    m_create = await client.post(
        f"/api/v1/assets/{eq_id}/maintenances",
        json={
            "maintenance_date": "2026-08-01T00:00:00Z",
            "maintenance_type": "corretiva",
            "description": "Troca de Teclado",
        },
    )
    mid = m_create.json()["id"]

    update_resp = await client.put(
        f"/api/v1/assets/{eq_id}/maintenances/{mid}",
        json={
            "description": "Troca de Teclado e Bateria Nova",
            "service_provider": "Apple Care",
            "cost": 890.00,
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Troca de Teclado e Bateria Nova"
    assert update_resp.json()["service_provider"] == "Apple Care"


@pytest.mark.anyio
async def test_tier1_maintenance_delete(client: AsyncClient, tecnico_tokens):
    """Testa exclusão de um registro de manutenção do histórico do ativo."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-MAINT-004",
            "description": "Notebook Test Delete Maint",
            "brand": "Dell",
            "model": "Notebook Test Delete Maint",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )
    eq_id = created.json()["id"]

    m_create = await client.post(
        f"/api/v1/assets/{eq_id}/maintenances",
        json={
            "maintenance_date": "2026-08-01T00:00:00Z",
            "maintenance_type": "preventiva",
            "description": "Manutenção Provisória",
        },
    )
    mid = m_create.json()["id"]

    del_resp = await client.delete(f"/api/v1/assets/{eq_id}/maintenances/{mid}")
    assert del_resp.status_code == 204

    detail = (await client.get(f"/api/v1/assets/{eq_id}")).json()
    assert len(detail["maintenances"]) == 0


@pytest.mark.anyio
async def test_tier1_movement_record_updates_location(
    client: AsyncClient, tecnico_tokens, e2e_users
):
    """Testa que movimentação atualiza localização e custódia e permite aceite de termo."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    dest_loc = (
        await client.post(
            "/api/v1/locations",
            json={"building": "Bloco B", "floor": "2", "sector": "Auditório Central"},
        )
    ).json()

    created = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-MOV-001",
            "description": "Projetor Epson Auditório",
            "brand": "Epson",
            "model": "Projetor Epson",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
            "status": "em_uso",
        },
    )
    eq_id = created.json()["id"]

    movement_payload = {
        "origin_location_id": tecnico_tokens["location_id"],
        "dest_location_id": dest_loc["id"],
        "to_user_id": e2e_users["colaborador"].id,
        "notes": "Transferência definitiva para palestras",
    }
    mov_resp = await client.post(f"/api/v1/assets/{eq_id}/movements", json=movement_payload)
    assert mov_resp.status_code == 201
    mov_id = mov_resp.json()["id"]

    accept_resp = await client.post(f"/api/v1/movements/{mov_id}/accept-term")
    assert accept_resp.status_code == 200
    assert accept_resp.json()["term_accepted_at"] is not None

    detail = (await client.get(f"/api/v1/assets/{eq_id}")).json()
    assert detail["location_id"] == dest_loc["id"]
    assert detail["assigned_user_id"] == e2e_users["colaborador"].id
    assert len(detail["movements"]) == 1


@pytest.mark.anyio
async def test_tier1_equipment_detail_chronological_histories(client: AsyncClient, tecnico_tokens):
    """Testa persistência de múltiplas manutenções no detalhe do ativo."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-CHRONO-001",
            "description": "Impressora Laser HP",
            "brand": "HP",
            "model": "Impressora Laser",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )
    eq_id = created.json()["id"]

    await client.post(
        f"/api/v1/assets/{eq_id}/maintenances",
        json={
            "maintenance_date": "2026-01-10T00:00:00Z",
            "maintenance_type": "preventiva",
            "description": "Manutenção 1",
        },
    )
    await client.post(
        f"/api/v1/assets/{eq_id}/maintenances",
        json={
            "maintenance_date": "2026-06-15T00:00:00Z",
            "maintenance_type": "corretiva",
            "description": "Manutenção 2",
        },
    )

    detail = (await client.get(f"/api/v1/assets/{eq_id}")).json()
    assert len(detail["maintenances"]) == 2


# ==============================================================================
# F4: Categories & Physical Locations CRUD
# ==============================================================================


@pytest.mark.anyio
async def test_tier1_tag_list_all(client: AsyncClient, tecnico_tokens):
    """Testa listagem de categorias e localizações cadastradas no sistema."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    cat_resp = await client.get("/api/v1/categories")
    loc_resp = await client.get("/api/v1/locations")
    assert cat_resp.status_code == 200
    assert loc_resp.status_code == 200
    assert isinstance(cat_resp.json(), list)
    assert isinstance(loc_resp.json(), list)


@pytest.mark.anyio
async def test_tier1_tag_filter_by_category(client: AsyncClient, tecnico_tokens):
    """Testa criação e consulta separada de Categorias e Localizações."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    await client.post(
        "/api/v1/categories",
        json={"name": "Tablet Especial", "requires_serial_number": True},
    )
    await client.post(
        "/api/v1/locations",
        json={"building": "Prédio Central", "floor": "2", "sector": "Setor Beta"},
    )

    resp_cat = await client.get("/api/v1/categories")
    assert resp_cat.status_code == 200
    assert any(c["name"] == "Tablet Especial" for c in resp_cat.json())

    resp_loc = await client.get("/api/v1/locations")
    assert resp_loc.status_code == 200
    assert any(loc["sector"] == "Setor Beta" for loc in resp_loc.json())


@pytest.mark.anyio
async def test_tier1_tag_create_new(client: AsyncClient, tecnico_tokens):
    """Testa cadastro de nova categoria com parâmetros contábeis."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    payload = {
        "name": "Periférico Gamer",
        "useful_life_months": 24,
        "residual_value_rate": 5.0,
        "requires_serial_number": False,
    }
    response = await client.post("/api/v1/categories", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Periférico Gamer"
    assert data["useful_life_months"] == 24


@pytest.mark.anyio
async def test_tier1_tag_rename_propagates_to_equipments(client: AsyncClient, tecnico_tokens):
    """Testa que atualizar localização reflete imediatamente nos ativos vinculados via FK."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    loc_resp = await client.post(
        "/api/v1/locations",
        json={"building": "Anexo", "floor": "Térreo", "sector": "Almoxarifado Antigo"},
    )
    loc_id = loc_resp.json()["id"]

    eq_resp = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-LOC-PROP",
            "description": "Item no Almoxarifado",
            "brand": "Generico",
            "model": "Item no Almoxarifado",
            "category_id": tecnico_tokens["category_id"],
            "location_id": loc_id,
        },
    )
    eq_id = eq_resp.json()["id"]

    rename_resp = await client.put(
        f"/api/v1/locations/{loc_id}",
        json={"sector": "Depósito Central Moderno"},
    )
    assert rename_resp.status_code == 200

    detail = (await client.get(f"/api/v1/assets/{eq_id}")).json()
    assert detail["location"]["sector"] == "Depósito Central Moderno"


@pytest.mark.anyio
async def test_tier1_tag_delete_preserves_equipment_data(client: AsyncClient, tecnico_tokens):
    """Testa que exclusão de categoria com ativos vinculados retorna 409 Conflict (ON DELETE RESTRICT) e sem ativos retorna 204."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    cat_used = (
        await client.post(
            "/api/v1/categories",
            json={"name": "Tipo Em Uso", "requires_serial_number": False},
        )
    ).json()
    cat_unused = (
        await client.post(
            "/api/v1/categories",
            json={"name": "Tipo Sem Uso", "requires_serial_number": False},
        )
    ).json()

    await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-RESTRICT-1",
            "description": "Item Raro",
            "brand": "Raro",
            "category_id": cat_used["id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )

    conflict_resp = await client.delete(f"/api/v1/categories/{cat_used['id']}")
    assert conflict_resp.status_code == 409

    ok_resp = await client.delete(f"/api/v1/categories/{cat_unused['id']}")
    assert ok_resp.status_code == 204


@pytest.mark.anyio
async def test_tier1_tag_create_inline_category_localizacao(client: AsyncClient, tecnico_tokens):
    """Testa criação inline de localização física e disponibilidade imediata."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    resp = await client.post(
        "/api/v1/locations",
        json={"building": "Bloco C", "floor": "1", "sector": "Estúdio de Gravação"},
    )
    assert resp.status_code == 201
    assert resp.json()["sector"] == "Estúdio de Gravação"


# ==============================================================================
# F5: Spreadsheet Import & Export
# ==============================================================================


@pytest.mark.anyio
async def test_tier1_import_preview_xlsx(client: AsyncClient, tecnico_tokens, make_excel_bytes):
    """Testa pré-visualização de planilha Excel (.xlsx) contendo cabeçalhos corporativos."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    headers = [
        "TIPO",
        "LOCALIZAÇÃO",
        "SITUAÇÃO",
        "DESCRIÇÃO",
        "Nº PATRIMÔNIO",
        "Nº SÉRIE",
        "MARCA",
        "ÚLTIMA MANUTENÇÃO",
        "CHAVE WINDOWS",
        "Nº PRODUTO",
        "HISTÓRICO DE MOVIMENTAÇÕES",
        "HOSTNAME",
        "OBSERVAÇÕES",
    ]
    row = [
        "NOTEBOOK",
        "DIRETORIA",
        "EM USO",
        "Dell Inspiron 15",
        "PAT-IMP-01",
        "SN-IMP-01",
        "DELL",
        "15/08/2026",
        "W269N-WFGWX-YVC9B-4J6C9-T83GX",
        "PRD-01",
        "Limpeza de coolers",
        "NOTE-DIR-01",
        "Uso executivo",
    ]
    file_bytes = make_excel_bytes(rows=[row], headers=headers)

    files = {
        "file": (
            "patrimonio.xlsx",
            file_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = await client.post("/api/v1/equipments/import/preview", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 1
    assert len(data["sample_rows"]) == 1
    assert data["sample_rows"][0]["equipment_type"] == "NOTEBOOK"


@pytest.mark.anyio
async def test_tier1_import_preview_csv(client: AsyncClient, tecnico_tokens, make_csv_bytes):
    """Testa pré-visualização de arquivo CSV delimitado por ponto-e-vírgula."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    headers = ["TIPO", "LOCALIZAÇÃO", "SITUAÇÃO", "DESCRIÇÃO", "Nº PATRIMÔNIO"]
    row = ["DESKTOP", "CTM", "EM USO", "HP ProDesk 600", "PAT-CSV-01"]
    file_bytes = make_csv_bytes(rows=[row], headers=headers, delimiter=";")

    files = {"file": ("dados.csv", file_bytes, "text/csv")}
    response = await client.post("/api/v1/equipments/import/preview", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 1
    assert data["sample_rows"][0]["patrimony_number"] == "PAT-CSV-01"


@pytest.mark.anyio
async def test_tier1_import_execute_creates_equipments_and_tags(
    client: AsyncClient, tecnico_tokens, make_excel_bytes
):
    """Testa execução de importação criando ativos, categorias, localizações e manutenções."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    headers = [
        "TIPO",
        "LOCALIZAÇÃO",
        "SITUAÇÃO",
        "DESCRIÇÃO",
        "Nº PATRIMÔNIO",
        "Nº SÉRIE",
        "HISTÓRICO DE MOVIMENTAÇÕES",
    ]
    row = [
        "SWITCH",
        "RACK TI",
        "EM OPERACAO",
        "Cisco Catalyst 2960",
        "PAT-SW-01",
        "SN-SW-01",
        "Instalação inicial",
    ]
    file_bytes = make_excel_bytes(rows=[row], headers=headers)

    files = {
        "file": (
            "equipamentos.xlsx",
            file_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = await client.post("/api/v1/equipments/import/execute", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["created_count"] == 1

    list_resp = await client.get("/api/v1/assets?search=PAT-SW-01")
    assert list_resp.json()["total"] == 1


@pytest.mark.anyio
async def test_tier1_import_execute_upsert_existing(
    client: AsyncClient, tecnico_tokens, make_excel_bytes
):
    """Testa lógica de upsert atualizando ativo já existente pelo número de patrimônio."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-UPSERT-01",
            "description": "Versao Antiga",
            "brand": "LG",
            "model": "Versao Antiga",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )

    headers = ["Nº PATRIMÔNIO", "DESCRIÇÃO", "TIPO", "LOCALIZAÇÃO", "SITUAÇÃO"]
    row = ["PAT-UPSERT-01", "Versao Atualizada via Upsert", "Monitor", "TI", "Em uso"]
    file_bytes = make_excel_bytes(rows=[row], headers=headers)

    files = {
        "file": (
            "upsert.xlsx",
            file_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = await client.post("/api/v1/equipments/import/execute", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["updated_count"] == 1
    assert data["created_count"] == 0


@pytest.mark.anyio
async def test_tier1_export_xlsx_structure(client: AsyncClient, tecnico_tokens):
    """Testa exportação para Excel validando aba 'Ativos Patrimoniais' e 12 colunas canônicas."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-EXP-01",
            "description": "Desktop para Exportação",
            "brand": "HP",
            "model": "Desktop para Exportação",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
            "status": "em_uso",
        },
    )

    response = await client.get("/api/v1/assets/export")
    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment; filename=" in response.headers["content-disposition"]

    wb = openpyxl.load_workbook(io.BytesIO(response.content))
    assert "Ativos Patrimoniais" in wb.sheetnames
    ws = wb["Ativos Patrimoniais"]
    assert ws.max_column == 12
    headers = [cell.value for cell in ws[1]]
    assert headers[0] == "CATEGORIA"
    assert headers[1] == "LOCALIZAÇÃO"
    assert headers[2] == "STATUS"
    assert headers[3] == "DESCRIÇÃO"
    assert headers[4] == "Nº PATRIMÔNIO"


@pytest.mark.anyio
async def test_tier1_export_with_query_filters(client: AsyncClient, tecnico_tokens):
    """Testa exportação filtrada respeitando parâmetros de consulta."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    cat_exp = (
        await client.post(
            "/api/v1/categories",
            json={"name": "Notebook Export", "requires_serial_number": False},
        )
    ).json()

    await client.post(
        "/api/v1/assets",
        json={
            "serial_number": "SN-EXP-F1",
            "patrimony_number": "PAT-EXP-F1",
            "description": "Notebook Alfa",
            "brand": "Dell",
            "model": "Notebook Alfa",
            "category_id": cat_exp["id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )
    await client.post(
        "/api/v1/assets",
        json={
            "serial_number": "SN-EXP-F2",
            "patrimony_number": "PAT-EXP-F2",
            "description": "Desktop Beta",
            "brand": "HP",
            "model": "Desktop Beta",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )

    response = await client.get(f"/api/v1/assets/export?category_id={cat_exp['id']}")
    assert response.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(response.content))
    ws = wb["Ativos Patrimoniais"]
    assert ws.max_row == 2
    assert ws.cell(row=2, column=1).value == "Notebook Export"


# ==============================================================================
# F6: Dashboard & Operational Health
# ==============================================================================


@pytest.mark.anyio
async def test_tier1_health_check_endpoint(client: AsyncClient):
    """Testa endpoint público de healthcheck operacional /health."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data


@pytest.mark.anyio
async def test_tier1_dashboard_metrics_tecnico(client: AsyncClient, tecnico_tokens):
    """Testa retorno de métricas do dashboard para usuário com role técnico."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    response = await client.get("/api/v1/dashboard/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "assets_total" in data
    assert data["assets_total"] is not None
    assert "assets_in_use" in data
    assert "assets_in_maintenance" in data
    assert "assets_available" in data
    assert "assets_decommissioned" in data


@pytest.mark.anyio
async def test_tier1_dashboard_metrics_colaborador(client: AsyncClient, colaborador_tokens):
    """Testa retorno de métricas do dashboard para role colaborador."""
    client.cookies.set("access_token", colaborador_tokens["access_token"])
    response = await client.get("/api/v1/dashboard/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "assets_total" in data


@pytest.mark.anyio
async def test_tier1_dashboard_unauthenticated_rejected(client: AsyncClient):
    """Testa que solicitação de métricas sem autenticação é recusada com HTTP 401."""
    response = await client.get("/api/v1/dashboard/metrics")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_tier1_equipment_autocomplete_suggestions(client: AsyncClient, tecnico_tokens):
    """Testa endpoint de sugestões de autocompletar para prefixos válidos."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-SUGG-100",
            "description": "Equipamento Sugg",
            "brand": "LG",
            "model": "Equipamento Sugg",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )

    response = await client.get(
        "/api/v1/assets/suggestions?field=patrimony_number&prefix=PAT-S"
    )
    assert response.status_code == 200
    suggestions = response.json()
    assert "PAT-SUGG-100" in suggestions


@pytest.mark.anyio
async def test_tier1_dashboard_equipment_count_reflects_db(client: AsyncClient, tecnico_tokens):
    """Testa que o contador do dashboard reflete exatamente a quantidade de ativos."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    initial_count = (await client.get("/api/v1/dashboard/metrics")).json()["assets_total"]

    await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-DASH-1",
            "description": "Item 1",
            "brand": "Dell",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )
    await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-DASH-2",
            "description": "Item 2",
            "brand": "Dell",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )

    new_count = (await client.get("/api/v1/dashboard/metrics")).json()["assets_total"]
    assert new_count == initial_count + 2
