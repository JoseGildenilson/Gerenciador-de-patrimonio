"""Schemas Pydantic para validação e transporte de dados (DTOs)."""

import ipaddress
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


class LoginAttemptResponse(BaseModel):
    """Schema para resposta de tentativa de login (auditoria)."""

    id: int
    email_attempted: str
    ip_address: str
    attempted_at: datetime
    success: bool

    model_config = ConfigDict(from_attributes=True)


# --- Schemas de Catálogos Estruturais ---


class CatalogItemCreate(BaseModel):
    """Schema base para criação de item de catálogo."""

    name: str = Field(..., min_length=1, description="Nome padronizado do item de catálogo")

    @field_validator("name")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("O nome do item não pode ser vazio.")
        return clean


class CatalogItemUpdate(BaseModel):
    """Schema base para atualização de item de catálogo."""

    name: str = Field(..., min_length=1, description="Novo nome do item de catálogo")

    @field_validator("name")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("O nome do item não pode ser vazio.")
        return clean


class CatalogItemResponse(BaseModel):
    """Schema base de resposta para item de catálogo."""

    id: int
    name: str
    created_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# Tipos específicos para cada catálogo
class EquipmentTypeCreate(CatalogItemCreate):
    pass


class EquipmentTypeUpdate(CatalogItemUpdate):
    pass


class EquipmentTypeResponse(CatalogItemResponse):
    pass


class SectorCreate(CatalogItemCreate):
    pass


class SectorUpdate(CatalogItemUpdate):
    pass


class SectorResponse(CatalogItemResponse):
    pass


class EquipmentStatusCreate(CatalogItemCreate):
    pass


class EquipmentStatusUpdate(CatalogItemUpdate):
    pass


class EquipmentStatusResponse(CatalogItemResponse):
    pass


class MaintenanceTypeCreate(CatalogItemCreate):
    pass


class MaintenanceTypeUpdate(CatalogItemUpdate):
    pass


class MaintenanceTypeResponse(CatalogItemResponse):
    pass


# --- Schemas de Movimentação ---


class EquipmentMovementCreate(BaseModel):
    """Schema para registro de movimentação de localização/setor."""

    origin_sector_id: int = Field(..., description="ID do setor de origem")
    destination_sector_id: int = Field(..., description="ID do setor de destino")
    movement_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data da movimentação",
    )
    notes: str | None = Field(default=None, description="Observação opcional")


class EquipmentMovementUpdate(BaseModel):
    """Schema para alteração de movimentação."""

    origin_sector_id: int | None = Field(default=None, description="ID do setor de origem")
    destination_sector_id: int | None = Field(default=None, description="ID do setor de destino")
    movement_date: datetime | None = Field(default=None, description="Data da movimentação")
    notes: str | None = Field(default=None, description="Observação opcional")


class EquipmentMovementResponse(BaseModel):
    """Schema de resposta para movimentação."""

    id: int
    equipment_id: int
    origin_sector_id: int
    origin_sector: SectorResponse | None = None
    destination_sector_id: int
    destination_sector: SectorResponse | None = None
    movement_date: datetime
    performed_by_user_id: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Schemas de Manutenção ---


class EquipmentMaintenanceStart(BaseModel):
    """Schema para início de manutenção."""

    maintenance_type_id: int = Field(..., description="ID do tipo de manutenção")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data/hora de início",
    )
    description: str | None = Field(default=None, description="Descrição da intervenção")
    notes: str | None = Field(default=None, description="Observações técnicas adicionais")


class EquipmentMaintenanceComplete(BaseModel):
    """Schema para conclusão de manutenção."""

    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data/hora de conclusão",
    )
    new_status_id: int = Field(..., description="Nova situação patrimonial do equipamento")
    description: str | None = Field(default=None, description="Descrição final da intervenção")
    notes: str | None = Field(default=None, description="Observações finais")


class EquipmentMaintenanceUpdate(BaseModel):
    """Schema para edição de manutenção existente."""

    maintenance_type_id: int | None = Field(default=None, description="ID do tipo de manutenção")
    started_at: datetime | None = Field(default=None, description="Data/hora de início")
    completed_at: datetime | None = Field(default=None, description="Data/hora de conclusão")
    description: str | None = Field(default=None, description="Descrição da intervenção")
    notes: str | None = Field(default=None, description="Observações técnicas")


class EquipmentMaintenanceResponse(BaseModel):
    """Schema de resposta para manutenção."""

    id: int
    equipment_id: int
    started_at: datetime
    completed_at: datetime | None = None
    maintenance_type_id: int
    maintenance_type: MaintenanceTypeResponse | None = None
    performed_by_user_id: int | None = None
    description: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Schemas de Equipamentos (Patrimônio) ---


