"""Testes unitários e de integração para os Casos de Uso de Equipamentos, Catálogos, Movimentações e Manutenções."""

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
from src.domain.schemas import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentMovementCreate,
    EquipmentMovementUpdate,
    EquipmentMaintenanceStart,
    EquipmentMaintenanceComplete,
    EquipmentMaintenanceUpdate,
    CatalogItemCreate,
    CatalogItemUpdate,
)
from src.use_cases.equipment_use_cases import (
    CreateEquipmentUseCase,
    ListEquipmentsUseCase,
    GetEquipmentDetailUseCase,
    UpdateEquipmentUseCase,
    DeleteEquipmentUseCase,
    RestoreEquipmentUseCase,
    GetDecryptedWindowsKeyUseCase,
    MovementsUseCase,
    MaintenancesUseCase,
    ManageCatalogsUseCase,
    GetSuggestionsUseCase,
    ExportEquipmentsUseCase,
    ConflictError,
)


def test_create_equipment_use_case_success_and_duplicates(db_session: Session, test_catalogs):
    """Testa cadastro de equipamento com validações de catálogos, criptografia e unicidade."""
    create_uc = CreateEquipmentUseCase(db_session)

    data = EquipmentCreate(
        patrimony_number="PAT-UC-001",
        serial_number="SN-UC-001",
        hostname="host-uc-001",
        description="ThinkPad X1",
        model="ThinkPad X1 Carbon",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
        ip_address="192.168.1.10",
        mac_address="00:1A:2B:3C:4D:5E",
        printer_identifier="PRN-UC-01",
        windows_product_key="VK9X2-N8Y4R-W3M2T-K7P1Q-L9Z0A",
    )
    eq = create_uc.execute(data)
    assert eq.id is not None
    assert eq.patrimony_number == "PAT-UC-001"
    assert eq.windows_product_key_encrypted is not None
    assert eq.windows_product_key_encrypted != "VK9X2-N8Y4R-W3M2T-K7P1Q-L9Z0A"

    # Duplicidade de patrimônio permanente
    with pytest.raises(ValueError, match="Número de patrimônio.*já está cadastrado"):
        create_uc.execute(
            EquipmentCreate(
                patrimony_number="pat-uc-001",
                equipment_type_id=test_catalogs["type"].id,
                sector_id=test_catalogs["sector_ti"].id,
                status_id=test_catalogs["status_em_uso"].id,
            )
        )

    # Duplicidade de serial permanente
    with pytest.raises(ValueError, match="Número de série.*já está cadastrado"):
        create_uc.execute(
            EquipmentCreate(
                patrimony_number="PAT-OUTRO",
                serial_number="sn-uc-001",
                equipment_type_id=test_catalogs["type"].id,
                sector_id=test_catalogs["sector_ti"].id,
                status_id=test_catalogs["status_em_uso"].id,
            )
        )

    # Duplicidade de hostname ativo
    with pytest.raises(ValueError, match="Hostname.*já está em uso"):
        create_uc.execute(
            EquipmentCreate(
                patrimony_number="PAT-OUTRO2",
                hostname="HOST-UC-001",
                equipment_type_id=test_catalogs["type"].id,
                sector_id=test_catalogs["sector_ti"].id,
                status_id=test_catalogs["status_em_uso"].id,
            )
        )

    # Duplicidade de IP ativo
    with pytest.raises(ValueError, match="Endereço IP.*já está em uso"):
        create_uc.execute(
            EquipmentCreate(
                patrimony_number="PAT-OUTRO3",
                ip_address="192.168.1.10",
                equipment_type_id=test_catalogs["type"].id,
                sector_id=test_catalogs["sector_ti"].id,
                status_id=test_catalogs["status_em_uso"].id,
            )
        )

    # Duplicidade de MAC ativo
    with pytest.raises(ValueError, match="Endereço MAC.*já está em uso"):
        create_uc.execute(
            EquipmentCreate(
                patrimony_number="PAT-OUTRO4",
                mac_address="00:1A:2B:3C:4D:5E",
                equipment_type_id=test_catalogs["type"].id,
                sector_id=test_catalogs["sector_ti"].id,
                status_id=test_catalogs["status_em_uso"].id,
            )
        )

    # Duplicidade de Printer ID ativo
    with pytest.raises(ValueError, match="Identificador de impressora.*já está em uso"):
        create_uc.execute(
            EquipmentCreate(
                patrimony_number="PAT-OUTRO5",
                printer_identifier="PRN-UC-01",
                equipment_type_id=test_catalogs["type"].id,
                sector_id=test_catalogs["sector_ti"].id,
                status_id=test_catalogs["status_em_uso"].id,
            )
        )

    # Catálogos inválidos ou inativos
    with pytest.raises(ValueError, match="Tipo de equipamento.*inválido"):
        create_uc.execute(
            EquipmentCreate(
                patrimony_number="PAT-ERR-CAT1",
                equipment_type_id=99999,
                sector_id=test_catalogs["sector_ti"].id,
                status_id=test_catalogs["status_em_uso"].id,
            )
        )

    with pytest.raises(ValueError, match="Setor.*inválido"):
        create_uc.execute(
            EquipmentCreate(
                patrimony_number="PAT-ERR-CAT2",
                equipment_type_id=test_catalogs["type"].id,
                sector_id=99999,
                status_id=test_catalogs["status_em_uso"].id,
            )
        )

    with pytest.raises(ValueError, match="Situação patrimonial.*inválida"):
        create_uc.execute(
            EquipmentCreate(
                patrimony_number="PAT-ERR-CAT3",
                equipment_type_id=test_catalogs["type"].id,
                sector_id=test_catalogs["sector_ti"].id,
                status_id=99999,
            )
        )


