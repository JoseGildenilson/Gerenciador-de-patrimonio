"""Rotas HTTP para gestão de categorias patrimoniais."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_user, require_tecnico_or_admin
from src.core.database import get_db
from src.core.exceptions import ConflictError, NotFoundError
from src.domain.models import User
from src.domain.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from src.use_cases.category_use_cases import CategoryUseCases

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Lista todas as categorias patrimoniais cadastradas."""
    use_case = CategoryUseCases(db)
    return use_case.list_categories()


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_tecnico_or_admin),
):
    """Cadastra uma nova categoria patrimonial (requer perfil técnico ou administrador)."""
    use_case = CategoryUseCases(db)
    try:
        return use_case.create_category(data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{id}", response_model=CategoryResponse)
def get_category(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Obtém detalhes de uma categoria por ID."""
    use_case = CategoryUseCases(db)
    try:
        return use_case.get_category(id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{id}", response_model=CategoryResponse)
def update_category(
    id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_tecnico_or_admin),
):
    """Atualiza dados de uma categoria existente."""
    use_case = CategoryUseCases(db)
    try:
        return use_case.update_category(id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
