"""Testes de API HTTP para os endpoints de Gestão de Equipamentos e Catálogos (FastAPI)."""

from datetime import datetime, timezone
import io
import openpyxl
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_user
from src.core.security import create_access_token
from src.domain.models import Equipment, User
from src.main import app


@pytest.fixture
def auth_tecnico(create_test_user):
    user = create_test_user(email="tecnico_api@empresa.com", role="tecnico")
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {"user": user, "token": token, "cookies": {"access_token": token}}


@pytest.mark.anyio
async def test_equipment_api_rbac_forbidden_for_non_tecnico(client: AsyncClient):
    """Testa que usuário sem perfil técnico recebe HTTP 403 Forbidden (RN-EQ-10)."""
    app.dependency_overrides[get_current_user] = lambda: User(
        id=999,
        email="colaborador@empresa.com",
        role="colaborador",
        is_active=True,
    )
    try:
        response = await client.get("/api/v1/equipments")
        assert response.status_code == 403
        assert "restrito" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.anyio
async def test_equipment_api_create_and_get_detail_tecnico(
    client: AsyncClient,
    auth_tecnico,
    test_catalogs,
):
    """Testa cadastro e consulta detalhada de equipamento por Técnico."""
    client.cookies.set("access_token", auth_tecnico["token"])

    type_id = test_catalogs["type"].id
    sector_id = test_catalogs["sector_ti"].id
    status_id = test_catalogs["status_em_uso"].id

    payload = {
        "patrimony_number": "PAT-API-001",
        "serial_number": "SN-API-001",
        "hostname": "HOST-API-01",
        "description": "Dell OptiPlex 7090 API",
        "equipment_type_id": type_id,
        "sector_id": sector_id,
        "status_id": status_id,
        "brand": "Dell",
        "model": "OptiPlex 7090",
        "ip_address": "192.168.1.100",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "windows_product_key": "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
    }
    create_resp = await client.post("/api/v1/equipments", json=payload)
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["id"] is not None
    assert data["patrimony_number"] == "PAT-API-001"
    assert data["serial_number"] == "SN-API-001"
    assert data["windows_product_key"] == "••••••••••••••••"

    eq_id = data["id"]

    # Consulta detalhada
    detail_resp = await client.get(f"/api/v1/equipments/{eq_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["description"] == "Dell OptiPlex 7090 API"
    assert detail_data["equipment_type"]["id"] == type_id
    assert detail_data["sector"]["id"] == sector_id
    assert detail_data["status"]["id"] == status_id


@pytest.mark.anyio
async def test_equipment_api_get_detail_404(client: AsyncClient, auth_tecnico):
    """Testa HTTP 404 ao buscar equipamento inexistente."""
    client.cookies.set("access_token", auth_tecnico["token"])
    resp = await client.get("/api/v1/equipments/99999")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_equipment_api_duplicate_error_400(
    client: AsyncClient,
    auth_tecnico,
    test_catalogs,
):
    """Testa erro HTTP 400 em duplicidade de Patrimônio e Serial."""
    client.cookies.set("access_token", auth_tecnico["token"])

    type_id = test_catalogs["type"].id
    sector_id = test_catalogs["sector_ti"].id
    status_id = test_catalogs["status_em_uso"].id

    payload = {
        "patrimony_number": "PAT-DUP-API",
        "serial_number": "SN-DUP-API",
        "equipment_type_id": type_id,
        "sector_id": sector_id,
        "status_id": status_id,
    }
    resp1 = await client.post("/api/v1/equipments", json=payload)
    assert resp1.status_code == 201

    # Segunda tentativa com o mesmo patrimônio
    resp_dup = await client.post("/api/v1/equipments", json=payload)
    assert resp_dup.status_code == 400
    assert "já está cadastrado" in resp_dup.json()["detail"]


@pytest.mark.anyio
async def test_equipment_api_list_and_filters(
    client: AsyncClient,
    auth_tecnico,
    test_catalogs,
):
    """Testa listagem paginada e filtros na API HTTP."""
    client.cookies.set("access_token", auth_tecnico["token"])

    type_id = test_catalogs["type"].id
    sector_id = test_catalogs["sector_ti"].id
    status_id = test_catalogs["status_em_uso"].id

    for i in range(1, 4):
        await client.post(
            "/api/v1/equipments",
            json={
                "patrimony_number": f"PAT-LIST-{i}",
                "serial_number": f"SN-LIST-{i}",
                "description": f"Equipamento Teste {i}",
                "equipment_type_id": type_id,
                "sector_id": sector_id,
                "status_id": status_id,
                "model": f"Model-{i}",
            },
        )

    response = await client.get(
        f"/api/v1/equipments?page=1&limit=25&type={type_id}&sector={sector_id}&status={status_id}&patrimony_number=PAT-LIST-2"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["patrimony_number"] == "PAT-LIST-2"


@pytest.mark.anyio
async def test_equipment_api_update(
    client: AsyncClient,
    auth_tecnico,
    test_catalogs,
):
    """Testa atualização de equipamento e tratamento de erros."""
    client.cookies.set("access_token", auth_tecnico["token"])

    res = await client.post(
        "/api/v1/equipments",
        json={
            "patrimony_number": "PAT-UPD-1",
            "serial_number": "SN-UPD-1",
            "equipment_type_id": test_catalogs["type"].id,
            "sector_id": test_catalogs["sector_ti"].id,
            "status_id": test_catalogs["status_em_uso"].id,
        },
    )
    eq_id = res.json()["id"]

    # Atualização OK
    upd_resp = await client.put(
        f"/api/v1/equipments/{eq_id}",
        json={
            "description": "Modificado",
            "brand": "Dell",
            "model": "P123",
            "notes": "Obs editada",
        },
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["description"] == "Modificado"

    # Update 404
    upd_404 = await client.put("/api/v1/equipments/99999", json={"description": "Novo"})
    assert upd_404.status_code == 404

    # Update 400 (duplicidade)
    await client.post(
        "/api/v1/equipments",
        json={
            "patrimony_number": "PAT-UPD-EXISTING",
            "equipment_type_id": test_catalogs["type"].id,
            "sector_id": test_catalogs["sector_ti"].id,
            "status_id": test_catalogs["status_em_uso"].id,
        },
    )
    upd_400 = await client.put(
        f"/api/v1/equipments/{eq_id}", json={"patrimony_number": "PAT-UPD-EXISTING"}
    )
    assert upd_400.status_code == 400


@pytest.mark.anyio
async def test_equipment_api_soft_delete_and_restore(
    client: AsyncClient,
    auth_tecnico,
    test_catalogs,
):
    """Testa exclusão lógica e restauração com detecção de conflitos (HTTP 409)."""
    client.cookies.set("access_token", auth_tecnico["token"])

    res = await client.post(
        "/api/v1/equipments",
        json={
            "patrimony_number": "PAT-SD-1",
            "hostname": "HOST-CONFLICT",
            "equipment_type_id": test_catalogs["type"].id,
            "sector_id": test_catalogs["sector_ti"].id,
            "status_id": test_catalogs["status_em_uso"].id,
        },
    )
    eq_id = res.json()["id"]

    # Exclusão lógica
    del_res = await client.delete(f"/api/v1/equipments/{eq_id}")
    assert del_res.status_code == 200

    # Delete 404
    del_404 = await client.delete("/api/v1/equipments/99999")
    assert del_404.status_code == 404

    # Cria outro com o mesmo hostname (permitido pois o anterior está soft-deleted)
    await client.post(
        "/api/v1/equipments",
        json={
            "patrimony_number": "PAT-SD-2",
            "hostname": "HOST-CONFLICT",
            "equipment_type_id": test_catalogs["type"].id,
            "sector_id": test_catalogs["sector_ti"].id,
            "status_id": test_catalogs["status_em_uso"].id,
        },
    )

    # Restauração com conflito -> 409
    res_conflict = await client.post(f"/api/v1/equipments/{eq_id}/restore")
    assert res_conflict.status_code == 409
    assert "já está em uso" in res_conflict.json()["detail"].lower()

    # Restore 404
    res_404 = await client.post("/api/v1/equipments/99999/restore")
    assert res_404.status_code == 404

    # Restauração com sucesso de bem sem conflito
    res_clean = await client.post(
        "/api/v1/equipments",
        json={
            "patrimony_number": "PAT-SD-CLEAN",
            "equipment_type_id": test_catalogs["type"].id,
            "sector_id": test_catalogs["sector_ti"].id,
            "status_id": test_catalogs["status_em_uso"].id,
        },
    )
    clean_id = res_clean.json()["id"]
    await client.delete(f"/api/v1/equipments/{clean_id}")
    res_restore_success = await client.post(f"/api/v1/equipments/{clean_id}/restore")
    assert res_restore_success.status_code == 200
    assert res_restore_success.json()["id"] == clean_id


@pytest.mark.anyio
async def test_equipment_api_windows_key_reveal(
    client: AsyncClient,
    auth_tecnico,
    test_catalogs,
):
    """Testa revelação da chave criptografada do Windows."""
    client.cookies.set("access_token", auth_tecnico["token"])

    res = await client.post(
        "/api/v1/equipments",
        json={
            "patrimony_number": "PAT-WIN-1",
            "equipment_type_id": test_catalogs["type"].id,
            "sector_id": test_catalogs["sector_ti"].id,
            "status_id": test_catalogs["status_em_uso"].id,
            "windows_product_key": "ABCDE-FGHIJ-KLMNO-PQRST-UVWXY",
        },
    )
    eq_id = res.json()["id"]

    key_res = await client.get(f"/api/v1/equipments/{eq_id}/windows-key")
    assert key_res.status_code == 200
    assert key_res.json()["windows_product_key"] == "ABCDE-FGHIJ-KLMNO-PQRST-UVWXY"

    key_404 = await client.get("/api/v1/equipments/99999/windows-key")
    assert key_404.status_code == 404


@pytest.mark.anyio
async def test_equipment_api_catalogs_endpoints(client: AsyncClient, auth_tecnico):
    """Testa operações completas de catálogos via API HTTP."""
    client.cookies.set("access_token", auth_tecnico["token"])

    # 1. Cria item de tipo
    res_type = await client.post("/api/v1/equipment-types", json={"name": "Scanner"})
    assert res_type.status_code == 201
    type_id = res_type.json()["id"]

    # 2. Duplicado -> 400
    res_dup = await client.post("/api/v1/equipment-types", json={"name": "scanner"})
    assert res_dup.status_code == 400

    # 3. Listagem e detalhe
    res_list = await client.get("/api/v1/equipment-types")
    assert res_list.status_code == 200
    assert any(i["name"] == "Scanner" for i in res_list.json())

    res_get = await client.get(f"/api/v1/equipment-types/{type_id}")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Scanner"

    res_get_404 = await client.get("/api/v1/equipment-types/99999")
    assert res_get_404.status_code == 404

    # 4. Atualização
    res_upd = await client.put(f"/api/v1/equipment-types/{type_id}", json={"name": "Scanner 3D"})
    assert res_upd.status_code == 200
    assert res_upd.json()["name"] == "Scanner 3D"

    res_upd_404 = await client.put("/api/v1/equipment-types/99999", json={"name": "Outro"})
    assert res_upd_404.status_code == 404

    # Atualização duplicando nome existente de outro item -> 400
    res_other = await client.post("/api/v1/equipment-types", json={"name": "Impressora"})
    assert res_other.status_code == 201
    res_dup_upd = await client.put(
        f"/api/v1/equipment-types/{type_id}", json={"name": "Impressora"}
    )
    assert res_dup_upd.status_code == 400

    # 5. Exclusão lógica
    res_del_404 = await client.delete("/api/v1/equipment-types/99999")
    assert res_del_404.status_code == 404

    res_del = await client.delete(f"/api/v1/equipment-types/{type_id}")
    assert res_del.status_code == 200

    # 6. Restauração
    res_rest_404 = await client.post("/api/v1/equipment-types/99999/restore")
    assert res_rest_404.status_code == 404

    res_rest = await client.post(f"/api/v1/equipment-types/{type_id}/restore")
    assert res_rest.status_code == 200


@pytest.mark.anyio
async def test_equipment_api_movements(
    client: AsyncClient,
    auth_tecnico,
    test_catalogs,
):
    """Testa endpoints de movimentações com auto-ajuste e validações."""
    client.cookies.set("access_token", auth_tecnico["token"])

    s_ti = test_catalogs["sector_ti"].id
    s_com = test_catalogs["sector_com"].id
    s_dir = test_catalogs["sector_dir"].id

    res_eq = await client.post(
        "/api/v1/equipments",
        json={
            "patrimony_number": "PAT-MOV-API",
            "equipment_type_id": test_catalogs["type"].id,
            "sector_id": s_ti,
            "status_id": test_catalogs["status_em_uso"].id,
        },
    )
    eq_id = res_eq.json()["id"]

    # 1. Movimentação para o mesmo setor -> 400
    mov_same = await client.post(
        f"/api/v1/equipments/{eq_id}/movements",
        json={
            "origin_sector_id": s_ti,
            "destination_sector_id": s_ti,
            "movement_date": "2026-01-01T10:00:00Z",
        },
    )
    assert mov_same.status_code == 400

    # 2. Movimentação válida
    mov_valid = await client.post(
        f"/api/v1/equipments/{eq_id}/movements",
        json={
            "origin_sector_id": s_ti,
            "destination_sector_id": s_com,
            "movement_date": "2026-01-01T10:00:00Z",
            "notes": "Transferência para Comunicação",
        },
    )
    assert mov_valid.status_code == 201
    mov_id = mov_valid.json()["id"]

    # 3. Equipamento 404
    mov_404 = await client.post(
        "/api/v1/equipments/99999/movements",
        json={
            "origin_sector_id": s_ti,
            "destination_sector_id": s_com,
            "movement_date": "2026-01-01T10:00:00Z",
        },
    )
    assert mov_404.status_code == 404

    # 4. Atualização de movimentação
    upd_mov = await client.put(
        f"/api/v1/equipments/{eq_id}/movements/{mov_id}",
        json={
            "destination_sector_id": s_dir,
        },
    )
    assert upd_mov.status_code == 200
    assert upd_mov.json()["destination_sector"]["id"] == s_dir

    # Atualização 404 (movimentação inexistente)
    upd_404 = await client.put(
        f"/api/v1/equipments/{eq_id}/movements/99999", json={"destination_sector_id": s_dir}
    )
    assert upd_404.status_code == 404

    # Atualização 400 (origem igual ao destino)
    upd_400 = await client.put(
        f"/api/v1/equipments/{eq_id}/movements/{mov_id}",
        json={
            "origin_sector_id": s_ti,
            "destination_sector_id": s_ti,
        },
    )
    assert upd_400.status_code == 400


@pytest.mark.anyio
async def test_equipment_api_maintenances(
    client: AsyncClient,
    auth_tecnico,
    test_catalogs,
):
    """Testa ciclo de vida de manutenções via API HTTP."""
    client.cookies.set("access_token", auth_tecnico["token"])

    st_uso = test_catalogs["status_em_uso"].id
    st_manut = test_catalogs["status_em_manutencao"].id
    st_ocioso = test_catalogs["status_ocioso"].id
    m_prev = test_catalogs["maint_prev"].id

    res_eq = await client.post(
        "/api/v1/equipments",
        json={
            "patrimony_number": "PAT-MAINT-API",
            "equipment_type_id": test_catalogs["type"].id,
            "sector_id": test_catalogs["sector_ti"].id,
            "status_id": st_uso,
        },
    )
    assert res_eq.status_code == 201
    eq_id = res_eq.json()["id"]

    # Iniciar manutenção 404 (equipamento inexistente)
    start_404 = await client.post(
        "/api/v1/equipments/99999/maintenances",
        json={
            "maintenance_type_id": m_prev,
        },
    )
    assert start_404.status_code == 404

    # Iniciar manutenção 400 (tipo inválido)
    start_400 = await client.post(
        f"/api/v1/equipments/{eq_id}/maintenances",
        json={
            "maintenance_type_id": 99999,
        },
    )
    assert start_400.status_code == 400

    # 1. Inicia manutenção -> situação vira 'Em manutenção'
    res_start = await client.post(
        f"/api/v1/equipments/{eq_id}/maintenances",
        json={
            "maintenance_type_id": m_prev,
            "description": "Limpeza periódica",
        },
    )
    assert res_start.status_code == 201
    maint_id = res_start.json()["id"]

    # Valida status do equipamento atualizado para 'Em manutenção'
    eq_detail = await client.get(f"/api/v1/equipments/{eq_id}")
    assert eq_detail.json()["status"]["name"] == "Em manutenção"

    # 2. Iniciar segunda manutenção em aberto -> 409 Conflito
    res_dup_maint = await client.post(
        f"/api/v1/equipments/{eq_id}/maintenances",
        json={
            "maintenance_type_id": m_prev,
            "description": "Segunda manutenção simultânea",
        },
    )
    assert res_dup_maint.status_code == 409

    # 3. Atualizar dados cadastrais da manutenção
    res_upd_m = await client.put(
        f"/api/v1/equipments/{eq_id}/maintenances/{maint_id}",
        json={
            "description": "Limpeza periódica e troca de pasta",
        },
    )
    assert res_upd_m.status_code == 200
    assert res_upd_m.json()["description"] == "Limpeza periódica e troca de pasta"

    # Atualizar manutenção 404 e 400
    upd_m_404 = await client.put(
        f"/api/v1/equipments/99999/maintenances/{maint_id}", json={"description": "X"}
    )
    assert upd_m_404.status_code == 404
    upd_m_400 = await client.put(
        f"/api/v1/equipments/{eq_id}/maintenances/{maint_id}", json={"maintenance_type_id": 99999}
    )
    assert upd_m_400.status_code == 400

    # Concluir manutenção 404 e 400
    comp_404 = await client.post(
        f"/api/v1/equipments/99999/maintenances/{maint_id}/complete",
        json={"new_status_id": st_ocioso},
    )
    assert comp_404.status_code == 404
    comp_400 = await client.post(
        f"/api/v1/equipments/{eq_id}/maintenances/{maint_id}/complete",
        json={"new_status_id": st_manut},
    )
    assert comp_400.status_code == 400

    # 4. Concluir manutenção exigindo nova situação
    res_complete = await client.post(
        f"/api/v1/equipments/{eq_id}/maintenances/{maint_id}/complete",
        json={
            "new_status_id": st_ocioso,
            "description": "Concluído com êxito",
        },
    )
    assert res_complete.status_code == 200
    assert res_complete.json()["completed_at"] is not None

    # Valida nova situação aplicada ao bem
    eq_after = await client.get(f"/api/v1/equipments/{eq_id}")
    assert eq_after.json()["status"]["id"] == st_ocioso


@pytest.mark.anyio
async def test_equipment_api_suggestions_and_export(
    client: AsyncClient,
    auth_tecnico,
    test_catalogs,
):
    """Testa endpoints de sugestões e exportação em Excel."""
    client.cookies.set("access_token", auth_tecnico["token"])

    await client.post(
        "/api/v1/equipments",
        json={
            "patrimony_number": "PAT-SUG-01",
            "serial_number": "SN-SUG-01",
            "model": "Precision 5550",
            "equipment_type_id": test_catalogs["type"].id,
            "sector_id": test_catalogs["sector_ti"].id,
            "status_id": test_catalogs["status_em_uso"].id,
        },
    )

    # Suggestions
    res_sug = await client.get("/api/v1/equipments/suggestions?field=model&prefix=Pre")
    assert res_sug.status_code == 200
    assert len(res_sug.json()) >= 1

    # Suggestions bad field -> 400
    bad_field = await client.get("/api/v1/equipments/suggestions?field=invalido&prefix=Pre")
    assert bad_field.status_code == 400

    # Suggestions short prefix -> 400
    short_prefix = await client.get("/api/v1/equipments/suggestions?field=model&prefix=P")
    assert short_prefix.status_code == 400

    # Export
    exp_res = await client.get("/api/v1/equipments/export")
    assert exp_res.status_code == 200
    assert (
        exp_res.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert len(exp_res.content) > 100
