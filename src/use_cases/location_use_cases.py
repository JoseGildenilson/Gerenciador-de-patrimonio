"""Casos de uso para gestão de localizações físicas."""

from sqlalchemy.orm import Session
from src.core.exceptions import ConflictError, NotFoundError
from src.domain.models import Location
from src.domain.schemas import LocationCreate, LocationUpdate, LocationResponse
from src.infrastructure.repositories import LocationRepository


class LocationUseCases:
    """Implementa as regras de negócio para localizações físicas."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = LocationRepository(db)

    def list_locations(
        self, building: str | None = None, sector: str | None = None
    ) -> list[LocationResponse]:
        """Lista localizações filtradas opcionalmente por prédio ou setor."""
        locations = self.repo.list_all(building=building, sector=sector)
        return [LocationResponse.model_validate(loc) for loc in locations]

    def get_location(self, location_id: int) -> LocationResponse:
        """Obtém detalhes de uma localização física por ID."""
        location = self.repo.get_by_id(location_id)
        if not location:
            raise NotFoundError(f"Localização com ID {location_id} não encontrada.")
        return LocationResponse.model_validate(location)

    def create_location(self, data: LocationCreate) -> LocationResponse:
        """Cadastra nova localização garantindo unicidade do espaço físico."""
        clean_room = data.room_number.strip() if data.room_number and data.room_number.strip() else None
        existing = self.repo.get_by_physical_space(
            building=data.building,
            floor=data.floor,
            sector=data.sector,
            room_number=clean_room,
        )
        if existing:
            raise ConflictError(
                f"Espaço físico já cadastrado: prédio '{data.building}', andar '{data.floor}', setor '{data.sector}', sala '{clean_room}'."
            )

        location = Location(
            building=data.building.strip(),
            floor=data.floor.strip(),
            sector=data.sector.strip(),
            room_number=clean_room,
            description=data.description.strip() if data.description else None,
        )
        self.repo.create(location)
        try:
            self.db.commit()
            self.db.refresh(location)
            return LocationResponse.model_validate(location)
        except Exception:
            self.db.rollback()
            raise

    def update_location(self, location_id: int, data: LocationUpdate) -> LocationResponse:
        """Atualiza dados de uma localização física."""
        location = self.repo.get_by_id(location_id)
        if not location:
            raise NotFoundError(f"Localização com ID {location_id} não encontrada.")

        new_b = data.building.strip() if data.building is not None else location.building
        new_f = data.floor.strip() if data.floor is not None else location.floor
        new_s = data.sector.strip() if data.sector is not None else location.sector
        if "room_number" in data.model_fields_set:
            new_r = data.room_number.strip() if data.room_number and data.room_number.strip() else None
        else:
            new_r = location.room_number

        existing = self.repo.get_by_physical_space(
            building=new_b,
            floor=new_f,
            sector=new_s,
            room_number=new_r,
        )
        if existing and existing.id != location_id:
            raise ConflictError(
                f"Conflito com espaço físico existente: prédio '{new_b}', andar '{new_f}', setor '{new_s}', sala '{new_r}'."
            )

        location.building = new_b
        location.floor = new_f
        location.sector = new_s
        location.room_number = new_r
        if data.description is not None:
            location.description = data.description.strip() or None

        try:
            self.db.commit()
            self.db.refresh(location)
            return LocationResponse.model_validate(location)
        except Exception:
            self.db.rollback()
            raise

    def delete_location(self, location_id: int) -> None:
        """Exclui uma localização se não houver ativos ou movimentações vinculadas (ON DELETE RESTRICT)."""
        location = self.repo.get_by_id(location_id)
        if not location:
            raise NotFoundError(f"Localização com ID {location_id} não encontrada.")

        if self.repo.has_dependencies(location_id):
            raise ConflictError(
                "Não é possível excluir a localização pois existem ativos ou movimentações vinculadas."
            )

        self.repo.delete(location)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
