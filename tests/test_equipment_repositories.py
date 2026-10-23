"""Testes de integração para os repositórios de Equipamentos, Catálogos e Históricos."""

from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session
from src.domain.models import (
    Equipment,
    EquipmentType,
    Sector,
    EquipmentStatus,
    MaintenanceType,
    EquipmentMovement,
    EquipmentMaintenance,
)
from src.infrastructure.repositories import (
    EquipmentRepository,
    CatalogsRepository,
    EquipmentMovementRepository,
    EquipmentMaintenanceRepository,
    DashboardRepository,
    UserRepository,
)


def test_catalogs_repository_crud(db_session: Session):
    """Testa métodos de CRUD, soft delete e restauração em CatalogsRepository."""
    cat_repo = CatalogsRepository(db_session)

    item = EquipmentType(name="Servidor Blade")
    cat_repo.create(item)
    db_session.flush()

    assert item.id is not None
    assert cat_repo.get_by_id(EquipmentType, item.id) is not None
    assert cat_repo.get_by_name_lower(EquipmentType, "servidor blade") is not None
    assert cat_repo.get_by_name_lower(EquipmentType, "inexistente") is None

    # Update
    cat_repo.update(item, "Servidor Rack")
    db_session.flush()
    assert item.name == "Servidor Rack"

    # Soft delete
    cat_repo.soft_delete(item)
    db_session.flush()
    assert item.deleted_at is not None

    active_items = cat_repo.list_active(EquipmentType)
    assert not any(i.id == item.id for i in active_items)

    all_items = cat_repo.list_all(EquipmentType)
    assert any(i.id == item.id for i in all_items)

    # Restore
    cat_repo.restore(item)
    db_session.flush()
    assert item.deleted_at is None
    assert any(i.id == item.id for i in cat_repo.list_active(EquipmentType))


def test_equipment_repository_lookups_and_active_uniqueness(db_session: Session, test_catalogs):
    """Testa buscas por patrimônio, serial e identificadores ativos em EquipmentRepository."""
    repo = EquipmentRepository(db_session)

    eq = Equipment(
        description="ThinkPad T480",
        serial_number="SN_T480",
        patrimony_number="PAT_T480",
        hostname="host_t480",
        model="T480",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
        ip_address="192.168.1.80",
        mac_address="00:1A:2B:3C:4D:80",
        printer_identifier="PRN-T480",
    )
    repo.create(eq)
    db_session.flush()

    # Lookups
    assert repo.get_by_id(eq.id) is not None
    assert repo.get_by_patrimony_number("pat_t480") is not None
    assert repo.get_by_serial_number("sn_t480") is not None
    assert repo.get_active_by_hostname("HOST_T480") is not None
    assert repo.get_active_by_ip("192.168.1.80") is not None
    assert repo.get_active_by_mac("00:1A:2B:3C:4D:80") is not None
    assert repo.get_active_by_printer_identifier("prn-t480") is not None

    assert repo.get_by_serial_number("INEXISTENTE") is None
    assert repo.get_by_serial_number(None) is None
    assert repo.get_by_patrimony_number(None) is None
    assert repo.get_by_patrimony_number("") is None
    assert repo.get_by_hostname(None) is None
    assert repo.get_by_hostname("") is None
    assert repo.get_by_hostname("HOST_T480") is not None
    assert repo.get_by_hostname("INEXISTENTE") is None
    assert repo.get_active_by_hostname(None) is None
    assert repo.get_active_by_ip(None) is None
    assert repo.get_active_by_mac(None) is None
    assert repo.get_active_by_printer_identifier(None) is None


def test_equipment_repository_soft_delete_and_restoration_conflicts(
    db_session: Session, test_catalogs
):
    """Testa exclusão lógica, detecção de conflitos de restauração e restauração de bem."""
    repo = EquipmentRepository(db_session)

    eq1 = Equipment(
        description="Servidor 1",
        patrimony_number="PAT-SRV-001",
        hostname="srv-prod.local",
        ip_address="10.0.0.100",
        mac_address="00:1A:2B:3C:4D:99",
        printer_identifier="PRN-SRV-1",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
    )
    repo.create(eq1)
    db_session.flush()

    # Exclui logicamente eq1
    repo.soft_delete(eq1)
    db_session.flush()

    assert repo.get_by_id(eq1.id) is None
    assert repo.get_by_id(eq1.id, include_deleted=True) is not None

    # Cria eq2 ativo ocupando os mesmos identificadores
    eq2 = Equipment(
        description="Servidor 2",
        patrimony_number="PAT-SRV-002",
        hostname="srv-prod.local",
        ip_address="10.0.0.100",
        mac_address="00:1A:2B:3C:4D:99",
        printer_identifier="PRN-SRV-1",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
    )
    repo.create(eq2)
    db_session.flush()

    # Tenta restaurar eq1 -> deve detectar conflitos em todos os identificadores
    conflicts = repo.check_restoration_conflicts(eq1)
    assert len(conflicts) == 4

    # Remove conflito de eq2 e restaura eq1
    repo.soft_delete(eq2)
    db_session.flush()

    conflicts_resolved = repo.check_restoration_conflicts(eq1)
    assert len(conflicts_resolved) == 0

    repo.restore(eq1)
    db_session.flush()
    assert repo.get_by_id(eq1.id) is not None


