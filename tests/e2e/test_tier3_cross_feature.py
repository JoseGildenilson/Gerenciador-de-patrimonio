"""E2E Test Suite - Tier 3: Cross-Feature Combinations (Pairwise Interactions).

Validates multi-feature interactions and integration boundaries:
1. Tag Rename Cascade: Tag rename propagating across Equipment and Export.
2. Full Pipeline: Import -> Maintenance Logging -> Status Update -> Export.
3. Movement Lifecycle: Equipment Creation -> Movements -> Dashboard Metrics.
4. Security: Multi-IP Brute-Force Rate Limiting Lockout vs Legitimate User.
5. Tag Deletion: Dynamic Tag Deletion preserving historical references.
6. Discovery & Upsert: Bulk CSV Import with dynamic taxonomy discovery and upsert.
"""

import io

import openpyxl
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_tier3_tag_rename_propagation_across_equipments_and_export(
    client: AsyncClient, tecnico_tokens
):
    """Testa propagação de renomeação de tag: Tag -> Equipamento -> Busca -> Exportação."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])

    # 1. Cria nova tag de localização
    tag_create = await client.post(
        "/api/v1/equipments/tags",
        json={"category": "localizacao", "name": "Lab Prototipagem Antigo"},
    )
    assert tag_create.status_code == 201
    tag_id = tag_create.json()["id"]

    # 2. Cadastra 2 equipamentos associados a essa localização
    eq1 = await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-T3-CASCADE-1",
            "description": "Osciloscópio Digital",
            "equipment_type": "Laboratório",
            "location": "Lab Prototipagem Antigo",
            "status": "Em uso",
        },
    )
    assert eq1.status_code == 201
    eq1_id = eq1.json()["id"]

    eq2 = await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-T3-CASCADE-2",
            "description": "Gerador de Funções",
            "equipment_type": "Laboratório",
            "location": "Lab Prototipagem Antigo",
            "status": "Em uso",
        },
    )
    assert eq2.status_code == 201

    # 3. Renomeia a tag de localização para novo nome
    rename_resp = await client.put(
        f"/api/v1/equipments/tags/{tag_id}",
        json={"name": "Centro de Inovação e Testes"},
    )
    assert rename_resp.status_code == 200
    assert rename_resp.json()["name"] == "Centro de Inovação e Testes"

    # 4. Verifica se os equipamentos foram atualizados automaticamente
    eq1_detail = (await client.get(f"/api/v1/equipments/{eq1_id}")).json()
    assert eq1_detail["location"] == "Centro de Inovação e Testes"

    # 5. Verifica se busca por filtro reflete o novo nome
    search_resp = await client.get("/api/v1/equipments?location=Centro de Inovação e Testes")
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 2

    # 6. Exporta planilha e inspeciona o binário .xlsx
    export_resp = await client.get("/api/v1/equipments/export?location=Centro de Inovação e Testes")
    assert export_resp.status_code == 200

    wb = openpyxl.load_workbook(io.BytesIO(export_resp.content))
    ws = wb["Patrimônio"]
    assert ws.max_row == 3  # Cabeçalho + 2 linhas

    # Coluna B (índice 2) é LOCALIZAÇÃO
    for row in range(2, 4):
        assert ws.cell(row=row, column=2).value == "Centro de Inovação e Testes"


@pytest.mark.anyio
async def test_tier3_import_spreadsheet_then_record_maintenance_and_export(
    client: AsyncClient, tecnico_tokens, make_excel_bytes
):
    """Testa fluxo completo: Importação XLSX -> Manutenção -> Edição em lote -> Exportação."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])

    # 1. Importa planilha inicial
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

    # 2. Localiza o equipamento importado
    search = (await client.get("/api/v1/equipments?patrimony_number=PAT-PIPE-01")).json()
    eq = search["items"][0]
    eq_id = eq["id"]

    # 3. Registra uma segunda manutenção com data posterior e múltiplos itens
    maint_payload = {
        "maintenance_date": "2026-09-15T14:30:00Z",
        "maintenance_type": "Manutenção",
        "description": "Upgrade de memória para 256GB, Substituição de ventilador redundante",
        "notes": "Chamado emergencial atendido",
    }
    maint_resp = await client.post(f"/api/v1/equipments/{eq_id}/maintenances", json=maint_payload)
    assert maint_resp.status_code == 201

    # 4. Atualiza a situação do equipamento manualmente para 'Em manutenção'
    update_resp = await client.put(f"/api/v1/equipments/{eq_id}", json={"status": "Em manutenção"})
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "Em manutenção"

    # 5. Exporta equipamentos e inspeciona se o histórico consolida as intervenções
    export_resp = await client.get("/api/v1/equipments/export?patrimony_number=PAT-PIPE-01")
    assert export_resp.status_code == 200

    wb = openpyxl.load_workbook(io.BytesIO(export_resp.content))
    ws = wb["Patrimônio"]
    assert ws.max_row == 2

    # Coluna C = SITUAÇÃO, Coluna K = HISTÓRICO DE MOVIMENTAÇÕES
    assert ws.cell(row=2, column=3).value == "Em manutenção"
    hist_cell_value = ws.cell(row=2, column=11).value
    assert hist_cell_value is not None
    assert "Upgrade de memória" in hist_cell_value


