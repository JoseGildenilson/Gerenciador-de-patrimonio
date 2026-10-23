"""Rotas HTTP para gestão de localizações físicas."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_user, require_tecnico_or_admin
from src.core.database import get_db
from src.core.exceptions import ConflictError, NotFoundError
from src.domain.models import User
from src.domain.schemas import LocationCreate, LocationUpdate, LocationResponse
from src.use_cases.location_use_cases import LocationUseCases

router = APIRouter(prefix="/api/v1/locations", tags=["Locations"])


@router.get("", response_model=list[LocationResponse])
def list_locations(
    building: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Lista localizações físicas filtradas opcionalmente por prédio ou setor."""
    use_case = LocationUseCases(db)
    return use_case.list_locations(building=building, sector=sector)


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    data: LocationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_tecnico_or_admin),
):
    """Cadastra nova localização física garantindo unicidade espacial."""
    use_case = LocationUseCases(db)
    try:
        return use_case.create_location(data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{id}", response_model=LocationResponse)
def get_location(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Obtém detalhes de uma localização física."""
    use_case = LocationUseCases(db)
    try:
        return use_case.get_location(id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{id}", response_model=LocationResponse)
def update_location(
    id: int,
    data: LocationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_tecnico_or_admin),
):
    """Atualiza dados cadastrais de uma localização física."""
    use_case = LocationUseCases(db)
    try:
        return use_case.update_location(id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
