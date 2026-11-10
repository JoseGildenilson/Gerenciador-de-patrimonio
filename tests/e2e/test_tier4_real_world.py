"""E2E Test Suite - Tier 4: Real-World Scenarios (Canonical SisPatrimonio).

Simulates end-to-end operational workflows observed in enterprise production:
- Scenario 1: IT Technician & Admin Onboarding & Inventory Setup
- Scenario 2: Asset Incident & Maintenance Lifecycle
- Scenario 3: Enterprise Security Incident & Recovery
- Scenario 4: Legacy Data Migration & Reconciliation
- Scenario 5: Multi-Role RBAC Enforcement (`administrador`, `tecnico`, `colaborador`) & Asset Provisioning
"""

import io

import openpyxl
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_tier4_scenario_it_technician_onboarding_and_inventory_setup(
    client: AsyncClient, e2e_users
):
    """Cenário 1: Fluxo diário do técnico de TI — Login, dashboard, categorias/locais e ativos."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": e2e_users["tecnico"].email, "password": e2e_users["raw_password"]},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    client.cookies.set("access_token", token)

    dash_init = (await client.get("/api/v1/dashboard/metrics")).json()
    assert dash_init["assets_total"] is not None
    init_total = dash_init["assets_total"]

    cat_resp = await client.post(
        "/api/v1/categories",
        json={"name": "Workstation CAD", "requires_serial_number": True},
    )
    assert cat_resp.status_code == 201
    cat_id = cat_resp.json()["id"]

    loc_resp = await client.post(
        "/api/v1/locations",
        json={"building": "Bloco Eng", "floor": "3", "sector": "Setor de Engenharia 3D"},
    )
    assert loc_resp.status_code == 201
    loc_id = loc_resp.json()["id"]

    for i in range(1, 4):
        create_resp = await client.post(
            "/api/v1/assets",
            json={
                "serial_number": f"SN-CAD-00{i}",
                "patrimony_number": f"PAT-CAD-00{i}",
                "description": f"Workstation CAD Precision #{i}",
                "brand": "Dell",
                "model": f"Workstation CAD Precision #{i}",
                "category_id": cat_id,
                "location_id": loc_id,
                "status": "disponivel",
                "specs": {
                    "hostname": f"ENG-WS-0{i}",
                },
            },
        )
        assert create_resp.status_code == 201

    sugg_resp = await client.get("/api/v1/assets/suggestions?field=patrimony_number&prefix=PAT-CAD")
    assert sugg_resp.status_code == 200
    suggestions = sugg_resp.json()
    assert len(suggestions) == 3

    list_resp = await client.get(f"/api/v1/assets?location_id={loc_id}")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 3

    dash_after = (await client.get("/api/v1/dashboard/metrics")).json()
    assert dash_after["assets_total"] == init_total + 3


@pytest.mark.anyio
async def test_tier4_scenario_equipment_incident_and_maintenance_lifecycle(
    client: AsyncClient, tecnico_tokens
):
    """Cenário 2: Atendimento e reparo técnico de ativo com exportação."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])

    loc_eng = (
        await client.post(
            "/api/v1/locations",
            json={"building": "Sede", "floor": "2", "sector": "Engenharia"},
        )
    ).json()
    loc_lab = (
        await client.post(
            "/api/v1/locations",
            json={"building": "Sede", "floor": "1", "sector": "Laboratório TI"},
        )
    ).json()

    created = await client.post(
        "/api/v1/assets",
        json={
            "serial_number": "SN-DELL-ENG-01",
            "patrimony_number": "PAT-DELL-ENG-01",
            "description": "Dell XPS 15 9520",
            "brand": "Dell",
            "model": "Dell XPS 15 9520",
            "category_id": tecnico_tokens["category_id"],
            "location_id": loc_eng["id"],
            "status": "em_uso",
            "specs": {"hostname": "ENG-LAP-01"},
        },
    )
    assert created.status_code == 201
    eq_id = created.json()["id"]

    mov1 = await client.post(
        f"/api/v1/assets/{eq_id}/movements",
        json={
            "origin_location_id": loc_eng["id"],
            "dest_location_id": loc_lab["id"],
            "notes": "Recolhido com artefatos de vídeo e superaquecimento",
        },
    )
    assert mov1.status_code == 201

    eq_mid = (await client.get(f"/api/v1/assets/{eq_id}")).json()
    assert eq_mid["location_id"] == loc_lab["id"]

    m1 = await client.post(
        f"/api/v1/assets/{eq_id}/maintenances",
        json={
            "maintenance_date": "2026-09-10T14:00:00Z",
            "maintenance_type": "corretiva",
            "service_provider": "Lab TI Interno",
            "description": "Limpeza do cooler e substituição da pasta térmica de metal líquido",
        },
    )
    assert m1.status_code == 201

    m2 = await client.post(
        f"/api/v1/assets/{eq_id}/maintenances",
        json={
            "maintenance_date": "2026-09-13T16:00:00Z",
            "maintenance_type": "corretiva",
            "service_provider": "Lab TI Interno",
            "description": (
                "Substituição do módulo de ventoinha secundária, "
                "Teste de estresse FurMark por 2 horas"
            ),
        },
    )
    assert m2.status_code == 201

    mov2 = await client.post(
        f"/api/v1/assets/{eq_id}/movements",
        json={
            "origin_location_id": loc_lab["id"],
            "dest_location_id": loc_eng["id"],
            "notes": "Devolvido operando perfeitamente",
        },
    )
    assert mov2.status_code == 201

    final_detail = (await client.get(f"/api/v1/assets/{eq_id}")).json()
    assert final_detail["location_id"] == loc_eng["id"]
    assert len(final_detail["movements"]) == 2
    assert len(final_detail["maintenances"]) == 2
    assert "2026-09-13" in final_detail["last_maintenance_at"]

    export_resp = await client.get("/api/v1/assets/export?search=PAT-DELL-ENG-01")
    assert export_resp.status_code == 200

    wb = openpyxl.load_workbook(io.BytesIO(export_resp.content))
    ws = wb["Ativos Patrimoniais"]
    assert ws.max_row == 2
    assert "Engenharia" in ws.cell(row=2, column=2).value
    maint_cell = ws.cell(row=2, column=11).value
    assert maint_cell is not None
    assert "Limpeza do cooler" in maint_cell
    assert "Substituição do módulo de ventoinha" in maint_cell


