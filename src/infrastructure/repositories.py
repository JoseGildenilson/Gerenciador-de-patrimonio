"""Repositórios SQLAlchemy para persistência de dados.

Nota: Em cumprimento à Constituição, os repositórios NÃO executam commit ou rollback.
O controle de transação é feito no nível do caso de uso ou rota HTTP.
"""

from datetime import datetime, timedelta, timezone
from typing import Type, TypeVar
from sqlalchemy import select, update, func, or_, desc, asc
from sqlalchemy.orm import Session, selectinload
from src.domain.models import (
    User,
    LoginAttempt,
    Equipment,
    EquipmentType,
    Sector,
    EquipmentStatus,
    MaintenanceType,
    EquipmentMovement,
    EquipmentMaintenance,
    Location,
    Category,
    Asset,
    PatrimonyHistory,
    AssetMovement,
    AssetMaintenance,
)

T = TypeVar("T", EquipmentType, Sector, EquipmentStatus, MaintenanceType)


class CatalogsRepository:
    """Repositório genérico para gerenciamento dos 4 catálogos estruturais."""

    def __init__(self, db: Session):
        self.db = db

    def list_active(self, model_class: Type[T]) -> list[T]:
        """Retorna itens ativos do catálogo (deleted_at IS NULL) ordenados por nome."""
        stmt = (
            select(model_class)
            .where(model_class.deleted_at.is_(None))
            .order_by(asc(model_class.name))
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_all(self, model_class: Type[T]) -> list[T]:
        """Retorna todos os itens do catálogo, incluindo logicamente excluídos."""
        stmt = select(model_class).order_by(asc(model_class.name))
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, model_class: Type[T], item_id: int) -> T | None:
        """Busca item por ID."""
        stmt = select(model_class).where(model_class.id == item_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name_lower(self, model_class: Type[T], name: str) -> T | None:
        """Busca item do catálogo de forma case-insensitive."""
        stmt = select(model_class).where(func.lower(model_class.name) == name.strip().lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, item: T) -> T:
        """Adiciona novo item do catálogo à sessão (sem commit)."""
        self.db.add(item)
        return item

    def update(self, item: T, new_name: str) -> T:
        """Atualiza o nome de um item de catálogo."""
        item.name = new_name.strip()
        return item

    def soft_delete(self, item: T) -> T:
        """Marca o item como excluído logicamente."""
        item.deleted_at = datetime.now(timezone.utc)
        return item

    def restore(self, item: T) -> T:
        """Restaura item logicamente excluído."""
        item.deleted_at = None
        return item


class DashboardRepository:
    """Repositório para consulta de métricas patrimoniais do Dashboard."""

    def __init__(self, db: Session):
        self.db = db

    def get_metrics(self) -> dict:
        """Calcula os indicadores patrimoniais para equipamentos ativos (deleted_at IS NULL)."""
        # Total de equipamentos ativos
        total_stmt = select(func.count(Equipment.id)).where(Equipment.deleted_at.is_(None))
        equipments_total = self.db.execute(total_stmt).scalar() or 0

        # Contagem por Situação
        status_stmt = (
            select(EquipmentStatus.name, func.count(Equipment.id))
            .join(Equipment, Equipment.status_id == EquipmentStatus.id)
            .where(Equipment.deleted_at.is_(None))
            .group_by(EquipmentStatus.name)
        )
        by_status = dict(self.db.execute(status_stmt).all())

        # Contagem por Tipo
        type_stmt = (
            select(EquipmentType.name, func.count(Equipment.id))
            .join(Equipment, Equipment.equipment_type_id == EquipmentType.id)
            .where(Equipment.deleted_at.is_(None))
            .group_by(EquipmentType.name)
        )
        by_type = dict(self.db.execute(type_stmt).all())

        # Contagem por Setor
        sector_stmt = (
            select(Sector.name, func.count(Equipment.id))
            .join(Equipment, Equipment.sector_id == Sector.id)
            .where(Equipment.deleted_at.is_(None))
            .group_by(Sector.name)
        )
        by_sector = dict(self.db.execute(sector_stmt).all())

        # Contagens rápidas
        equipments_in_maintenance = by_status.get("Em manutenção", 0)
        equipments_in_use = by_status.get("Em uso", 0)
        equipments_idle = by_status.get("Ocioso", 0)

        return {
            "equipments_total": equipments_total,
            "equipments_in_maintenance": equipments_in_maintenance,
            "equipments_in_use": equipments_in_use,
            "equipments_idle": equipments_idle,
            "by_status": by_status,
            "by_type": by_type,
            "by_sector": by_sector,
        }


class UserRepository:
    """Repositório de acesso a dados da entidade User."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str, include_deleted: bool = False) -> User | None:
        """Busca usuário por email (case-insensitive)."""
        stmt = select(User).where(func.lower(User.email) == email.strip().lower())
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, user_id: int, include_deleted: bool = False) -> User | None:
        """Busca usuário por ID."""
        stmt = select(User).where(User.id == user_id)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, user: User) -> User:
        """Adiciona novo usuário à sessão (sem commit)."""
        self.db.add(user)
        return user

    def soft_delete(self, user: User) -> User:
        """Exclui logicamente o usuário."""
        user.deleted_at = datetime.now(timezone.utc)
        return user

    def restore(self, user: User) -> User:
        """Restaura usuário logicamente excluído."""
        user.deleted_at = None
        return user


class LoginAttemptRepository:
    """Repositório de registro e contagem de tentativas de login por IP e e-mail."""

    def __init__(self, db: Session):
        self.db = db

    def count_recent_failed_attempts(self, ip_address: str, window_minutes: int = 15) -> int:
        """Conta tentativas malsucedidas de um IP na janela de tempo especificada."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        stmt = select(func.count(LoginAttempt.id)).where(
            LoginAttempt.ip_address == ip_address,
            LoginAttempt.success.is_(False),
            LoginAttempt.attempted_at >= cutoff_time,
        )
        count = self.db.execute(stmt).scalar()
        return count or 0

    def count_recent_failed_attempts_by_email(self, email: str, window_minutes: int = 15) -> int:
        """Conta tentativas malsucedidas de um email na janela de tempo especificada (ISSUE-007)."""
        if not email:
            return 0
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        stmt = select(func.count(LoginAttempt.id)).where(
            func.lower(LoginAttempt.email_attempted) == email.lower().strip(),
            LoginAttempt.success.is_(False),
            LoginAttempt.attempted_at >= cutoff_time,
        )
        count = self.db.execute(stmt).scalar()
        return count or 0

    def record_attempt(self, ip_address: str, email_attempted: str, success: bool) -> LoginAttempt:
        """Registra uma nova tentativa de login com IP e email informado (sem commit)."""
        attempt = LoginAttempt(
            ip_address=ip_address,
            email_attempted=email_attempted,
            success=success,
            attempted_at=datetime.now(timezone.utc),
        )
        self.db.add(attempt)
        return attempt


