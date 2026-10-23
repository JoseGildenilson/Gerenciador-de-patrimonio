"""Rotas HTTP para movimentações físicas, custódia e manutenções de ativos."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_user, require_tecnico_or_admin
from src.core.database import get_db
from src.core.exceptions import NotFoundError
from src.domain.models import User
from src.domain.schemas import (
    AssetMovementCreate,
    AssetMovementResponse,
    AssetMaintenanceCreate,
    AssetMaintenanceResponse,
)
from src.use_cases.movement_use_cases import AssetMovementUseCases
from src.use_cases.maintenance_use_cases import MaintenanceUseCases

router = APIRouter(tags=["Movements & Maintenances"])


@router.get("/api/v1/assets/{id}/movements", response_model=list[AssetMovementResponse])
def list_asset_movements(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Lista o histórico de movimentações e transferências de um ativo."""
    use_case = AssetMovementUseCases(db)
    try:
        return use_case.list_by_asset(id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/api/v1/assets/{id}/movements",
    response_model=AssetMovementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_asset_movement(
    id: int,
    data: AssetMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tecnico_or_admin),
):
    """Registra uma transferência física ou de custódia patrimonial."""
    use_case = AssetMovementUseCases(db)
    try:
        return use_case.create_movement(id, data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/api/v1/movements/{movement_id}/accept-term",
    response_model=AssetMovementResponse,
)
def accept_custody_term(
    movement_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Registra o aceite eletrônico do termo de responsabilidade pelo custodiante."""
    use_case = AssetMovementUseCases(db)
    try:
        return use_case.accept_custody_term(movement_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/api/v1/assets/{id}/maintenances", response_model=list[AssetMaintenanceResponse])
def list_asset_maintenances(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Lista o histórico de manutenções de um ativo patrimonial."""
    use_case = MaintenanceUseCases(db)
    try:
        return use_case.list_by_asset(id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/api/v1/assets/{id}/maintenances",
    response_model=AssetMaintenanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_asset_maintenance(
    id: int,
    data: AssetMaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tecnico_or_admin),
):
    """Lança intervenção de manutenção preventiva ou corretiva para o ativo."""
    use_case = MaintenanceUseCases(db)
    try:
        return use_case.create_maintenance(id, data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
