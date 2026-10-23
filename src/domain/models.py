import enum
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Any
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Date,
    Integer,
    Numeric,
    ForeignKey,
    Text,
    CheckConstraint,
    Index,
    JSON,
    Enum as SAEnum,
    func,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from src.core.database import Base


class UserRole(str, enum.Enum):
    ADMINISTRADOR = "administrador"
    TECNICO = "tecnico"
    COLABORADOR = "colaborador"


class AssetStatus(str, enum.Enum):
    DISPONIVEL = "disponivel"
    EM_USO = "em_uso"
    EM_MANUTENCAO = "em_manutencao"
    BAIXADO = "baixado"


class MaintenanceTypeEnum(str, enum.Enum):
    PREVENTIVA = "preventiva"
    CORRETIVA = "corretiva"


class IPAddressType(TypeDecorator):
    """Tipo agnóstico a dialeto de banco para endereços IP (PostgreSQL INET ou String fallback)."""

    impl = String(45)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import INET

            return dialect.type_descriptor(INET())
        return dialect.type_descriptor(String(45))

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return str(value) if value is not None else None


class MACAddressType(TypeDecorator):
    """Tipo agnóstico a dialeto de banco para endereços MAC (PostgreSQL MACADDR ou String fallback)."""

    impl = String(17)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import MACADDR

            return dialect.type_descriptor(MACADDR())
        return dialect.type_descriptor(String(17))

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return str(value) if value is not None else None


class EquipmentType(Base):
    """Modelo ORM representando o catálogo de tipos de equipamentos."""

    __tablename__ = "equipment_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (Index("uq_equipment_types_name_lower", func.lower(name), unique=True),)


class Sector(Base):
    """Modelo ORM representando o catálogo de setores / localizações."""

    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (Index("uq_sectors_name_lower", func.lower(name), unique=True),)


class EquipmentStatus(Base):
    """Modelo ORM representando o catálogo de situações patrimoniais."""

    __tablename__ = "equipment_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (Index("uq_equipment_statuses_name_lower", func.lower(name), unique=True),)


class MaintenanceType(Base):
    """Modelo ORM representando o catálogo de tipos de manutenção."""

    __tablename__ = "maintenance_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (Index("uq_maintenance_types_name_lower", func.lower(name), unique=True),)


