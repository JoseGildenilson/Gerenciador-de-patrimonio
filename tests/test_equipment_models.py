"""Testes de unidade e integração dos modelos ORM, constraints, triggers e índices no PostgreSQL."""

from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, InternalError
from sqlalchemy.orm import Session
from src.domain.models import (
    User,
    Equipment,
    EquipmentType,
    Sector,
    EquipmentStatus,
    MaintenanceType,
    EquipmentMovement,
    EquipmentMaintenance,
)


def test_create_equipment_with_catalog_fks_and_network(
    db_session: Session, test_catalogs, create_test_user
):
    """Testa criação bem-sucedida do modelo Equipment com chaves estrangeiras de catálogo e tipos nativos."""
    tecnico = create_test_user(email="tecnico_model@empresa.com")
    eq = Equipment(
        patrimony_number="PAT-MOD-01",
        serial_number="SN-MOD-01",
        description="Desktop i7",
        model="OptiPlex 7090",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
        ip_address="192.168.1.50",
        mac_address="00:1A:2B:3C:4D:5E",
        printer_identifier="PRN-01",
        windows_product_key_encrypted="encrypted-secret-token",
    )
    db_session.add(eq)
    db_session.flush()

    assert eq.id is not None
    assert eq.patrimony_number == "PAT-MOD-01"
    assert eq.equipment_type.name == "Desktop"
    assert eq.sector.name == "TI"
    assert eq.status.name == "Em uso"
    assert str(eq.ip_address) == "192.168.1.50"
    assert str(eq.mac_address).lower() == "00:1a:2b:3c:4d:5e"


def test_chk_users_role_tecnico_rejected(db_session: Session):
    """Testa que cadastrar um usuário com role inválida viola constraint CHECK."""
    user = User(email="colab@empresa.com", hashed_password="hash", role="invalido")
    db_session.add(user)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_chk_equipments_ip_host_only_rejected(db_session: Session, test_catalogs):
    """Testa rejeição de IP com máscara de rede diferente de host (/24)."""
    if db_session.bind.dialect.name == "sqlite":
        pytest.skip("PostgreSQL family() function not supported in SQLite fallback")
    eq = Equipment(
        patrimony_number="PAT-IP-ERR",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
        ip_address="192.168.1.0/24",
    )
    db_session.add(eq)
    with pytest.raises(IntegrityError, match="chk_equipments_ip_host_only"):
        db_session.flush()
    db_session.rollback()


def test_chk_movement_different_sectors_rejected(
    db_session: Session, test_catalogs, create_test_user
):
    """Testa rejeição de movimentação para o mesmo setor de origem."""
    tecnico = create_test_user(email="tec_mov_diff@empresa.com")
    eq = Equipment(
        patrimony_number="PAT-MOV-DIFF",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
    )
    db_session.add(eq)
    db_session.flush()

    mov = EquipmentMovement(
        equipment_id=eq.id,
        origin_sector_id=test_catalogs["sector_ti"].id,
        destination_sector_id=test_catalogs["sector_ti"].id,
        performed_by_user_id=tecnico.id,
    )
    db_session.add(mov)
    with pytest.raises(IntegrityError, match="chk_movement_different_sectors"):
        db_session.flush()
    db_session.rollback()


def test_chk_movement_date_not_future_rejected(
    db_session: Session, test_catalogs, create_test_user
):
    """Testa rejeição de movimentação com data futura superior a 5 minutos."""
    if db_session.bind.dialect.name == "sqlite":
        pytest.skip("PostgreSQL INTERVAL expression not supported in SQLite fallback")
    tecnico = create_test_user(email="tec_mov_fut@empresa.com")
    eq = Equipment(
        patrimony_number="PAT-MOV-FUT",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
    )
    db_session.add(eq)
    db_session.flush()

    future_date = datetime.now(timezone.utc) + timedelta(minutes=10)
    mov = EquipmentMovement(
        equipment_id=eq.id,
        origin_sector_id=test_catalogs["sector_ti"].id,
        destination_sector_id=test_catalogs["sector_com"].id,
        movement_date=future_date,
        performed_by_user_id=tecnico.id,
    )
    db_session.add(mov)
    with pytest.raises(IntegrityError, match="chk_movement_date_not_future"):
        db_session.flush()
    db_session.rollback()