def test_list_and_get_equipment_detail_use_cases(db_session: Session, test_catalogs):
    """Testa busca detalhada e listagem paginada com mascaramento da chave Windows."""
    create_uc = CreateEquipmentUseCase(db_session)
    list_uc = ListEquipmentsUseCase(db_session)
    detail_uc = GetEquipmentDetailUseCase(db_session)

    eq = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-DET-01",
            description="Monitor LG 29",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
            windows_product_key="SECRET-WINDOWS-KEY",
        )
    )

    # Get Detail
    found = detail_uc.execute(eq.id)
    assert found.description == "Monitor LG 29"
    assert found.windows_product_key == "••••••••••••••••"

    with pytest.raises(KeyError, match="não foi encontrado"):
        detail_uc.execute(99999)

    # List com múltiplos filtros
    response = list_uc.execute(
        page=1,
        limit=10,
        equipment_type_ids=[test_catalogs["type"].id],
        sector_ids=[test_catalogs["sector_ti"].id],
        status_ids=[test_catalogs["status_em_uso"].id],
    )
    assert response.total >= 1
    assert response.items[0].windows_product_key == "••••••••••••••••"


def test_update_equipment_use_case(db_session: Session, test_catalogs):
    """Testa atualização de equipamento e regras de validação."""
    create_uc = CreateEquipmentUseCase(db_session)
    update_uc = UpdateEquipmentUseCase(db_session)

    eq1 = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-UPD-01",
            serial_number="SN-UPD-01",
            hostname="host-upd-01",
            description="Desk Original",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
        )
    )
    eq2 = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-UPD-02",
            serial_number="SN-UPD-02",
            hostname="host-upd-02",
            description="Desk 2",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_com"].id,
            status_id=test_catalogs["status_em_uso"].id,
        )
    )

    # Atualização válida
    updated = update_uc.execute(
        eq1.id,
        EquipmentUpdate(
            patrimony_number="PAT-UPD-01-MOD",
            serial_number="SN-UPD-01-MOD",
            hostname="host-upd-01-mod",
            description="Desk Atualizado",
            brand="Dell",
            model="OptiPlex 7090",
            ip_address="192.168.1.55",
            mac_address="00:1A:2B:3C:4D:77",
            printer_identifier="PRN-NEW",
            windows_product_key="NEW-KEY-12345",
            notes="Novas observações",
        ),
    )
    assert updated.patrimony_number == "PAT-UPD-01-MOD"
    assert updated.model == "OptiPlex 7090"

    # Atualização vazia
    assert update_uc.execute(eq1.id, EquipmentUpdate()).id == eq1.id

    # Duplicidade de serial ao atualizar
    with pytest.raises(ValueError, match="Número de série.*já está cadastrado"):
        update_uc.execute(eq1.id, EquipmentUpdate(serial_number="SN-UPD-02"))

    # Duplicidade de patrimônio ao atualizar
    with pytest.raises(ValueError, match="Número de patrimônio.*já está cadastrado"):
        update_uc.execute(eq1.id, EquipmentUpdate(patrimony_number="PAT-UPD-02"))

    # Duplicidade de hostname ativo ao atualizar
    with pytest.raises(ValueError, match="Hostname.*já está em uso"):
        update_uc.execute(eq1.id, EquipmentUpdate(hostname="host-upd-02"))

    # Erro de equipamento inexistente
    with pytest.raises(KeyError, match="não foi encontrado"):
        update_uc.execute(99999, EquipmentUpdate(description="Inexistente"))


