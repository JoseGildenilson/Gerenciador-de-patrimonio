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
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship
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


class User(Base):
    """Modelo ORM representando um usuário registrado no sistema."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Usuário")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        SAEnum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.COLABORADOR.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
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

    __table_args__ = (
        CheckConstraint(
            "role IN ('administrador', 'tecnico', 'colaborador')", name="chk_users_role_valid"
        ),
        Index("uq_users_email_lower", func.lower(email), unique=True),
    )


class Location(Base):
    """Modelo ORM representando uma localização física."""

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
    """Modelo ORM representando uma categoria patrimonial."""

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
    """Modelo ORM representando um bem patrimonial (Ativo)."""

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
    """Modelo ORM registrando renumeração de patrimônio."""

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
    """Modelo ORM registrando movimentações físicas e trocas de custodiante."""

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
    """Modelo ORM registrando manutenções técnicas preventivas e corretivas."""

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