class User(Base):
    """Modelo ORM representando um usuário registrado no sistema."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Usuário")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(
        "password_hash", String(255), nullable=False, default=""
    )
    role: Mapped[str] = mapped_column(
        SAEnum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.COLABORADOR.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    hashed_password = synonym("password_hash")

    __table_args__ = (
        CheckConstraint(
            "role IN ('administrador', 'tecnico', 'colaborador')", name="chk_users_role_valid"
        ),
        Index("uq_users_email_lower", func.lower(email), unique=True),
    )


class LoginAttempt(Base):
    """Modelo ORM registrando tentativas de login por IP para controle de rate limit e auditoria."""

    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email_attempted: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(IPAddressType, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_login_attempts_ip_attempted_at", "ip_address", "attempted_at"),
        Index("ix_login_attempts_email_attempted_at", "email_attempted", "attempted_at"),
    )


class Equipment(Base):
    """Modelo ORM representando um equipamento de TI (Patrimônio)."""

    __tablename__ = "equipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patrimony_number: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    serial_number: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)

    equipment_type_id: Mapped[int] = mapped_column(ForeignKey("equipment_types.id"), nullable=False)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id"), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("equipment_statuses.id"), nullable=False)

    ip_address: Mapped[str | None] = mapped_column(IPAddressType, nullable=True)
    mac_address: Mapped[str | None] = mapped_column(MACAddressType, nullable=True)
    printer_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    windows_product_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    version_id: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __mapper_args__ = {"version_id_col": version_id}

    __table_args__ = (
        CheckConstraint(
            "ip_address IS NULL OR (family(ip_address) = 4 AND masklen(ip_address) = 32) OR (family(ip_address) = 6 AND masklen(ip_address) = 128)",
            name="chk_equipments_ip_host_only",
        ),
        Index("uq_equipments_patrimony_number_lower", func.lower(patrimony_number), unique=True),
        Index(
            "uq_equipments_serial_number_lower",
            func.lower(serial_number),
            unique=True,
            postgresql_where=text("serial_number IS NOT NULL"),
            sqlite_where=text("serial_number IS NOT NULL"),
        ),
        Index(
            "uq_equipments_hostname_active",
            func.lower(hostname),
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND hostname IS NOT NULL"),
            sqlite_where=text("deleted_at IS NULL AND hostname IS NOT NULL"),
        ),
        Index(
            "uq_equipments_ip_address_active",
            "ip_address",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND ip_address IS NOT NULL"),
            sqlite_where=text("deleted_at IS NULL AND ip_address IS NOT NULL"),
        ),
        Index(
            "uq_equipments_mac_address_active",
            "mac_address",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND mac_address IS NOT NULL"),
            sqlite_where=text("deleted_at IS NULL AND mac_address IS NOT NULL"),
        ),
        Index(
            "uq_equipments_printer_identifier_active",
            func.lower(printer_identifier),
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND printer_identifier IS NOT NULL"),
            sqlite_where=text("deleted_at IS NULL AND printer_identifier IS NOT NULL"),
        ),
    )

    equipment_type: Mapped["EquipmentType"] = relationship("EquipmentType")
    sector: Mapped["Sector"] = relationship("Sector")
    status: Mapped["EquipmentStatus"] = relationship("EquipmentStatus")

    movements: Mapped[list["EquipmentMovement"]] = relationship(
        "EquipmentMovement",
        back_populates="equipment",
        cascade="all, delete-orphan",
        order_by="asc(EquipmentMovement.movement_date), asc(EquipmentMovement.id)",
    )
    maintenances: Mapped[list["EquipmentMaintenance"]] = relationship(
        "EquipmentMaintenance",
        back_populates="equipment",
        cascade="all, delete-orphan",
        order_by="desc(EquipmentMaintenance.started_at)",
    )


class EquipmentMovement(Base):
    """Modelo ORM registrando histórico imutável de transferências de setor."""

    __tablename__ = "equipment_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipments.id"), index=True, nullable=False
    )
    origin_sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id"), nullable=False)
    destination_sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id"), nullable=False)
    movement_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    performed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "origin_sector_id <> destination_sector_id", name="chk_movement_different_sectors"
        ),
        CheckConstraint(
            "movement_date <= (now() + interval '5 minutes')", name="chk_movement_date_not_future"
        ),
    )

    equipment: Mapped["Equipment"] = relationship("Equipment", back_populates="movements")
    origin_sector: Mapped["Sector"] = relationship("Sector", foreign_keys=[origin_sector_id])
    destination_sector: Mapped["Sector"] = relationship(
        "Sector", foreign_keys=[destination_sector_id]
    )
    performed_by_user: Mapped["User"] = relationship("User", foreign_keys=[performed_by_user_id])


class EquipmentMaintenance(Base):
    """Modelo ORM registrando intervenção e ciclo de vida de manutenção."""

    __tablename__ = "equipment_maintenances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipments.id"), index=True, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    maintenance_type_id: Mapped[int] = mapped_column(
        ForeignKey("maintenance_types.id"), nullable=False
    )
    performed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, default=None
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name="chk_maintenance_completion_after_start",
        ),
        Index(
            "uq_equipment_maintenances_one_open_per_equipment",
            "equipment_id",
            unique=True,
            postgresql_where=text("completed_at IS NULL"),
            sqlite_where=text("completed_at IS NULL"),
        ),
    )

    equipment: Mapped["Equipment"] = relationship("Equipment", back_populates="maintenances")
    maintenance_type: Mapped["MaintenanceType"] = relationship("MaintenanceType")
    performed_by_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[performed_by_user_id]
    )


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    building: Mapped[str] = mapped_column(String(100), nullable=False)
    floor: Mapped[str] = mapped_column(String(50), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    room_number: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "uq_locations_physical_space",
            "building",
            "floor",
            "sector",
            "room_number",
            unique=True,
        ),
    )

    assets: Mapped[list["Asset"]] = relationship("Asset", back_populates="location")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    useful_life_months: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    residual_value_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    requires_serial_number: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    assets: Mapped[list["Asset"]] = relationship("Asset", back_populates="category")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patrimony_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    serial_number: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True, default=None
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    assigned_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, default=None
    )
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    purchase_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True, default=None
    )
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    status: Mapped[str] = mapped_column(
        SAEnum(AssetStatus, name="asset_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AssetStatus.DISPONIVEL.value,
    )
    specs: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    category: Mapped["Category"] = relationship("Category", back_populates="assets")
    location: Mapped["Location"] = relationship("Location", back_populates="assets")
    assigned_user: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_user_id])
    patrimony_histories: Mapped[list["PatrimonyHistory"]] = relationship(
        "PatrimonyHistory", back_populates="asset", cascade="all, delete-orphan"
    )
    movements: Mapped[list["AssetMovement"]] = relationship(
        "AssetMovement", back_populates="asset", cascade="all, delete-orphan"
    )
    maintenances: Mapped[list["AssetMaintenance"]] = relationship(
        "AssetMaintenance", back_populates="asset", cascade="all, delete-orphan"
    )


class PatrimonyHistory(Base):
    __tablename__ = "patrimony_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    old_patrimony_number: Mapped[str] = mapped_column(String(100), nullable=False)
    new_patrimony_number: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    asset: Mapped["Asset"] = relationship("Asset", back_populates="patrimony_histories")
    changed_by: Mapped["User"] = relationship("User", foreign_keys=[changed_by_id])


class AssetMovement(Base):
    __tablename__ = "asset_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    origin_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    dest_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"), nullable=True, default=None
    )
    from_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, default=None
    )
    to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, default=None
    )
    moved_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    term_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    movement_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="movements")
    origin_location: Mapped["Location"] = relationship(
        "Location", foreign_keys=[origin_location_id]
    )
    dest_location: Mapped["Location | None"] = relationship(
        "Location", foreign_keys=[dest_location_id]
    )
    from_user: Mapped["User | None"] = relationship("User", foreign_keys=[from_user_id])
    to_user: Mapped["User | None"] = relationship("User", foreign_keys=[to_user_id])
    moved_by: Mapped["User"] = relationship("User", foreign_keys=[moved_by_id])


class AssetMaintenance(Base):
    __tablename__ = "asset_maintenances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    registered_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    maintenance_type: Mapped[str] = mapped_column(
        SAEnum(
            MaintenanceTypeEnum,
            name="maintenance_type",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    service_provider: Mapped[str | None] = mapped_column(String(150), nullable=True, default=None)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True, default=None)
    maintenance_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    asset: Mapped["Asset"] = relationship("Asset", back_populates="maintenances")
    registered_by: Mapped["User"] = relationship("User", foreign_keys=[registered_by_id])