def test_soft_delete_and_restore_use_case(db_session: Session, test_catalogs):
    """Testa exclusão lógica e restauração com conflito HTTP 409 Conflict."""
    create_uc = CreateEquipmentUseCase(db_session)
    delete_uc = DeleteEquipmentUseCase(db_session)
    restore_uc = RestoreEquipmentUseCase(db_session)

    eq1 = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-SD-01",
            hostname="srv-restore.local",
            ip_address="10.0.0.50",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
        )
    )

    # Soft delete
    delete_uc.execute(eq1.id)
    assert eq1.deleted_at is not None

    with pytest.raises(KeyError):
        delete_uc.execute(99999)

    # Cria eq2 ocupando o hostname de eq1
    eq2 = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-SD-02",
            hostname="srv-restore.local",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
        )
    )

    # Tentativa de restauração de eq1 deve levantar ConflictError (HTTP 409)
    with pytest.raises(ConflictError, match="Hostname.*já está em uso"):
        restore_uc.execute(eq1.id)

    # Remove eq2 e restaura eq1 com sucesso
    delete_uc.execute(eq2.id)
    restored = restore_uc.execute(eq1.id)
    assert restored.deleted_at is None

    # Restaurar já ativo não quebra
    assert restore_uc.execute(eq1.id).deleted_at is None

    with pytest.raises(KeyError):
        restore_uc.execute(99999)


def test_get_decrypted_windows_key_use_case(db_session: Session, test_catalogs):
    """Testa decriptação temporária e segura da chave Windows para o técnico."""
    create_uc = CreateEquipmentUseCase(db_session)
    secret_uc = GetDecryptedWindowsKeyUseCase(db_session)

    raw_key = "VK9X2-N8Y4R-W3M2T-K7P1Q-L9Z0A"
    eq = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-WIN-SEC",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
            windows_product_key=raw_key,
        )
    )

    result = secret_uc.execute(eq.id)
    assert result.windows_product_key == raw_key

    with pytest.raises(KeyError):
        secret_uc.execute(99999)


def test_manage_catalogs_use_case(db_session: Session):
    """Testa CRUD genérico de catálogos e unicidade case-insensitive permanente."""
    uc = ManageCatalogsUseCase(db_session)

    # Create
    item = uc.create_item(EquipmentType, CatalogItemCreate(name="Tablet"))
    assert item.id is not None
    assert item.name == "Tablet"

    # Duplicidade de nome permanente
    with pytest.raises(ValueError, match="já está cadastrado no catálogo"):
        uc.create_item(EquipmentType, CatalogItemCreate(name="tablet"))

    # Update
    uc.update_item(EquipmentType, item.id, CatalogItemUpdate(name="Tablet Pro"))
    assert item.name == "Tablet Pro"

    # Soft delete & Restore
    uc.delete_item(EquipmentType, item.id)
    assert item.deleted_at is not None

    uc.restore_item(EquipmentType, item.id)
    assert item.deleted_at is None

    with pytest.raises(KeyError):
        uc.get_item(EquipmentType, 99999)
    with pytest.raises(KeyError):
        uc.restore_item(EquipmentType, 99999)


