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
        existing = self.repo.get_by_physical_space(
            building=data.building,
            floor=data.floor,
            sector=data.sector,
            room_number=data.room_number,
        )
        if existing:
            raise ConflictError(
                f"Espaço físico já cadastrado: prédio '{data.building}', andar '{data.floor}', setor '{data.sector}', sala '{data.room_number}'."
            )

        location = Location(
            building=data.building.strip(),
            floor=data.floor.strip(),
            sector=data.sector.strip(),
            room_number=data.room_number.strip() if data.room_number else None,
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
        new_r = data.room_number.strip() if data.room_number is not None else location.room_number

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
        location.room_number = new_r if new_r else None
        if data.description is not None:
            location.description = data.description.strip() if data.description else None

        try:
            self.db.commit()
            self.db.refresh(location)
            return LocationResponse.model_validate(location)
        except Exception:
            self.db.rollback()
            raise