def test_equipment_repository_list_paginated_and_filtered(db_session: Session, test_catalogs):
    """Testa paginação, filtros por múltiplos IDs de catálogos e busca global."""
    repo = EquipmentRepository(db_session)

    for i in range(1, 15):
        eq = Equipment(
            description=f"Equipamento {i} Dell",
            serial_number=f"SN_PG_{i:03d}",
            patrimony_number=f"PAT_PG_{i:03d}",
            model="Latitude" if i % 2 == 0 else "OptiPlex",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id if i <= 7 else test_catalogs["sector_com"].id,
            status_id=test_catalogs["status_em_uso"].id
            if i <= 10
            else test_catalogs["status_ocioso"].id,
        )
        repo.create(eq)
    db_session.flush()

    # Paginação
    items, total = repo.list_paginated_and_filtered(page=1, limit=10)
    assert total == 14
    assert len(items) == 10

    # Filtro por múltiplos IDs de setor
    items_sec, total_sec = repo.list_paginated_and_filtered(
        sector_ids=[test_catalogs["sector_ti"].id],
    )
    assert total_sec == 7

    # Filtro por status
    items_st, total_st = repo.list_paginated_and_filtered(
        status_ids=[test_catalogs["status_ocioso"].id],
    )
    assert total_st == 4

    # Busca textual
    items_search, total_search = repo.list_paginated_and_filtered(search="Equipamento 1")
    assert total_search >= 1

    # list_all_filtered
    all_filtered = repo.list_all_filtered(sector_ids=[test_catalogs["sector_ti"].id])
    assert len(all_filtered) == 7


def test_equipment_repository_get_distinct_values_by_prefix(db_session: Session, test_catalogs):
    """Testa busca de sugestões distintas por prefixo com ordenação e limite."""
    repo = EquipmentRepository(db_session)

    equipments_data = [
        ("PAT_SUG_100", "SN_SUG_01", "OptiPlex 7090"),
        ("PAT_SUG_101", "SN_SUG_02", "OptiPlex 3080"),
        ("PAT_SUG_200", "SN_SUG_03", "Latitude 3420"),
    ]

    for pat, sn, mod in equipments_data:
        eq = Equipment(
            patrimony_number=pat,
            serial_number=sn,
            model=mod,
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
        )
        repo.create(eq)
    db_session.flush()

    pats = repo.get_distinct_values_by_prefix("patrimony_number", "pat_sug", limit=10)
    assert len(pats) == 3

    serials = repo.get_distinct_values_by_prefix("serial_number", "sn_sug", limit=2)
    assert len(serials) == 2

    models = repo.get_distinct_values_by_prefix("model", "opti", limit=10)
    assert len(models) == 2

    # Campo inválido
    assert repo.get_distinct_values_by_prefix("campo_fake", "teste") == []


def test_movement_and_maintenance_repositories(
    db_session: Session, test_catalogs, create_test_user
):
    """Testa persistência e ordenação cronológica nos repositórios de histórico."""
    tecnico = create_test_user(email="tec_hist_repo@empresa.com")
    eq_repo = EquipmentRepository(db_session)
    mov_repo = EquipmentMovementRepository(db_session)
    maint_repo = EquipmentMaintenanceRepository(db_session)

    eq = Equipment(
        patrimony_number="PAT-HIST-01",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
    )
    eq_repo.create(eq)
    db_session.flush()

    now = datetime.now(timezone.utc)
    mov1 = EquipmentMovement(
        equipment_id=eq.id,
        origin_sector_id=test_catalogs["sector_ti"].id,
        destination_sector_id=test_catalogs["sector_com"].id,
        movement_date=now - timedelta(days=5),
        performed_by_user_id=tecnico.id,
    )
    mov2 = EquipmentMovement(
        equipment_id=eq.id,
        origin_sector_id=test_catalogs["sector_com"].id,
        destination_sector_id=test_catalogs["sector_dir"].id,
        movement_date=now - timedelta(days=1),
        performed_by_user_id=tecnico.id,
    )
    mov_repo.create(mov1)
    mov_repo.create(mov2)
    db_session.flush()

    ordered_movs = mov_repo.get_ordered_movements(eq.id)
    assert len(ordered_movs) == 2
    assert ordered_movs[0].id == mov1.id
    assert ordered_movs[1].id == mov2.id

    assert mov_repo.get_by_id(mov1.id) is not None
    assert mov_repo.get_by_id(999999) is None

    # Manutenções
    maint_open = EquipmentMaintenance(
        equipment_id=eq.id,
        started_at=now,
        completed_at=None,
        maintenance_type_id=test_catalogs["maint_corr"].id,
        performed_by_user_id=tecnico.id,
    )
    maint_repo.create(maint_open)
    db_session.flush()

    assert maint_repo.get_open_maintenance(eq.id) is not None
    assert maint_repo.get_by_id(maint_open.id) is not None
    assert maint_repo.get_by_id(999999) is None

    maints = maint_repo.list_by_equipment(eq.id)
    assert len(maints) == 1