@pytest.mark.anyio
async def test_tier3_movement_history_and_dashboard_reconciliation(
    client: AsyncClient, tecnico_tokens
):
    """Testa rastreabilidade de movimentações sucessivas com reconciliação no dashboard."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])

    # 1. Pega métricas iniciais do dashboard
    dash_init = (await client.get("/api/v1/dashboard/metrics")).json()
    init_total = dash_init["equipments_total"]

    # 2. Cria equipamento novo
    created = await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-T3-MOV-01",
            "description": "Notebook Suporte Avançado",
            "equipment_type": "Notebook",
            "location": "Almoxarifado TI",
            "status": "Ocioso",
        },
    )
    eq_id = created.json()["id"]

    # 3. Movimenta para Bancada de Preparação
    mov1 = await client.post(
        f"/api/v1/equipments/{eq_id}/movements",
        json={
            "origin_location": "Almoxarifado TI",
            "destination_location": "Bancada de Preparação",
            "movement_date": "2026-10-01T08:00:00Z",
            "notes": "Instalação de imagem corporativa",
        },
    )
    assert mov1.status_code == 201

    # 4. Movimenta para Financeiro
    mov2 = await client.post(
        f"/api/v1/equipments/{eq_id}/movements",
        json={
            "origin_location": "Bancada de Preparação",
            "destination_location": "Financeiro",
            "movement_date": "2026-10-02T10:00:00Z",
            "notes": "Entrega ao usuário final",
        },
    )
    assert mov2.status_code == 201

    # 5. Verifica integridade do histórico e localização atual
    detail = (await client.get(f"/api/v1/equipments/{eq_id}")).json()
    assert detail["location"] == "Financeiro"
    assert detail["status"] == "Ocioso"  # Movimentação não muda status automaticamente (RN-EQ-12)
    assert len(detail["movements"]) == 2

    # 6. Reconciliação no Dashboard: total deve ter aumentado em exatamente 1
    dash_final = (await client.get("/api/v1/dashboard/metrics")).json()
    assert dash_final["equipments_total"] == init_total + 1


@pytest.mark.anyio
async def test_tier3_rate_limiting_lockout_and_multi_ip_isolation(client: AsyncClient, e2e_users):
    """Testa que rate limit bloqueia o IP atacante mantendo o IP legítimo funcional."""
    attacker_ip = {"X-Forwarded-For": "198.51.100.222"}
    legit_ip = {"X-Forwarded-For": "203.0.113.88"}

    # Atacante falha 10 vezes
    for _ in range(10):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": e2e_users["tecnico"].email, "password": "WrongPassword!"},
            headers=attacker_ip,
        )
        assert resp.status_code == 401

    # 11ª tentativa do atacante é bloqueada com 429
    attacker_blocked = await client.post(
        "/api/v1/auth/login",
        json={"email": e2e_users["tecnico"].email, "password": e2e_users["raw_password"]},
        headers=attacker_ip,
    )
    assert attacker_blocked.status_code == 429

    # Usuário legítimo de outro IP acessa normalmente com sucesso
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
    """Testa que excluir tag preserva integridade de equipamentos, filtros e exportações."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])

    # 1. Cria tag 'Em Homologação'
    tag_resp = await client.post(
        "/api/v1/equipments/tags", json={"category": "situacao", "name": "Em Homologação"}
    )
    tag = tag_resp.json()
    tag_id = tag["id"]

    # 2. Cria equipamento usando essa situação
    await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-T3-HOMOLOG-01",
            "description": "Switch de Testes",
            "equipment_type": "Rede",
            "location": "Bancada",
            "status": "Em Homologação",
        },
    )

    # 3. Exclui a tag da taxonomia
    del_resp = await client.delete(f"/api/v1/equipments/tags/{tag_id}")
    assert del_resp.status_code == 200

    # 4. A tag foi removida da lista de tags
    tags = (await client.get("/api/v1/equipments/tags?category=situacao")).json()
    assert not any(t["id"] == tag_id for t in tags)

    # 5. Mas o equipamento mantém a situação e pode ser filtrado e exportado
    equipments = (await client.get("/api/v1/equipments?status=Em Homologação")).json()["items"]
    assert len(equipments) == 1
    assert equipments[0]["status"] == "Em Homologação"

    export_resp = await client.get("/api/v1/equipments/export?status=Em Homologação")
    assert export_resp.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(export_resp.content))
    ws = wb["Patrimônio"]
    assert ws.max_row == 2
    assert ws.cell(row=2, column=3).value == "Em Homologação"