def test_chk_maintenance_completion_after_start_rejected(
    db_session: Session, test_catalogs, create_test_user
):
    """Testa rejeição de conclusão de manutenção com data anterior ao início."""
    tecnico = create_test_user(email="tec_maint_chk@empresa.com")
    eq = Equipment(
        patrimony_number="PAT-MAINT-CHK",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
    )
    db_session.add(eq)
    db_session.flush()

    now = datetime.now(timezone.utc)
    maint = EquipmentMaintenance(
        equipment_id=eq.id,
        started_at=now,
        completed_at=now - timedelta(hours=1),
        maintenance_type_id=test_catalogs["maint_prev"].id,
        performed_by_user_id=tecnico.id,
    )
    db_session.add(maint)
    with pytest.raises(IntegrityError, match="chk_maintenance_completion_after_start"):
        db_session.flush()
    db_session.rollback()


def test_unique_open_maintenance_per_equipment(
    db_session: Session, test_catalogs, create_test_user
):
    """Testa que o índice parcial impede duas manutenções em andamento simultâneas para o mesmo bem."""
    tecnico = create_test_user(email="tec_maint_open@empresa.com")
    eq = Equipment(
        patrimony_number="PAT-ONE-OPEN",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_manutencao"].id,
    )
    db_session.add(eq)
    db_session.flush()

    m1 = EquipmentMaintenance(
        equipment_id=eq.id,
        maintenance_type_id=test_catalogs["maint_prev"].id,
        performed_by_user_id=tecnico.id,
        completed_at=None,
    )
    db_session.add(m1)
    db_session.flush()

    m2 = EquipmentMaintenance(
        equipment_id=eq.id,
        maintenance_type_id=test_catalogs["maint_corr"].id,
        performed_by_user_id=tecnico.id,
        completed_at=None,
    )
    db_session.add(m2)
    with pytest.raises(
        IntegrityError,
        match="uq_equipment_maintenances_one_open_per_equipment|equipment_maintenances",
    ):
        db_session.flush()
    db_session.rollback()


def test_permanent_uniqueness_case_insensitive_patrimony_even_after_soft_delete(
    db_session: Session, test_catalogs
):
    """Testa que patrimônio não pode ser reutilizado mesmo após exclusão lógica (Cenário 3)."""
    eq1 = Equipment(
        patrimony_number="PAT-100",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
        deleted_at=datetime.now(timezone.utc),
    )
    db_session.add(eq1)
    db_session.flush()

    eq2 = Equipment(
        patrimony_number="pat-100",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
    )
    db_session.add(eq2)
    with pytest.raises(IntegrityError, match="uq_equipments_patrimony_number_lower"):
        db_session.flush()
    db_session.rollback()


def test_partial_unique_hostname_liberation_after_soft_delete(db_session: Session, test_catalogs):
    """Testa que hostname é liberado após soft delete do equipamento anterior (Cenário 4)."""
    eq1 = Equipment(
        patrimony_number="PAT-SRV-01",
        hostname="srv-app.local",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
        deleted_at=datetime.now(timezone.utc),
    )
    db_session.add(eq1)
    db_session.flush()

    # Novo equipamento ativo pode reutilizar o hostname sem violação
    eq2 = Equipment(
        patrimony_number="PAT-SRV-02",
        hostname="SRV-APP.LOCAL",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
    )
    db_session.add(eq2)
    db_session.flush()
    assert eq2.id is not None


def test_triggers_update_updated_at(db_session: Session, test_catalogs, create_test_user):
    """Testa que os triggers PL/pgSQL atualizam updated_at automaticamente."""
    if db_session.bind.dialect.name == "sqlite":
        pytest.skip("PostgreSQL PL/pgSQL trigger not installed in SQLite fallback")
    tecnico = create_test_user(email="tec_trg@empresa.com")
    past = datetime.now(timezone.utc) - timedelta(days=2)

    eq = Equipment(
        patrimony_number="PAT-TRG-01",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
        created_at=past,
        updated_at=past,
    )
    db_session.add(eq)
    db_session.flush()
    original_updated_at = eq.updated_at

    # Atualiza equipamento via UPDATE SQL para acionar trigger
    db_session.execute(
        text("UPDATE equipments SET description = 'Alterado por Trigger' WHERE id = :id"),
        {"id": eq.id},
    )
    db_session.flush()
    db_session.refresh(eq)

    assert eq.updated_at > original_updated_at