def validate_host_ip(v: str | None) -> str | None:
    if v is None or not str(v).strip():
        return None
    clean = str(v).strip()
    if "/" in clean:
        try:
            iface = ipaddress.ip_interface(clean)
            if iface.network.prefixlen not in (32, 128):
                raise ValueError(
                    "Endereço IP deve ser de host único (/32 ou /128), sem máscara de sub-rede."
                )
            return str(iface.ip)
        except ValueError as e:
            if "host único" in str(e):
                raise
            raise ValueError(f"Endereço IP inválido: {clean}") from e
    else:
        try:
            ipaddress.ip_address(clean)
            return clean
        except ValueError as e:
            raise ValueError(f"Endereço IP inválido: {clean}") from e


class EquipmentCreate(BaseModel):
    """Schema para cadastro de equipamento."""

    patrimony_number: str = Field(
        ..., min_length=1, description="Nº de Patrimônio (Obrigatório e único)"
    )
    equipment_type_id: int = Field(..., description="ID do Tipo de Equipamento")
    sector_id: int = Field(..., description="ID do Setor / Localização")
    status_id: int = Field(..., description="ID da Situação Patrimonial")
    description: str | None = Field(default=None, description="Descrição do equipamento")
    serial_number: str | None = Field(
        default=None, description="Nº de Série (Opcional, único se preenchido)"
    )
    hostname: str | None = Field(default=None, description="Hostname (Opcional, único ativo)")
    brand: str | None = Field(default=None, description="Marca")
    model: str | None = Field(
        default=None, description="Modelo comercial (substitui product_number)"
    )
    ip_address: str | None = Field(default=None, description="Endereço IP de host (/32 ou /128)")
    mac_address: str | None = Field(default=None, description="Endereço MAC")
    printer_identifier: str | None = Field(default=None, description="Identificador de Impressora")
    windows_product_key: str | None = Field(
        default=None, description="Chave Windows em texto simples"
    )
    notes: str | None = Field(default=None, description="Observações")

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, v: str | None) -> str | None:
        return validate_host_ip(v)


class EquipmentUpdate(BaseModel):
    """Schema para atualização parcial/total de equipamento."""

    patrimony_number: str | None = None
    equipment_type_id: int | None = None
    sector_id: int | None = None
    status_id: int | None = None
    description: str | None = None
    serial_number: str | None = None
    hostname: str | None = None
    brand: str | None = None
    model: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None
    printer_identifier: str | None = None
    windows_product_key: str | None = None
    notes: str | None = None

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, v: str | None) -> str | None:
        return validate_host_ip(v)


class EquipmentListItemResponse(BaseModel):
    """DTO enxuto para listagem paginada de equipamentos."""

    id: int
    patrimony_number: str
    description: str | None = None
    serial_number: str | None = None
    hostname: str | None = None
    brand: str | None = None
    model: str | None = None
    equipment_type_id: int
    equipment_type: EquipmentTypeResponse
    sector_id: int
    sector: SectorResponse
    status_id: int
    status: EquipmentStatusResponse
    ip_address: str | None = None
    mac_address: str | None = None
    printer_identifier: str | None = None
    windows_product_key: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class EquipmentResponse(EquipmentListItemResponse):
    """Schema de resposta completo do equipamento com históricos."""

    movements: list[EquipmentMovementResponse] = []
    maintenances: list[EquipmentMaintenanceResponse] = []


class EquipmentListResponse(BaseModel):
    """Schema para resposta paginada de equipamentos."""

    items: list[EquipmentListItemResponse]
    total: int
    page: int
    limit: int
    pages: int


class EquipmentSecretKeyResponse(BaseModel):
    """DTO específico para retorno da chave de produto do Windows decriptografada."""

    equipment_id: int
    windows_product_key: str | None = None


# --- Schemas do Dashboard ---


class DashboardMetricsResponse(BaseModel):
    """Schema para resposta dos indicadores do Dashboard patrimonial."""

    equipments_total: int
    equipments_in_maintenance: int
    equipments_in_use: int
    equipments_idle: int
    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_sector: dict[str, int] = {}


# --- Schemas de Importação de Planilha ---


class SpreadsheetRowPreview(BaseModel):
    """Schema representando uma linha na pré-visualização da planilha."""

    row_number: int
    equipment_type: str | None = None
    location: str | None = None
    status: str | None = None
    description: str | None = None
    patrimony_number: str | None = None
    serial_number: str | None = None
    brand: str | None = None
    model: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None
    printer_identifier: str | None = None
    windows_key: str | None = None
    last_maintenance_at: str | None = None
    hist_mov: str | None = None
    hostname: str | None = None
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
    catalogs_created_count: int = 0
    tags_created_count: int = 0
    maintenances_created_count: int
    errors: list[str] = []
    message: str


# --- Schemas de Tags Legadas / Catálogos Adaptados ---


class TagResponse(BaseModel):
    """Schema para tags de equipamentos mapeadas aos catálogos."""

    id: int
    category: str
    name: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TagCreate(BaseModel):
    """Schema para criação de tag associada a categoria."""

    category: str
    name: str


class TagUpdate(BaseModel):
    """Schema para atualização do nome de uma tag."""

    name: str


# --- Schemas de SisPatrimonio (Categorias, Localizações, Ativos, Movimentações e Manutenções) ---


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
