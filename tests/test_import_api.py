"""Testes de integração e API para as rotas de importação de planilhas."""

import io
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from src.core.security import create_access_token
from tests.test_spreadsheet_parser import create_mock_excel


@pytest.fixture
def auth_headers(create_test_user):
    def _headers(role: str = "tecnico") -> dict[str, str]:
        user = create_test_user(email=f"user_{role}@teste.com", role=role)
        token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
        return {"Authorization": f"Bearer {token}"}

    return _headers


@pytest.mark.anyio
async def test_preview_endpoint_success(client: AsyncClient, auth_headers):
    headers = auth_headers(role="tecnico")

    excel_headers = ["TIPO", "LOCALIZAÇÃO", "SITUAÇÃO", "DESCRIÇÃO", "Nº PATRIMÔNIO", "Nº SÉRIE"]
    row1 = ["DESKTOP", "CTM", "EM USO", "PC HP 800", "PAT-100", "SN-100"]
    excel_bytes = create_mock_excel("Patrimônio", [excel_headers, row1])

    files = {
        "file": (
            "patrimonio.xlsx",
            excel_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = await client.post("/api/v1/equipments/import/preview", headers=headers, files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "patrimonio.xlsx"
    assert data["total_rows"] == 1
    assert data["sample_rows"][0]["equipment_type"] == "DESKTOP"
    assert data["sample_rows"][0]["patrimony_number"] == "PAT-100"


@pytest.mark.anyio
async def test_preview_endpoint_csv_success(client: AsyncClient, auth_headers):
    headers = auth_headers(role="tecnico")
    csv_bytes = (
        "TIPO;LOCALIZAÇÃO;SITUAÇÃO;DESCRIÇÃO;Nº PATRIMÔNIO\nNOTEBOOK;TI;EM USO;Dell XPS;PAT-200\n"
    ).encode("utf-8")

    files = {"file": ("dados.csv", csv_bytes, "text/csv")}
    response = await client.post("/api/v1/equipments/import/preview", headers=headers, files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 1
    assert data["sample_rows"][0]["equipment_type"] == "NOTEBOOK"


@pytest.mark.anyio
async def test_preview_endpoint_empty_file_bad_request(client: AsyncClient, auth_headers):
    headers = auth_headers(role="tecnico")
    files = {
        "file": (
            "vazio.xlsx",
            b"",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = await client.post("/api/v1/equipments/import/preview", headers=headers, files=files)

    assert response.status_code == 400
    assert "está vazio" in response.json()["detail"]


@pytest.mark.anyio
async def test_preview_endpoint_empty_filename_bad_request(client: AsyncClient, auth_headers):
    headers = auth_headers(role="tecnico")
    files = {"file": ("", b"some data", "text/csv")}
    response = await client.post("/api/v1/equipments/import/preview", headers=headers, files=files)

    assert response.status_code in (400, 422)


@pytest.mark.anyio
async def test_preview_endpoint_colaborador_forbidden(client: AsyncClient):
    from src.api.dependencies import get_current_user
    from src.domain.models import User
    from src.main import app

    app.dependency_overrides[get_current_user] = lambda: User(
        id=999, email="colab@empresa.com", role="colaborador", is_active=True
    )
    try:
        files = {
            "file": (
                "teste.xlsx",
                b"data",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        response = await client.post("/api/v1/equipments/import/preview", files=files)
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.anyio
async def test_execute_import_endpoint_success(client: AsyncClient, auth_headers):
    headers = auth_headers(role="tecnico")

    excel_headers = [
        "TIPO",
        "LOCALIZAÇÃO",
        "SITUAÇÃO",
        "DESCRIÇÃO",
        "Nº PATRIMÔNIO",
        "Nº SÉRIE",
        "MARCA",
        "ÚLTIMA MANUTENÇÃO",
        "HISTÓRICO DE MOVIMENTAÇÕES",
        "OBSERVAÇÕES",
    ]
    row1 = [
        "MONITOR",
        "SALA 101",
        "EM USO",
        "Monitor Dell 27",
        "PAT-301",
        "SN-301",
        "Dell",
        "15/04/2023",
        "Troca de cabo HDMI",
        "Setor de edição",
    ]
    excel_bytes = create_mock_excel("Patrimônio", [excel_headers, row1])

    files = {
        "file": (
            "importacao.xlsx",
            excel_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = await client.post("/api/v1/equipments/import/execute", headers=headers, files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["created_count"] == 1
    assert data["tags_created_count"] >= 2
    assert data["maintenances_created_count"] == 1

    # Faz o preview ou listagem para confirmar que foi inserido
    get_res = await client.get("/api/v1/assets", headers=headers)
    assert get_res.status_code == 200
    eq_list = get_res.json()["items"]
    assert any(eq["patrimony_number"] == "PAT-301" for eq in eq_list)


@pytest.mark.anyio
async def test_execute_import_endpoint_empty_filename_bad_request(
    client: AsyncClient, auth_headers
):
    headers = auth_headers(role="tecnico")
    files = {"file": ("", b"data", "text/csv")}
    response = await client.post("/api/v1/equipments/import/execute", headers=headers, files=files)

    assert response.status_code in (400, 422)


@pytest.mark.anyio
async def test_execute_import_endpoint_invalid_file_bad_request(client: AsyncClient, auth_headers):
    headers = auth_headers(role="tecnico")
    files = {
        "file": (
            "corrupt.xlsx",
            b"not valid",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = await client.post("/api/v1/equipments/import/execute", headers=headers, files=files)

    assert response.status_code == 400
    assert "Não foi possível abrir o arquivo Excel" in response.json()["detail"]


@pytest.mark.anyio
async def test_execute_import_endpoint_colaborador_forbidden(client: AsyncClient):
    from src.api.dependencies import get_current_user
    from src.domain.models import User
    from src.main import app

    app.dependency_overrides[get_current_user] = lambda: User(
        id=999, email="colab@empresa.com", role="colaborador", is_active=True
    )
    try:
        files = {
            "file": (
                "planilha.xlsx",
                b"data",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        response = await client.post("/api/v1/equipments/import/execute", files=files)
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.anyio
async def test_endpoints_unauthorized_without_token(client: AsyncClient):
    files = {"file": ("teste.xlsx", b"data", "text/csv")}
    res_preview = await client.post("/api/v1/equipments/import/preview", files=files)
    assert res_preview.status_code == 401

    res_exec = await client.post("/api/v1/equipments/import/execute", files=files)
    assert res_exec.status_code == 401


@pytest.mark.anyio
async def test_preview_and_execute_internal_server_errors(
    client: AsyncClient, auth_headers, monkeypatch
):
    headers = auth_headers(role="tecnico")
    excel_bytes = create_mock_excel("Patrimônio", [["TIPO"], ["DESKTOP"]])
    files = {
        "file": (
            "teste.xlsx",
            excel_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    # Força exceção não tratada em Preview
    from src.use_cases.import_spreadsheet_use_cases import (
        PreviewSpreadsheetUseCase,
        ExecuteSpreadsheetImportUseCase,
    )

    def mock_preview_error(*args, **kwargs):
        raise TypeError("Erro inesperado de tipo")

    monkeypatch.setattr(PreviewSpreadsheetUseCase, "execute", mock_preview_error)

    res_preview = await client.post(
        "/api/v1/equipments/import/preview", headers=headers, files=files
    )
    assert res_preview.status_code == 500
    assert "Erro interno ao processar a planilha" in res_preview.json()["detail"]

    # Força exceção não tratada em Execute
    def mock_execute_error(*args, **kwargs):
        raise TypeError("Erro inesperado na execução")

    monkeypatch.setattr(ExecuteSpreadsheetImportUseCase, "execute", mock_execute_error)

    files2 = {
        "file": (
            "teste.xlsx",
            excel_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    res_exec = await client.post("/api/v1/equipments/import/execute", headers=headers, files=files2)
    assert res_exec.status_code == 500
    assert "Erro interno ao importar a planilha" in res_exec.json()["detail"]
