"""Casos de uso para manutenções preventivas e corretivas de ativos."""

from sqlalchemy.orm import Session
from src.core.exceptions import BusinessRuleError, NotFoundError
from src.domain.models import AssetMaintenance
from src.domain.schemas import (
    AssetMaintenanceCreate,
    AssetMaintenanceUpdate,
    AssetMaintenanceResponse,
)
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

        if asset.status == "baixado":
            raise BusinessRuleError(
                "Ativo com status 'baixado' não pode receber novas manutenções sem restauração prévia."
            )

        m_type = (
            data.maintenance_type.value
            if hasattr(data.maintenance_type, "value")
            else str(data.maintenance_type)
        )

        maintenance = AssetMaintenance(
            asset_id=asset.id,
            registered_by_id=registered_by_id,
            maintenance_type=m_type,
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

    def update_maintenance(
        self, asset_id: int, maintenance_id: int, data: AssetMaintenanceUpdate
    ) -> AssetMaintenanceResponse:
        """Atualiza um registro existente de manutenção de um ativo."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Ativo com ID {asset_id} não encontrado.")

        maintenance = self.maintenance_repo.get_by_id(maintenance_id)
        if not maintenance or maintenance.asset_id != asset_id:
            raise NotFoundError(f"Manutenção com ID {maintenance_id} não encontrada.")

        fields_set = data.model_fields_set
        if "maintenance_type" in fields_set and data.maintenance_type is not None:
            maintenance.maintenance_type = (
                data.maintenance_type.value
                if hasattr(data.maintenance_type, "value")
                else str(data.maintenance_type)
            )
        if "service_provider" in fields_set:
            maintenance.service_provider = (
                data.service_provider.strip() if data.service_provider else None
            )
        if "description" in fields_set and data.description is not None:
            maintenance.description = data.description.strip()
        if "cost" in fields_set:
            maintenance.cost = data.cost
        if "maintenance_date" in fields_set and data.maintenance_date is not None:
            maintenance.maintenance_date = data.maintenance_date

        try:
            self.db.commit()
            self.db.refresh(maintenance)
            return AssetMaintenanceResponse.model_validate(maintenance)
        except Exception:
            self.db.rollback()
            raise

    def delete_maintenance(self, asset_id: int, maintenance_id: int) -> None:
        """Remove um registro de manutenção de um ativo."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Ativo com ID {asset_id} não encontrado.")

        maintenance = self.maintenance_repo.get_by_id(maintenance_id)
        if not maintenance or maintenance.asset_id != asset_id:
            raise NotFoundError(f"Manutenção com ID {maintenance_id} não encontrada.")

        self.maintenance_repo.delete(maintenance)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
