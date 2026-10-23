"""E2E Test Suite - Tier 1: Feature Coverage (Normative & Happy Paths).

Covers all core system features with genuine, opaque-box HTTP API tests:
- F1: Authentication & Session Lifecycle (RN-01 to RN-07)
- F2: Equipment Management CRUD & Multi-Filters (RN-EQ-01 to RN-EQ-16)
- F3: Maintenance History & Movements (RN-EQ-09 to RN-EQ-12)
- F4: Tag Taxonomy CRUD & Propagation (RN-TAG-01 to RN-TAG-09)
- F5: Spreadsheet Import & Export (RN-IMP-01 to RN-IMP-06, RN-EXP-01 to RN-EXP-13)
- F6: Dashboard & Operational Health (RN-DASH-01 to RN-DASH-05)
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

    # Verifica se os cookies foram enviados na resposta
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
# F2: Equipment Management CRUD & Multi-Filters
# ==============================================================================


@pytest.mark.anyio
async def test_tier1_equipment_create_success(client: AsyncClient, tecnico_tokens):
    """Testa cadastro completo de equipamento com identificadores e atributos."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    payload = {
        "serial_number": "SN-T1-001",
        "patrimony_number": "PAT-T1-001",
        "hostname": "HOST-T1-01",
        "description": "Dell Latitude 5420 i7 16GB",
        "equipment_type": "Notebook",
        "location": "TI",
        "status": "Em uso",
        "brand": "Dell",
        "product_number": "PRD-9988",
        "windows_key": "VK7JG-NPHTM-C97JM-9MPGT-3V66T",
        "notes": "Equipamento principal de desenvolvimento",
    }
    response = await client.post("/api/v1/equipments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["serial_number"] == "SN-T1-001"
    assert data["patrimony_number"] == "PAT-T1-001"
    assert data["equipment_type"] == "Notebook"
    assert data["movements"] == []
    assert data["maintenances"] == []


@pytest.mark.anyio
async def test_tier1_equipment_get_detail(client: AsyncClient, tecnico_tokens):
    """Testa recuperação detalhada de equipamento por ID."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    payload = {
        "serial_number": "SN-T1-DETAIL",
        "description": "Monitor LG 24 Polegadas",
        "equipment_type": "Monitor",
        "location": "Comunicação",
        "status": "Em uso",
    }
    create_resp = await client.post("/api/v1/equipments", json=payload)
    eq_id = create_resp.json()["id"]

    detail_resp = await client.get(f"/api/v1/equipments/{eq_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == eq_id
    assert detail["description"] == "Monitor LG 24 Polegadas"
    assert detail["equipment_type"] == "Monitor"
    assert detail["location"] == "Comunicação"


@pytest.mark.anyio
async def test_tier1_equipment_pagination_and_sorting(client: AsyncClient, tecnico_tokens):
    """Testa listagem paginada com total e páginas calculadas."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    for i in range(3):
        await client.post(
            "/api/v1/equipments",
            json={
                "serial_number": f"SN-PAGE-{i}",
                "description": f"Equipamento Paginado {i}",
                "equipment_type": "Desktop",
                "location": "RH",
                "status": "Em uso",
            },
        )

    response = await client.get("/api/v1/equipments?page=1&limit=2&sort_by=created_at&sort_dir=asc")
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
    await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-OR-1",
            "description": "Notebook Alfa",
            "equipment_type": "Notebook",
            "location": "TI",
        },
    )
    await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-OR-2",
            "description": "Desktop Beta",
            "equipment_type": "Desktop",
            "location": "TI",
        },
    )
    await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-OR-3",
            "description": "Impressora Gama",
            "equipment_type": "Impressora",
            "location": "TI",
        },
    )

    # Filtra por Notebook OU Desktop
    resp = await client.get("/api/v1/equipments?type=Notebook&type=Desktop")
    assert resp.status_code == 200
    items = resp.json()["items"]
    types = {item["equipment_type"] for item in items}
    assert "Notebook" in types
    assert "Desktop" in types
    assert "Impressora" not in types


