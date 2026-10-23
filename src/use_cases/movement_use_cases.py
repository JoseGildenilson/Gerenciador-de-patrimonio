"""Casos de uso para movimentação patrimonial e aceite de termos de responsabilidade."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.core.exceptions import NotFoundError
from src.domain.models import AssetMovement
from src.domain.schemas import AssetMovementCreate, AssetMovementResponse
from src.infrastructure.repositories import (
    AssetMovementRepository,
    AssetRepository,
    LocationRepository,
    UserRepository,
)


class AssetMovementUseCases:
    """Implementa as regras de negócio para transferências e custódia."""

    def __init__(self, db: Session):
        self.db = db
        self.movement_repo = AssetMovementRepository(db)
        self.asset_repo = AssetRepository(db)
        self.location_repo = LocationRepository(db)
        self.user_repo = UserRepository(db)

    def list_by_asset(self, asset_id: int) -> list[AssetMovementResponse]:
        """Lista o histórico de movimentações de um ativo específico."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Ativo com ID {asset_id} não encontrado.")
        movements = self.movement_repo.list_by_asset(asset_id)
        return [AssetMovementResponse.model_validate(m) for m in movements]

    def create_movement(
        self, asset_id: int, data: AssetMovementCreate, moved_by_id: int
    ) -> AssetMovementResponse:
        """Registra movimentação física ou transferência de custódia de um bem."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Ativo com ID {asset_id} não encontrado.")

        # Validar origem
        origin_loc = self.location_repo.get_by_id(data.origin_location_id)
        if not origin_loc:
            raise NotFoundError(
                f"Localização de origem com ID {data.origin_location_id} não encontrada."
            )

        # Validar destino se informado (pode ser nulo para baixa patrimonial)
        if data.dest_location_id is not None:
            dest_loc = self.location_repo.get_by_id(data.dest_location_id)
            if not dest_loc:
                raise NotFoundError(
                    f"Localização de destino com ID {data.dest_location_id} não encontrada."
                )
            asset.location_id = data.dest_location_id
        else:
            asset.status = "baixado"

        # Validar usuários envolvidos
        if data.from_user_id is not None:
            from_u = self.user_repo.get_by_id(data.from_user_id)
            if not from_u:
                raise NotFoundError(f"Usuário de origem com ID {data.from_user_id} não encontrado.")

        if data.to_user_id is not None:
            to_u = self.user_repo.get_by_id(data.to_user_id)
            if not to_u:
                raise NotFoundError(f"Usuário de destino com ID {data.to_user_id} não encontrado.")
            asset.assigned_user_id = data.to_user_id
        elif data.dest_location_id is None:
            # Baixa do bem remove custodiante
            asset.assigned_user_id = None

        movement = AssetMovement(
            asset_id=asset.id,
            origin_location_id=data.origin_location_id,
            dest_location_id=data.dest_location_id,
            from_user_id=data.from_user_id,
            to_user_id=data.to_user_id,
            moved_by_id=moved_by_id,
            movement_date=data.movement_date,
            notes=data.notes.strip() if data.notes else None,
        )
        self.movement_repo.create(movement)

        try:
            self.db.commit()
            self.db.refresh(movement)
            return AssetMovementResponse.model_validate(movement)
        except Exception:
            self.db.rollback()
            raise

    def accept_custody_term(self, movement_id: int) -> AssetMovementResponse:
        """Registra o aceite eletrônico do termo de responsabilidade pelo custodiante."""
        movement = self.movement_repo.get_by_id(movement_id)
        if not movement:
            raise NotFoundError(f"Movimentação com ID {movement_id} não encontrada.")

        movement.term_accepted_at = datetime.now(timezone.utc)
        try:
            self.db.commit()
            self.db.refresh(movement)
            return AssetMovementResponse.model_validate(movement)
        except Exception:
            self.db.rollback()
            raise
