"""Testes unitários para os casos de uso de importação de planilhas de ativos."""

from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session
from src.domain.models import Asset, Category, Location, AssetMaintenance
from src.infrastructure.repositories import (
    AssetRepository,
    CategoryRepository,
    LocationRepository,
)
from src.use_cases.import_spreadsheet_use_cases import (
    PreviewSpreadsheetUseCase,
    ExecuteSpreadsheetImportUseCase,
)
from tests.test_spreadsheet_parser import create_mock_excel


def test_preview_spreadsheet_use_case():
    headers = [
        "TIPO",
        "LOCALIZAÇÃO",
        "SITUAÇÃO",
        "DESCRIÇÃO",
        "Nº PATRIMÔNIO",
        "Nº SÉRIE",
        "ÚLTIMA MANUTENÇÃO",
    ]
    rows = [headers]
    for i in range(15):
        rows.append(
            [
                "DESKTOP",
                f"SALA {i}",
                "EM USO",
                f"PC {i}",
                f"PAT-{i}",
                f"SN-{i}",
                datetime(2023, 1, 1),
            ]
        )

    excel_bytes = create_mock_excel("Patrimônio", rows)
    use_case = PreviewSpreadsheetUseCase()
    preview = use_case.execute(excel_bytes, "inventario.xlsx")

    assert preview.total_rows == 15
    assert len(preview.sample_rows) == 10
    assert preview.detected_sheet == "Patrimônio"
    assert preview.sample_rows[0].patrimony_number == "PAT-0"
    assert preview.sample_rows[0].category == "DESKTOP"


def test_execute_spreadsheet_import_empty_rows(db_session: Session):
    headers = ["TIPO", "LOCALIZAÇÃO", "SITUAÇÃO", "DESCRIÇÃO"]
    excel_bytes = create_mock_excel("Patrimônio", [headers])
    use_case = ExecuteSpreadsheetImportUseCase(db_session)
    result = use_case.execute(excel_bytes, "vazio.xlsx")

    assert result.success is True
    assert result.total_rows == 0
    assert result.created_count == 0


def test_execute_spreadsheet_import_creation_and_catalogs(db_session: Session):
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
        "OBSERVAÇÕES",
    ]
    row1 = [
        "NOTEBOOK",
        "SALA DIRETORIA",
        "EM USO",
        "Dell Latitude 5420",
        "PAT-1001",
        "SN-NOTE-1",
        "Dell",
        "10/05/2023",
        "Troca de teclado e limpeza",
        "Uso exclusivo da gerência",
    ]
    row_sem_ident = [
        "PERIFÉRICO",
        "ALMOXARIFADO",
        "DISPONIVEL",
        "Mouse USB",
        None,
        None,
        "Logitech",
        None,
        None,
        "Reserva de estoque",
    ]

    excel_bytes = create_mock_excel("Patrimônio", [headers, row1, row_sem_ident])
    use_case = ExecuteSpreadsheetImportUseCase(db_session)
    result = use_case.execute(excel_bytes, "lote1.xlsx")

    assert result.success is True
    assert result.total_rows == 2
    assert result.created_count == 2
    assert result.updated_count == 0
    assert result.categories_created_count >= 2
    assert result.locations_created_count >= 2
    assert result.maintenances_created_count == 1

    # Valida no banco
    asset_repo = AssetRepository(db_session)
    a1 = asset_repo.get_by_patrimony_number("PAT-1001")
    assert a1 is not None
    assert a1.description == "Dell Latitude 5420"
    assert a1.serial_number == "SN-NOTE-1"
    assert a1.specs.get("notes") == "Uso exclusivo da gerência"
    assert len(a1.maintenances) == 1
    assert a1.maintenances[0].description == "Manutenção registrada durante importação de planilha"

    # Valida criação do catálogo (categoria)
    cat_repo = CategoryRepository(db_session)
    cat_note = cat_repo.get_by_name("NOTEBOOK")
    assert cat_note is not None