@pytest.mark.anyio
async def test_tier3_bulk_csv_import_dynamic_tag_discovery_and_api_upsert(
    client: AsyncClient, tecnico_tokens, make_csv_bytes
):
    """Testa importação descobrindo tags dinâmicas, uso em novas criações e upsert idempotente."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])

    # 1. Prepara CSV com tipo e localização inéditos
    headers = ["TIPO", "LOCALIZAÇÃO", "SITUAÇÃO", "DESCRIÇÃO", "Nº PATRIMÔNIO", "Nº SÉRIE"]
    row1 = ["Acelerador GPU", "Cluster IA", "Em uso", "Nvidia A100", "PAT-GPU-01", "SN-GPU-01"]
    csv_bytes = make_csv_bytes(rows=[row1], headers=headers, delimiter=";")

    # 2. Importa
    import_resp = await client.post(
        "/api/v1/equipments/import/execute",
        files={"file": ("cluster.csv", csv_bytes, "text/csv")},
    )
    assert import_resp.status_code == 200
    assert import_resp.json()["created_count"] == 1

    # 3. Verifica se tags foram cadastradas automaticamente no sistema
    tags_tipo = (await client.get("/api/v1/equipments/tags?category=tipo")).json()
    assert any(t["name"] == "Acelerador GPU" for t in tags_tipo)

    tags_loc = (await client.get("/api/v1/equipments/tags?category=localizacao")).json()
    assert any(t["name"] == "Cluster IA" for t in tags_loc)

    # 4. Cadastra segundo item via API usando as mesmas tags recém-descobertas
    api_create = await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-GPU-02",
            "description": "Nvidia H100",
            "equipment_type": "Acelerador GPU",
            "location": "Cluster IA",
            "status": "Em uso",
        },
    )
    assert api_create.status_code == 201

    # 5. Reimporta planilha com descrição atualizada (upsert idempotente)
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

    # 6. Verifica se total de itens é exatamente 2
    list_resp = await client.get("/api/v1/equipments?type=Acelerador GPU")
    assert list_resp.json()["total"] == 2
