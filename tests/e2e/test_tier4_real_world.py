"""E2E Test Suite - Tier 4: Real-World Scenarios (Multi-Step User Journeys).

Simulates end-to-end operational workflows observed in enterprise production:
- Scenario 1: IT Technician Onboarding & Inventory Setup
- Scenario 2: Equipment Incident & Maintenance Lifecycle
- Scenario 3: Enterprise Security Incident & Recovery
- Scenario 4: Legacy Data Migration & Reconciliation
- Scenario 5: Multi-Role RBAC Enforcement & Asset Provisioning
"""

import io

import openpyxl
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_tier4_scenario_it_technician_onboarding_and_inventory_setup(
    client: AsyncClient, e2e_users
):
    """Cenário 1: Fluxo diário do técnico de TI — Login, dashboard, taxonomia e ativos."""
    # 1. Login do Técnico
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": e2e_users["tecnico"].email, "password": e2e_users["raw_password"]},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    client.cookies.set("access_token", token)

    # 2. Consulta inicial do Dashboard
    dash_init = (await client.get("/api/v1/dashboard/metrics")).json()
    assert dash_init["equipments_total"] is not None
    init_total = dash_init["equipments_total"]

    # 3. Cadastro de novas Tags corporativas
    await client.post(
        "/api/v1/equipments/tags", json={"category": "tipo", "name": "Workstation CAD"}
    )
    await client.post(
        "/api/v1/equipments/tags",
        json={"category": "localizacao", "name": "Setor de Engenharia 3D"},
    )
    await client.post(
        "/api/v1/equipments/tags", json={"category": "situacao", "name": "Pronto para Uso"}
    )

    # 4. Cadastro de 3 equipamentos
    for i in range(1, 4):
        create_resp = await client.post(
            "/api/v1/equipments",
            json={
                "serial_number": f"SN-CAD-00{i}",
                "patrimony_number": f"PAT-CAD-00{i}",
                "hostname": f"ENG-WS-0{i}",
                "description": f"Workstation CAD Precision #{i}",
                "equipment_type": "Workstation CAD",
                "location": "Setor de Engenharia 3D",
                "status": "Pronto para Uso",
                "brand": "Dell",
            },
        )
        assert create_resp.status_code == 201

    # 5. Validação de autocompletar (Suggestions)
    sugg_resp = await client.get(
        "/api/v1/equipments/suggestions?field=patrimony_number&prefix=PAT-CAD"
    )
    assert sugg_resp.status_code == 200
    suggestions = sugg_resp.json()
    assert len(suggestions) == 3

    # 6. Listagem filtrada por localização
    list_resp = await client.get("/api/v1/equipments?location=Setor de Engenharia 3D")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 3

    # 7. Verificação de incremento no Dashboard
    dash_after = (await client.get("/api/v1/dashboard/metrics")).json()
    assert dash_after["equipments_total"] == init_total + 3


