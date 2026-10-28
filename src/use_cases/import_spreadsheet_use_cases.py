"""Casos de uso para pré-visualização e execução de importação de planilhas de ativos."""

from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from src.domain.models import Asset, Category, Location, AssetMaintenance
from src.domain.schemas import (
    SpreadsheetImportPreviewResponse,
    SpreadsheetImportResultResponse,
    SpreadsheetRowPreview,
)
from src.infrastructure.repositories import (
    AssetRepository,
    CategoryRepository,
    LocationRepository,
    AssetMaintenanceRepository,
)
from src.infrastructure.spreadsheet_parser import parse_spreadsheet


class PreviewSpreadsheetUseCase:
    """Caso de uso para gerar prévia da planilha enviada sem persistência."""

    def execute(self, file_bytes: bytes, filename: str) -> SpreadsheetImportPreviewResponse:
        parsed = parse_spreadsheet(file_bytes, filename)

        sample_rows: list[SpreadsheetRowPreview] = []
        for r in parsed.rows[:10]:
            sample_rows.append(
                SpreadsheetRowPreview(
                    row_number=r.row_number,
                    category=r.equipment_type,
                    equipment_type=r.equipment_type,
                    location=r.location,
                    status=r.status,
                    description=r.description,
                    patrimony_number=r.patrimony_number,
                    serial_number=r.serial_number,
                    brand=r.brand,
                    model=r.model,
                    purchase_cost=None,
                    purchase_date=None,
                    notes=r.notes,
                )
            )

        return SpreadsheetImportPreviewResponse(
            filename=parsed.filename,
            total_rows=len(parsed.rows),
            sample_rows=sample_rows,
            detected_sheet=parsed.detected_sheet,
            headers=parsed.headers,
        )


class ExecuteSpreadsheetImportUseCase:
    """Caso de uso para execução transacional da importação da planilha no banco de dados."""

    def __init__(self, db: Session):
        self.db = db
        self.asset_repo = AssetRepository(db)
        self.category_repo = CategoryRepository(db)
        self.location_repo = LocationRepository(db)
        self.maintenance_repo = AssetMaintenanceRepository(db)

    def execute(self, file_bytes: bytes, filename: str) -> SpreadsheetImportResultResponse:
        parsed = parse_spreadsheet(file_bytes, filename)

        if not parsed.rows:
            return SpreadsheetImportResultResponse(
                success=True,
                total_rows=0,
                created_count=0,
                updated_count=0,
                categories_created_count=0,
                locations_created_count=0,
                maintenances_created_count=0,
                errors=[],
                message="Nenhuma linha de dados encontrada na planilha.",
            )

        # Caches em memória
        all_categories = {c.name.lower(): c for c in self.category_repo.list_all()}
        all_locations = {
            f"{loc.building.lower()}|{loc.sector.lower()}": loc
            for loc in self.location_repo.list_all()
        }

        categories_created_count = 0
        locations_created_count = 0

        def ensure_category(name: str) -> Category:
            nonlocal categories_created_count
            clean_name = name.strip()
            key = clean_name.lower()
            if key in all_categories:
                return all_categories[key]
            cat = Category(name=clean_name)
            self.category_repo.create(cat)
            self.db.flush()
            all_categories[key] = cat
            categories_created_count += 1
            return cat

        def ensure_location(loc_name: str) -> Location:
            nonlocal locations_created_count
            clean_sec = loc_name.strip()
            key = f"prédio central|{clean_sec.lower()}"
            if key in all_locations:
                return all_locations[key]
            loc = Location(
                building="Prédio Central",
                floor="1º Andar",
                sector=clean_sec,
                room_number=None,
                description="Localização gerada via importação de planilha",
            )
            self.location_repo.create(loc)
            self.db.flush()
            all_locations[key] = loc
            locations_created_count += 1
            return loc

        created_count = 0
        updated_count = 0
        maintenances_created_count = 0
        errors: list[str] = []

        try:
            for row in parsed.rows:
                cat = ensure_category(row.equipment_type or "Geral")
                loc = ensure_location(row.location or "Almoxarifado")

                # Normalização de status para o enum asset_status
                valid_status = "disponivel"
                if row.status:
                    norm_status = row.status.strip().lower()
                    if norm_status in ("em uso", "em_uso", "ativo", "alocado"):
                        valid_status = "em_uso"
                    elif norm_status in ("manutencao", "em manutencao", "em_manutencao", "conserto"):
                        valid_status = "em_manutencao"
                    elif norm_status in ("baixado", "desincorporado", "sucata"):
                        valid_status = "baixado"

                specs: dict = {}
                if row.hostname:
                    specs["hostname"] = row.hostname
                if row.ip_address:
                    specs["ip_address"] = row.ip_address
                if row.mac_address:
                    specs["mac_address"] = row.mac_address
                if row.notes:
                    specs["notes"] = row.notes

                patrimony_num = row.patrimony_number.strip() if row.patrimony_number else f"IMP-{row.row_number:05d}"
                serial_num = row.serial_number.strip() if row.serial_number else None

                asset = self.asset_repo.get_by_patrimony_number(patrimony_num)
                if asset is None and serial_num:
                    asset = self.asset_repo.get_by_serial_number(serial_num)

                if asset is not None:
                    asset.category_id = cat.id
                    asset.location_id = loc.id
                    asset.status = valid_status
                    if row.description:
                        asset.description = row.description
                    if row.brand:
                        asset.brand = row.brand
                    if row.model:
                        asset.model = row.model
                    asset.specs = specs
                    updated_count += 1
                else:
                    asset = Asset(
                        patrimony_number=patrimony_num,
                        serial_number=serial_num,
                        description=row.description or f"Ativo importado {patrimony_num}",
                        category_id=cat.id,
                        location_id=loc.id,
                        brand=row.brand or "Genérico",
                        model=row.model,
                        status=valid_status,
                        specs=specs,
                    )
                    self.asset_repo.create(asset)
                    created_count += 1

                self.db.flush()

                if row.last_maintenance_at:
                    maint = AssetMaintenance(
                        asset_id=asset.id,
                        registered_by_id=1,
                        maintenance_type="preventiva",
                        service_provider="Histórico Importado",
                        description="Manutenção registrada durante importação de planilha",
                        cost=Decimal("0.00"),
                        maintenance_date=row.last_maintenance_at,
                    )
                    self.maintenance_repo.create(maint)
                    maintenances_created_count += 1

            self.db.commit()

            return SpreadsheetImportResultResponse(
                success=True,
                total_rows=len(parsed.rows),
                created_count=created_count,
                updated_count=updated_count,
                categories_created_count=categories_created_count,
                locations_created_count=locations_created_count,
                catalogs_created_count=categories_created_count + locations_created_count,
                tags_created_count=categories_created_count + locations_created_count,
                maintenances_created_count=maintenances_created_count,
                errors=errors,
                message=f"Importação concluída: {created_count} criados, {updated_count} atualizados.",
            )
        except Exception as exc:
            self.db.rollback()
            raise ValueError(f"Falha ao persistir dados da planilha: {str(exc)}") from exc