def test_scenario_8_retroactive_movement_and_chain_auto_adjust(
    db_session: Session, test_catalogs, create_test_user
):
    """Testa Cenário 8: movimentação retroativa intermediária e auto-ajuste da cadeia de setores."""
    tecnico = create_test_user(email="tec_mov_c8@empresa.com")
    create_uc = CreateEquipmentUseCase(db_session)
    mov_uc = MovementsUseCase(db_session)

    sec_almox = test_catalogs["sector_dir"]  # Setor inicial
    sec_ti = test_catalogs["sector_ti"]
    sec_com = test_catalogs["sector_com"]

    # Criar outro setor para destino final
    cat_repo = ManageCatalogsUseCase(db_session)
    sec_radio = cat_repo.create_item(Sector, CatalogItemCreate(name="Rádio Produção Setor"))

    eq = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-MOV-SCENARIO8",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=sec_almox.id,
            status_id=test_catalogs["status_em_uso"].id,
        )
    )

    # Mov 1: 01/10 - Almoxarifado -> TI
    d1 = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
    mov1 = mov_uc.record_movement(
        eq.id,
        EquipmentMovementCreate(
            origin_sector_id=sec_almox.id,
            destination_sector_id=sec_ti.id,
            movement_date=d1,
        ),
        performed_by_user_id=tecnico.id,
    )

    # Mov 2: 10/10 - TI -> Rádio
    d2 = datetime(2026, 10, 10, 10, 0, tzinfo=timezone.utc)
    mov2 = mov_uc.record_movement(
        eq.id,
        EquipmentMovementCreate(
            origin_sector_id=sec_ti.id,
            destination_sector_id=sec_radio.id,
            movement_date=d2,
        ),
        performed_by_user_id=tecnico.id,
    )

    # Equipamento está em Rádio
    db_session.refresh(eq)
    assert eq.sector_id == sec_radio.id

    # Mov 3 retroativa: 05/10 - TI -> Comunicação
    d3 = datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc)
    mov3 = mov_uc.record_movement(
        eq.id,
        EquipmentMovementCreate(
            origin_sector_id=sec_ti.id,
            destination_sector_id=sec_com.id,
            movement_date=d3,
        ),
        performed_by_user_id=tecnico.id,
    )

    # Verifica auto-ajuste da cadeia:
    # 01/10: Almox -> TI
    # 05/10: TI -> Comunicação
    # 10/10: Comunicação -> Rádio (origin_sector_id de mov2 foi alterado para Comunicação!)
    db_session.refresh(mov1)
    db_session.refresh(mov2)
    db_session.refresh(mov3)
    db_session.refresh(eq)

    assert mov1.destination_sector_id == sec_ti.id
    assert mov3.origin_sector_id == sec_ti.id
    assert mov3.destination_sector_id == sec_com.id
    assert mov2.origin_sector_id == sec_com.id  # Auto-ajustado!
    assert mov2.destination_sector_id == sec_radio.id
    assert eq.sector_id == sec_radio.id  # Destino final preservado!


def test_scenario_9_movement_to_same_sector_rejected(
    db_session: Session, test_catalogs, create_test_user
):
    """Testa Cenário 9: rejeição de movimentação para o mesmo setor de origem."""
    tecnico = create_test_user(email="tec_mov_c9@empresa.com")
    create_uc = CreateEquipmentUseCase(db_session)
    mov_uc = MovementsUseCase(db_session)

    eq = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-MOV-SAME",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
        )
    )

    with pytest.raises(ValueError, match="setor de origem deve ser diferente do setor de destino"):
        mov_uc.record_movement(
            eq.id,
            EquipmentMovementCreate(
                origin_sector_id=test_catalogs["sector_ti"].id,
                destination_sector_id=test_catalogs["sector_ti"].id,
            ),
            performed_by_user_id=tecnico.id,
        )


