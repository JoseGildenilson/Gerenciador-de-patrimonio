"""Repositórios SQLAlchemy para persistência de dados.

Nota: Em cumprimento à Constituição, os repositórios NÃO executam commit ou rollback.
O controle de transação é feito no nível do caso de uso ou rota HTTP.
"""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.orm import Session, selectinload, joinedload, load_only
from src.domain.models import (
    User,
    Location,
    Category,
    Asset,
    PatrimonyHistory,
    AssetMovement,
    AssetMaintenance,
)


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

    def get_by_id(
        self, user_id: int, include_deleted: bool = False, load_full: bool = False
    ) -> User | None:
        """Busca usuário por ID (com load_only por padrão para não carregar hash de senha)."""
        stmt = select(User).where(User.id == user_id)
        if not load_full:
            stmt = stmt.options(
                load_only(
                    User.id,
                    User.name,
                    User.email,
                    User.role,
                    User.is_active,
                    User.deleted_at,
                    User.created_at,
                    User.updated_at,
                )
            )
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def list_active(self) -> list[User]:
        """Lista usuários ativos e não deletados ordenados por nome."""
        stmt = (
            select(User)
            .where(User.deleted_at.is_(None), User.is_active.is_(True))
            .order_by(asc(User.name))
        )
        return list(self.db.execute(stmt).scalars().all())

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


class DashboardRepository:
    """Repositório para agregação de indicadores e métricas patrimoniais."""

    def __init__(self, db: Session):
        self.db = db

    def get_metrics(self) -> dict:
        total_stmt = select(func.count(Asset.id)).where(Asset.deleted_at.is_(None))
        assets_total = self.db.execute(total_stmt).scalar() or 0

        status_stmt = (
            select(Asset.status, func.count(Asset.id))
            .where(Asset.deleted_at.is_(None))
            .group_by(Asset.status)
        )
        by_status = dict(self.db.execute(status_stmt).all())

        cat_stmt = (
            select(Category.name, func.count(Asset.id))
            .join(Category, Asset.category_id == Category.id)
            .where(Asset.deleted_at.is_(None))
            .group_by(Category.name)
        )
        by_type = dict(self.db.execute(cat_stmt).all())

        loc_stmt = (
            select(Location.sector, func.count(Asset.id))
            .join(Location, Asset.location_id == Location.id)
            .where(Asset.deleted_at.is_(None))
            .group_by(Location.sector)
        )
        by_sector = dict(self.db.execute(loc_stmt).all())

        assets_in_maintenance = by_status.get("em_manutencao", 0)
        assets_in_use = by_status.get("em_uso", 0)
        assets_available = by_status.get("disponivel", 0)
        assets_decommissioned = by_status.get("baixado", 0)

        return {
            "assets_total": assets_total,
            "assets_in_maintenance": assets_in_maintenance,
            "assets_in_use": assets_in_use,
            "assets_available": assets_available,
            "assets_decommissioned": assets_decommissioned,
            "equipments_total": assets_total,
            "equipments_in_maintenance": assets_in_maintenance,
            "equipments_in_use": assets_in_use,
            "equipments_idle": assets_available,
            "by_status": by_status,
            "by_type": by_type,
            "by_sector": by_sector,
            "by_category": by_type,
            "by_location": by_sector,
        }


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

    def has_assets(self, category_id: int) -> bool:
        stmt = select(func.count(Asset.id)).where(Asset.category_id == category_id)
        return (self.db.execute(stmt).scalar() or 0) > 0

    def delete(self, category: Category) -> None:
        self.db.delete(category)


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
        if room_number is None or not room_number.strip():
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

    def has_dependencies(self, location_id: int) -> bool:
        asset_cnt = (
            self.db.execute(
                select(func.count(Asset.id)).where(Asset.location_id == location_id)
            ).scalar()
            or 0
        )
        mov_cnt = (
            self.db.execute(
                select(func.count(AssetMovement.id)).where(
                    or_(
                        AssetMovement.origin_location_id == location_id,
                        AssetMovement.dest_location_id == location_id,
                    )
                )
            ).scalar()
            or 0
        )
        return (asset_cnt + mov_cnt) > 0

    def delete(self, location: Location) -> None:
        self.db.delete(location)