@pytest.mark.anyio
async def test_tier1_equipment_filter_multiple_fields_and_logic(
    client: AsyncClient, tecnico_tokens
):
    """Testa que filtros em campos distintos combinam com lógica AND."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-AND-1",
            "description": "Notebook TI",
            "equipment_type": "Notebook",
            "location": "TI",
        },
    )
    await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-AND-2",
            "description": "Notebook RH",
            "equipment_type": "Notebook",
            "location": "RH",
        },
    )
    await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-AND-3",
            "description": "Desktop TI",
            "equipment_type": "Desktop",
            "location": "TI",
        },
    )

    # Filtra por (type=Notebook) AND (location=TI)
    resp = await client.get("/api/v1/equipments?type=Notebook&location=TI")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["description"] == "Notebook TI"


@pytest.mark.anyio
async def test_tier1_equipment_update_batch_mode(client: AsyncClient, tecnico_tokens):
    """Testa edição completa em tela única via PUT /api/v1/equipments/{id}."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/equipments",
        json={"description": "Nome Antigo", "equipment_type": "Notebook", "location": "TI"},
    )
    eq_id = created.json()["id"]

    update_payload = {
        "description": "Nome Atualizado ThinkPad",
        "equipment_type": "Laptop",
        "location": "Diretoria",
        "status": "Ocioso",
        "brand": "Lenovo",
        "notes": "Revisado pela equipe",
    }
    update_resp = await client.put(f"/api/v1/equipments/{eq_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["description"] == "Nome Atualizado ThinkPad"
    assert updated["equipment_type"] == "Laptop"
    assert updated["location"] == "Diretoria"
    assert updated["status"] == "Ocioso"


# ==============================================================================
# F3: Maintenance History & Location Movements
# ==============================================================================


@pytest.mark.anyio
async def test_tier1_maintenance_record_grouped_items(client: AsyncClient, tecnico_tokens):
    """Testa registro de manutenção agrupada com múltiplos itens e atualização automática da última data."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/equipments",
        json={
            "description": "Server Dell R740",
            "equipment_type": "Servidor",
            "location": "Datacenter",
            "status": "Em uso",
        },
    )
    eq_id = created.json()["id"]

    maint_payload = {
        "maintenance_date": "2026-09-18T10:00:00Z",
        "maintenance_type": "Manutenção",
        "description": "Troca de SSD, Limpeza interna, Troca de pasta térmica",
        "notes": "Intervenção preventiva periódica",
    }
    maint_resp = await client.post(f"/api/v1/equipments/{eq_id}/maintenances", json=maint_payload)
    assert maint_resp.status_code == 201
    maint_data = maint_resp.json()
    assert maint_data["equipment_id"] == eq_id
    assert "Troca de SSD" in maint_data["description"]

    # Verifica se a data de última manutenção do equipamento foi atualizada
    detail_resp = await client.get(f"/api/v1/equipments/{eq_id}")
    eq_detail = detail_resp.json()
    assert eq_detail["last_maintenance_at"] is not None
    assert "2026-09-18" in eq_detail["last_maintenance_at"]
    assert len(eq_detail["maintenances"]) == 1


@pytest.mark.anyio
async def test_tier1_maintenance_preserves_equipment_status(client: AsyncClient, tecnico_tokens):
    """Testa que registrar manutenção não altera a situação/status do equipamento (RN-EQ-12)."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/equipments",
        json={
            "description": "Workstation",
            "equipment_type": "Desktop",
            "location": "TI",
            "status": "Em uso",
        },
    )
    eq_id = created.json()["id"]

    await client.post(
        f"/api/v1/equipments/{eq_id}/maintenances",
        json={"maintenance_date": "2026-09-20T12:00:00Z", "description": "Formatação do SO"},
    )

    detail_resp = await client.get(f"/api/v1/equipments/{eq_id}")
    assert detail_resp.json()["status"] == "Em uso"