def test_scenarios_5_6_7_maintenances_lifecycle(
    db_session: Session, test_catalogs, create_test_user
):
    """Testa Cenários 5, 6 e 7: Início de manutenção muda status para 'Em manutenção', impede concorrente e conclusão exige novo status."""
    tecnico = create_test_user(email="tec_maint_cycle@empresa.com")
    create_uc = CreateEquipmentUseCase(db_session)
    maint_uc = MaintenancesUseCase(db_session)

    eq = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-MAINT-CYCLE",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
        )
    )
    assert eq.status.name == "Em uso"

    # Cenário 5: Início de manutenção corretiva
    now = datetime.now(timezone.utc)
    maint = maint_uc.start_maintenance(
        equipment_id=eq.id,
        data=EquipmentMaintenanceStart(
            maintenance_type_id=test_catalogs["maint_corr"].id,
            started_at=now,
            description="Troca de placa-mãe",
        ),
        performed_by_user_id=tecnico.id,
    )
    db_session.refresh(eq)
    assert maint.id is not None
    assert maint.completed_at is None
    assert eq.status.name == "Em manutenção"

    # Cenário 6: Impedir abertura de segunda manutenção concorrente
    with pytest.raises(ConflictError, match="manutenção em andamento"):
        maint_uc.start_maintenance(
            equipment_id=eq.id,
            data=EquipmentMaintenanceStart(
                maintenance_type_id=test_catalogs["maint_prev"].id,
                started_at=now,
            ),
            performed_by_user_id=tecnico.id,
        )

    # Cenário 7: Conclusão de manutenção
    # Rejeição se nova situação for 'Em manutenção'
    with pytest.raises(ValueError, match="não pode ser 'Em manutenção'"):
        maint_uc.complete_maintenance(
            equipment_id=eq.id,
            maintenance_id=maint.id,
            data=EquipmentMaintenanceComplete(
                completed_at=now + timedelta(hours=2),
                new_status_id=test_catalogs["status_em_manutencao"].id,
            ),
        )

    # Conclusão com sucesso para 'Em uso'
    completed = maint_uc.complete_maintenance(
        equipment_id=eq.id,
        maintenance_id=maint.id,
        data=EquipmentMaintenanceComplete(
            completed_at=now + timedelta(hours=2),
            new_status_id=test_catalogs["status_em_uso"].id,
            description="Concluído com sucesso",
        ),
    )
    db_session.refresh(eq)
    assert completed.completed_at is not None
    assert eq.status.name == "Em uso"


def test_suggestions_and_export_use_cases(db_session: Session, test_catalogs):
    """Testa autocomplete e exportação em Excel."""
    sug_uc = GetSuggestionsUseCase(db_session)
    exp_uc = ExportEquipmentsUseCase(db_session)
    create_uc = CreateEquipmentUseCase(db_session)

    create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-EXP-01",
            serial_number="SN-EXP-01",
            model="Dell Precision",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
        )
    )

    # Suggestions
    sugs = sug_uc.execute(field="model", prefix="Dell", limit=5)
    assert len(sugs) >= 1

    with pytest.raises(ValueError, match="pelo menos 2 caracteres"):
        sug_uc.execute(field="model", prefix="D")

    with pytest.raises(ValueError, match="Campo inválido"):
        sug_uc.execute(field="campo_errado", prefix="Dell")

    # Export
    file_bytes, filename = exp_uc.execute(
        equipment_type_ids=[test_catalogs["type"].id],
    )
    assert len(file_bytes) > 100
    assert filename.startswith("PATRIMONIO_")