@pytest.mark.anyio
async def test_tier4_scenario_equipment_incident_and_maintenance_lifecycle(
    client: AsyncClient, tecnico_tokens
):
    """Cenário 2: Atendimento e reparo técnico de equipamento com exportação."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])

    # 1. Cadastro inicial do equipamento em uso
    created = await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-DELL-ENG-01",
            "patrimony_number": "PAT-DELL-ENG-01",
            "hostname": "ENG-LAP-01",
            "description": "Dell XPS 15 9520",
            "equipment_type": "Notebook",
            "location": "Engenharia",
            "status": "Em uso",
            "brand": "Dell",
        },
    )
    eq_id = created.json()["id"]

    # 2. Incidente reportado: Movimentação para o Laboratório de TI
    mov1 = await client.post(
        f"/api/v1/equipments/{eq_id}/movements",
        json={
            "origin_location": "Engenharia",
            "destination_location": "Laboratório TI",
            "movement_date": "2026-09-10T09:00:00Z",
            "notes": "Recolhido com artefatos de vídeo e superaquecimento",
        },
    )
    assert mov1.status_code == 201

    # Situação do equipamento permanece 'Em uso' (RN-EQ-12)
    eq_mid = (await client.get(f"/api/v1/equipments/{eq_id}")).json()
    assert eq_mid["location"] == "Laboratório TI"
    assert eq_mid["status"] == "Em uso"

    # 3. Primeira intervenção no dia 1
    m1 = await client.post(
        f"/api/v1/equipments/{eq_id}/maintenances",
        json={
            "maintenance_date": "2026-09-10T14:00:00Z",
            "maintenance_type": "Manutenção",
            "description": "Limpeza do cooler e substituição da pasta térmica de metal líquido",
            "notes": "Testes de temperatura iniciados",
        },
    )
    assert m1.status_code == 201

    # 4. Segunda intervenção no dia 3 com múltiplos itens agrupados
    m2 = await client.post(
        f"/api/v1/equipments/{eq_id}/maintenances",
        json={
            "maintenance_date": "2026-09-13T16:00:00Z",
            "maintenance_type": "Manutenção",
            "description": (
                "Substituição do módulo de ventoinha secundária, "
                "Teste de estresse FurMark por 2 horas"
            ),
            "notes": "Equipamento aprovado para devolução",
        },
    )
    assert m2.status_code == 201

    # 5. Devolução: Movimentação de retorno para a Engenharia
    mov2 = await client.post(
        f"/api/v1/equipments/{eq_id}/movements",
        json={
            "origin_location": "Laboratório TI",
            "destination_location": "Engenharia",
            "movement_date": "2026-09-14T10:00:00Z",
            "notes": "Devolvido operando perfeitamente",
        },
    )
    assert mov2.status_code == 201

    # 6. Verificação final no detalhe do equipamento
    final_detail = (await client.get(f"/api/v1/equipments/{eq_id}")).json()
    assert final_detail["location"] == "Engenharia"
    assert len(final_detail["movements"]) == 2
    assert len(final_detail["maintenances"]) == 2
    assert "2026-09-13" in final_detail["last_maintenance_at"]

    # 7. Exportação e verificação do dossiê em planilha
    export_resp = await client.get("/api/v1/equipments/export?patrimony_number=PAT-DELL-ENG-01")
    assert export_resp.status_code == 200

    wb = openpyxl.load_workbook(io.BytesIO(export_resp.content))
    ws = wb["Patrimônio"]
    assert ws.max_row == 2
    assert ws.cell(row=2, column=2).value == "Engenharia"
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

    # 1. Atacante realiza 10 tentativas com senhas erradas
    for i in range(1, 11):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": f"AttackPass_{i}"},
            headers=malicious_ip,
        )
        assert resp.status_code == 401
        assert "inválid" in resp.json()["detail"].lower()

    # 2. Na 11ª tentativa, IP atacante é bloqueado pelo Rate Limit (HTTP 429)
    blocked_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "QualquerSenha!"},
        headers=malicious_ip,
    )
    assert blocked_resp.status_code == 429
    assert "bloqueado" in blocked_resp.json()["detail"].lower()

    # 3. Técnico legítimo conecta da rede corporativa com credencial correta
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

    # 4. Acesso ao perfil protegido
    me_resp = await client.get("/api/v1/auth/me", headers=corporate_ip)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email

    # 5. Renovação de sessão via refresh token
    refresh_resp = await client.post("/api/v1/auth/refresh", headers=corporate_ip)
    assert refresh_resp.status_code == 200
    new_token = refresh_resp.json()["access_token"]
    assert new_token is not None

    # 6. Logout ordenado
    logout_resp = await client.post("/api/v1/auth/logout", headers=corporate_ip)
    assert logout_resp.status_code == 200
    assert "Logout realizado" in logout_resp.json()["message"]


@pytest.mark.anyio
async def test_tier4_scenario_legacy_spreadsheet_migration_and_reconciliation(
    client: AsyncClient, tecnico_tokens, make_excel_bytes
):
    """Cenário 4: Migração legada, criação de tags, reconciliação e exportação."""
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

    # 1. Pré-visualização dos dados (Preview)
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

    # 2. Execução da importação
    import_resp = await client.post("/api/v1/equipments/import/execute", files=files)
    assert import_resp.status_code == 200
    import_data = import_resp.json()
    assert import_data["created_count"] == 2

    # 3. Verificação das tags dinâmicas geradas automaticamente
    types = [t["name"] for t in (await client.get("/api/v1/equipments/tags?category=tipo")).json()]
    assert "Roteador" in types
    assert "Firewall" in types

    # 4. Reconciliação: Reenvio de planilha com atualização do firewall (upsert)
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

    # 5. Exportação e verificação do inventário reconciliado
    export_resp = await client.get("/api/v1/equipments/export?location=NOC Central")
    assert export_resp.status_code == 200

    wb = openpyxl.load_workbook(io.BytesIO(export_resp.content))
    ws = wb["Patrimônio"]
    assert ws.max_row == 3  # Cabeçalho + 2 itens
    descricoes = [ws.cell(row=r, column=4).value for r in range(2, 4)]
    assert "FortiGate 60F High Availability" in descricoes


@pytest.mark.anyio
async def test_tier4_scenario_multi_role_rbac_and_equipment_lifecycle(
    client: AsyncClient, e2e_users, make_csv_bytes
):
    """Cenário 5: Verificação estrita de RBAC multi-usuário e fluxo de provisionamento de ativo."""
    # 1. Login do Colaborador
    colab_login = await client.post(
        "/api/v1/auth/login",
        json={"email": e2e_users["colaborador"].email, "password": e2e_users["raw_password"]},
    )
    assert colab_login.status_code == 200
    colab_token = colab_login.json()["access_token"]
    client.cookies.set("access_token", colab_token)

    # 2. Colaborador tenta acessar recursos restritos e é barrado com 403
    assert (await client.get("/api/v1/equipments")).status_code == 403
    assert (await client.get("/api/v1/equipments/export")).status_code == 403
    tag_bad = await client.post(
        "/api/v1/equipments/tags", json={"category": "tipo", "name": "Hack"}
    )
    assert tag_bad.status_code == 403
    csv_file = {"file": ("t.csv", make_csv_bytes([["NOTEBOOK"]], ["TIPO"]), "text/csv")}
    import_resp = await client.post("/api/v1/equipments/import/preview", files=csv_file)
    assert import_resp.status_code == 403

    # Colaborador tem acesso permitido ao dashboard restrito (sem total de equipamentos)
    colab_dash = (await client.get("/api/v1/dashboard/metrics")).json()
    assert colab_dash["equipments_total"] is None

    # 3. Técnico faz login para provisionar o equipamento para o colaborador
    tec_login = await client.post(
        "/api/v1/auth/login",
        json={"email": e2e_users["tecnico"].email, "password": e2e_users["raw_password"]},
    )
    assert tec_login.status_code == 200
    tec_token = tec_login.json()["access_token"]
    client.cookies.set("access_token", tec_token)

    # 4. Técnico cadastra o equipamento para o colaborador
    provision_resp = await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-COLAB-DEV-01",
            "patrimony_number": "PAT-COLAB-DEV-01",
            "hostname": "MKT-NOTE-01",
            "description": "Lenovo ThinkPad E14",
            "equipment_type": "Notebook",
            "location": "Almoxarifado TI",
            "status": "Em uso",
            "brand": "Lenovo",
            "windows_key": "W269N-WFGWX-YVC9B-4J6C9-T83GX",
        },
    )
    assert provision_resp.status_code == 201
    eq_id = provision_resp.json()["id"]

    # 5. Técnico registra a entrega formal (movimentação para Marketing)
    mov_resp = await client.post(
        f"/api/v1/equipments/{eq_id}/movements",
        json={
            "origin_location": "Almoxarifado TI",
            "destination_location": "Marketing",
            "movement_date": "2026-10-14T11:00:00Z",
            "notes": f"Entregue para o colaborador {e2e_users['colaborador'].email}",
        },
    )
    assert mov_resp.status_code == 201

    # 6. Técnico verifica o equipamento com sua chave e localização
    detail = (await client.get(f"/api/v1/equipments/{eq_id}")).json()
    assert detail["location"] == "Marketing"
    assert detail["windows_key"] == "W269N-WFGWX-YVC9B-4J6C9-T83GX"
    assert len(detail["movements"]) == 1
