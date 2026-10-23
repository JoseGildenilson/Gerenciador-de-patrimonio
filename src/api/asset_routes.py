"""Rotas HTTP para gestão de ativos patrimoniais e renumeração."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_user, require_tecnico_or_admin
from src.core.database import get_db
from src.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from src.domain.models import User
from src.domain.schemas import (
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    AssetDetailResponse,
    AssetListResponse,
    PatrimonyHistoryResponse,
    PatrimonyRenumberRequest,
)
from src.use_cases.asset_use_cases import AssetUseCases

router = APIRouter(prefix="/api/v1/assets", tags=["Assets"])


@router.get("", response_model=AssetListResponse)
def list_assets(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
    category_id: int | None = Query(default=None),
    location_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Lista ativos patrimoniais com filtros e paginação."""
    use_case = AssetUseCases(db)
    return use_case.list_assets(
        category_id=category_id,
        location_id=location_id,
        status=status_filter,
        search=search,
        page=page,
        limit=limit,
    )


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    data: AssetCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_tecnico_or_admin),
):
    """Cadastra novo ativo patrimonial validando serial se exigido pela categoria."""
    use_case = AssetUseCases(db)
    try:
        return use_case.create_asset(data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{id}", response_model=AssetDetailResponse)
def get_asset_detail(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Obtém detalhes do ativo com histórico de renumeração."""
    use_case = AssetUseCases(db)
    try:
        return use_case.get_asset(id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{id}", response_model=AssetResponse)
def update_asset(
    id: int,
    data: AssetUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_tecnico_or_admin),
):
    """Atualiza dados cadastrais do ativo patrimonial."""
    use_case = AssetUseCases(db)
    try:
        return use_case.update_asset(id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{id}/renumber", response_model=PatrimonyHistoryResponse)
def renumber_patrimony(
    id: int,
    data: PatrimonyRenumberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tecnico_or_admin),
):
    """Renumera a plaqueta de patrimônio de um ativo e registra histórico imutável."""
    use_case = AssetUseCases(db)
    try:
        return use_case.renumber_patrimony(id, data, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_tecnico_or_admin),
):
    """Exclui logicamente um ativo patrimonial."""
    use_case = AssetUseCases(db)
    try:
        use_case.delete_asset(id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