@pytest.mark.anyio
async def test_tier4_scenario_security_bruteforce_defense_and_session_recovery(
    client: AsyncClient, e2e_users
):
    """Cenário 3: Ataque de força bruta com bloqueio e autenticação de outro IP."""
    malicious_ip = {"X-Forwarded-For": "198.51.100.99"}
    corporate_ip = {"X-Forwarded-For": "10.0.10.5"}
    email = e2e_users["tecnico"].email

    for i in range(1, 11):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": f"attack_attempt_{i}@empresa.com", "password": f"AttackPass_{i}"},
            headers=malicious_ip,
        )
        assert resp.status_code == 401
        assert "inválid" in resp.json()["detail"].lower()

    blocked_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "attack_attempt_11@empresa.com", "password": "QualquerSenha!"},
        headers=malicious_ip,
    )
    assert blocked_resp.status_code == 429
    assert "bloqueado" in blocked_resp.json()["detail"].lower()

    legit_login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": e2e_users["raw_password"]},
        headers=corporate_ip,
    )
    assert legit_login.status_code == 200
    token_data = legit_login.json()
    assert token_data["user"]["role"] == "tecnico"

    client.cookies.set("access_token", token_data["access_token"])
    client.cookies.set("refresh_token", legit_login.cookies.get("refresh_token"))

    me_resp = await client.get("/api/v1/auth/me", headers=corporate_ip)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email

    refresh_resp = await client.post("/api/v1/auth/refresh", headers=corporate_ip)
    assert refresh_resp.status_code == 200
    assert refresh_resp.json()["access_token"] is not None

    logout_resp = await client.post("/api/v1/auth/logout", headers=corporate_ip)
    assert logout_resp.status_code == 200
    assert "Logout realizado" in logout_resp.json()["message"]


