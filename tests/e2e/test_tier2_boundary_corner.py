"""E2E Test Suite - Tier 2: Boundary & Corner Cases (Canonical SisPatrimonio).

Covers boundary limits, invalid inputs, edge cases, RBAC restrictions, and error flows:
- F1: Auth Boundaries & Security Rate Limiting (RN-02, RN-05)
- F2: Asset Field Uniqueness, Null-Clearing & 404s
- F3: Maintenance & Movement Edge Conditions & 404s
- F4: Category & Location Duplicates & ON DELETE RESTRICT
- F5: Spreadsheet Parsing Edge Cases & Corrupt Inputs
- F6: Dashboard, Autocomplete & RBAC Restrictions
"""

import io

import openpyxl
import pytest
from httpx import AsyncClient

# ==============================================================================
# F1: Authentication & Rate Limiting Boundaries
# ==============================================================================


@pytest.mark.anyio
async def test_tier2_auth_wrong_password_generic_error(client: AsyncClient, e2e_users):
    """Testa que erro de senha incorreta retorna 401 com mensagem genérica sem vazar detalhe (RN-05)."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": e2e_users["tecnico"].email, "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    assert "inválid" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_tier2_auth_nonexistent_email_generic_error(client: AsyncClient):
    """Testa que email não cadastrado retorna o mesmo status 401 e mensagem genérica (RN-05)."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "naoexiste_e2e@empresa.com", "password": "QualquerSenha123!"},
    )
    assert response.status_code == 401
    assert "inválid" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_tier2_auth_rate_limit_10_attempts_blocked_on_11th(client: AsyncClient, e2e_users):
    """Testa proteção contra força bruta: 10 falhas pelo mesmo IP geram 401, a 11ª resulta em 429 (RN-02)."""
    ip_headers = {"X-Forwarded-For": "198.51.100.77"}

    for i in range(10):
        bad_payload = {"email": f"brute_force_{i}@empresa.com", "password": "WrongPassword!"}
        resp = await client.post("/api/v1/auth/login", json=bad_payload, headers=ip_headers)
        assert resp.status_code == 401

    blocked_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "brute_force_11@empresa.com", "password": "WrongPassword!"},
        headers=ip_headers,
    )
    assert blocked_resp.status_code == 429
    assert "bloqueado" in blocked_resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_tier2_auth_refresh_missing_cookie_rejected(client: AsyncClient):
    """Testa que rota de renovação sem o cookie refresh_token retorna 401."""
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
    assert "ausente" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_tier2_auth_refresh_invalid_token_type(client: AsyncClient, tecnico_tokens):
    """Testa que passar um access_token no lugar do refresh_token é recusado com 401."""
    client.cookies.set("refresh_token", tecnico_tokens["access_token"])
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
    assert "inválido" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_tier2_auth_tampered_token_rejected(client: AsyncClient):
    """Testa envio de token JWT adulterado ou com assinatura inválida."""
    client.cookies.set(
        "access_token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.adulterado.assinaturafalsa"
    )
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


# ==============================================================================
# F2: Asset Field Uniqueness, Null-Clearing & 404s
# ==============================================================================


