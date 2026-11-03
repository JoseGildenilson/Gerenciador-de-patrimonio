"""Casos de uso para gestão de ativos patrimoniais, exportação, sugestões e renumeração."""

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
    AssetMovementResponse,
    AssetMaintenanceResponse,
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
from src.infrastructure.spreadsheet_exporter import generate_assets_spreadsheet


def _to_asset_response(asset: Asset) -> AssetResponse:
    """Converte entidade Asset em AssetResponse preenchendo last_maintenance_at."""
    resp = AssetResponse.model_validate(asset)
    if hasattr(asset, "computed_last_maintenance_at"):
        resp.last_maintenance_at = asset.computed_last_maintenance_at
    elif asset.maintenances:
        resp.last_maintenance_at = max(m.maintenance_date for m in asset.maintenances)
    return resp


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
            items=[_to_asset_response(a) for a in items],
            total=total,
            page=safe_page,
            limit=safe_limit,
            pages=pages,
        )

    def export_assets(
        self,
        category_id: int | None = None,
        location_id: int | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> bytes:
        """Exporta ativos filtrados em formato de planilha Excel (.xlsx)."""
        assets = self.asset_repo.list_for_export(
            category_id=category_id,
            location_id=location_id,
            status=status,
            search=search,
        )
        return generate_assets_spreadsheet(assets)

    def get_asset_suggestions(self, field: str, query: str | None = None) -> list[str]:
        """Retorna sugestões de valores distintos para autocomplete de filtros."""
        return self.asset_repo.get_suggestions(field=field, query=query)

    def get_asset(self, asset_id: int) -> AssetDetailResponse:
        """Obtém detalhes do ativo com histórico de renumeração, movimentações e manutenções."""
        asset = self.asset_repo.get_by_id(asset_id, eager_history=True)
        if not asset:
            raise NotFoundError(f"Ativo com ID {asset_id} não encontrado.")

        histories = [
            PatrimonyHistoryResponse.model_validate(h)
            for h in sorted(asset.patrimony_histories, key=lambda x: x.changed_at, reverse=True)
        ]
        movements = [
            AssetMovementResponse.model_validate(m)
            for m in sorted(asset.movements, key=lambda x: x.movement_date, reverse=True)
        ]
        maintenances = [
            AssetMaintenanceResponse.model_validate(m)
            for m in sorted(asset.maintenances, key=lambda x: x.maintenance_date, reverse=True)
        ]
        resp = AssetDetailResponse.model_validate(asset)
        resp.patrimony_history = histories
        resp.movements = movements
        resp.maintenances = maintenances
        if maintenances:
            resp.last_maintenance_at = maintenances[0].maintenance_date
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
            if not user.is_active:
                raise BusinessRuleError(
                    "Usuário custodiante está inativo e não pode receber atribuição de ativos."
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

        status_val = data.status.value if hasattr(data.status, "value") else str(data.status)

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
            status=status_val,
            specs=data.specs,
        )
        self.asset_repo.create(asset)
        try:
            self.db.commit()
            self.db.refresh(asset)
            return _to_asset_response(asset)
        except Exception:
            self.db.rollback()
            raise

    def update_asset(self, asset_id: int, data: AssetUpdate) -> AssetResponse:
        """Atualiza atributos cadastrais de um ativo patrimonial."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Ativo com ID {asset_id} não encontrado.")

        fields_set = data.model_fields_set

        if "category_id" in fields_set and data.category_id is not None:
            cat = self.cat_repo.get_by_id(data.category_id)
            if not cat:
                raise NotFoundError(f"Categoria com ID {data.category_id} não encontrada.")
            asset.category_id = data.category_id
        else:
            cat = self.cat_repo.get_by_id(asset.category_id)

        if "location_id" in fields_set and data.location_id is not None:
            loc = self.loc_repo.get_by_id(data.location_id)
            if not loc:
                raise NotFoundError(f"Localização com ID {data.location_id} não encontrada.")
            asset.location_id = data.location_id

        if "assigned_user_id" in fields_set:
            if data.assigned_user_id is None:
                asset.assigned_user_id = None
            else:
                user = self.user_repo.get_by_id(data.assigned_user_id)
                if not user:
                    raise NotFoundError(f"Usuário com ID {data.assigned_user_id} não encontrado.")
                if not user.is_active:
                    raise BusinessRuleError(
                        "Usuário custodiante está inativo e não pode receber atribuição de ativos."
                    )
                asset.assigned_user_id = data.assigned_user_id

        if "serial_number" in fields_set:
            clean_serial = data.serial_number.strip() if data.serial_number else None
            if clean_serial:
                existing_s = self.asset_repo.get_by_serial_number(clean_serial)
                if existing_s and existing_s.id != asset_id:
                    raise ConflictError(f"Número de série '{clean_serial}' já cadastrado.")
            effective_serial = clean_serial
        else:
            effective_serial = asset.serial_number

        if cat.requires_serial_number and not effective_serial:
            raise BusinessRuleError(
                f"A categoria '{cat.name}' exige o preenchimento obrigatório do número de série."
            )

        if "serial_number" in fields_set:
            asset.serial_number = effective_serial

        if "description" in fields_set and data.description is not None:
            asset.description = data.description.strip()
        if "brand" in fields_set and data.brand is not None:
            asset.brand = data.brand.strip()
        if "model" in fields_set:
            asset.model = data.model.strip() if data.model else None
        if "purchase_cost" in fields_set:
            asset.purchase_cost = data.purchase_cost
        if "purchase_date" in fields_set:
            asset.purchase_date = data.purchase_date
        if "status" in fields_set and data.status is not None:
            asset.status = data.status.value if hasattr(data.status, "value") else str(data.status)
        if "specs" in fields_set and data.specs is not None:
            asset.specs = data.specs

        try:
            self.db.commit()
            self.db.refresh(asset)
            return _to_asset_response(asset)
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
