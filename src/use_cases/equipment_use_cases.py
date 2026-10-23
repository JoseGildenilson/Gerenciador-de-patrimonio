"""Casos de uso de negócio para Gestão de Patrimônio e Equipamentos."""

import math
from datetime import datetime, timezone, timedelta
from typing import Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from src.core.security import (
    encrypt_windows_product_key,
    decrypt_windows_product_key,
    mask_windows_product_key,
)
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
    EquipmentResponse,
    EquipmentListItemResponse,
    EquipmentListResponse,
    EquipmentSecretKeyResponse,
    EquipmentMovementCreate,
    EquipmentMovementUpdate,
    EquipmentMovementResponse,
    EquipmentMaintenanceStart,
    EquipmentMaintenanceComplete,
    EquipmentMaintenanceUpdate,
    EquipmentMaintenanceResponse,
    CatalogItemCreate,
    CatalogItemUpdate,
    CatalogItemResponse,
    SectorResponse,
    EquipmentTypeResponse,
    EquipmentStatusResponse,
    MaintenanceTypeResponse,
)
from src.infrastructure.repositories import (
    EquipmentRepository,
    CatalogsRepository,
    EquipmentMovementRepository,
    EquipmentMaintenanceRepository,
)
from src.infrastructure.spreadsheet_exporter import generate_equipments_excel


class ConflictError(Exception):
    """Exceção para conflitos de identificadores únicos ativos (HTTP 409 Conflict)."""

    pass


