"""Casos de uso para gestão de ativos patrimoniais e renumeração."""

from datetime import datetime, timezone
import math
from sqlalchemy.orm import Session
from src.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from src.domain.models import Asset, PatrimonyHistory
from src.domain.schemas import (
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    AssetDetailResponse,
    AssetListResponse,
    PatrimonyHistoryResponse,
    PatrimonyRenumberRequest,
)
from src.infrastructure.repositories import (
    AssetRepository,
    CategoryRepository,
    LocationRepository,
    PatrimonyHistoryRepository,
    UserRepository,
)


class AssetUseCases:
    """Implementa as regras de negócio para ativos patrimoniais."""

    def __init__(self, db: Session):
        self.db = db
        self.asset_repo = AssetRepository(db)
        self.cat_repo = CategoryRepository(db)
        self.loc_repo = LocationRepository(db)
        self.user_repo = UserRepository(db)
        self.history_repo = PatrimonyHistoryRepository(db)

    def list_assets(
        self,
        category_id: int | None = None,
        location_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 25,
    ) -> AssetListResponse:
        """Lista ativos de forma paginada com filtros opcionais."""
        safe_page = max(1, page)
        safe_limit = max(1, min(limit, 100))
        items, total = self.asset_repo.list(
            category_id=category_id,
            location_id=location_id,
            status=status,
            search=search,
            page=safe_page,
            limit=safe_limit,
        )
        pages = math.ceil(total / safe_limit) if total > 0 else 1
        return AssetListResponse(
            items=[AssetResponse.model_validate(a) for a in items],
            total=total,
            page=safe_page,
            limit=safe_limit,
            pages=pages,
        )

    def get_asset(self, asset_id: int) -> AssetDetailResponse:
        """Obtém detalhes do ativo com histórico de renumeração."""
        asset = self.asset_repo.get_by_id(asset_id, eager_history=True)
        if not asset:
            raise NotFoundError(f"Ativo com ID {asset_id} não encontrado.")

        histories = [
            PatrimonyHistoryResponse.model_validate(h)
            for h in sorted(asset.patrimony_histories, key=lambda x: x.changed_at, reverse=True)
        ]
        resp = AssetDetailResponse.model_validate(asset)
        resp.patrimony_history = histories
        return resp

    def create_asset(self, data: AssetCreate) -> AssetResponse:
        """Cadastra novo ativo patrimonial validando integridade e unicidade."""
        # 1. Validar categoria
        category = self.cat_repo.get_by_id(data.category_id)
        if not category:
            raise NotFoundError(f"Categoria com ID {data.category_id} não encontrada.")

        # 2. Validar serial se categoria exigir
        clean_serial = data.serial_number.strip() if data.serial_number else None
        if category.requires_serial_number and not clean_serial:
            raise BusinessRuleError(
                f"A categoria '{category.name}' exige o preenchimento obrigatório do número de série."
            )

        # 3. Validar localização
        location = self.loc_repo.get_by_id(data.location_id)
        if not location:
            raise NotFoundError(f"Localização com ID {data.location_id} não encontrada.")

        # 4. Validar usuário atribuído se informado
        if data.assigned_user_id is not None:
            user = self.user_repo.get_by_id(data.assigned_user_id)
            if not user:
                raise NotFoundError(
                    f"Usuário custodiante com ID {data.assigned_user_id} não encontrado."
                )

        # 5. Validar unicidade de patrimony_number
        existing_pat = self.asset_repo.get_by_patrimony_number(data.patrimony_number)
        if existing_pat:
            raise ConflictError(f"Número de patrimônio '{data.patrimony_number}' já cadastrado.")

        # 6. Validar unicidade de serial_number
        if clean_serial:
            existing_serial = self.asset_repo.get_by_serial_number(clean_serial)
            if existing_serial:
                raise ConflictError(f"Número de série '{clean_serial}' já cadastrado.")

        asset = Asset(
            patrimony_number=data.patrimony_number.strip(),
            serial_number=clean_serial,
            description=data.description.strip(),
            category_id=data.category_id,
            location_id=data.location_id,
            assigned_user_id=data.assigned_user_id,
            brand=data.brand.strip(),
            model=data.model.strip() if data.model else None,
            purchase_cost=data.purchase_cost,
            purchase_date=data.purchase_date,
            status=data.status,
            specs=data.specs,
        )
        self.asset_repo.create(asset)
        try:
            self.db.commit()
            self.db.refresh(asset)
            return AssetResponse.model_validate(asset)
        except Exception:
            self.db.rollback()
            raise

    def update_asset(self, asset_id: int, data: AssetUpdate) -> AssetResponse:
        """Atualiza atributos cadastrais de um ativo patrimonial."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Ativo com ID {asset_id} não encontrado.")

        if data.category_id is not None:
            cat = self.cat_repo.get_by_id(data.category_id)
            if not cat:
                raise NotFoundError(f"Categoria com ID {data.category_id} não encontrada.")
            asset.category_id = data.category_id

        if data.location_id is not None:
            loc = self.loc_repo.get_by_id(data.location_id)
            if not loc:
                raise NotFoundError(f"Localização com ID {data.location_id} não encontrada.")
            asset.location_id = data.location_id

        if data.assigned_user_id is not None:
            user = self.user_repo.get_by_id(data.assigned_user_id)
            if not user:
                raise NotFoundError(f"Usuário com ID {data.assigned_user_id} não encontrado.")
            asset.assigned_user_id = data.assigned_user_id

        if data.serial_number is not None:
            clean_serial = data.serial_number.strip() if data.serial_number else None
            if clean_serial:
                existing_s = self.asset_repo.get_by_serial_number(clean_serial)
                if existing_s and existing_s.id != asset_id:
                    raise ConflictError(f"Número de série '{clean_serial}' já cadastrado.")
            asset.serial_number = clean_serial

        if data.description is not None:
            asset.description = data.description.strip()
        if data.brand is not None:
            asset.brand = data.brand.strip()
        if data.model is not None:
            asset.model = data.model.strip() if data.model else None
        if data.purchase_cost is not None:
            asset.purchase_cost = data.purchase_cost
        if data.purchase_date is not None:
            asset.purchase_date = data.purchase_date
        if data.status is not None:
            asset.status = data.status
        if data.specs is not None:
            asset.specs = data.specs

        try:
            self.db.commit()
            self.db.refresh(asset)
            return AssetResponse.model_validate(asset)
        except Exception:
            self.db.rollback()
            raise

    def renumber_patrimony(
        self, asset_id: int, data: PatrimonyRenumberRequest, changed_by_user_id: int
    ) -> PatrimonyHistoryResponse:
        """Renumera o patrimônio do ativo e registra entrada no histórico imutável."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Ativo com ID {asset_id} não encontrado.")

        new_number = data.new_patrimony_number.strip()
        if new_number.lower() == asset.patrimony_number.lower():
            raise ConflictError("O novo número de patrimônio deve ser diferente do número atual.")

        existing = self.asset_repo.get_by_patrimony_number(new_number)
        if existing:
            raise ConflictError(f"Número de patrimônio '{new_number}' já cadastrado no sistema.")

        old_number = asset.patrimony_number
        asset.patrimony_number = new_number

        history = PatrimonyHistory(
            asset_id=asset.id,
            old_patrimony_number=old_number,
            new_patrimony_number=new_number,
            reason=data.reason.strip(),
            changed_by_id=changed_by_user_id,
            changed_at=datetime.now(timezone.utc),
        )
        self.history_repo.create(history)

        try:
            self.db.commit()
            self.db.refresh(history)
            return PatrimonyHistoryResponse.model_validate(history)
        except Exception:
            self.db.rollback()
            raise

    def delete_asset(self, asset_id: int) -> None:
        """Exclui logicamente um ativo."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Ativo com ID {asset_id} não encontrado.")
        self.asset_repo.soft_delete(asset)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
