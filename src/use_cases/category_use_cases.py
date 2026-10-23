"""Casos de uso para gestão de categorias patrimoniais."""

from sqlalchemy.orm import Session
from src.core.exceptions import ConflictError, NotFoundError
from src.domain.models import Category
from src.domain.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from src.infrastructure.repositories import CategoryRepository


class CategoryUseCases:
    """Implementa as regras de negócio para categorias patrimoniais."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CategoryRepository(db)

    def list_categories(self) -> list[CategoryResponse]:
        """Lista todas as categorias cadastradas."""
        categories = self.repo.list_all()
        return [CategoryResponse.model_validate(c) for c in categories]

    def get_category(self, category_id: int) -> CategoryResponse:
        """Obtém os detalhes de uma categoria por ID."""
        category = self.repo.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Categoria com ID {category_id} não encontrada.")
        return CategoryResponse.model_validate(category)

    def create_category(self, data: CategoryCreate) -> CategoryResponse:
        """Cria uma nova categoria garantindo unicidade de nome."""
        existing = self.repo.get_by_name(data.name)
        if existing:
            raise ConflictError(f"Categoria com nome '{data.name}' já cadastrada.")

        category = Category(
            name=data.name.strip(),
            useful_life_months=data.useful_life_months,
            residual_value_rate=data.residual_value_rate,
            requires_serial_number=data.requires_serial_number,
        )
        self.repo.create(category)
        try:
            self.db.commit()
            self.db.refresh(category)
            return CategoryResponse.model_validate(category)
        except Exception:
            self.db.rollback()
            raise

    def update_category(self, category_id: int, data: CategoryUpdate) -> CategoryResponse:
        """Atualiza uma categoria existente."""
        category = self.repo.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Categoria com ID {category_id} não encontrada.")

        if data.name is not None and data.name.strip().lower() != category.name.lower():
            existing = self.repo.get_by_name(data.name)
            if existing and existing.id != category_id:
                raise ConflictError(f"Categoria com nome '{data.name}' já cadastrada.")
            category.name = data.name.strip()

        if data.useful_life_months is not None:
            category.useful_life_months = data.useful_life_months
        if data.residual_value_rate is not None:
            category.residual_value_rate = data.residual_value_rate
        if data.requires_serial_number is not None:
            category.requires_serial_number = data.requires_serial_number

        try:
            self.db.commit()
            self.db.refresh(category)
            return CategoryResponse.model_validate(category)
        except Exception:
            self.db.rollback()
            raise