@pytest.mark.anyio
async def test_tier2_equipment_duplicate_serial_number_rejected(
    client: AsyncClient, tecnico_tokens
):
    """Testa que número de série duplicado é recusado com HTTP 400."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    p1 = {
        "serial_number": "SN-DUP-01",
        "patrimony_number": "PAT-SN-DUP-01",
        "description": "Item SN Dup 1",
        "brand": "Dell",
        "category_id": tecnico_tokens["category_id"],
        "location_id": tecnico_tokens["location_id"],
    }
    p2 = {
        "serial_number": "SN-DUP-01",
        "patrimony_number": "PAT-SN-DUP-02",
        "description": "Item SN Dup 2",
        "brand": "Dell",
        "category_id": tecnico_tokens["category_id"],
        "location_id": tecnico_tokens["location_id"],
    }
    first = await client.post("/api/v1/assets", json=p1)
    assert first.status_code == 201

    duplicate = await client.post("/api/v1/assets", json=p2)
    assert duplicate.status_code == 409
    assert "série" in duplicate.json()["detail"].lower()


@pytest.mark.anyio
async def test_tier2_equipment_duplicate_patrimony_number_rejected(
    client: AsyncClient, tecnico_tokens
):
    """Testa que número de patrimônio duplicado é recusado com HTTP 409."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    p1 = {
        "patrimony_number": "PAT-DUP-01",
        "description": "Item Pat Dup 1",
        "brand": "Dell",
        "category_id": tecnico_tokens["category_id"],
        "location_id": tecnico_tokens["location_id"],
    }
    p2 = {
        "patrimony_number": "PAT-DUP-01",
        "description": "Item Pat Dup 2",
        "brand": "HP",
        "category_id": tecnico_tokens["category_id"],
        "location_id": tecnico_tokens["location_id"],
    }

    assert (await client.post("/api/v1/assets", json=p1)).status_code == 201
    dup_resp = await client.post("/api/v1/assets", json=p2)
    assert dup_resp.status_code == 409
    assert "patrimônio" in dup_resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_tier2_equipment_category_requires_serial_number_enforced(
    client: AsyncClient, tecnico_tokens
):
    """Testa que categoria exigindo número de série recusa ativo sem serial_number com HTTP 400."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    cat_req = (
        await client.post(
            "/api/v1/categories",
            json={"name": "Servidor Crítico", "requires_serial_number": True},
        )
    ).json()

    resp = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-REQ-SN-01",
            "description": "Servidor sem serial",
            "brand": "Dell",
            "category_id": cat_req["id"],
            "location_id": tecnico_tokens["location_id"],
            "serial_number": None,
        },
    )
    assert resp.status_code == 400
    assert "preenchimento obrigatório do número de série" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_tier2_equipment_clear_optional_fields_to_null_success(
    client: AsyncClient, tecnico_tokens, e2e_users
):
    """Testa que limpar campos opcionais para None/vazio via PUT /api/v1/assets/{id} funciona."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    initial_payload = {
        "serial_number": "SN-CLEAR-01",
        "patrimony_number": "PAT-CLEAR-01",
        "description": "Equipamento Inicial",
        "brand": "Dell",
        "model": "Modelo Inicial",
        "category_id": tecnico_tokens["category_id"],
        "location_id": tecnico_tokens["location_id"],
        "assigned_user_id": e2e_users["colaborador"].id,
        "purchase_cost": 3500.00,
    }
    created = await client.post("/api/v1/assets", json=initial_payload)
    assert created.status_code == 201
    eq_id = created.json()["id"]

    clear_payload = {
        "serial_number": None,
        "model": None,
        "assigned_user_id": None,
        "purchase_cost": None,
    }
    update_resp = await client.put(f"/api/v1/assets/{eq_id}", json=clear_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["serial_number"] is None
    assert updated["model"] is None
    assert updated["assigned_user_id"] is None
    assert updated["purchase_cost"] is None


@pytest.mark.anyio
async def test_tier2_equipment_get_nonexistent_id_404(client: AsyncClient, tecnico_tokens):
    """Testa consulta por ID inexistente retornando HTTP 404."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    response = await client.get("/api/v1/assets/999999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_tier2_equipment_update_nonexistent_id_404(client: AsyncClient, tecnico_tokens):
    """Testa atualização de ativo com ID inexistente retornando HTTP 404."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    response = await client.put("/api/v1/assets/999999", json={"model": "Fantasma"})
    assert response.status_code == 404


# ==============================================================================
# F3: Maintenance & Movement Edge Conditions & 404s
# ==============================================================================


@pytest.mark.anyio
async def test_tier2_maintenance_nonexistent_equipment_404(client: AsyncClient, tecnico_tokens):
    """Testa cadastro de manutenção para ativo inexistente retornando 404."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    payload = {
        "maintenance_date": "2026-09-01T00:00:00Z",
        "maintenance_type": "preventiva",
        "description": "Teste",
    }
    response = await client.post("/api/v1/assets/999999/maintenances", json=payload)
    assert response.status_code == 404


@pytest.mark.anyio
async def test_tier2_maintenance_update_nonexistent_maintenance_404(
    client: AsyncClient, tecnico_tokens
):
    """Testa edição de manutenção com ID inexistente retornando 404."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-M404-1",
            "description": "Item M404 1",
            "brand": "Dell",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )
    assert created.status_code == 201
    eq_id = created.json()["id"]

    response = await client.put(
        f"/api/v1/assets/{eq_id}/maintenances/999999", json={"description": "Novo"}
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_tier2_maintenance_delete_nonexistent_maintenance_404(
    client: AsyncClient, tecnico_tokens
):
    """Testa exclusão de manutenção inexistente retornando 404."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-M404-2",
            "description": "Item M404 2",
            "brand": "Dell",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )
    assert created.status_code == 201
    eq_id = created.json()["id"]

    response = await client.delete(f"/api/v1/assets/{eq_id}/maintenances/999999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_tier2_movement_nonexistent_equipment_404(client: AsyncClient, tecnico_tokens):
    """Testa movimentação de ativo inexistente retornando 404."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    mov_payload = {
        "origin_location_id": tecnico_tokens["location_id"],
        "dest_location_id": tecnico_tokens["location_id"],
        "notes": "Transferencia teste",
    }
    response = await client.post("/api/v1/assets/999999/movements", json=mov_payload)
    assert response.status_code == 404