def test_equipment_use_cases_edge_cases_and_branches(
    db_session: Session, test_catalogs, create_test_user
):
    """Cobre todas as branches e casos de borda de validação em equipment_use_cases.py."""
    user = create_test_user(email="edge_cases_tecnico@empresa.com", role="tecnico")
    cat_uc = ManageCatalogsUseCase(db_session)
    create_uc = CreateEquipmentUseCase(db_session)
    update_uc = UpdateEquipmentUseCase(db_session)
    mov_uc = MovementsUseCase(db_session)
    maint_uc = MaintenancesUseCase(db_session)

    # 1. ManageCatalogsUseCase
    all_types = cat_uc.list_items(EquipmentType, include_inactive=True)
    assert len(all_types) >= 1

    # Renomear para mesmo nome (casing diferente)
    type_item = cat_uc.create_item(EquipmentType, CatalogItemCreate(name="Notebook Gamer"))
    updated_type = cat_uc.update_item(
        EquipmentType, type_item.id, CatalogItemUpdate(name="NOTEBOOK GAMER")
    )
    assert updated_type.name == "NOTEBOOK GAMER"

    # 2. UpdateEquipmentUseCase
    eq1 = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-EDGE-1",
            serial_number="SN-EDGE-1",
            hostname="HOST-EDGE-1",
            ip_address="192.168.99.10",
            mac_address="00:11:22:33:44:01",
            printer_identifier="PRN-EDGE-1",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
        )
    )
    eq2 = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-EDGE-2",
            serial_number="SN-EDGE-2",
            hostname="HOST-EDGE-2",
            ip_address="192.168.99.20",
            mac_address="00:11:22:33:44:02",
            printer_identifier="PRN-EDGE-2",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
        )
    )

    # Catálogos inválidos no update
    with pytest.raises(ValueError, match="Tipo de equipamento ID"):
        update_uc.execute(eq1.id, EquipmentUpdate(equipment_type_id=99999))
    with pytest.raises(ValueError, match="Setor ID"):
        update_uc.execute(eq1.id, EquipmentUpdate(sector_id=99999))
    with pytest.raises(ValueError, match="Situação patrimonial ID"):
        update_uc.execute(eq1.id, EquipmentUpdate(status_id=99999))

    # Atualização válida de catálogos
    upd_valid_cats = update_uc.execute(
        eq1.id,
        EquipmentUpdate(
            equipment_type_id=type_item.id,
            sector_id=test_catalogs["sector_com"].id,
            status_id=test_catalogs["status_ocioso"].id,
        ),
        performed_by_user_id=user.id,
    )
    assert upd_valid_cats.equipment_type_id == type_item.id
    assert upd_valid_cats.sector_id == test_catalogs["sector_com"].id
    assert upd_valid_cats.status_id == test_catalogs["status_ocioso"].id

    # Reverte setor para TI para os testes de movimentação seguintes
    update_uc.execute(
        eq1.id,
        EquipmentUpdate(
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
        ),
        performed_by_user_id=user.id,
    )

    # Manter mesmos identificadores (clean == old)
    upd_same = update_uc.execute(
        eq1.id,
        EquipmentUpdate(
            serial_number="SN-EDGE-1",
            hostname="HOST-EDGE-1",
            ip_address="192.168.99.10",
            mac_address="00:11:22:33:44:01",
            printer_identifier="PRN-EDGE-1",
        ),
    )
    assert upd_same.patrimony_number == "PAT-EDGE-1"

    # Conflitos de identificadores ativos em outro bem no update
    with pytest.raises(ValueError, match="Endereço IP"):
        update_uc.execute(eq1.id, EquipmentUpdate(ip_address="192.168.99.20"))
    with pytest.raises(ValueError, match="Endereço MAC"):
        update_uc.execute(eq1.id, EquipmentUpdate(mac_address="00:11:22:33:44:02"))
    with pytest.raises(ValueError, match="Identificador de impressora"):
        update_uc.execute(eq1.id, EquipmentUpdate(printer_identifier="PRN-EDGE-2"))

    # 3. MovementsUseCase
    eq_mov = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-EDGE-MOV",
            serial_number="SN-EDGE-MOV",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
        )
    )
    # Recalculate chain guard clauses
    mov_uc._recalculate_chain(99999)
    mov_uc._recalculate_chain(eq_mov.id)

    # Naive date e data futura
    naive_date = datetime.now()
    mov1 = mov_uc.record_movement(
        eq_mov.id,
        EquipmentMovementCreate(
            origin_sector_id=test_catalogs["sector_ti"].id,
            destination_sector_id=test_catalogs["sector_com"].id,
            movement_date=naive_date,
        ),
        performed_by_user_id=user.id,
    )
    assert mov1.id is not None

    with pytest.raises(ValueError, match="Data da movimentação não pode ser futura"):
        mov_uc.record_movement(
            eq_mov.id,
            EquipmentMovementCreate(
                origin_sector_id=test_catalogs["sector_com"].id,
                destination_sector_id=test_catalogs["sector_dir"].id,
                movement_date=datetime.now(timezone.utc) + timedelta(minutes=15),
            ),
            performed_by_user_id=user.id,
        )

    with pytest.raises(ValueError, match="Setor de origem ID"):
        mov_uc.record_movement(
            eq_mov.id,
            EquipmentMovementCreate(
                origin_sector_id=99999,
                destination_sector_id=test_catalogs["sector_dir"].id,
                movement_date=datetime.now(timezone.utc),
            ),
            performed_by_user_id=user.id,
        )

    with pytest.raises(ValueError, match="Setor de destino ID"):
        mov_uc.record_movement(
            eq_mov.id,
            EquipmentMovementCreate(
                origin_sector_id=test_catalogs["sector_com"].id,
                destination_sector_id=99999,
                movement_date=datetime.now(timezone.utc),
            ),
            performed_by_user_id=user.id,
        )

    # Update movement branches
    upd_mov = mov_uc.update_movement(
        eq_mov.id,
        mov1.id,
        EquipmentMovementUpdate(
            destination_sector_id=test_catalogs["sector_dir"].id,
            movement_date=datetime.now(),
            notes="Ajuste com data naive e notas",
        ),
    )
    assert upd_mov.destination_sector_id == test_catalogs["sector_dir"].id

    with pytest.raises(ValueError, match="Data da movimentação não pode ser futura"):
        mov_uc.update_movement(
            eq_mov.id,
            mov1.id,
            EquipmentMovementUpdate(
                movement_date=datetime.now(timezone.utc) + timedelta(minutes=20),
            ),
        )

    # Cadeia gerando origin == destination
    # mov1: TI -> DIR
    # Adicionar mov2 em data posterior com DIR -> COM
    mov2 = mov_uc.record_movement(
        eq_mov.id,
        EquipmentMovementCreate(
            origin_sector_id=test_catalogs["sector_dir"].id,
            destination_sector_id=test_catalogs["sector_com"].id,
            movement_date=datetime.now(timezone.utc) + timedelta(seconds=2),
        ),
        performed_by_user_id=user.id,
    )
    # Agora atualizar mov1 para destino COM -> cadeia auto-ajusta mov2.origin para COM, ficando COM -> COM!
    with pytest.raises(ValueError, match="Ajuste da cadeia gerou transferência para o mesmo setor"):
        mov_uc.update_movement(
            eq_mov.id,
            mov1.id,
            EquipmentMovementUpdate(
                destination_sector_id=test_catalogs["sector_com"].id,
            ),
        )

    # 4. MaintenancesUseCase
    # Resilience fallback: criar manutenção quando status 'Em manutenção' foi excluído do catálogo
    status_maint = (
        db_session.query(EquipmentStatus).filter(EquipmentStatus.name == "Em manutenção").first()
    )
    db_session.delete(status_maint)
    db_session.flush()

    maint_naive = maint_uc.start_maintenance(
        eq1.id,
        EquipmentMaintenanceStart(
            maintenance_type_id=test_catalogs["maint_prev"].id,
            started_at=datetime.now(),
            description="Manutenção com started_at naive e recriação de status",
        ),
        performed_by_user_id=user.id,
    )
    assert maint_naive.id is not None

    # Complete maintenance edge cases
    with pytest.raises(KeyError, match="não foi encontrada para este equipamento"):
        maint_uc.complete_maintenance(
            eq1.id,
            99999,
            EquipmentMaintenanceComplete(
                new_status_id=test_catalogs["status_ocioso"].id,
            ),
        )

    with pytest.raises(ValueError, match="A data/hora de conclusão não pode ser anterior"):
        maint_uc.complete_maintenance(
            eq1.id,
            maint_naive.id,
            EquipmentMaintenanceComplete(
                completed_at=maint_naive.started_at - timedelta(days=1),
                new_status_id=test_catalogs["status_ocioso"].id,
            ),
        )

    with pytest.raises(ValueError, match="Nova situação ID"):
        maint_uc.complete_maintenance(
            eq1.id,
            maint_naive.id,
            EquipmentMaintenanceComplete(
                new_status_id=99999,
            ),
        )

    # Complete successfully with naive datetime, description and notes (covers naive started_at branch in PostgreSQL)
    maint_naive.started_at = datetime(2026, 1, 1, 10, 0, 0)
    completed_maint = maint_uc.complete_maintenance(
        eq1.id,
        maint_naive.id,
        EquipmentMaintenanceComplete(
            completed_at=datetime(2026, 1, 1, 12, 0, 0),
            new_status_id=test_catalogs["status_ocioso"].id,
            description="Desc concluída",
            notes="Notas concluídas",
        ),
    )
    assert completed_maint.completed_at is not None

    # Completar novamente -> ValueError
    with pytest.raises(ValueError, match="já foi concluída"):
        maint_uc.complete_maintenance(
            eq1.id,
            maint_naive.id,
            EquipmentMaintenanceComplete(
                new_status_id=test_catalogs["status_ocioso"].id,
            ),
        )

    # Update maintenance edge cases
    with pytest.raises(KeyError, match="não foi encontrada para este equipamento"):
        maint_uc.update_maintenance(eq1.id, 99999, EquipmentMaintenanceUpdate())

    with pytest.raises(KeyError, match="não foi encontrada para este equipamento"):
        maint_uc.update_maintenance(eq2.id, maint_naive.id, EquipmentMaintenanceUpdate())

    with pytest.raises(KeyError, match="não foi encontrada para este equipamento"):
        maint_uc.complete_maintenance(
            eq2.id,
            maint_naive.id,
            EquipmentMaintenanceComplete(
                new_status_id=test_catalogs["status_ocioso"].id,
            ),
        )

    with pytest.raises(ValueError, match="Tipo de manutenção ID"):
        maint_uc.update_maintenance(
            eq1.id,
            maint_naive.id,
            EquipmentMaintenanceUpdate(
                maintenance_type_id=99999,
            ),
        )

    with pytest.raises(ValueError, match="A conclusão não pode ser anterior"):
        maint_uc.update_maintenance(
            eq1.id,
            maint_naive.id,
            EquipmentMaintenanceUpdate(
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc) - timedelta(hours=2),
            ),
        )

    # Update maintenance com None em todos os campos
    maint_empty_upd = maint_uc.update_maintenance(
        eq1.id, maint_naive.id, EquipmentMaintenanceUpdate()
    )
    assert maint_empty_upd.id == maint_naive.id

    # Update maintenance com datetimes naive e novos dados
    upd_maint = maint_uc.update_maintenance(
        eq1.id,
        maint_naive.id,
        EquipmentMaintenanceUpdate(
            maintenance_type_id=test_catalogs["maint_prev"].id,
            started_at=datetime.now() - timedelta(hours=1),
            completed_at=datetime.now(),
            description="Nova desc",
            notes="Novas notas",
        ),
    )
    assert upd_maint.description == "Nova desc"
    assert upd_maint.notes == "Novas notas"

    # Start maintenance edge cases: tipo inválido e started_at None
    with pytest.raises(ValueError, match="Tipo de manutenção ID"):
        maint_uc.start_maintenance(
            eq2.id,
            EquipmentMaintenanceStart(
                maintenance_type_id=99999,
            ),
            performed_by_user_id=user.id,
        )

    maint_eq2 = maint_uc.start_maintenance(
        eq2.id,
        EquipmentMaintenanceStart(
            maintenance_type_id=test_catalogs["maint_prev"].id,
        ),
        performed_by_user_id=user.id,
    )
    assert maint_eq2.id is not None

    # Complete maintenance com descrição e notas vazias (None)
    comp_eq2 = maint_uc.complete_maintenance(
        eq2.id,
        maint_eq2.id,
        EquipmentMaintenanceComplete(
            new_status_id=test_catalogs["status_ocioso"].id,
        ),
    )
    assert comp_eq2.completed_at is not None

    # Update movement com origin_sector_id
    upd_mov_orig = mov_uc.update_movement(
        eq_mov.id,
        mov1.id,
        EquipmentMovementUpdate(
            origin_sector_id=test_catalogs["sector_ti"].id,
        ),
    )
    assert upd_mov_orig.origin_sector_id == test_catalogs["sector_ti"].id