class AssetRepository:
    """Repositório de acesso a dados da entidade Asset."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self, asset_id: int, include_deleted: bool = False, eager_history: bool = False
    ) -> Asset | None:
        stmt = (
            select(Asset)
            .where(Asset.id == asset_id)
            .options(
                joinedload(Asset.category),
                joinedload(Asset.location),
                joinedload(Asset.assigned_user),
            )
        )
        if not include_deleted:
            stmt = stmt.where(Asset.deleted_at.is_(None))
        if eager_history:
            stmt = stmt.options(
                selectinload(Asset.maintenances).joinedload(AssetMaintenance.registered_by),
                selectinload(Asset.patrimony_histories).joinedload(PatrimonyHistory.changed_by),
                selectinload(Asset.movements).options(
                    joinedload(AssetMovement.origin_location),
                    joinedload(AssetMovement.dest_location),
                    joinedload(AssetMovement.from_user),
                    joinedload(AssetMovement.to_user),
                    joinedload(AssetMovement.moved_by),
                ),
            )
        else:
            stmt = stmt.options(
                selectinload(Asset.maintenances).joinedload(AssetMaintenance.registered_by)
            )
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

    def _build_filter_stmt(
        self,
        category_id: int | None = None,
        location_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
    ):
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
        return stmt

    def list(
        self,
        category_id: int | None = None,
        location_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 25,
    ) -> tuple[list[Asset], int]:
        stmt = self._build_filter_stmt(
            category_id=category_id, location_id=location_id, status=status, search=search
        )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        last_maint_subq = (
            select(func.max(AssetMaintenance.maintenance_date))
            .where(AssetMaintenance.asset_id == Asset.id)
            .correlate(Asset)
            .scalar_subquery()
        )

        offset = max(0, (page - 1) * limit)
        data_stmt = select(Asset, last_maint_subq.label("last_maintenance_at")).where(
            Asset.deleted_at.is_(None)
        )
        if category_id is not None:
            data_stmt = data_stmt.where(Asset.category_id == category_id)
        if location_id is not None:
            data_stmt = data_stmt.where(Asset.location_id == location_id)
        if status is not None:
            data_stmt = data_stmt.where(Asset.status == status)
        if search:
            term = f"%{search.strip()}%"
            data_stmt = data_stmt.where(
                or_(
                    Asset.patrimony_number.ilike(term),
                    Asset.serial_number.ilike(term),
                    Asset.description.ilike(term),
                    Asset.brand.ilike(term),
                    Asset.model.ilike(term),
                )
            )

        data_stmt = (
            data_stmt.options(
                joinedload(Asset.category),
                joinedload(Asset.location),
                joinedload(Asset.assigned_user),
            )
            .order_by(desc(Asset.created_at))
            .offset(offset)
            .limit(limit)
        )
        rows = self.db.execute(data_stmt).all()
        items = []
        for asset, last_maint in rows:
            asset.computed_last_maintenance_at = last_maint
            items.append(asset)
        return items, total

    def list_for_export(
        self,
        category_id: int | None = None,
        location_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[Asset]:
        stmt = (
            self._build_filter_stmt(
                category_id=category_id, location_id=location_id, status=status, search=search
            )
            .options(
                joinedload(Asset.category),
                joinedload(Asset.location),
                joinedload(Asset.assigned_user),
                selectinload(Asset.maintenances),
            )
            .order_by(asc(Asset.patrimony_number))
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_suggestions(self, field: str, query: str | None = None, limit: int = 10) -> list[str]:
        col_map = {
            "patrimony_number": Asset.patrimony_number,
            "serial_number": Asset.serial_number,
            "brand": Asset.brand,
            "model": Asset.model,
            "description": Asset.description,
        }
        col = col_map.get(field)
        if col is None:
            return []
        stmt = select(col).where(Asset.deleted_at.is_(None), col.is_not(None)).distinct()
        if query and query.strip():
            stmt = stmt.where(col.ilike(f"%{query.strip()}%"))
        stmt = stmt.order_by(asc(col)).limit(limit)
        return [val for val in self.db.execute(stmt).scalars().all() if val]

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
            .options(selectinload(PatrimonyHistory.changed_by))
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
        stmt = (
            select(AssetMovement)
            .where(AssetMovement.id == movement_id)
            .options(
                selectinload(AssetMovement.origin_location),
                selectinload(AssetMovement.dest_location),
                selectinload(AssetMovement.from_user),
                selectinload(AssetMovement.to_user),
                selectinload(AssetMovement.moved_by),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_asset(self, asset_id: int) -> list[AssetMovement]:
        stmt = (
            select(AssetMovement)
            .where(AssetMovement.asset_id == asset_id)
            .options(
                selectinload(AssetMovement.origin_location),
                selectinload(AssetMovement.dest_location),
                selectinload(AssetMovement.from_user),
                selectinload(AssetMovement.to_user),
                selectinload(AssetMovement.moved_by),
            )
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
        stmt = (
            select(AssetMaintenance)
            .where(AssetMaintenance.id == maintenance_id)
            .options(selectinload(AssetMaintenance.registered_by))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_asset(self, asset_id: int) -> list[AssetMaintenance]:
        stmt = (
            select(AssetMaintenance)
            .where(AssetMaintenance.asset_id == asset_id)
            .options(selectinload(AssetMaintenance.registered_by))
            .order_by(desc(AssetMaintenance.maintenance_date))
        )
        return list(self.db.execute(stmt).scalars().all())

    def delete(self, maintenance: AssetMaintenance) -> None:
        self.db.delete(maintenance)