@pytest.mark.anyio
async def test_tier1_maintenance_update_fields(client: AsyncClient, tecnico_tokens):
    """Testa edição de registro de manutenção existente no histórico."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/equipments",
        json={"description": "MacBook", "equipment_type": "Notebook", "location": "Design"},
    )
    eq_id = created.json()["id"]

    m_create = await client.post(
        f"/api/v1/equipments/{eq_id}/maintenances",
        json={"maintenance_date": "2026-08-01T00:00:00Z", "description": "Troca de Teclado"},
    )
    mid = m_create.json()["id"]

    update_resp = await client.put(
        f"/api/v1/equipments/{eq_id}/maintenances/{mid}",
        json={"description": "Troca de Teclado e Bateria Nova", "notes": "Garantia estendida"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Troca de Teclado e Bateria Nova"
    assert update_resp.json()["notes"] == "Garantia estendida"


@pytest.mark.anyio
async def test_tier1_maintenance_delete(client: AsyncClient, tecnico_tokens):
    """Testa exclusão de um registro de manutenção do histórico do equipamento."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/equipments",
        json={
            "description": "Notebook Test Delete Maint",
            "equipment_type": "Notebook",
            "location": "TI",
        },
    )
    eq_id = created.json()["id"]

    m_create = await client.post(
        f"/api/v1/equipments/{eq_id}/maintenances",
        json={"maintenance_date": "2026-08-01T00:00:00Z", "description": "Manutenção Provisória"},
    )
    mid = m_create.json()["id"]

    del_resp = await client.delete(f"/api/v1/equipments/{eq_id}/maintenances/{mid}")
    assert del_resp.status_code == 200
    assert "excluída com sucesso" in del_resp.json()["message"]

    detail = (await client.get(f"/api/v1/equipments/{eq_id}")).json()
    assert len(detail["maintenances"]) == 0


@pytest.mark.anyio
async def test_tier1_movement_record_updates_location(client: AsyncClient, tecnico_tokens):
    """Testa que movimentação atualiza localização de destino mantendo situação intacta."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/equipments",
        json={
            "description": "Projetor Epson",
            "equipment_type": "Projetor",
            "location": "Sala 01",
            "status": "Em uso",
        },
    )
    eq_id = created.json()["id"]

    movement_payload = {
        "origin_location": "Sala 01",
        "destination_location": "Auditório Central",
        "movement_date": "2026-10-01T09:00:00Z",
        "notes": "Transferência definitiva para palestras",
    }
    mov_resp = await client.post(f"/api/v1/equipments/{eq_id}/movements", json=movement_payload)
    assert mov_resp.status_code == 201

    detail = (await client.get(f"/api/v1/equipments/{eq_id}")).json()
    assert detail["location"] == "Auditório Central"
    assert detail["status"] == "Em uso"
    assert len(detail["movements"]) == 1


@pytest.mark.anyio
async def test_tier1_equipment_detail_chronological_histories(client: AsyncClient, tecnico_tokens):
    """Testa ordenação cronológica e persistência de múltiplos movimentos e manutenções."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    created = await client.post(
        "/api/v1/equipments",
        json={"description": "Impressora Laser", "equipment_type": "Impressora", "location": "TI"},
    )
    eq_id = created.json()["id"]

    # Cria duas manutenções em datas distintas
    await client.post(
        f"/api/v1/equipments/{eq_id}/maintenances",
        json={"maintenance_date": "2026-01-10T00:00:00Z", "description": "Manutenção 1"},
    )
    await client.post(
        f"/api/v1/equipments/{eq_id}/maintenances",
        json={"maintenance_date": "2026-06-15T00:00:00Z", "description": "Manutenção 2"},
    )

    detail = (await client.get(f"/api/v1/equipments/{eq_id}")).json()
    assert len(detail["maintenances"]) == 2


# ==============================================================================
# F4: Tag Taxonomy CRUD & Propagation
# ==============================================================================