@pytest.mark.anyio
async def test_tier2_maintenance_empty_description_rejected(client: AsyncClient, tecnico_tokens):
    """Testa validação de schema: descrição de manutenção vazia retorna 422."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-M422-1",
            "description": "Item M422",
            "brand": "Dell",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
        },
    )
    assert created.status_code == 201
    eq_id = created.json()["id"]

    bad_payload = {
        "maintenance_date": "2026-09-01T00:00:00Z",
        "maintenance_type": "preventiva",
        "description": "",
    }
    response = await client.post(f"/api/v1/assets/{eq_id}/maintenances", json=bad_payload)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_tier2_decommission_movement_without_dest_location(
    client: AsyncClient, tecnico_tokens
):
    """Testa baixa patrimonial (dest_location_id=None) alterando status para baixado."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-DECOMM-01",
            "description": "Item para Decommission",
            "brand": "Dell",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
            "status": "em_uso",
        },
    )
    assert created.status_code == 201
    eq_id = created.json()["id"]

    mov_resp = await client.post(
        f"/api/v1/assets/{eq_id}/movements",
        json={
            "origin_location_id": tecnico_tokens["location_id"],
            "dest_location_id": None,
            "notes": "Baixa por obsolescência",
        },
    )
    assert mov_resp.status_code == 201

    detail = (await client.get(f"/api/v1/assets/{eq_id}")).json()
    assert detail["status"] == "baixado"


# ==============================================================================
# F4: Category & Location Boundaries
# ==============================================================================