@pytest.mark.anyio
async def test_tier4_scenario_legacy_spreadsheet_migration_and_reconciliation(
    client: AsyncClient, tecnico_tokens, make_excel_bytes
):
    """Cenário 4: Migração legada, criação automática de categorias/locais, reconciliação e exportação."""
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
        "HISTÓRICO DE MOVIMENTAÇÕES",
    ]
    rows = [
        [
            "Roteador",
            "NOC Central",
            "Em uso",
            "MikroTik CCR2004",
            "PAT-MIG-01",
            "SN-MIG-01",
            "MikroTik",
            "01/06/2026",
            "01/06/2026: Firmware 7.15",
        ],
        [
            "Firewall",
            "NOC Central",
            "Em uso",
            "FortiGate 60F",
            "PAT-MIG-02",
            "SN-MIG-02",
            "Fortinet",
            "15/07/2026",
            "15/07/2026: Licença renovada",
        ],
    ]
    file_bytes = make_excel_bytes(rows=rows, headers=headers)

    files = {
        "file": (
            "migracao_legada.xlsx",
            file_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    preview_resp = await client.post("/api/v1/equipments/import/preview", files=files)
    assert preview_resp.status_code == 200
    assert preview_resp.json()["total_rows"] == 2

    import_resp = await client.post("/api/v1/equipments/import/execute", files=files)
    assert import_resp.status_code == 200
    assert import_resp.json()["created_count"] == 2

    types = [c["name"] for c in (await client.get("/api/v1/categories")).json()]
    assert "Roteador" in types
    assert "Firewall" in types

    locs = (await client.get("/api/v1/locations")).json()
    noc_loc = next((loc for loc in locs if loc["sector"] == "NOC Central"), None)
    assert noc_loc is not None

    rows_updated = [
        [
            "Firewall",
            "NOC Central",
            "Em uso",
            "FortiGate 60F High Availability",
            "PAT-MIG-02",
            "SN-MIG-02",
            "Fortinet",
            "15/07/2026",
            "15/07/2026: Cluster HA ativo",
        ],
    ]
    upd_file_bytes = make_excel_bytes(rows=rows_updated, headers=headers)
    upd_files = {
        "file": (
            "reconciliacao.xlsx",
            upd_file_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    reconcile_resp = await client.post("/api/v1/equipments/import/execute", files=upd_files)
    assert reconcile_resp.status_code == 200
    assert reconcile_resp.json()["updated_count"] == 1
    assert reconcile_resp.json()["created_count"] == 0

    export_resp = await client.get(f"/api/v1/assets/export?location_id={noc_loc['id']}")
    assert export_resp.status_code == 200

    wb = openpyxl.load_workbook(io.BytesIO(export_resp.content))
    ws = wb["Ativos Patrimoniais"]
    assert ws.max_row == 3
    descricoes = [ws.cell(row=r, column=4).value for r in range(2, 4)]
    assert "FortiGate 60F High Availability" in descricoes


@pytest.mark.anyio
async def test_tier4_scenario_multi_role_rbac_and_equipment_lifecycle(
    client: AsyncClient, e2e_users, make_csv_bytes
):
    """Cenário 5: Verificação estrita de RBAC multi-usuário (administrador, tecnico, colaborador) e entrega com aceite."""
    # 1. Login do Colaborador
    colab_login = await client.post(
        "/api/v1/auth/login",
        json={"email": e2e_users["colaborador"].email, "password": e2e_users["raw_password"]},
    )
    assert colab_login.status_code == 200
    colab_token = colab_login.json()["access_token"]
    client.cookies.set("access_token", colab_token)

    # 2. Colaborador tenta acessar recursos restritos e é barrado com 403
    cat_bad = await client.post("/api/v1/categories", json={"name": "Hack"})
    assert cat_bad.status_code == 403
    loc_bad = await client.post(
        "/api/v1/locations", json={"building": "B", "floor": "1", "sector": "S"}
    )
    assert loc_bad.status_code == 403
    asset_bad = await client.post(
        "/api/v1/assets",
        json={
            "patrimony_number": "PAT-HACK",
            "description": "Hack",
            "brand": "Hack",
            "category_id": e2e_users["default_category"].id,
            "location_id": e2e_users["default_location"].id,
        },
    )
    assert asset_bad.status_code == 403
    csv_file = {"file": ("t.csv", make_csv_bytes([["NOTEBOOK"]], ["TIPO"]), "text/csv")}
    import_resp = await client.post("/api/v1/equipments/import/preview", files=csv_file)
    assert import_resp.status_code == 403

    # 3. Administrador faz login e tem acesso total
    adm_login = await client.post(
        "/api/v1/auth/login",
        json={"email": e2e_users["administrador"].email, "password": e2e_users["raw_password"]},
    )
    assert adm_login.status_code == 200
    adm_token = adm_login.json()["access_token"]
    client.cookies.set("access_token", adm_token)

    users_resp = await client.get("/api/v1/users")
    assert users_resp.status_code == 200
    assert any(u["email"] == e2e_users["colaborador"].email for u in users_resp.json())

    loc_mkt = (
        await client.post(
            "/api/v1/locations",
            json={"building": "Sede", "floor": "3", "sector": "Marketing"},
        )
    ).json()

    # 4. Administrador cadastra o ativo e movimenta para o colaborador
    provision_resp = await client.post(
        "/api/v1/assets",
        json={
            "serial_number": "SN-COLAB-DEV-01",
            "patrimony_number": "PAT-COLAB-DEV-01",
            "description": "Lenovo ThinkPad E14",
            "brand": "Lenovo",
            "model": "ThinkPad E14",
            "category_id": e2e_users["default_category"].id,
            "location_id": e2e_users["default_location"].id,
            "status": "em_uso",
            "specs": {
                "hostname": "MKT-NOTE-01",
                "windows_key": "W269N-WFGWX-YVC9B-4J6C9-T83GX",
            },
        },
    )
    assert provision_resp.status_code == 201
    eq_id = provision_resp.json()["id"]

    mov_resp = await client.post(
        f"/api/v1/assets/{eq_id}/movements",
        json={
            "origin_location_id": e2e_users["default_location"].id,
            "dest_location_id": loc_mkt["id"],
            "to_user_id": e2e_users["colaborador"].id,
            "notes": f"Entregue para o colaborador {e2e_users['colaborador'].email}",
        },
    )
    assert mov_resp.status_code == 201
    mov_id = mov_resp.json()["id"]

    # 5. Aceite do termo de custódia
    accept_resp = await client.post(f"/api/v1/movements/{mov_id}/accept-term")
    assert accept_resp.status_code == 200
    assert accept_resp.json()["term_accepted_at"] is not None

    detail = (await client.get(f"/api/v1/assets/{eq_id}")).json()
    assert detail["location_id"] == loc_mkt["id"]
    assert detail["assigned_user_id"] == e2e_users["colaborador"].id
    assert detail["specs"]["windows_key"] == "W269N-WFGWX-YVC9B-4J6C9-T83GX"
    assert len(detail["movements"]) == 1
