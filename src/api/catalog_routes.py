"""Rotas HTTP do FastAPI para gerenciamento dos 4 catálogos estruturais."""

from typing import List, Type
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.api.dependencies import require_tecnico_role
from src.core.database import get_db
from src.domain.models import User, EquipmentType, Sector, EquipmentStatus, MaintenanceType
from src.domain.schemas import (
    EquipmentTypeCreate,
    EquipmentTypeUpdate,
    EquipmentTypeResponse,
    SectorCreate,
    SectorUpdate,
    SectorResponse,
    EquipmentStatusCreate,
    EquipmentStatusUpdate,
    EquipmentStatusResponse,
    MaintenanceTypeCreate,
    MaintenanceTypeUpdate,
    MaintenanceTypeResponse,
    MessageResponse,
)
from src.use_cases.equipment_use_cases import ManageCatalogsUseCase


def create_catalog_router(
    prefix: str,
    tag: str,
    model_cls,
    create_schema: Type,
    update_schema: Type,
    response_schema: Type,
) -> APIRouter:
    """Fábrica para gerar routers padronizados para cada catálogo estrutural."""
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("", response_model=List[response_schema])
    def list_items(
        include_inactive: bool = Query(
            default=False, description="Incluir itens inativos (soft deleted)"
        ),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_tecnico_role),
    ):
        use_case = ManageCatalogsUseCase(db)
        items = use_case.list_items(model_cls, include_inactive=include_inactive)
        return items

    @router.post("", response_model=response_schema, status_code=status.HTTP_201_CREATED)
    def create_item(
        data: create_schema,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_tecnico_role),
    ):
        use_case = ManageCatalogsUseCase(db)
        try:
            return use_case.create_item(model_cls, data)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @router.get("/{id}", response_model=response_schema)
    def get_item(
        id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_tecnico_role),
    ):
        use_case = ManageCatalogsUseCase(db)
        try:
            return use_case.get_item(model_cls, id)
        except KeyError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    @router.put("/{id}", response_model=response_schema)
    def update_item(
        id: int,
        data: update_schema,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_tecnico_role),
    ):
        use_case = ManageCatalogsUseCase(db)
        try:
            return use_case.update_item(model_cls, id, data)
        except KeyError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @router.delete("/{id}", response_model=MessageResponse)
    def delete_item(
        id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_tecnico_role),
    ):
        use_case = ManageCatalogsUseCase(db)
        try:
            use_case.delete_item(model_cls, id)
            return MessageResponse(message="Item excluído logicamente com sucesso.")
        except KeyError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @router.post("/{id}/restore", response_model=response_schema)
    def restore_item(
        id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_tecnico_role),
    ):
        use_case = ManageCatalogsUseCase(db)
        try:
            return use_case.restore_item(model_cls, id)
        except KeyError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return router


equipment_types_router = create_catalog_router(
    prefix="/api/v1/equipment-types",
    tag="Catálogo: Tipos de Equipamento",
    model_cls=EquipmentType,
    create_schema=EquipmentTypeCreate,
    update_schema=EquipmentTypeUpdate,
    response_schema=EquipmentTypeResponse,
)

sectors_router = create_catalog_router(
    prefix="/api/v1/sectors",
    tag="Catálogo: Setores",
    model_cls=Sector,
    create_schema=SectorCreate,
    update_schema=SectorUpdate,
    response_schema=SectorResponse,
)

equipment_statuses_router = create_catalog_router(
    prefix="/api/v1/equipment-statuses",
    tag="Catálogo: Situações Patrimoniais",
    model_cls=EquipmentStatus,
    create_schema=EquipmentStatusCreate,
    update_schema=EquipmentStatusUpdate,
    response_schema=EquipmentStatusResponse,
)

maintenance_types_router = create_catalog_router(
    prefix="/api/v1/maintenance-types",
    tag="Catálogo: Tipos de Manutenção",
    model_cls=MaintenanceType,
    create_schema=MaintenanceTypeCreate,
    update_schema=MaintenanceTypeUpdate,
    response_schema=MaintenanceTypeResponse,
)
