"""Casos de uso para manutenções preventivas e corretivas de ativos."""

from sqlalchemy.orm import Session
from src.core.exceptions import NotFoundError
from src.domain.models import AssetMaintenance
from src.domain.schemas import AssetMaintenanceCreate, AssetMaintenanceResponse
from src.infrastructure.repositories import (
    AssetMaintenanceRepository,
    AssetRepository,
)


class MaintenanceUseCases:
    """Implementa as regras de negócio para manutenções de ativos."""

    def __init__(self, db: Session):
        self.db = db
        self.maintenance_repo = AssetMaintenanceRepository(db)
        self.asset_repo = AssetRepository(db)

    def list_by_asset(self, asset_id: int) -> list[AssetMaintenanceResponse]:
        """Lista todas as intervenções de manutenção de um ativo patrimonial."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Ativo com ID {asset_id} não encontrado.")
        maintenances = self.maintenance_repo.list_by_asset(asset_id)
        return [AssetMaintenanceResponse.model_validate(m) for m in maintenances]

    def create_maintenance(
        self, asset_id: int, data: AssetMaintenanceCreate, registered_by_id: int
    ) -> AssetMaintenanceResponse:
        """Lança novo registro de manutenção preventiva ou corretiva."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Ativo com ID {asset_id} não encontrado.")

        maintenance = AssetMaintenance(
            asset_id=asset.id,
            registered_by_id=registered_by_id,
            maintenance_type=data.maintenance_type,
            service_provider=data.service_provider.strip() if data.service_provider else None,
            description=data.description.strip(),
            cost=data.cost,
            maintenance_date=data.maintenance_date,
        )
        self.maintenance_repo.create(maintenance)

        try:
            self.db.commit()
            self.db.refresh(maintenance)
            return AssetMaintenanceResponse.model_validate(maintenance)
        except Exception:
            self.db.rollback()
            raise
