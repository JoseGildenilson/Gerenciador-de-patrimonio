"""E2E Test Suite - Tier 3: Cross-Feature Combinations (Canonical SisPatrimonio).

Validates multi-feature interactions and integration boundaries:
1. Location Update Cascade: Location update propagating across Assets, Filter, and Export.
2. Full Pipeline: Import -> Maintenance Logging -> Status Update -> Export.
3. Movement Lifecycle: Asset Creation -> Movements -> Dashboard Metrics.
4. Security: Multi-IP Brute-Force Rate Limiting Lockout vs Legitimate User.
5. ON DELETE RESTRICT Protection: Category deletion with linked assets vs unlinked.
6. Discovery & Upsert: Bulk CSV Import with dynamic category/location discovery and upsert.
"""

import io

import openpyxl
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_tier3_tag_rename_propagation_across_equipments_and_export(
    client: AsyncClient, tecnico_tokens
):
    """Testa propagação de atualização de localização: Location -> Asset -> Filtro -> Exportação."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])

    loc_create = await client.post(
        "/api/v1/locations",
        json={"building": "Bloco Lab", "floor": "1", "sector": "Lab Prototipagem Antigo"},
    )
    assert loc_create.status_code == 201
    loc_id = loc_create.json()["id"]

    eq1 = await client.post(
        "/api/v1/assets",
        json={
            "serial_number": "SN-T3-CASCADE-1",
            "patrimony_number": "PAT-T3-CASCADE-1",
            "description": "Osciloscópio Digital",
            "brand": "Tektronix",
            "model": "Osciloscópio Digital",
            "category_id": tecnico_tokens["category_id"],
            "location_id": loc_id,
            "status": "em_uso",
        },
    )
    assert eq1.status_code == 201
    eq1_id = eq1.json()["id"]

    eq2 = await client.post(
        "/api/v1/assets",
        json={
            "serial_number": "SN-T3-CASCADE-2",
            "patrimony_number": "PAT-T3-CASCADE-2",
            "description": "Gerador de Funções",
            "brand": "Keysight",
            "model": "Gerador de Funções",
            "category_id": tecnico_tokens["category_id"],
            "location_id": loc_id,
            "status": "em_uso",
        },
    )
    assert eq2.status_code == 201

    rename_resp = await client.put(
        f"/api/v1/locations/{loc_id}",
        json={"sector": "Centro de Inovação e Testes"},
    )
    assert rename_resp.status_code == 200
    assert rename_resp.json()["sector"] == "Centro de Inovação e Testes"

    eq1_detail = (await client.get(f"/api/v1/assets/{eq1_id}")).json()
    assert eq1_detail["location"]["sector"] == "Centro de Inovação e Testes"

    search_resp = await client.get(f"/api/v1/assets?location_id={loc_id}")
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 2

    export_resp = await client.get(f"/api/v1/assets/export?location_id={loc_id}")
    assert export_resp.status_code == 200

    wb = openpyxl.load_workbook(io.BytesIO(export_resp.content))
    assert "Ativos Patrimoniais" in wb.sheetnames
    ws = wb["Ativos Patrimoniais"]
    assert ws.max_row == 3
    for row in range(2, 4):
        assert "Centro de Inovação e Testes" in ws.cell(row=row, column=2).value


@pytest.mark.anyio
async def test_tier3_import_spreadsheet_then_record_maintenance_and_export(
    client: AsyncClient, tecnico_tokens, make_excel_bytes
):
    """Testa fluxo completo: Importação XLSX -> Manutenção -> Edição de status -> Exportação."""
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
        "SERVIDOR",
        "DATACENTER A",
        "EM USO",
        "Dell PowerEdge R750xs",
        "PAT-PIPE-01",
        "SN-PIPE-01",
        "10/01/2026: Comissionamento inicial",
    ]
    file_bytes = make_excel_bytes(rows=[row], headers=headers)

    import_resp = await client.post(
        "/api/v1/equipments/import/execute",
        files={
            "file": (
                "servidores.xlsx",
                file_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert import_resp.status_code == 200
    assert import_resp.json()["created_count"] == 1

    search = (await client.get("/api/v1/assets?search=PAT-PIPE-01")).json()
    eq = search["items"][0]
    eq_id = eq["id"]

    maint_payload = {
        "maintenance_date": "2026-09-15T14:30:00Z",
        "maintenance_type": "corretiva",
        "service_provider": "Dell ProSupport",
        "description": "Upgrade de memória para 256GB, Substituição de ventilador redundante",
        "cost": 1200.00,
    }
    maint_resp = await client.post(f"/api/v1/assets/{eq_id}/maintenances", json=maint_payload)
    assert maint_resp.status_code == 201

    update_resp = await client.put(f"/api/v1/assets/{eq_id}", json={"status": "em_manutencao"})
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "em_manutencao"

    export_resp = await client.get("/api/v1/assets/export?search=PAT-PIPE-01")
    assert export_resp.status_code == 200

    wb = openpyxl.load_workbook(io.BytesIO(export_resp.content))
    ws = wb["Ativos Patrimoniais"]
    assert ws.max_row == 2
    assert ws.cell(row=2, column=3).value == "em_manutencao"
    hist_cell_value = ws.cell(row=2, column=11).value
    assert hist_cell_value is not None
    assert "Upgrade de memória" in hist_cell_value


@pytest.mark.anyio
async def test_tier3_movement_history_and_dashboard_reconciliation(
    client: AsyncClient, tecnico_tokens
):
    """Testa rastreabilidade de movimentações sucessivas com reconciliação no dashboard."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])

    dash_init = (await client.get("/api/v1/dashboard/metrics")).json()
    init_total = dash_init["assets_total"]

    loc1 = (
        await client.post(
            "/api/v1/locations",
            json={"building": "Sede", "floor": "1", "sector": "Bancada de Preparação"},
        )
    ).json()
    loc2 = (
        await client.post(
            "/api/v1/locations",
            json={"building": "Sede", "floor": "2", "sector": "Financeiro"},
        )
    ).json()

    created = await client.post(
        "/api/v1/assets",
        json={
            "serial_number": "SN-T3-MOV-01",
            "patrimony_number": "PAT-T3-MOV-01",
            "description": "Notebook Suporte Avançado",
            "brand": "Dell",
            "model": "Notebook Suporte Avançado",
            "category_id": tecnico_tokens["category_id"],
            "location_id": tecnico_tokens["location_id"],
            "status": "disponivel",
        },
    )
    assert created.status_code == 201
    eq_id = created.json()["id"]

    mov1 = await client.post(
        f"/api/v1/assets/{eq_id}/movements",
        json={
            "origin_location_id": tecnico_tokens["location_id"],
            "dest_location_id": loc1["id"],
            "notes": "Instalação de imagem corporativa",
        },
    )
    assert mov1.status_code == 201

    mov2 = await client.post(
        f"/api/v1/assets/{eq_id}/movements",
        json={
            "origin_location_id": loc1["id"],
            "dest_location_id": loc2["id"],
            "notes": "Entrega ao setor Financeiro",
        },
    )
    assert mov2.status_code == 201

    detail = (await client.get(f"/api/v1/assets/{eq_id}")).json()
    assert detail["location_id"] == loc2["id"]
    assert len(detail["movements"]) == 2

    dash_final = (await client.get("/api/v1/dashboard/metrics")).json()
    assert dash_final["assets_total"] == init_total + 1