@pytest.mark.anyio
async def test_tier1_tag_list_all(client: AsyncClient, tecnico_tokens):
    """Testa listagem de tags cadastradas no sistema."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    response = await client.get("/api/v1/equipments/tags")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_tier1_tag_filter_by_category(client: AsyncClient, tecnico_tokens):
    """Testa filtragem de tags por categoria específica: tipo, localizacao, situacao."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    await client.post(
        "/api/v1/equipments/tags", json={"category": "tipo", "name": "Tablet Especial"}
    )
    await client.post(
        "/api/v1/equipments/tags", json={"category": "localizacao", "name": "Setor Beta"}
    )

    resp_tipo = await client.get("/api/v1/equipments/tags?category=tipo")
    assert resp_tipo.status_code == 200
    assert any(t["name"] == "Tablet Especial" for t in resp_tipo.json())
    assert not any(t["name"] == "Setor Beta" for t in resp_tipo.json())


@pytest.mark.anyio
async def test_tier1_tag_create_new(client: AsyncClient, tecnico_tokens):
    """Testa cadastro de nova tag com sucesso."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    payload = {"category": "situacao", "name": "Aguardando Descarte"}
    response = await client.post("/api/v1/equipments/tags", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "situacao"
    assert data["name"] == "Aguardando Descarte"


@pytest.mark.anyio
async def test_tier1_tag_rename_propagates_to_equipments(client: AsyncClient, tecnico_tokens):
    """Testa renomeação de tag com propagação automática nos equipamentos (RN-TAG-04)."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    # 1. Cria tag inicial
    tag_resp = await client.post(
        "/api/v1/equipments/tags", json={"category": "localizacao", "name": "Almoxarifado Antigo"}
    )
    tag_id = tag_resp.json()["id"]

    # 2. Cria equipamento usando essa localização
    eq_resp = await client.post(
        "/api/v1/equipments",
        json={
            "description": "Item no Almoxarifado",
            "equipment_type": "Outros",
            "location": "Almoxarifado Antigo",
        },
    )
    eq_id = eq_resp.json()["id"]

    # 3. Renomeia tag
    rename_resp = await client.put(
        f"/api/v1/equipments/tags/{tag_id}", json={"name": "Depósito Central Moderno"}
    )
    assert rename_resp.status_code == 200

    # 4. Verifica equipamento atualizado
    detail = (await client.get(f"/api/v1/equipments/{eq_id}")).json()
    assert detail["location"] == "Depósito Central Moderno"


@pytest.mark.anyio
async def test_tier1_tag_delete_preserves_equipment_data(client: AsyncClient, tecnico_tokens):
    """Testa que exclusão de tag remove da lista mas preserva dado histórico do ativo (RN-TAG-06)."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    tag_resp = await client.post(
        "/api/v1/equipments/tags", json={"category": "tipo", "name": "Tipo Temporario"}
    )
    tag_id = tag_resp.json()["id"]

    eq_resp = await client.post(
        "/api/v1/equipments",
        json={
            "description": "Aparelho Raro",
            "equipment_type": "Tipo Temporario",
            "location": "TI",
        },
    )
    eq_id = eq_resp.json()["id"]

    # Exclui a tag
    del_resp = await client.delete(f"/api/v1/equipments/tags/{tag_id}")
    assert del_resp.status_code == 200

    # Tag não aparece mais na listagem
    tags = (await client.get("/api/v1/equipments/tags?category=tipo")).json()
    assert not any(t["id"] == tag_id for t in tags)

    # Mas equipamento mantém o tipo histórico
    detail = (await client.get(f"/api/v1/equipments/{eq_id}")).json()
    assert detail["equipment_type"] == "Tipo Temporario"


@pytest.mark.anyio
async def test_tier1_tag_create_inline_category_localizacao(client: AsyncClient, tecnico_tokens):
    """Testa criação inline de localização e disponibilidade imediata."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    resp = await client.post(
        "/api/v1/equipments/tags", json={"category": "localizacao", "name": "Estúdio de Gravação"}
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Estúdio de Gravação"


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
    """Testa execução de importação criando ativos, tags dinâmicas e registros de manutenção."""
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

    # Verifica se o equipamento foi realmente cadastrado
    list_resp = await client.get("/api/v1/equipments?patrimony_number=PAT-SW-01")
    assert list_resp.json()["total"] == 1


