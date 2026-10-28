"""Schemas Pydantic para validação e transporte de dados (DTOs) do SisPatrimonio."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# --- Schemas de Usuários e Autenticação ---


class LoginRequest(BaseModel):
    """Schema para requisição de login."""

    email: EmailStr = Field(..., description="Endereço de email do usuário")
    password: str = Field(..., min_length=1, description="Senha do usuário")


class UserResponse(BaseModel):
    """Schema de resposta representando os dados públicos do usuário."""

    id: int
    name: str = "Usuário"
    email: str
    role: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema para resposta de autenticação com token."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Schema genérico para respostas de mensagem ou erro."""

    message: str


# --- Schemas de Dashboard ---


class DashboardMetricsResponse(BaseModel):
    """Schema de resposta com métricas consolidadas do patrimônio."""

    assets_total: int = 0
    assets_in_maintenance: int = 0
    assets_in_use: int = 0
    assets_available: int = 0
    assets_decommissioned: int = 0
    equipments_total: int | None = 0
    equipments_in_maintenance: int | None = 0
    equipments_in_use: int | None = 0
    equipments_idle: int | None = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    by_sector: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    by_location: dict[str, int] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)



# --- Schemas de Categorias ---


class CategoryCreate(BaseModel):
    """Schema para criação de categoria patrimonial."""

    name: str = Field(..., min_length=1, max_length=100)
    useful_life_months: int | None = Field(default=None, ge=1)
    residual_value_rate: Decimal = Field(
        default=Decimal("0.00"), ge=Decimal("0"), le=Decimal("100")
    )
    requires_serial_number: bool = False