@pytest.mark.anyio
async def test_tier3_rate_limiting_lockout_and_multi_ip_isolation(client: AsyncClient, e2e_users):
    """Testa que rate limit bloqueia o IP atacante mantendo o IP legítimo funcional."""
    attacker_ip = {"X-Forwarded-For": "198.51.100.222"}
    legit_ip = {"X-Forwarded-For": "203.0.113.88"}

    for i in range(10):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": f"attacker_{i}@empresa.com", "password": "WrongPassword!"},
            headers=attacker_ip,
        )
        assert resp.status_code == 401

    attacker_blocked = await client.post(
        "/api/v1/auth/login",
        json={"email": "attacker_11@empresa.com", "password": "WrongPassword!"},
        headers=attacker_ip,
    )
    assert attacker_blocked.status_code == 429

    legit_login = await client.post(
        "/api/v1/auth/login",
        json={"email": e2e_users["tecnico"].email, "password": e2e_users["raw_password"]},
        headers=legit_ip,
    )
    assert legit_login.status_code == 200
    assert "access_token" in legit_login.json()


@pytest.mark.anyio
async def test_tier3_tag_deletion_with_filter_and_export_integrity(
    client: AsyncClient, tecnico_tokens
):
    """Testa proteção ON DELETE RESTRICT em Categorias vinculadas e integridade de exportação."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])

    cat_resp = await client.post(
        "/api/v1/categories", json={"name": "Rede Homologação", "requires_serial_number": False}
    )
    assert cat_resp.status_code == 201
    cat_id = cat_resp.json()["id"]

    asset_resp = await client.post(
        "/api/v1/assets",
        json={
            "serial_number": "SN-T3-HOMOLOG-01",
            "patrimony_number": "PAT-T3-HOMOLOG-01",
            "description": "Switch de Testes",
            "brand": "Cisco",
            "model": "Switch de Testes",
            "category_id": cat_id,
            "location_id": tecnico_tokens["location_id"],
            "status": "em_manutencao",
        },
    )
    assert asset_resp.status_code == 201

    del_resp = await client.delete(f"/api/v1/categories/{cat_id}")
    assert del_resp.status_code == 409

    equipments = (await client.get("/api/v1/assets?status=em_manutencao")).json()["items"]
    assert any(e["patrimony_number"] == "PAT-T3-HOMOLOG-01" for e in equipments)

    export_resp = await client.get("/api/v1/assets/export?status=em_manutencao")
    assert export_resp.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(export_resp.content))
    ws = wb["Ativos Patrimoniais"]
    assert ws.max_row >= 2


@pytest.mark.anyio
async def test_tier3_bulk_csv_import_dynamic_tag_discovery_and_api_upsert(
    client: AsyncClient, tecnico_tokens, make_csv_bytes
):
    """Testa importação descobrindo categorias/localizações dinâmicas, uso em novas criações e upsert."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])

    headers = ["TIPO", "LOCALIZAÇÃO", "SITUAÇÃO", "DESCRIÇÃO", "Nº PATRIMÔNIO", "Nº SÉRIE"]
    row1 = ["Acelerador GPU", "Cluster IA", "Em uso", "Nvidia A100", "PAT-GPU-01", "SN-GPU-01"]
    csv_bytes = make_csv_bytes(rows=[row1], headers=headers, delimiter=";")

    import_resp = await client.post(
        "/api/v1/equipments/import/execute",
        files={"file": ("cluster.csv", csv_bytes, "text/csv")},
    )
    assert import_resp.status_code == 200
    assert import_resp.json()["created_count"] == 1

    cats = (await client.get("/api/v1/categories")).json()
    gpu_cat = next((c for c in cats if c["name"] == "Acelerador GPU"), None)
    assert gpu_cat is not None

    locs = (await client.get("/api/v1/locations")).json()
    cluster_loc = next((loc for loc in locs if loc["sector"] == "Cluster IA"), None)
    assert cluster_loc is not None

    api_create = await client.post(
        "/api/v1/assets",
        json={
            "serial_number": "SN-GPU-02",
            "patrimony_number": "PAT-GPU-02",
            "description": "Nvidia H100",
            "brand": "Nvidia",
            "model": "Nvidia H100",
            "category_id": gpu_cat["id"],
            "location_id": cluster_loc["id"],
            "status": "em_uso",
        },
    )
    assert api_create.status_code == 201

    row1_updated = [
        "Acelerador GPU",
        "Cluster IA",
        "Em uso",
        "Nvidia A100 80GB SXM4",
        "PAT-GPU-01",
        "SN-GPU-01",
    ]
    csv_updated_bytes = make_csv_bytes(rows=[row1_updated], headers=headers, delimiter=";")
    reimport_resp = await client.post(
        "/api/v1/equipments/import/execute",
        files={"file": ("cluster_upd.csv", csv_updated_bytes, "text/csv")},
    )
    assert reimport_resp.status_code == 200
    assert reimport_resp.json()["updated_count"] == 1
    assert reimport_resp.json()["created_count"] == 0

    list_resp = await client.get(f"/api/v1/assets?category_id={gpu_cat['id']}")
    assert list_resp.json()["total"] == 2