def test_execute_spreadsheet_import_upsert_all_fields(db_session: Session):
    cat_repo = CategoryRepository(db_session)
    loc_repo = LocationRepository(db_session)
    asset_repo = AssetRepository(db_session)

    cat = Category(name="Equipamento TI")
    cat_repo.create(cat)
    loc = Location(building="Prédio Central", floor="1", sector="TI")
    loc_repo.create(loc)
    db_session.flush()

    # Cria ativo inicial com apenas serial
    asset_existing = Asset(
        patrimony_number="PAT-TEMP-1",
        serial_number="SN-MATCH-1",
        description="Ativo Antigo",
        category_id=cat.id,
        location_id=loc.id,
        brand="HP Antigo",
        status="disponivel",
    )
    asset_repo.create(asset_existing)

    # Cria ativo inicial com apenas patrimônio
    asset_existing_pat = Asset(
        patrimony_number="PAT-MATCH-2",
        serial_number=None,
        description="Monitor Antigo",
        category_id=cat.id,
        location_id=loc.id,
        brand="Dell Antigo",
        status="disponivel",
    )
    asset_repo.create(asset_existing_pat)
    db_session.flush()

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
        "HOSTNAME",
        "MODELO",
        "OBSERVAÇÕES",
        "IP",
        "MAC",
    ]
    row1 = [
        "DESKTOP",
        "TI",
        "EM USO",
        "Desktop Atualizado Completo",
        "PAT-TEMP-1",
        "SN-MATCH-1",
        "HP",
        "01/02/2024",
        "Manutenção realizada",
        "HOST-100",
        "OptiPlex 7090",
        "Observação nova 1",
        "192.168.1.50",
        "AA:BB:CC:DD:EE:01",
    ]
    row2 = [
        "DESKTOP",
        "TI",
        "EM USO",
        "Monitor Atualizado Completo",
        "PAT-MATCH-2",
        "SN-FILLED-2",
        "Dell",
        None,
        None,
        "HOST-200",
        "Dell UltraSharp",
        "Observação nova 2",
        "192.168.1.51",
        "AA:BB:CC:DD:EE:02",
    ]
    excel_bytes = create_mock_excel("Patrimônio", [headers, row1, row2])

    use_case = ExecuteSpreadsheetImportUseCase(db_session)
    result = use_case.execute(excel_bytes, "update_all.xlsx")

    assert result.success is True
    assert result.updated_count == 2
    assert result.created_count == 0

    db_session.refresh(asset_existing)
    assert asset_existing.specs.get("hostname") == "HOST-100"
    assert asset_existing.model == "OptiPlex 7090"
    assert asset_existing.specs.get("notes") == "Observação nova 1"
    assert asset_existing.brand == "HP"
    assert asset_existing.specs.get("ip_address") == "192.168.1.50"
    assert asset_existing.status == "em_uso"

    db_session.refresh(asset_existing_pat)
    assert asset_existing_pat.model == "Dell UltraSharp"
    assert asset_existing_pat.specs.get("hostname") == "HOST-200"


def test_execute_spreadsheet_import_rollback_on_error(db_session: Session, monkeypatch):
    headers = ["TIPO", "LOCALIZAÇÃO", "SITUAÇÃO", "DESCRIÇÃO", "Nº PATRIMÔNIO", "Nº SÉRIE"]
    row = ["DESKTOP", "TI", "EM USO", "PC Teste", "PAT-FAIL", "SN-FAIL"]
    excel_bytes = create_mock_excel("Patrimônio", [headers, row])

    use_case = ExecuteSpreadsheetImportUseCase(db_session)

    def mock_create(self, eq):
        raise RuntimeError("Falha forçada de banco de dados")

    monkeypatch.setattr(AssetRepository, "create", mock_create)

    with pytest.raises(ValueError, match="Falha ao persistir dados da planilha: Falha forçada"):
        use_case.execute(excel_bytes, "falha.xlsx")

    asset_repo = AssetRepository(db_session)
    assert asset_repo.get_by_patrimony_number("PAT-FAIL") is None


def test_execute_spreadsheet_import_edge_branches(db_session: Session):
    cat_repo = CategoryRepository(db_session)
    loc_repo = LocationRepository(db_session)
    asset_repo = AssetRepository(db_session)

    # Pre-cria categoria e localização para exercitar o cache em memória
    cat = Category(name="Projetor")
    cat_repo.create(cat)
    loc = Location(building="Prédio Central", floor="1º Andar", sector="TI", room_number=None)
    loc_repo.create(loc)
    db_session.flush()

    # Pre-cria ativo que será encontrado por serial number
    asset_by_sn = Asset(
        patrimony_number="PAT-ORIGINAL",
        serial_number="SN-FIND-BY-SN",
        description="Ativo original",
        category_id=cat.id,
        location_id=loc.id,
        brand="Epson",
        status="disponivel",
    )
    asset_repo.create(asset_by_sn)
    db_session.flush()

    headers = [
        "TIPO",
        "LOCALIZAÇÃO",
        "SITUAÇÃO",
        "DESCRIÇÃO",
        "Nº PATRIMÔNIO",
        "Nº SÉRIE",
    ]
    # Linha 1: Encontrado por serial (patrimonio diferente), status 'conserto' -> em_manutencao
    row1 = [
        "Projetor",
        "TI",
        "conserto",
        "Projetor em Manutenção",
        "PAT-DIFERENTE",
        "SN-FIND-BY-SN",
    ]
    # Linha 2: Status 'baixado', sem patrimonio ou serial (gera IMP-00003)
    row2 = [
        "Projetor",
        "TI",
        "sucata",
        "Projetor Sucata",
        None,
        None,
    ]
    excel_bytes = create_mock_excel("Patrimônio", [headers, row1, row2])

    use_case = ExecuteSpreadsheetImportUseCase(db_session)
    result = use_case.execute(excel_bytes, "edge_test.xlsx")

    assert result.success is True
    assert result.updated_count == 1
    assert result.created_count == 1

    db_session.refresh(asset_by_sn)
    assert asset_by_sn.status == "em_manutencao"
    assert asset_by_sn.description == "Projetor em Manutenção"

    imp_asset = asset_repo.get_by_patrimony_number("IMP-00003")
    assert imp_asset is not None
    assert imp_asset.status == "baixado"