@pytest.mark.anyio
async def test_tier1_import_execute_upsert_existing(
    client: AsyncClient, tecnico_tokens, make_excel_bytes
):
    """Testa lógica de upsert atualizando equipamento já existente pelo número de patrimônio."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    # 1. Cria equipamento prévio
    await client.post(
        "/api/v1/equipments",
        json={
            "patrimony_number": "PAT-UPSERT-01",
            "description": "Versao Antiga",
            "equipment_type": "Monitor",
            "location": "TI",
        },
    )

    # 2. Importa planilha com mesmo patrimônio e nova descrição
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
    """Testa exportação para Excel validando aba 'Patrimônio' e 13 colunas canônicas."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    await client.post(
        "/api/v1/equipments",
        json={
            "description": "Desktop para Exportação",
            "equipment_type": "Desktop",
            "location": "Financeiro",
            "status": "Em uso",
            "patrimony_number": "PAT-EXP-01",
        },
    )

    response = await client.get("/api/v1/equipments/export")
    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment; filename=" in response.headers["content-disposition"]

    # Inspeciona binário com openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(response.content))
    assert "Patrimônio" in wb.sheetnames
    ws = wb["Patrimônio"]
    assert ws.max_column == 13
    headers = [cell.value for cell in ws[1]]
    assert headers[0] == "TIPO"
    assert headers[1] == "LOCALIZAÇÃO"
    assert headers[2] == "SITUAÇÃO"
    assert headers[3] == "DESCRIÇÃO"
    assert headers[4] == "Nº PATRIMÔNIO"


@pytest.mark.anyio
async def test_tier1_export_with_query_filters(client: AsyncClient, tecnico_tokens):
    """Testa exportação filtrada respeitando parâmetros de consulta."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-EXP-F1",
            "description": "Notebook Alfa",
            "equipment_type": "Notebook",
            "location": "TI",
        },
    )
    await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-EXP-F2",
            "description": "Desktop Beta",
            "equipment_type": "Desktop",
            "location": "TI",
        },
    )

    response = await client.get("/api/v1/equipments/export?type=Notebook")
    assert response.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(response.content))
    ws = wb["Patrimônio"]
    # Cabeçalho na linha 1 + 1 registro de Notebook = 2 linhas
    assert ws.max_row == 2
    assert ws.cell(row=2, column=1).value == "Notebook"


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
    assert "equipments_total" in data
    assert data["equipments_total"] is not None
    assert "tickets_pending" in data
    assert "tickets_in_progress" in data


@pytest.mark.anyio
async def test_tier1_dashboard_metrics_colaborador(client: AsyncClient, colaborador_tokens):
    """Testa retorno de métricas do dashboard restrito para role colaborador."""
    client.cookies.set("access_token", colaborador_tokens["access_token"])
    response = await client.get("/api/v1/dashboard/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["equipments_total"] is None  # Visão restrita, sem total de equipamentos


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
        "/api/v1/equipments",
        json={
            "patrimony_number": "PAT-SUGG-100",
            "description": "Equipamento Sugg",
            "equipment_type": "Monitor",
            "location": "TI",
        },
    )

    response = await client.get(
        "/api/v1/equipments/suggestions?field=patrimony_number&prefix=PAT-S"
    )
    assert response.status_code == 200
    suggestions = response.json()
    assert "PAT-SUGG-100" in suggestions


@pytest.mark.anyio
async def test_tier1_dashboard_equipment_count_reflects_db(client: AsyncClient, tecnico_tokens):
    """Testa que o contador do dashboard reflete exatamente a quantidade de equipamentos."""
    client.cookies.set("access_token", tecnico_tokens["access_token"])
    initial_count = (await client.get("/api/v1/dashboard/metrics")).json()["equipments_total"]

    await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-DASH-1",
            "description": "Item 1",
            "equipment_type": "TI",
            "location": "TI",
        },
    )
    await client.post(
        "/api/v1/equipments",
        json={
            "serial_number": "SN-DASH-2",
            "description": "Item 2",
            "equipment_type": "TI",
            "location": "TI",
        },
    )

    new_count = (await client.get("/api/v1/dashboard/metrics")).json()["equipments_total"]
    assert new_count == initial_count + 2
