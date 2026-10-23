"""Testes unitários para os casos de uso de importação de planilhas."""

from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session
from src.core.security import decrypt_windows_product_key
from src.domain.models import Equipment, EquipmentType, Sector, EquipmentStatus
from src.infrastructure.repositories import (
    EquipmentRepository,
    CatalogsRepository,
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
    assert preview.sample_rows[0].last_maintenance_at == "01/01/2023"


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
        "OCIOSO",
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
    assert (
        result.catalogs_created_count >= 4
    )  # NOTEBOOK, PERIFÉRICO, SALA DIRETORIA, ALMOXARIFADO, etc.
    assert result.maintenances_created_count == 1

    # Valida no banco
    eq_repo = EquipmentRepository(db_session)
    eq1 = eq_repo.get_by_patrimony_number("PAT-1001")
    assert eq1 is not None
    assert eq1.description == "Dell Latitude 5420"
    assert eq1.serial_number == "SN-NOTE-1"
    assert eq1.notes == "Uso exclusivo da gerência"
    assert len(eq1.maintenances) == 1
    assert eq1.maintenances[0].description == "Troca de teclado e limpeza"
    assert (
        eq1.maintenances[0].started_at.astimezone(timezone.utc).strftime("%Y-%m-%d") == "2023-05-10"
    )

    # Valida criação do catálogo
    cat_repo = CatalogsRepository(db_session)
    cat_note = cat_repo.get_by_name_lower(EquipmentType, "NOTEBOOK")
    assert cat_note is not None


def test_execute_spreadsheet_import_upsert_all_fields(db_session: Session, test_catalogs):
    eq_repo = EquipmentRepository(db_session)
    type_id = test_catalogs["type"].id
    sector_id = test_catalogs["sector_ti"].id
    status_id = test_catalogs["status_ocioso"].id

    # Cria equipamento inicial com apenas serial
    eq_existing = Equipment(
        patrimony_number="PAT-TEMP-1",
        equipment_type_id=type_id,
        sector_id=sector_id,
        status_id=status_id,
        description="Equipamento Antigo",
        serial_number="SN-MATCH-1",
        brand=None,
        hostname=None,
        windows_product_key_encrypted=None,
        notes=None,
    )
    eq_repo.create(eq_existing)

    # Cria equipamento inicial com apenas patrimônio
    eq_existing_pat = Equipment(
        patrimony_number="PAT-MATCH-2",
        equipment_type_id=type_id,
        sector_id=sector_id,
        status_id=status_id,
        description="Monitor Antigo",
        serial_number=None,
    )
    eq_repo.create(eq_existing_pat)
    db_session.flush()

    # Planilha atualizando ambos
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
        "CHAVE WINDOWS",
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
        "AAAAA-BBBBB-CCCCC-DDDDD-EEEEE",
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
        "05/03/2024",
        None,
        "HOST-200",
        "Dell UltraSharp",
        "11111-22222-33333-44444-55555",
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

    # Verifica atualização de todos os campos
    db_session.refresh(eq_existing)
    assert eq_existing.hostname == "HOST-100"
    assert eq_existing.model == "OptiPlex 7090"
    assert (
        decrypt_windows_product_key(eq_existing.windows_product_key_encrypted)
        == "AAAAA-BBBBB-CCCCC-DDDDD-EEEEE"
    )
    assert eq_existing.notes == "Observação nova 1"
    assert eq_existing.brand == "HP"
    assert eq_existing.ip_address == "192.168.1.50"
    assert eq_existing.mac_address.lower() == "aa:bb:cc:dd:ee:01"

    db_session.refresh(eq_existing_pat)
    assert eq_existing_pat.serial_number == "SN-FILLED-2"
    assert eq_existing_pat.hostname == "HOST-200"


def test_execute_spreadsheet_import_rollback_on_error(db_session: Session, monkeypatch):
    headers = ["TIPO", "LOCALIZAÇÃO", "SITUAÇÃO", "DESCRIÇÃO", "Nº PATRIMÔNIO", "Nº SÉRIE"]
    row = ["DESKTOP", "TI", "EM USO", "PC Teste", "PAT-FAIL", "SN-FAIL"]
    excel_bytes = create_mock_excel("Patrimônio", [headers, row])

    use_case = ExecuteSpreadsheetImportUseCase(db_session)

    # Simula erro de banco durante o flush/commit
    def mock_create(self, eq):
        raise RuntimeError("Falha forçada de banco de dados")

    monkeypatch.setattr(EquipmentRepository, "create", mock_create)

    with pytest.raises(RuntimeError, match="Falha forçada de banco de dados"):
        use_case.execute(excel_bytes, "falha.xlsx")

    # Verifica que não salvou
    eq_repo = EquipmentRepository(db_session)
    assert eq_repo.get_by_patrimony_number("PAT-FAIL") is None


def test_execute_spreadsheet_import_edge_branches(db_session: Session, test_catalogs):
    cat_repo = CatalogsRepository(db_session)
    eq_repo = EquipmentRepository(db_session)

    # 1. Catálogo deletado que deve ser restaurado
    deleted_type = EquipmentType(name="Projetor", deleted_at=datetime.now(timezone.utc))
    cat_repo.create(deleted_type)

    # 2. Equipamento deletado que deve ser restaurado, com serial e patrimônio vazio
    deleted_eq = Equipment(
        patrimony_number="",
        serial_number="SN-RESTORE-IMPORT",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
        deleted_at=datetime.now(timezone.utc),
    )
    eq_repo.create(deleted_eq)
    db_session.flush()

    headers = [
        "TIPO",
        "LOCALIZAÇÃO",
        "SITUAÇÃO",
        "DESCRIÇÃO",
        "Nº PATRIMÔNIO",
        "Nº SÉRIE",
        "IP",
        "CHAVE WINDOWS",
    ]
    # row com tipo deletado, IP inválido, sem chave windows, preenchendo serial
    row = [
        "Projetor",
        "TI",
        "EM USO",
        "Projetor Epson",
        "PAT-RESTORE-01",
        "SN-RESTORE-IMPORT",
        "999.999.999.999",
        None,
    ]
    excel_bytes = create_mock_excel("Patrimônio", [headers, row])

    use_case = ExecuteSpreadsheetImportUseCase(db_session)
    result = use_case.execute(excel_bytes, "restore_test.xlsx")

    assert result.success is True
    assert result.updated_count == 1

    db_session.refresh(deleted_type)
    assert deleted_type.deleted_at is None

    db_session.refresh(deleted_eq)
    assert deleted_eq.deleted_at is None
    assert deleted_eq.serial_number == "SN-RESTORE-IMPORT"
    assert deleted_eq.ip_address is None