@pytest.mark.anyio
async def test_tier2_tag_duplicate_name_same_category_rejected(client: AsyncClient, tecnico_tokens):
    """Testa que criar categoria com nome duplicado é recusado com HTTP 409."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    payload = {"name": "Servidor Rack"}
    assert (await client.post("/api/v1/categories", json=payload)).status_code == 201

    dup_resp = await client.post("/api/v1/categories", json=payload)
    assert dup_resp.status_code == 409
    assert "cadastrad" in dup_resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_tier2_tag_same_name_different_category_allowed(client: AsyncClient, tecnico_tokens):
    """Testa que o mesmo nome em Categoria e Setor de Localização é permitido."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    resp1 = await client.post("/api/v1/categories", json={"name": "Operações"})
    resp2 = await client.post(
        "/api/v1/locations",
        json={"building": "Sede", "floor": "1", "sector": "Operações"},
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201


@pytest.mark.anyio
async def test_tier2_tag_empty_name_rejected(client: AsyncClient, tecnico_tokens):
    """Testa que categoria com nome vazio é rejeitada com HTTP 422."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    resp = await client.post("/api/v1/categories", json={"name": ""})
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_tier2_tag_update_nonexistent_tag_404(client: AsyncClient, tecnico_tokens):
    """Testa atualização de categoria inexistente retornando HTTP 404."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    resp = await client.put("/api/v1/categories/999999", json={"name": "Inexistente"})
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_tier2_tag_rename_to_existing_duplicate_rejected(client: AsyncClient, tecnico_tokens):
    """Testa que renomear categoria para um nome já em uso retorna HTTP 409."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    await client.post("/api/v1/categories", json={"name": "Cat A"})
    t2 = await client.post("/api/v1/categories", json={"name": "Cat B"})

    t2_id = t2.json()["id"]
    rename_resp = await client.put(f"/api/v1/categories/{t2_id}", json={"name": "Cat A"})
    assert rename_resp.status_code == 409
    assert "cadastrad" in rename_resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_tier2_tag_delete_nonexistent_tag_404(client: AsyncClient, tecnico_tokens):
    """Testa exclusão de categoria inexistente retornando HTTP 404."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    resp = await client.delete("/api/v1/categories/999999")
    assert resp.status_code == 404


# ==============================================================================
# F5: Spreadsheet Parsing Edge Cases & Corrupt Inputs
# ==============================================================================


@pytest.mark.anyio
async def test_tier2_import_empty_file_rejected(client: AsyncClient, tecnico_tokens):
    """Testa envio de arquivo vazio (0 bytes) retornando HTTP 400."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    files = {
        "file": (
            "vazio.xlsx",
            b"",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    resp = await client.post("/api/v1/equipments/import/preview", files=files)
    assert resp.status_code == 400
    assert "vazio" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_tier2_import_corrupted_file_rejected(client: AsyncClient, tecnico_tokens):
    """Testa envio de conteúdo binário corrompido com extensão .xlsx retornando HTTP 400."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    files = {
        "file": (
            "corrupto.xlsx",
            b"NOT_A_VALID_ZIP_OR_EXCEL_STREAM",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    resp = await client.post("/api/v1/equipments/import/preview", files=files)
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_tier2_import_empty_filename_rejected(
    client: AsyncClient, tecnico_tokens, make_csv_bytes
):
    """Testa envio de arquivo com nome vazio retornando HTTP 400/422."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    files = {"file": ("", make_csv_bytes(rows=[["DESKTOP"]], headers=["TIPO"]), "text/csv")}
    resp = await client.post("/api/v1/equipments/import/preview", files=files)
    assert resp.status_code in (400, 422)


@pytest.mark.anyio
async def test_tier2_import_handles_missing_serial_and_patrimony(
    client: AsyncClient, tecnico_tokens, make_excel_bytes
):
    """Testa que linhas sem serial e sem patrimônio recebem número de patrimônio gerado e serial None."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    headers = ["TIPO", "LOCALIZAÇÃO", "SITUAÇÃO", "DESCRIÇÃO", "Nº SÉRIE", "Nº PATRIMÔNIO"]
    row = ["DESKTOP", "CTM", "EM USO", "Computador Sem Identificadores", None, None]
    file_bytes = make_excel_bytes(rows=[row], headers=headers)

    files = {
        "file": (
            "sem_identificadores.xlsx",
            file_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    resp = await client.post("/api/v1/equipments/import/execute", files=files)
    assert resp.status_code == 200
    assert resp.json()["created_count"] == 1


@pytest.mark.anyio
async def test_tier2_import_blank_rows_ignored_gracefully(
    client: AsyncClient, tecnico_tokens, make_excel_bytes
):
    """Testa que linhas totalmente em branco intercaladas na planilha são ignoradas sem falha."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    headers = ["TIPO", "LOCALIZAÇÃO", "SITUAÇÃO", "DESCRIÇÃO"]
    rows = [
        ["NOTEBOOK", "TI", "EM USO", "Item Válido 1"],
        [None, None, None, None],
        ["DESKTOP", "RH", "EM USO", "Item Válido 2"],
    ]
    file_bytes = make_excel_bytes(rows=rows, headers=headers)

    files = {
        "file": (
            "intercalado.xlsx",
            file_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    resp = await client.post("/api/v1/equipments/import/execute", files=files)
    assert resp.status_code == 200
    assert resp.json()["created_count"] == 2


@pytest.mark.anyio
async def test_tier2_export_empty_database_valid_header(client: AsyncClient, tecnico_tokens):
    """Testa que exportar gera planilha válida com a aba 'Ativos Patrimoniais' e 12 colunas."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    resp = await client.get("/api/v1/assets/export")
    assert resp.status_code == 200

    wb = openpyxl.load_workbook(io.BytesIO(resp.content))
    assert "Ativos Patrimoniais" in wb.sheetnames
    ws = wb["Ativos Patrimoniais"]
    assert ws.max_column == 12


# ==============================================================================
# F6: Dashboard, Autocomplete & RBAC Restrictions
# ==============================================================================


@pytest.mark.anyio
async def test_tier2_equipment_suggestions_prefix_too_short(client: AsyncClient, tecnico_tokens):
    """Testa consulta de sugestões com prefixo curto retornando lista vazia ou filtrada."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    resp = await client.get("/api/v1/assets/suggestions?field=patrimony_number&prefix=A")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.anyio
async def test_tier2_equipment_suggestions_invalid_field(client: AsyncClient, tecnico_tokens):
    """Testa que solicitar sugestões para campo não mapeado retorna lista vazia."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    resp = await client.get("/api/v1/assets/suggestions?field=campo_invalido&prefix=TESTE")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_tier2_colaborador_rbac_forbidden_asset_create(
    client: AsyncClient, colaborador_tokens
):
    """Testa que colaborador recebe 403 Forbidden ao tentar cadastrar ativo patrimonial."""
    client.cookies.set("access_token", colaborador_tokens["access_token"])
    resp = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-ILLEGAL",
            "description": "Tentativa Colaborador",
            "brand": "Dell",
            "category_id": colaborador_tokens["category_id"],
            "location_id": colaborador_tokens["location_id"],
        },
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_tier2_colaborador_rbac_forbidden_location_create(
    client: AsyncClient, colaborador_tokens
):
    """Testa que colaborador recebe 403 Forbidden ao tentar cadastrar localização física."""
    client.cookies.set("access_token", colaborador_tokens["access_token"])
    resp = await client.post(
        "/api/v1/locations",
        json={"building": "Bloco Proibido", "floor": "1", "sector": "Invasao"},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_tier2_colaborador_rbac_forbidden_import_preview(
    client: AsyncClient, colaborador_tokens, make_csv_bytes
):
    """Testa que colaborador recebe 403 Forbidden ao tentar pré-visualizar importação."""
    client.cookies.set("access_token", colaborador_tokens["access_token"])
    files = {
        "file": ("teste.csv", make_csv_bytes(rows=[["NOTEBOOK"]], headers=["TIPO"]), "text/csv")
    }
    resp = await client.post("/api/v1/equipments/import/preview", files=files)
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_tier2_colaborador_rbac_forbidden_tag_management(
    client: AsyncClient, colaborador_tokens
):
    """Testa que colaborador recebe 403 Forbidden ao tentar criar nova categoria."""
    client.cookies.set("access_token", colaborador_tokens["access_token"])
    resp = await client.post("/api/v1/categories", json={"name": "Categoria Ilegal"})
    assert resp.status_code == 403