def test_dashboard_repository_metrics(db_session: Session, test_catalogs):
    """Testa consolidação patrimonial em DashboardRepository."""
    dash_repo = DashboardRepository(db_session)
    eq_repo = EquipmentRepository(db_session)

    eq1 = Equipment(
        patrimony_number="PAT-DASH-01",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
    )
    eq2 = Equipment(
        patrimony_number="PAT-DASH-02",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_com"].id,
        status_id=test_catalogs["status_em_manutencao"].id,
    )
    eq3 = Equipment(
        patrimony_number="PAT-DASH-03",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_dir"].id,
        status_id=test_catalogs["status_ocioso"].id,
        deleted_at=datetime.now(timezone.utc),  # Excluído não deve contar
    )
    eq_repo.create(eq1)
    eq_repo.create(eq2)
    eq_repo.create(eq3)
    db_session.flush()

    metrics = dash_repo.get_metrics()
    assert metrics["equipments_total"] >= 2
    assert metrics["equipments_in_use"] >= 1
    assert metrics["equipments_in_maintenance"] >= 1
    assert "TI" in metrics["by_sector"]
    assert "Desktop" in metrics["by_type"]


def test_repository_edge_cases_and_filters(db_session: Session, test_catalogs, create_test_user):
    user_repo = UserRepository(db_session)
    eq_repo = EquipmentRepository(db_session)

    # 1. User include_deleted
    user = create_test_user(email="deleted_user@empresa.com", role="tecnico")
    user_repo.soft_delete(user)
    db_session.flush()

    assert user_repo.get_by_email("deleted_user@empresa.com", include_deleted=False) is None
    assert user_repo.get_by_email("deleted_user@empresa.com", include_deleted=True) is not None
    assert user_repo.get_by_id(user.id, include_deleted=False) is None
    assert user_repo.get_by_id(user.id, include_deleted=True) is not None

    # 2. Filters with single int, single str, sort_dir="asc", include_deleted=True
    eq_active = Equipment(
        patrimony_number="PAT-FILTER-1",
        serial_number="SN-FILTER-1",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
        ip_address="192.168.10.10",
        mac_address="00:11:22:33:44:55",
        printer_identifier="PRN-REP-01",
    )
    eq_deleted = Equipment(
        patrimony_number="PAT-FILTER-2",
        serial_number="SN-FILTER-2",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
        deleted_at=datetime.now(timezone.utc),
    )
    eq_repo.create(eq_active)
    eq_repo.create(eq_deleted)
    db_session.flush()

    assert eq_repo.get_by_id(eq_deleted.id, include_deleted=False) is None
    assert eq_repo.get_by_id(eq_deleted.id, include_deleted=True) is not None
    assert eq_repo.get_by_patrimony_number("PAT-FILTER-2", include_deleted=False) is None
    assert eq_repo.get_by_patrimony_number("PAT-FILTER-2", include_deleted=True) is not None
    assert eq_repo.get_by_serial_number("SN-FILTER-2", include_deleted=False) is None
    assert eq_repo.get_by_serial_number("SN-FILTER-2", include_deleted=True) is not None

    items, total = eq_repo.list_paginated_and_filtered(
        equipment_type_ids=test_catalogs["type"].id,
        sector_ids=test_catalogs["sector_ti"].id,
        status_ids=test_catalogs["status_em_uso"].id,
        patrimony_number=["PAT-FILTER", ""],
        serial_number=["SN-FILTER", None],
        sort_by="patrimony_number",
        sort_dir="asc",
        include_deleted=True,
    )
    assert total >= 2

    all_items = eq_repo.list_all_filtered(
        serial_number="SN-FILTER-1",
        sort_by="patrimony_number",
        sort_dir="asc",
    )
    assert len(all_items) == 1

    # 3. Check restoration conflicts for IP, MAC, Printer
    eq_to_restore = Equipment(
        patrimony_number="PAT-COLLIDE",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
        ip_address="192.168.10.10",
        mac_address="00:11:22:33:44:55",
        printer_identifier="PRN-REP-01",
    )
    conflicts = eq_repo.check_restoration_conflicts(eq_to_restore)
    assert any("Endereço IP" in c for c in conflicts)
    assert any("Endereço MAC" in c for c in conflicts)
    assert any("Identificador de impressora" in c for c in conflicts)