class CategoryUpdate(BaseModel):
    """Schema para atualização de categoria patrimonial."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    useful_life_months: int | None = Field(default=None, ge=1)
    residual_value_rate: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("100"))
    requires_serial_number: bool | None = None


class CategoryResponse(BaseModel):
    """Schema de resposta para categoria patrimonial."""

    id: int
    name: str
    useful_life_months: int | None = None
    residual_value_rate: Decimal = Decimal("0.00")
    requires_serial_number: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# --- Schemas de Localizações Físicas ---


class LocationCreate(BaseModel):
    """Schema para criação de localização física."""

    building: str = Field(..., min_length=1, max_length=100)
    floor: str = Field(..., min_length=1, max_length=50)
    sector: str = Field(..., min_length=1, max_length=100)
    room_number: str | None = Field(default=None, max_length=50)
    description: str | None = None


class LocationUpdate(BaseModel):
    """Schema para atualização de localização física."""

    building: str | None = Field(default=None, min_length=1, max_length=100)
    floor: str | None = Field(default=None, min_length=1, max_length=50)
    sector: str | None = Field(default=None, min_length=1, max_length=100)
    room_number: str | None = Field(default=None, max_length=50)
    description: str | None = None


class LocationResponse(BaseModel):
    """Schema de resposta para localização física."""

    id: int
    building: str
    floor: str
    sector: str
    room_number: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# --- Schemas de Ativos Patrimoniais (Assets) ---


class AssetCreate(BaseModel):
    """Schema para criação de ativo patrimonial."""

    patrimony_number: str = Field(..., min_length=1, max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)
    description: str = Field(..., min_length=1, max_length=255)
    category_id: int
    location_id: int
    assigned_user_id: int | None = None
    brand: str = Field(..., min_length=1, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    purchase_cost: Decimal | None = Field(default=None, ge=Decimal("0"))
    purchase_date: date | None = None
    status: str = Field(default="disponivel")
    specs: dict[str, Any] = Field(default_factory=dict)


class AssetUpdate(BaseModel):
    """Schema para atualização cadastral de ativo patrimonial."""

    serial_number: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=255)
    category_id: int | None = None
    location_id: int | None = None
    assigned_user_id: int | None = None
    brand: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    purchase_cost: Decimal | None = Field(default=None, ge=Decimal("0"))
    purchase_date: date | None = None
    status: str | None = None
    specs: dict[str, Any] | None = None


class PatrimonyHistoryResponse(BaseModel):
    """Schema para histórico de renumeração de patrimônio."""

    id: int
    asset_id: int
    old_patrimony_number: str
    new_patrimony_number: str
    reason: str
    changed_by_id: int
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatrimonyRenumberRequest(BaseModel):
    """Schema para requisição de renumeração de patrimônio."""

    new_patrimony_number: str = Field(..., min_length=1, max_length=100)
    reason: str = Field(..., min_length=1, max_length=255)


class AssetResponse(BaseModel):
    """Schema de resposta padrão para ativo patrimonial."""

    id: int
    patrimony_number: str
    serial_number: str | None = None
    description: str
    category_id: int
    location_id: int
    assigned_user_id: int | None = None
    brand: str
    model: str | None = None
    purchase_cost: Decimal | None = None
    purchase_date: date | None = None
    status: str
    specs: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AssetDetailResponse(AssetResponse):
    """Schema de resposta detalhada para ativo patrimonial com histórico."""

    patrimony_history: list[PatrimonyHistoryResponse] = Field(default_factory=list)


class AssetListResponse(BaseModel):
    """Schema para listagem paginada de ativos."""

    items: list[AssetResponse]
    total: int
    page: int
    limit: int
    pages: int


# --- Schemas de Movimentações Físicas ---


class AssetMovementCreate(BaseModel):
    """Schema para registro de movimentação física/transferência de ativo."""

    origin_location_id: int
    dest_location_id: int | None = None
    from_user_id: int | None = None
    to_user_id: int | None = None
    movement_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str | None = None


class AssetMovementResponse(BaseModel):
    """Schema de resposta para movimentação de ativo."""

    id: int
    asset_id: int
    origin_location_id: int
    dest_location_id: int | None = None
    from_user_id: int | None = None
    to_user_id: int | None = None
    moved_by_id: int
    term_accepted_at: datetime | None = None
    movement_date: datetime
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


# --- Schemas de Manutenções Técnicas ---


class AssetMaintenanceCreate(BaseModel):
    """Schema para lançamento de manutenção preventiva ou corretiva."""

    maintenance_type: str = Field(..., description="preventiva ou corretiva")
    service_provider: str | None = Field(default=None, max_length=150)
    description: str = Field(..., min_length=1)
    cost: Decimal | None = Field(default=None, ge=Decimal("0"))
    maintenance_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssetMaintenanceResponse(BaseModel):
    """Schema de resposta para manutenção de ativo."""

    id: int
    asset_id: int
    registered_by_id: int
    maintenance_type: str
    service_provider: str | None = None
    description: str
    cost: Decimal | None = None
    maintenance_date: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# --- Schemas de Importação de Planilha ---


class SpreadsheetRowPreview(BaseModel):
    """Schema representando uma linha na pré-visualização da planilha."""

    row_number: int
    category: str | None = None
    equipment_type: str | None = None
    location: str | None = None
    status: str | None = None
    description: str | None = None
    patrimony_number: str | None = None
    serial_number: str | None = None
    brand: str | None = None
    model: str | None = None
    purchase_cost: str | None = None
    purchase_date: str | None = None
    notes: str | None = None


class SpreadsheetImportPreviewResponse(BaseModel):
    """Schema de resposta para pré-visualização da planilha importada."""

    filename: str
    total_rows: int
    sample_rows: list[SpreadsheetRowPreview]
    detected_sheet: str | None = None
    headers: list[str]


class SpreadsheetImportResultResponse(BaseModel):
    """Schema de resposta para o resultado final da importação."""

    success: bool
    total_rows: int
    created_count: int
    updated_count: int
    categories_created_count: int = 0
    locations_created_count: int = 0
    catalogs_created_count: int = 0
    tags_created_count: int = 0
    maintenances_created_count: int = 0
    errors: list[str] = []
    message: str