class EquipmentRepository:
    """Repositório de persistência e consulta da entidade Equipment."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, equipment_id: int, include_deleted: bool = False) -> Equipment | None:
        """Busca equipamento por ID com relacionamentos carregados."""
        stmt = (
            select(Equipment)
            .options(
                selectinload(Equipment.equipment_type),
                selectinload(Equipment.sector),
                selectinload(Equipment.status),
                selectinload(Equipment.movements).selectinload(EquipmentMovement.origin_sector),
                selectinload(Equipment.movements).selectinload(
                    EquipmentMovement.destination_sector
                ),
                selectinload(Equipment.maintenances).selectinload(
                    EquipmentMaintenance.maintenance_type
                ),
            )
            .where(Equipment.id == equipment_id)
        )
        if not include_deleted:
            stmt = stmt.where(Equipment.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_patrimony_number(
        self, patrimony_number: str, exclude_id: int | None = None, include_deleted: bool = True
    ) -> Equipment | None:
        """Busca equipamento por Nº de Patrimônio (case-insensitive permanente, inclusive excluídos por padrão)."""
        if not patrimony_number or not str(patrimony_number).strip():
            return None
        stmt = select(Equipment).where(
            func.lower(Equipment.patrimony_number) == str(patrimony_number).strip().lower()
        )
        if not include_deleted:
            stmt = stmt.where(Equipment.deleted_at.is_(None))
        if exclude_id is not None:
            stmt = stmt.where(Equipment.id != exclude_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_serial_number(
        self, serial_number: str, exclude_id: int | None = None, include_deleted: bool = True
    ) -> Equipment | None:
        """Busca equipamento por Nº de Série (case-insensitive permanente onde não nulo)."""
        if not serial_number or not str(serial_number).strip():
            return None
        stmt = select(Equipment).where(
            func.lower(Equipment.serial_number) == str(serial_number).strip().lower()
        )
        if not include_deleted:
            stmt = stmt.where(Equipment.deleted_at.is_(None))
        if exclude_id is not None:
            stmt = stmt.where(Equipment.id != exclude_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_active_by_hostname(
        self, hostname: str, exclude_id: int | None = None
    ) -> Equipment | None:
        """Busca por hostname ativo (case-insensitive apenas entre bens não excluídos)."""
        if not hostname or not str(hostname).strip():
            return None
        stmt = select(Equipment).where(
            Equipment.deleted_at.is_(None),
            func.lower(Equipment.hostname) == str(hostname).strip().lower(),
        )
        if exclude_id is not None:
            stmt = stmt.where(Equipment.id != exclude_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_hostname(
        self, hostname: str | None, exclude_id: int | None = None
    ) -> Equipment | None:
        """Busca equipamento ativo por Hostname (compatibilidade)."""
        if not hostname or not str(hostname).strip():
            return None
        return self.get_active_by_hostname(str(hostname), exclude_id=exclude_id)

    def get_active_by_ip(self, ip_address: str, exclude_id: int | None = None) -> Equipment | None:
        """Busca por IP ativo (apenas entre bens não excluídos)."""
        if not ip_address or not ip_address.strip():
            return None
        stmt = select(Equipment).where(
            Equipment.deleted_at.is_(None),
            Equipment.ip_address == ip_address.strip(),
        )
        if exclude_id is not None:
            stmt = stmt.where(Equipment.id != exclude_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_active_by_mac(
        self, mac_address: str, exclude_id: int | None = None
    ) -> Equipment | None:
        """Busca por MAC ativo (apenas entre bens não excluídos)."""
        if not mac_address or not mac_address.strip():
            return None
        stmt = select(Equipment).where(
            Equipment.deleted_at.is_(None),
            Equipment.mac_address == mac_address.strip(),
        )
        if exclude_id is not None:
            stmt = stmt.where(Equipment.id != exclude_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_active_by_printer_identifier(
        self, printer_identifier: str, exclude_id: int | None = None
    ) -> Equipment | None:
        """Busca por identificador de impressora ativo (case-insensitive apenas entre ativos)."""
        if not printer_identifier or not printer_identifier.strip():
            return None
        stmt = select(Equipment).where(
            Equipment.deleted_at.is_(None),
            func.lower(Equipment.printer_identifier) == printer_identifier.strip().lower(),
        )
        if exclude_id is not None:
            stmt = stmt.where(Equipment.id != exclude_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def check_restoration_conflicts(self, equipment: Equipment) -> list[str]:
        """Verifica se algum identificador único de bem ativo colide com o bem a ser restaurado."""
        conflicts = []
        if equipment.hostname:
            c = self.get_active_by_hostname(equipment.hostname, exclude_id=equipment.id)
            if c:
                conflicts.append(
                    f"Hostname '{equipment.hostname}' já está em uso pelo equipamento ativo ID {c.id}."
                )
        if equipment.ip_address:
            c = self.get_active_by_ip(str(equipment.ip_address), exclude_id=equipment.id)
            if c:
                conflicts.append(
                    f"Endereço IP '{equipment.ip_address}' já está em uso pelo equipamento ativo ID {c.id}."
                )
        if equipment.mac_address:
            c = self.get_active_by_mac(str(equipment.mac_address), exclude_id=equipment.id)
            if c:
                conflicts.append(
                    f"Endereço MAC '{equipment.mac_address}' já está em uso pelo equipamento ativo ID {c.id}."
                )
        if equipment.printer_identifier:
            c = self.get_active_by_printer_identifier(
                equipment.printer_identifier, exclude_id=equipment.id
            )
            if c:
                conflicts.append(
                    f"Identificador de impressora '{equipment.printer_identifier}' já está em uso pelo equipamento ativo ID {c.id}."
                )
        return conflicts

    def _build_filter_query(
        self,
        equipment_type_ids: list[int] | int | None = None,
        sector_ids: list[int] | int | None = None,
        status_ids: list[int] | int | None = None,
        patrimony_number: list[str] | str | None = None,
        serial_number: list[str] | str | None = None,
        search: str | None = None,
        include_deleted: bool = False,
    ):
        query = select(Equipment).options(
            selectinload(Equipment.equipment_type),
            selectinload(Equipment.sector),
            selectinload(Equipment.status),
        )

        if not include_deleted:
            query = query.where(Equipment.deleted_at.is_(None))

        def normalize_int_list(val: list[int] | int | None) -> list[int]:
            if val is None:
                return []
            if isinstance(val, list):
                return [int(v) for v in val if v is not None]
            return [int(val)]

        def normalize_str_list(val: list[str] | str | None) -> list[str]:
            if val is None:
                return []
            if isinstance(val, list):
                return [v.strip() for v in val if v and v.strip()]
            return [val.strip()] if val and val.strip() else []

        types = normalize_int_list(equipment_type_ids)
        if types:
            query = query.where(Equipment.equipment_type_id.in_(types))

        sectors = normalize_int_list(sector_ids)
        if sectors:
            query = query.where(Equipment.sector_id.in_(sectors))

        statuses = normalize_int_list(status_ids)
        if statuses:
            query = query.where(Equipment.status_id.in_(statuses))

        patrimonies = normalize_str_list(patrimony_number)
        if patrimonies:
            query = query.where(
                or_(*[Equipment.patrimony_number.ilike(f"%{p}%") for p in patrimonies])
            )

        serials = normalize_str_list(serial_number)
        if serials:
            query = query.where(or_(*[Equipment.serial_number.ilike(f"%{s}%") for s in serials]))

        if search and search.strip():
            pat = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Equipment.description.ilike(pat),
                    Equipment.brand.ilike(pat),
                    Equipment.model.ilike(pat),
                    Equipment.patrimony_number.ilike(pat),
                    Equipment.serial_number.ilike(pat),
                    Equipment.hostname.ilike(pat),
                    Equipment.printer_identifier.ilike(pat),
                    Equipment.notes.ilike(pat),
                )
            )

        return query

    def list_paginated_and_filtered(
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
    ) -> tuple[list[Equipment], int]:
        """Retorna equipamentos paginados e filtrados com contagem total."""
        query = self._build_filter_query(
            equipment_type_ids=equipment_type_ids,
            sector_ids=sector_ids,
            status_ids=status_ids,
            patrimony_number=patrimony_number,
            serial_number=serial_number,
            search=search,
            include_deleted=include_deleted,
        )

        count_stmt = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_stmt).scalar() or 0

        sort_column = getattr(Equipment, sort_by, Equipment.created_at)
        if sort_dir.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        items = list(self.db.execute(query).scalars().all())
        return items, total

    def list_all_filtered(
        self,
        equipment_type_ids: list[int] | int | None = None,
        sector_ids: list[int] | int | None = None,
        status_ids: list[int] | int | None = None,
        patrimony_number: list[str] | str | None = None,
        serial_number: list[str] | str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        include_deleted: bool = False,
    ) -> list[Equipment]:
        """Retorna todos os equipamentos filtrados sem paginação com relacionamentos e manutenções."""
        query = self._build_filter_query(
            equipment_type_ids=equipment_type_ids,
            sector_ids=sector_ids,
            status_ids=status_ids,
            patrimony_number=patrimony_number,
            serial_number=serial_number,
            search=search,
            include_deleted=include_deleted,
        ).options(
            selectinload(Equipment.maintenances).selectinload(
                EquipmentMaintenance.maintenance_type
            ),
            selectinload(Equipment.movements),
        )

        sort_column = getattr(Equipment, sort_by, Equipment.created_at)
        if sort_dir.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        return list(self.db.execute(query).scalars().all())

    def create(self, equipment: Equipment) -> Equipment:
        """Adiciona novo equipamento à sessão."""
        self.db.add(equipment)
        return equipment

    def soft_delete(self, equipment: Equipment) -> Equipment:
        """Aplica soft delete no equipamento."""
        equipment.deleted_at = datetime.now(timezone.utc)
        return equipment

    def restore(self, equipment: Equipment) -> Equipment:
        """Restaura equipamento logicamente excluído."""
        equipment.deleted_at = None
        return equipment

    def get_distinct_values_by_prefix(
        self,
        field_name: str,
        prefix: str,
        limit: int = 10,
    ) -> list[str]:
        """Retorna valores distintos ordenados filtrados por prefixo em bens ativos."""
        column = getattr(Equipment, field_name, None)
        if column is None:
            return []

        stmt = (
            select(column)
            .where(
                Equipment.deleted_at.is_(None),
                column.is_not(None),
                column.ilike(f"{prefix}%"),
            )
            .distinct()
            .order_by(asc(column))
            .limit(limit)
        )
        results = self.db.execute(stmt).scalars().all()
        return [str(r) for r in results if r]


class EquipmentMovementRepository:
    """Repositório de histórico de transferências/movimentações."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, movement: EquipmentMovement) -> EquipmentMovement:
        """Adiciona movimentação à sessão."""
        self.db.add(movement)
        return movement

    def get_by_id(self, movement_id: int) -> EquipmentMovement | None:
        """Busca movimentação por ID com setores carregados."""
        stmt = (
            select(EquipmentMovement)
            .options(
                selectinload(EquipmentMovement.origin_sector),
                selectinload(EquipmentMovement.destination_sector),
                selectinload(EquipmentMovement.performed_by_user),
            )
            .where(EquipmentMovement.id == movement_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_ordered_movements(self, equipment_id: int) -> list[EquipmentMovement]:
        """Retorna o histórico cronológico de transferências ordenado estritamente por (movement_date ASC, id ASC)."""
        stmt = (
            select(EquipmentMovement)
            .options(
                selectinload(EquipmentMovement.origin_sector),
                selectinload(EquipmentMovement.destination_sector),
            )
            .where(EquipmentMovement.equipment_id == equipment_id)
            .order_by(asc(EquipmentMovement.movement_date), asc(EquipmentMovement.id))
        )
        return list(self.db.execute(stmt).scalars().all())


class EquipmentMaintenanceRepository:
    """Repositório de histórico e ciclo de vida de manutenção."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, maintenance: EquipmentMaintenance) -> EquipmentMaintenance:
        """Adiciona nova manutenção à sessão."""
        self.db.add(maintenance)
        return maintenance

    def get_by_id(self, maintenance_id: int) -> EquipmentMaintenance | None:
        """Busca manutenção por ID."""
        stmt = (
            select(EquipmentMaintenance)
            .options(
                selectinload(EquipmentMaintenance.maintenance_type),
                selectinload(EquipmentMaintenance.performed_by_user),
            )
            .where(EquipmentMaintenance.id == maintenance_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_open_maintenance(self, equipment_id: int) -> EquipmentMaintenance | None:
        """Retorna a manutenção em andamento (completed_at IS NULL) se existir."""
        stmt = select(EquipmentMaintenance).where(
            EquipmentMaintenance.equipment_id == equipment_id,
            EquipmentMaintenance.completed_at.is_(None),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_equipment(self, equipment_id: int) -> list[EquipmentMaintenance]:
        """Retorna manutenções do equipamento ordenadas da mais recente para a mais antiga."""
        stmt = (
            select(EquipmentMaintenance)
            .options(
                selectinload(EquipmentMaintenance.maintenance_type),
                selectinload(EquipmentMaintenance.performed_by_user),
            )
            .where(EquipmentMaintenance.equipment_id == equipment_id)
            .order_by(desc(EquipmentMaintenance.started_at))
        )
        return list(self.db.execute(stmt).scalars().all())


# --- Repositórios do Modelo SisPatrimonio ---


class CategoryRepository:
    """Repositório de acesso a dados da entidade Category."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, category_id: int) -> Category | None:
        stmt = select(Category).where(Category.id == category_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, name: str) -> Category | None:
        stmt = select(Category).where(func.lower(Category.name) == name.strip().lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[Category]:
        stmt = select(Category).order_by(asc(Category.name))
        return list(self.db.execute(stmt).scalars().all())

    def create(self, category: Category) -> Category:
        self.db.add(category)
        return category


class LocationRepository:
    """Repositório de acesso a dados da entidade Location."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, location_id: int) -> Location | None:
        stmt = select(Location).where(Location.id == location_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_physical_space(
        self, building: str, floor: str, sector: str, room_number: str | None = None
    ) -> Location | None:
        stmt = select(Location).where(
            func.lower(Location.building) == building.strip().lower(),
            func.lower(Location.floor) == floor.strip().lower(),
            func.lower(Location.sector) == sector.strip().lower(),
        )
        if room_number is None:
            stmt = stmt.where(Location.room_number.is_(None))
        else:
            stmt = stmt.where(func.lower(Location.room_number) == room_number.strip().lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self, building: str | None = None, sector: str | None = None) -> list[Location]:
        stmt = select(Location)
        if building:
            stmt = stmt.where(func.lower(Location.building) == building.strip().lower())
        if sector:
            stmt = stmt.where(func.lower(Location.sector) == sector.strip().lower())
        stmt = stmt.order_by(asc(Location.building), asc(Location.floor), asc(Location.sector))
        return list(self.db.execute(stmt).scalars().all())

    def create(self, location: Location) -> Location:
        self.db.add(location)
        return location


class AssetRepository:
    """Repositório de acesso a dados da entidade Asset."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self, asset_id: int, include_deleted: bool = False, eager_history: bool = False
    ) -> Asset | None:
        stmt = select(Asset).where(Asset.id == asset_id)
        if not include_deleted:
            stmt = stmt.where(Asset.deleted_at.is_(None))
        if eager_history:
            stmt = stmt.options(selectinload(Asset.patrimony_histories))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_patrimony_number(
        self, patrimony_number: str, include_deleted: bool = False
    ) -> Asset | None:
        stmt = select(Asset).where(
            func.lower(Asset.patrimony_number) == patrimony_number.strip().lower()
        )
        if not include_deleted:
            stmt = stmt.where(Asset.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_serial_number(
        self, serial_number: str, include_deleted: bool = False
    ) -> Asset | None:
        stmt = select(Asset).where(func.lower(Asset.serial_number) == serial_number.strip().lower())
        if not include_deleted:
            stmt = stmt.where(Asset.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def list(
        self,
        category_id: int | None = None,
        location_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 25,
    ) -> tuple[list[Asset], int]:
        stmt = select(Asset).where(Asset.deleted_at.is_(None))

        if category_id is not None:
            stmt = stmt.where(Asset.category_id == category_id)
        if location_id is not None:
            stmt = stmt.where(Asset.location_id == location_id)
        if status is not None:
            stmt = stmt.where(Asset.status == status)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Asset.patrimony_number.ilike(term),
                    Asset.serial_number.ilike(term),
                    Asset.description.ilike(term),
                    Asset.brand.ilike(term),
                    Asset.model.ilike(term),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        offset = max(0, (page - 1) * limit)
        stmt = stmt.order_by(desc(Asset.created_at)).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def create(self, asset: Asset) -> Asset:
        self.db.add(asset)
        return asset

    def soft_delete(self, asset: Asset) -> Asset:
        asset.deleted_at = datetime.now(timezone.utc)
        return asset


class PatrimonyHistoryRepository:
    """Repositório para histórico imutável de renumeração de patrimônio."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, history: PatrimonyHistory) -> PatrimonyHistory:
        self.db.add(history)
        return history

    def list_by_asset(self, asset_id: int) -> list[PatrimonyHistory]:
        stmt = (
            select(PatrimonyHistory)
            .where(PatrimonyHistory.asset_id == asset_id)
            .order_by(desc(PatrimonyHistory.changed_at))
        )
        return list(self.db.execute(stmt).scalars().all())


class AssetMovementRepository:
    """Repositório para movimentações físicas e transferências de custódia."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, movement: AssetMovement) -> AssetMovement:
        self.db.add(movement)
        return movement

    def get_by_id(self, movement_id: int) -> AssetMovement | None:
        stmt = select(AssetMovement).where(AssetMovement.id == movement_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_asset(self, asset_id: int) -> list[AssetMovement]:
        stmt = (
            select(AssetMovement)
            .where(AssetMovement.asset_id == asset_id)
            .order_by(desc(AssetMovement.movement_date))
        )
        return list(self.db.execute(stmt).scalars().all())


class AssetMaintenanceRepository:
    """Repositório para manutenções preventivas e corretivas de ativos."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, maintenance: AssetMaintenance) -> AssetMaintenance:
        self.db.add(maintenance)
        return maintenance

    def get_by_id(self, maintenance_id: int) -> AssetMaintenance | None:
        stmt = select(AssetMaintenance).where(AssetMaintenance.id == maintenance_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_asset(self, asset_id: int) -> list[AssetMaintenance]:
        stmt = (
            select(AssetMaintenance)
            .where(AssetMaintenance.asset_id == asset_id)
            .order_by(desc(AssetMaintenance.maintenance_date))
        )
        return list(self.db.execute(stmt).scalars().all())