class ManageCatalogsUseCase:
    """Caso de uso para CRUD dos 4 catálogos estruturais com controle de transação no caso de uso."""

    def __init__(self, db: Session, repo: CatalogsRepository | None = None):
        self.db = db
        self.repo = repo or CatalogsRepository(db)

    def list_items(self, model_class, include_inactive: bool = False):
        if include_inactive:
            return self.repo.list_all(model_class)
        return self.repo.list_active(model_class)

    def get_item(self, model_class, item_id: int):
        item = self.repo.get_by_id(model_class, item_id)
        if not item:
            raise KeyError(f"Item com ID {item_id} não encontrado no catálogo.")
        return item

    def create_item(self, model_class, data: CatalogItemCreate):
        clean_name = data.name.strip()
        existing = self.repo.get_by_name_lower(model_class, clean_name)
        if existing:
            raise ValueError(
                f"Item '{clean_name}' já está cadastrado no catálogo (unicidade permanente)."
            )
        try:
            item = model_class(name=clean_name)
            self.repo.create(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Item '{clean_name}' já está cadastrado no catálogo.") from e
        except Exception:
            self.db.rollback()
            raise

    def update_item(self, model_class, item_id: int, data: CatalogItemUpdate):
        item = self.get_item(model_class, item_id)
        clean_name = data.name.strip()
        if clean_name.lower() != item.name.lower():
            existing = self.repo.get_by_name_lower(model_class, clean_name)
            if existing and existing.id != item_id:
                raise ValueError(f"Item '{clean_name}' já está cadastrado no catálogo.")
        try:
            self.repo.update(item, clean_name)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Item '{clean_name}' já está cadastrado no catálogo.") from e
        except Exception:
            self.db.rollback()
            raise

    def delete_item(self, model_class, item_id: int):
        item = self.get_item(model_class, item_id)

        # ISSUE-012: Valida se existem referências ativas antes de excluir
        has_active_refs = False
        if model_class == EquipmentType:
            has_active_refs = (
                self.db.query(Equipment.id)
                .filter(Equipment.equipment_type_id == item_id, Equipment.deleted_at.is_(None))
                .first()
                is not None
            )
        elif model_class == Sector:
            has_active_refs = (
                self.db.query(Equipment.id)
                .filter(Equipment.sector_id == item_id, Equipment.deleted_at.is_(None))
                .first()
                is not None
            )
        elif model_class == EquipmentStatus:
            has_active_refs = (
                self.db.query(Equipment.id)
                .filter(Equipment.status_id == item_id, Equipment.deleted_at.is_(None))
                .first()
                is not None
            )
        elif model_class == MaintenanceType:
            has_active_refs = (
                self.db.query(EquipmentMaintenance.id)
                .filter(EquipmentMaintenance.maintenance_type_id == item_id)
                .first()
                is not None
            )

        if has_active_refs:
            raise ValueError(
                f"Não é possível excluir o item '{item.name}' pois existem equipamentos ou registros associados a ele."
            )

        try:
            self.repo.soft_delete(item)
            self.db.commit()
            return item
        except Exception:
            self.db.rollback()
            raise

    def restore_item(self, model_class, item_id: int):
        item = self.repo.get_by_id(model_class, item_id)
        if not item:
            raise KeyError(f"Item com ID {item_id} não encontrado no catálogo.")
        if item.deleted_at is None:
            raise ValueError(f"Item com ID {item_id} já está ativo no catálogo.")
        try:
            self.repo.restore(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except Exception:
            self.db.rollback()
            raise


class CreateEquipmentUseCase:
    """Caso de uso para cadastro de novos equipamentos com validações estritas de unicidade e vínculos."""

    def __init__(
        self,
        db: Session,
        eq_repo: EquipmentRepository | None = None,
        cat_repo: CatalogsRepository | None = None,
    ):
        self.db = db
        self.eq_repo = eq_repo or EquipmentRepository(db)
        self.cat_repo = cat_repo or CatalogsRepository(db)

    def execute(self, data: EquipmentCreate) -> Equipment:
        # 1. Valida existência e status ativo dos catálogos
        eq_type = self.cat_repo.get_by_id(EquipmentType, data.equipment_type_id)
        if not eq_type or eq_type.deleted_at is not None:
            raise ValueError(
                f"Tipo de equipamento ID {data.equipment_type_id} inválido ou inativo."
            )

        sector = self.cat_repo.get_by_id(Sector, data.sector_id)
        if not sector or sector.deleted_at is not None:
            raise ValueError(f"Setor ID {data.sector_id} inválido ou inativo.")

        status = self.cat_repo.get_by_id(EquipmentStatus, data.status_id)
        if not status or status.deleted_at is not None:
            raise ValueError(f"Situação patrimonial ID {data.status_id} inválida ou inativa.")

        # 2. Validações de unicidade permanente
        if self.eq_repo.get_by_patrimony_number(data.patrimony_number):
            raise ValueError(
                f"Número de patrimônio '{data.patrimony_number}' já está cadastrado no sistema."
            )

        if data.serial_number and self.eq_repo.get_by_serial_number(data.serial_number):
            raise ValueError(
                f"Número de série '{data.serial_number}' já está cadastrado no sistema."
            )

        # 3. Validações de unicidade ativa
        if data.hostname and self.eq_repo.get_active_by_hostname(data.hostname):
            raise ValueError(
                f"Hostname '{data.hostname}' já está em uso por outro equipamento ativo."
            )

        if data.ip_address and self.eq_repo.get_active_by_ip(data.ip_address):
            raise ValueError(
                f"Endereço IP '{data.ip_address}' já está em uso por outro equipamento ativo."
            )

        if data.mac_address and self.eq_repo.get_active_by_mac(data.mac_address):
            raise ValueError(
                f"Endereço MAC '{data.mac_address}' já está em uso por outro equipamento ativo."
            )

        if data.printer_identifier and self.eq_repo.get_active_by_printer_identifier(
            data.printer_identifier
        ):
            raise ValueError(
                f"Identificador de impressora '{data.printer_identifier}' já está em uso por outro equipamento ativo."
            )

        # 4. Criptografa chave do Windows se informada
        encrypted_windows_key = encrypt_windows_product_key(data.windows_product_key)

        equipment = Equipment(
            patrimony_number=data.patrimony_number.strip(),
            equipment_type_id=data.equipment_type_id,
            sector_id=data.sector_id,
            status_id=data.status_id,
            description=data.description,
            serial_number=data.serial_number.strip() if data.serial_number else None,
            hostname=data.hostname.strip() if data.hostname else None,
            brand=data.brand,
            model=data.model,
            ip_address=data.ip_address,
            mac_address=data.mac_address,
            printer_identifier=data.printer_identifier,
            windows_product_key_encrypted=encrypted_windows_key,
            notes=data.notes,
        )
        try:
            self.eq_repo.create(equipment)
            self.db.commit()
            self.db.refresh(equipment)
            return equipment
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError("Conflito de unicidade ao cadastrar equipamento.") from e
        except Exception:
            self.db.rollback()
            raise


class ListEquipmentsUseCase:
    """Caso de uso para listagem paginada e filtrada de equipamentos ativos com chaves mascaradas."""

    def __init__(self, db: Session):
        self.eq_repo = EquipmentRepository(db)

    def execute(
        self,
        page: int = 1,
        limit: int = 25,
        equipment_type_ids: list[int] | int | None = None,
        sector_ids: list[int] | int | None = None,
        status_ids: list[int] | int | None = None,
        patrimony_number: list[str] | str | None = None,
        serial_number: list[str] | str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        include_deleted: bool = False,
    ) -> EquipmentListResponse:
        items, total = self.eq_repo.list_paginated_and_filtered(
            page=page,
            limit=limit,
            equipment_type_ids=equipment_type_ids,
            sector_ids=sector_ids,
            status_ids=status_ids,
            patrimony_number=patrimony_number,
            serial_number=serial_number,
            search=search,
            sort_by=sort_by,
            sort_dir=sort_dir,
            include_deleted=include_deleted,
        )
        pages = math.ceil(total / limit) if total > 0 else 1

        response_items = []
        for eq in items:
            item_dto = EquipmentListItemResponse(
                id=eq.id,
                patrimony_number=eq.patrimony_number,
                description=eq.description,
                serial_number=eq.serial_number,
                hostname=eq.hostname,
                brand=eq.brand,
                model=eq.model,
                equipment_type_id=eq.equipment_type_id,
                equipment_type=EquipmentTypeResponse.model_validate(eq.equipment_type),
                sector_id=eq.sector_id,
                sector=SectorResponse.model_validate(eq.sector),
                status_id=eq.status_id,
                status=EquipmentStatusResponse.model_validate(eq.status),
                ip_address=str(eq.ip_address) if eq.ip_address is not None else None,
                mac_address=str(eq.mac_address) if eq.mac_address is not None else None,
                printer_identifier=eq.printer_identifier,
                windows_product_key=mask_windows_product_key(eq.windows_product_key_encrypted),
                notes=eq.notes,
                created_at=eq.created_at,
                updated_at=eq.updated_at,
                deleted_at=eq.deleted_at,
            )
            response_items.append(item_dto)

        return EquipmentListResponse(
            items=response_items,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )


class GetEquipmentDetailUseCase:
    """Caso de uso para consulta detalhada de equipamento por ID com chave Windows mascarada."""

    def __init__(self, db: Session):
        self.eq_repo = EquipmentRepository(db)

    def execute(self, equipment_id: int, include_deleted: bool = False) -> EquipmentResponse:
        equipment = self.eq_repo.get_by_id(equipment_id, include_deleted=include_deleted)
        if not equipment:
            raise KeyError(f"Equipamento com ID {equipment_id} não foi encontrado.")

        movements_dto = [
            EquipmentMovementResponse(
                id=m.id,
                equipment_id=m.equipment_id,
                origin_sector_id=m.origin_sector_id,
                origin_sector=SectorResponse.model_validate(m.origin_sector)
                if m.origin_sector
                else None,
                destination_sector_id=m.destination_sector_id,
                destination_sector=SectorResponse.model_validate(m.destination_sector)
                if m.destination_sector
                else None,
                movement_date=m.movement_date,
                performed_by_user_id=m.performed_by_user_id,
                notes=m.notes,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in equipment.movements
        ]

        maintenances_dto = [
            EquipmentMaintenanceResponse(
                id=m.id,
                equipment_id=m.equipment_id,
                started_at=m.started_at,
                completed_at=m.completed_at,
                maintenance_type_id=m.maintenance_type_id,
                maintenance_type=MaintenanceTypeResponse.model_validate(m.maintenance_type)
                if m.maintenance_type
                else None,
                performed_by_user_id=m.performed_by_user_id,
                description=m.description,
                notes=m.notes,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in equipment.maintenances
        ]

        return EquipmentResponse(
            id=equipment.id,
            patrimony_number=equipment.patrimony_number,
            description=equipment.description,
            serial_number=equipment.serial_number,
            hostname=equipment.hostname,
            brand=equipment.brand,
            model=equipment.model,
            equipment_type_id=equipment.equipment_type_id,
            equipment_type=EquipmentTypeResponse.model_validate(equipment.equipment_type),
            sector_id=equipment.sector_id,
            sector=SectorResponse.model_validate(equipment.sector),
            status_id=equipment.status_id,
            status=EquipmentStatusResponse.model_validate(equipment.status),
            ip_address=str(equipment.ip_address) if equipment.ip_address is not None else None,
            mac_address=str(equipment.mac_address) if equipment.mac_address is not None else None,
            printer_identifier=equipment.printer_identifier,
            windows_product_key=mask_windows_product_key(equipment.windows_product_key_encrypted),
            notes=equipment.notes,
            created_at=equipment.created_at,
            updated_at=equipment.updated_at,
            deleted_at=equipment.deleted_at,
            movements=movements_dto,
            maintenances=maintenances_dto,
        )


class UpdateEquipmentUseCase:
    """Caso de uso para atualização de equipamentos com validação de unicidade."""

    def __init__(
        self,
        db: Session,
        eq_repo: EquipmentRepository | None = None,
        cat_repo: CatalogsRepository | None = None,
    ):
        self.db = db
        self.eq_repo = eq_repo or EquipmentRepository(db)
        self.cat_repo = cat_repo or CatalogsRepository(db)

    def execute(
        self, equipment_id: int, data: EquipmentUpdate, performed_by_user_id: int | None = None
    ) -> Equipment:
        equipment = self.eq_repo.get_by_id(equipment_id)
        if not equipment:
            raise KeyError(f"Equipamento com ID {equipment_id} não foi encontrado.")

        # Validações de catálogos se alterados
        if (
            data.equipment_type_id is not None
            and data.equipment_type_id != equipment.equipment_type_id
        ):
            c = self.cat_repo.get_by_id(EquipmentType, data.equipment_type_id)
            if not c or c.deleted_at is not None:
                raise ValueError(
                    f"Tipo de equipamento ID {data.equipment_type_id} inválido ou inativo."
                )
            equipment.equipment_type_id = data.equipment_type_id

        if data.sector_id is not None and data.sector_id != equipment.sector_id:
            c = self.cat_repo.get_by_id(Sector, data.sector_id)
            if not c or c.deleted_at is not None:
                raise ValueError(f"Setor ID {data.sector_id} inválido ou inativo.")
            origin_sector_id = equipment.sector_id
            equipment.sector_id = data.sector_id
            # ISSUE-003: Auditoria automática de alteração de setor via EquipmentMovement
            movement = EquipmentMovement(
                equipment_id=equipment.id,
                origin_sector_id=origin_sector_id,
                destination_sector_id=data.sector_id,
                movement_date=datetime.now(timezone.utc),
                performed_by_user_id=performed_by_user_id or 1,
                notes="Movimentação auditada gerada automaticamente pela alteração cadastral de setor.",
            )
            self.db.add(movement)

        if data.status_id is not None and data.status_id != equipment.status_id:
            c = self.cat_repo.get_by_id(EquipmentStatus, data.status_id)
            if not c or c.deleted_at is not None:
                raise ValueError(f"Situação patrimonial ID {data.status_id} inválida ou inativa.")
            equipment.status_id = data.status_id

        # Validações de unicidade permanente
        if (
            data.patrimony_number is not None
            and data.patrimony_number.strip().lower() != equipment.patrimony_number.lower()
        ):
            if self.eq_repo.get_by_patrimony_number(data.patrimony_number, exclude_id=equipment_id):
                raise ValueError(
                    f"Número de patrimônio '{data.patrimony_number}' já está cadastrado no sistema."
                )
            equipment.patrimony_number = data.patrimony_number.strip()

        if data.serial_number is not None:
            clean_serial = data.serial_number.strip() if data.serial_number else None
            old_serial = equipment.serial_number.lower() if equipment.serial_number else None
            new_serial = clean_serial.lower() if clean_serial else None
            if new_serial != old_serial:
                if clean_serial and self.eq_repo.get_by_serial_number(
                    clean_serial, exclude_id=equipment_id
                ):
                    raise ValueError(
                        f"Número de série '{clean_serial}' já está cadastrado no sistema."
                    )
                equipment.serial_number = clean_serial

        # Validações de unicidade ativa
        if data.hostname is not None:
            clean_host = data.hostname.strip() if data.hostname else None
            old_host = equipment.hostname.lower() if equipment.hostname else None
            new_host = clean_host.lower() if clean_host else None
            if new_host != old_host:
                if clean_host and self.eq_repo.get_active_by_hostname(
                    clean_host, exclude_id=equipment_id
                ):
                    raise ValueError(
                        f"Hostname '{clean_host}' já está em uso por outro equipamento ativo."
                    )
                equipment.hostname = clean_host

        if data.ip_address is not None:
            clean_ip = data.ip_address.strip() if data.ip_address else None
            if clean_ip != (str(equipment.ip_address) if equipment.ip_address else None):
                if clean_ip and self.eq_repo.get_active_by_ip(clean_ip, exclude_id=equipment_id):
                    raise ValueError(
                        f"Endereço IP '{clean_ip}' já está em uso por outro equipamento ativo."
                    )
                equipment.ip_address = clean_ip

        if data.mac_address is not None:
            clean_mac = data.mac_address.strip() if data.mac_address else None
            if clean_mac != (str(equipment.mac_address) if equipment.mac_address else None):
                if clean_mac and self.eq_repo.get_active_by_mac(clean_mac, exclude_id=equipment_id):
                    raise ValueError(
                        f"Endereço MAC '{clean_mac}' já está em uso por outro equipamento ativo."
                    )
                equipment.mac_address = clean_mac

        if data.printer_identifier is not None:
            clean_prn = data.printer_identifier.strip() if data.printer_identifier else None
            old_prn = equipment.printer_identifier.lower() if equipment.printer_identifier else None
            new_prn = clean_prn.lower() if clean_prn else None
            if new_prn != old_prn:
                if clean_prn and self.eq_repo.get_active_by_printer_identifier(
                    clean_prn, exclude_id=equipment_id
                ):
                    raise ValueError(
                        f"Identificador de impressora '{clean_prn}' já está em uso por outro equipamento ativo."
                    )
                equipment.printer_identifier = clean_prn

        if data.description is not None:
            equipment.description = data.description
        if data.brand is not None:
            equipment.brand = data.brand
        if data.model is not None:
            equipment.model = data.model
        if data.notes is not None:
            equipment.notes = data.notes

        if data.windows_product_key is not None:
            equipment.windows_product_key_encrypted = encrypt_windows_product_key(
                data.windows_product_key
            )

        try:
            self.db.commit()
            self.db.refresh(equipment)
            return equipment
        except StaleDataError as e:
            self.db.rollback()
            raise ConflictError(
                "O equipamento foi modificado concorrentemente por outro usuário."
            ) from e
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError("Conflito de unicidade ao atualizar equipamento.") from e
        except Exception:
            self.db.rollback()
            raise


class DeleteEquipmentUseCase:
    """Caso de uso para exclusão lógica (soft delete) de equipamento."""

    def __init__(self, db: Session, eq_repo: EquipmentRepository | None = None):
        self.db = db
        self.eq_repo = eq_repo or EquipmentRepository(db)

    def execute(self, equipment_id: int) -> None:
        equipment = self.eq_repo.get_by_id(equipment_id)
        if not equipment:
            raise KeyError(f"Equipamento com ID {equipment_id} não foi encontrado.")
        try:
            self.eq_repo.soft_delete(equipment)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise


class RestoreEquipmentUseCase:
    """Caso de uso para restauração de equipamento excluído com validação de colisão de identificadores ativos."""

    def __init__(self, db: Session, eq_repo: EquipmentRepository | None = None):
        self.db = db
        self.eq_repo = eq_repo or EquipmentRepository(db)

    def execute(self, equipment_id: int) -> Equipment:
        equipment = self.eq_repo.get_by_id(equipment_id, include_deleted=True)
        if not equipment:
            raise KeyError(f"Equipamento com ID {equipment_id} não foi encontrado.")
        if equipment.deleted_at is None:
            return equipment  # Já ativo

        # Verifica colisões nos identificadores parciais com equipamentos atualmente ativos
        conflicts = self.eq_repo.check_restoration_conflicts(equipment)
        if conflicts:
            raise ConflictError("; ".join(conflicts))

        try:
            self.eq_repo.restore(equipment)
            self.db.commit()
            self.db.refresh(equipment)
            return equipment
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError("Conflito de unicidade ao restaurar equipamento.") from e
        except Exception:
            self.db.rollback()
            raise


class GetDecryptedWindowsKeyUseCase:
    """Caso de uso para revelação da chave Windows criptografada para o técnico autenticado."""

    def __init__(self, db: Session):
        self.eq_repo = EquipmentRepository(db)

    def execute(self, equipment_id: int) -> EquipmentSecretKeyResponse:
        equipment = self.eq_repo.get_by_id(equipment_id, include_deleted=True)
        if not equipment:
            raise KeyError(f"Equipamento com ID {equipment_id} não foi encontrado.")
        decrypted = decrypt_windows_product_key(equipment.windows_product_key_encrypted)
        return EquipmentSecretKeyResponse(equipment_id=equipment_id, windows_product_key=decrypted)


class MovementsUseCase:
    """Caso de uso para encadeamento cronológico de transferências e recálculo transacional do setor."""

    def __init__(
        self,
        db: Session,
        eq_repo: EquipmentRepository | None = None,
        cat_repo: CatalogsRepository | None = None,
        mov_repo: EquipmentMovementRepository | None = None,
    ):
        self.db = db
        self.eq_repo = eq_repo or EquipmentRepository(db)
        self.cat_repo = cat_repo or CatalogsRepository(db)
        self.mov_repo = mov_repo or EquipmentMovementRepository(db)

    def _recalculate_chain(self, equipment_id: int) -> None:
        """Reordena por (movement_date ASC, id ASC), ajusta Origem[n] = Destino[n-1] e atualiza equipments.sector_id."""
        equipment = self.eq_repo.get_by_id(equipment_id, include_deleted=True)
        if not equipment:
            return

        movements = self.mov_repo.get_ordered_movements(equipment_id)
        if not movements:
            return

        # Simula o encadeamento e valida que nenhum elo resultante possua origem == destino
        simulated_origins: dict[int, int] = {}
        for i in range(1, len(movements)):
            prev_dest = movements[i - 1].destination_sector_id
            simulated_origins[i] = prev_dest

        for i, m in enumerate(movements):
            orig = simulated_origins.get(i, m.origin_sector_id)
            if orig == m.destination_sector_id:
                raise ValueError(
                    f"Ajuste da cadeia gerou transferência para o mesmo setor (ID {orig}) no movimento ID {m.id}."
                )

        # Aplica o encadeamento validado
        for i in range(1, len(movements)):
            movements[i].origin_sector_id = simulated_origins[i]

        # Atualiza transacionalmente o setor do bem para o destino da última etapa
        equipment.sector_id = movements[-1].destination_sector_id
        self.db.flush()

    def record_movement(
        self,
        equipment_id: int,
        data: EquipmentMovementCreate,
        performed_by_user_id: int,
    ) -> EquipmentMovement:
        equipment = self.eq_repo.get_by_id(equipment_id)
        if not equipment:
            raise KeyError(f"Equipamento com ID {equipment_id} não foi encontrado.")

        if data.origin_sector_id == data.destination_sector_id:
            raise ValueError("O setor de origem deve ser diferente do setor de destino.")

        # Valida tolerância de relógio (máximo 5 minutos no futuro)
        max_future = datetime.now(timezone.utc) + timedelta(minutes=5)
        mov_date = data.movement_date
        if mov_date.tzinfo is None:
            mov_date = mov_date.replace(tzinfo=timezone.utc)
        if mov_date > max_future:
            raise ValueError("Data da movimentação não pode ser futura.")

        # Valida se os setores existem
        origin = self.cat_repo.get_by_id(Sector, data.origin_sector_id)
        if not origin:
            raise ValueError(f"Setor de origem ID {data.origin_sector_id} não encontrado.")
        dest = self.cat_repo.get_by_id(Sector, data.destination_sector_id)
        if not dest:
            raise ValueError(f"Setor de destino ID {data.destination_sector_id} não encontrado.")

        movement = EquipmentMovement(
            equipment_id=equipment_id,
            origin_sector_id=data.origin_sector_id,
            destination_sector_id=data.destination_sector_id,
            movement_date=mov_date,
            performed_by_user_id=performed_by_user_id,
            notes=data.notes,
        )
        try:
            self.mov_repo.create(movement)
            self.db.flush()

            # Recalcula e auto-ajusta a cadeia
            self._recalculate_chain(equipment_id)
            self.db.commit()
            self.db.refresh(movement)
            return movement
        except Exception:
            self.db.rollback()
            raise

    def update_movement(
        self,
        equipment_id: int,
        movement_id: int,
        data: EquipmentMovementUpdate,
    ) -> EquipmentMovement:
        movement = self.mov_repo.get_by_id(movement_id)
        if not movement or movement.equipment_id != equipment_id:
            raise KeyError(
                f"Movimentação ID {movement_id} não encontrada para o equipamento ID {equipment_id}."
            )

        old_origin = movement.origin_sector_id
        old_dest = movement.destination_sector_id
        old_date = movement.movement_date
        old_notes = movement.notes

        if data.origin_sector_id is not None:
            movement.origin_sector_id = data.origin_sector_id
        if data.destination_sector_id is not None:
            movement.destination_sector_id = data.destination_sector_id
        if data.movement_date is not None:
            mov_date = data.movement_date
            if mov_date.tzinfo is None:
                mov_date = mov_date.replace(tzinfo=timezone.utc)
            max_future = datetime.now(timezone.utc) + timedelta(minutes=5)
            if mov_date > max_future:
                raise ValueError("Data da movimentação não pode ser futura.")
            movement.movement_date = mov_date
        if data.notes is not None:
            movement.notes = data.notes

        if movement.origin_sector_id == movement.destination_sector_id:
            movement.origin_sector_id = old_origin
            movement.destination_sector_id = old_dest
            movement.movement_date = old_date
            movement.notes = old_notes
            raise ValueError("O setor de origem deve ser diferente do setor de destino.")

        try:
            self.db.flush()
            self._recalculate_chain(equipment_id)
            self.db.commit()
            self.db.refresh(movement)
            return movement
        except Exception:
            movement.origin_sector_id = old_origin
            movement.destination_sector_id = old_dest
            movement.movement_date = old_date
            movement.notes = old_notes
            self.db.rollback()
            raise


class MaintenancesUseCase:
    """Caso de uso para ciclo de vida de manutenções e transições de situação patrimonial."""

    def __init__(
        self,
        db: Session,
        eq_repo: EquipmentRepository | None = None,
        cat_repo: CatalogsRepository | None = None,
        maint_repo: EquipmentMaintenanceRepository | None = None,
    ):
        self.db = db
        self.eq_repo = eq_repo or EquipmentRepository(db)
        self.cat_repo = cat_repo or CatalogsRepository(db)
        self.maint_repo = maint_repo or EquipmentMaintenanceRepository(db)

    def start_maintenance(
        self,
        equipment_id: int,
        data: EquipmentMaintenanceStart,
        performed_by_user_id: int | None,
    ) -> EquipmentMaintenance:
        equipment = self.eq_repo.get_by_id(equipment_id)
        if not equipment:
            raise KeyError(f"Equipamento com ID {equipment_id} não foi encontrado.")

        # Verifica se já existe manutenção aberta
        open_maint = self.maint_repo.get_open_maintenance(equipment_id)
        if open_maint:
            raise ConflictError("Já existe uma manutenção em andamento para este equipamento.")

        maint_type = self.cat_repo.get_by_id(MaintenanceType, data.maintenance_type_id)
        if not maint_type or maint_type.deleted_at is not None:
            raise ValueError(
                f"Tipo de manutenção ID {data.maintenance_type_id} inválido ou inativo."
            )

        # Localiza o status "Em manutenção"
        in_maint_status = self.cat_repo.get_by_name_lower(EquipmentStatus, "Em manutenção")
        if not in_maint_status:
            # Cria se não existir (para resiliência)
            in_maint_status = EquipmentStatus(name="Em manutenção")
            self.cat_repo.create(in_maint_status)
            self.db.flush()

        started_at = data.started_at or datetime.now(timezone.utc)
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)

        maintenance = EquipmentMaintenance(
            equipment_id=equipment_id,
            maintenance_type_id=data.maintenance_type_id,
            started_at=started_at,
            performed_by_user_id=performed_by_user_id,
            description=data.description,
            notes=data.notes,
        )
        try:
            self.maint_repo.create(maintenance)
            # Transição automática da situação do bem
            equipment.status_id = in_maint_status.id
            self.db.commit()
            self.db.refresh(maintenance)
            return maintenance
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError(
                "Já existe uma manutenção em andamento para este equipamento."
            ) from e
        except Exception:
            self.db.rollback()
            raise

    def complete_maintenance(
        self,
        equipment_id: int,
        maintenance_id: int,
        data: EquipmentMaintenanceComplete,
    ) -> EquipmentMaintenance:
        equipment = self.eq_repo.get_by_id(equipment_id)
        if not equipment:
            raise KeyError(f"Equipamento com ID {equipment_id} não foi encontrado.")

        maintenance = self.maint_repo.get_by_id(maintenance_id)
        if not maintenance or maintenance.equipment_id != equipment_id:
            raise KeyError(
                f"Manutenção ID {maintenance_id} não foi encontrada para este equipamento."
            )

        if maintenance.completed_at is not None:
            raise ValueError("Esta manutenção já foi concluída anteriormente.")

        completed_at = data.completed_at or datetime.now(timezone.utc)
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=timezone.utc)

        started_at = maintenance.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)

        if completed_at < started_at:
            raise ValueError(
                "A data/hora de conclusão não pode ser anterior ao início da manutenção."
            )

        new_status = self.cat_repo.get_by_id(EquipmentStatus, data.new_status_id)
        if not new_status or new_status.deleted_at is not None:
            raise ValueError(f"Nova situação ID {data.new_status_id} inválida ou inativa.")

        if new_status.name.lower() == "em manutenção":
            raise ValueError("A situação de conclusão do equipamento não pode ser 'Em manutenção'.")

        maintenance.completed_at = completed_at
        if data.description is not None:
            maintenance.description = data.description
        if data.notes is not None:
            maintenance.notes = data.notes

        try:
            # Atualiza a nova situação patrimonial do equipamento
            equipment.status_id = data.new_status_id
            self.db.commit()
            self.db.refresh(maintenance)
            return maintenance
        except Exception:
            self.db.rollback()
            raise

    def update_maintenance(
        self,
        equipment_id: int,
        maintenance_id: int,
        data: EquipmentMaintenanceUpdate,
    ) -> EquipmentMaintenance:
        maintenance = self.maint_repo.get_by_id(maintenance_id)
        if not maintenance or maintenance.equipment_id != equipment_id:
            raise KeyError(
                f"Manutenção ID {maintenance_id} não foi encontrada para este equipamento."
            )

        if data.maintenance_type_id is not None:
            mt = self.cat_repo.get_by_id(MaintenanceType, data.maintenance_type_id)
            if not mt or mt.deleted_at is not None:
                raise ValueError(f"Tipo de manutenção ID {data.maintenance_type_id} inválido.")
            maintenance.maintenance_type_id = data.maintenance_type_id

        new_start = data.started_at or maintenance.started_at
        new_complete = (
            data.completed_at if data.completed_at is not None else maintenance.completed_at
        )

        if new_start and new_start.tzinfo is None:
            new_start = new_start.replace(tzinfo=timezone.utc)
        if new_complete and new_complete.tzinfo is None:
            new_complete = new_complete.replace(tzinfo=timezone.utc)

        if new_complete is not None and new_complete < new_start:
            raise ValueError("A conclusão não pode ser anterior ao início da manutenção.")

        if data.started_at is not None:
            maintenance.started_at = new_start
        if data.completed_at is not None:
            maintenance.completed_at = new_complete
        if data.description is not None:
            maintenance.description = data.description
        if data.notes is not None:
            maintenance.notes = data.notes

        try:
            self.db.commit()
            self.db.refresh(maintenance)
            return maintenance
        except Exception:
            self.db.rollback()
            raise


class GetSuggestionsUseCase:
    """Caso de uso para buscar sugestões de autocomplete em bens ativos por prefixo."""

    ALLOWED_FIELDS = {"patrimony_number", "serial_number", "model"}

    def __init__(self, db: Session):
        self.repo = EquipmentRepository(db)

    def execute(self, field: str, prefix: str, limit: int = 10) -> list[str]:
        if not field or field not in self.ALLOWED_FIELDS:
            raise ValueError(
                f"Campo inválido para sugestão: '{field}'. Campos permitidos: {', '.join(sorted(self.ALLOWED_FIELDS))}."
            )

        clean_prefix = prefix.strip() if prefix else ""
        if len(clean_prefix) < 2:
            raise ValueError("O prefixo de busca deve conter pelo menos 2 caracteres.")

        eff_limit = max(1, min(limit, 50))
        return self.repo.get_distinct_values_by_prefix(
            field_name=field,
            prefix=clean_prefix,
            limit=eff_limit,
        )


class ExportEquipmentsUseCase:
    """Caso de uso para exportação de equipamentos em planilha Excel (.xlsx) estilizada."""

    def __init__(self, db: Session):
        self.repo = EquipmentRepository(db)

    def execute(
        self,
        equipment_type_ids: list[int] | int | None = None,
        sector_ids: list[int] | int | None = None,
        status_ids: list[int] | int | None = None,
        patrimony_number: list[str] | str | None = None,
        serial_number: list[str] | str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> tuple[bytes, str]:
        equipments = self.repo.list_all_filtered(
            equipment_type_ids=equipment_type_ids,
            sector_ids=sector_ids,
            status_ids=status_ids,
            patrimony_number=patrimony_number,
            serial_number=serial_number,
            search=search,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

        excel_bytes = generate_equipments_excel(equipments)
        now_str = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"PATRIMONIO_{now_str}.xlsx"
        return excel_bytes, filename
