"""Casos de uso para pré-visualização e execução de importação de planilhas."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.core.security import encrypt_windows_product_key
from src.domain.models import (
    Equipment,
    EquipmentType,
    Sector,
    EquipmentStatus,
    MaintenanceType,
    EquipmentMaintenance,
)
from src.domain.schemas import (
    SpreadsheetImportPreviewResponse,
    SpreadsheetImportResultResponse,
    SpreadsheetRowPreview,
    validate_host_ip,
)
from src.infrastructure.repositories import (
    EquipmentRepository,
    CatalogsRepository,
    EquipmentMaintenanceRepository,
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
                    equipment_type=r.equipment_type,
                    location=r.location,
                    status=r.status,
                    description=r.description,
                    patrimony_number=r.patrimony_number,
                    serial_number=r.serial_number,
                    brand=r.brand,
                    model=r.model,
                    ip_address=r.ip_address,
                    mac_address=r.mac_address,
                    printer_identifier=r.printer_identifier,
                    windows_key=r.windows_key,
                    last_maintenance_at=r.last_maintenance_at.strftime("%d/%m/%Y")
                    if r.last_maintenance_at
                    else None,
                    hist_mov=r.hist_mov,
                    hostname=r.hostname,
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
        self.equipment_repo = EquipmentRepository(db)
        self.cat_repo = CatalogsRepository(db)
        self.maintenance_repo = EquipmentMaintenanceRepository(db)

    def execute(self, file_bytes: bytes, filename: str) -> SpreadsheetImportResultResponse:
        parsed = parse_spreadsheet(file_bytes, filename)

        if not parsed.rows:
            return SpreadsheetImportResultResponse(
                success=True,
                total_rows=0,
                created_count=0,
                updated_count=0,
                catalogs_created_count=0,
                tags_created_count=0,
                maintenances_created_count=0,
                errors=[],
                message="Nenhuma linha de dados encontrada na planilha.",
            )

        # Caches em memória dos catálogos
        all_types = {t.name.lower(): t for t in self.cat_repo.list_all(EquipmentType)}
        all_sectors = {s.name.lower(): s for s in self.cat_repo.list_all(Sector)}
        all_statuses = {st.name.lower(): st for st in self.cat_repo.list_all(EquipmentStatus)}
        all_maint_types = {mt.name.lower(): mt for mt in self.cat_repo.list_all(MaintenanceType)}

        catalogs_created_count = 0

        def ensure_catalog(model_cls, cache_dict: dict, name: str):
            nonlocal catalogs_created_count
            clean_name = name.strip()
            key = clean_name.lower()
            if key in cache_dict:
                item = cache_dict[key]
                if item.deleted_at is not None:
                    self.cat_repo.restore(item)
                return item

            item = model_cls(name=clean_name)
            self.cat_repo.create(item)
            self.db.flush()
            cache_dict[key] = item
            catalogs_created_count += 1
            return item

        created_count = 0
        updated_count = 0
        maintenances_created_count = 0
        errors: list[str] = []

        try:
            for row in parsed.rows:
                # 1. Resolve ou cria catálogos
                eq_type = ensure_catalog(EquipmentType, all_types, row.equipment_type)
                sector = ensure_catalog(Sector, all_sectors, row.location)
                status = ensure_catalog(EquipmentStatus, all_statuses, row.status)

                # 2. Sanitiza e valida IP
                cleaned_ip = None
                if row.ip_address:
                    try:
                        cleaned_ip = validate_host_ip(row.ip_address)
                    except Exception:
                        cleaned_ip = None

                # 3. Chave do Windows criptografada
                encrypted_windows_key = encrypt_windows_product_key(row.windows_key)

                # 4. Busca equipamento existente (patrimônio ou serial)
                equipment: Equipment | None = None
                if row.patrimony_number:
                    equipment = self.equipment_repo.get_by_patrimony_number(row.patrimony_number)
                if equipment is None and row.serial_number:
                    equipment = self.equipment_repo.get_by_serial_number(row.serial_number)

                if equipment is not None:
                    # Atualiza registro existente
                    if equipment.deleted_at is not None:
                        self.equipment_repo.restore(equipment)
                    equipment.equipment_type_id = eq_type.id
                    equipment.sector_id = sector.id
                    equipment.status_id = status.id
                    equipment.description = row.description
                    equipment.brand = row.brand or equipment.brand
                    equipment.model = row.model or equipment.model
                    equipment.hostname = row.hostname or equipment.hostname
                    equipment.ip_address = cleaned_ip or equipment.ip_address
                    equipment.mac_address = row.mac_address or equipment.mac_address
                    equipment.printer_identifier = (
                        row.printer_identifier or equipment.printer_identifier
                    )
                    if encrypted_windows_key:
                        equipment.windows_product_key_encrypted = encrypted_windows_key
                    equipment.notes = row.notes or equipment.notes
                    if row.patrimony_number and not equipment.patrimony_number:
                        equipment.patrimony_number = row.patrimony_number
                    if row.serial_number and not equipment.serial_number:
                        equipment.serial_number = row.serial_number

                    updated_count += 1
                else:
                    patrimony = row.patrimony_number or f"IMPORT-{row.row_number:05d}"
                    equipment = Equipment(
                        patrimony_number=patrimony,
                        equipment_type_id=eq_type.id,
                        sector_id=sector.id,
                        status_id=status.id,
                        description=row.description,
                        serial_number=row.serial_number,
                        brand=row.brand,
                        model=row.model,
                        hostname=row.hostname,
                        ip_address=cleaned_ip,
                        mac_address=row.mac_address,
                        printer_identifier=row.printer_identifier,
                        windows_product_key_encrypted=encrypted_windows_key,
                        notes=row.notes,
                    )
                    self.equipment_repo.create(equipment)
                    self.db.flush()
                    created_count += 1

                # 5. Registro consolidado de histórico de manutenção se houver
                if row.hist_mov:
                    hist_maint_type = ensure_catalog(
                        MaintenanceType, all_maint_types, "Histórico Importado"
                    )
                    maint_date = row.last_maintenance_at or datetime.now(timezone.utc)
                    maintenance = EquipmentMaintenance(
                        equipment_id=equipment.id,
                        started_at=maint_date,
                        completed_at=maint_date,
                        maintenance_type_id=hist_maint_type.id,
                        description=row.hist_mov,
                        notes=None,
                    )
                    self.maintenance_repo.create(maintenance)
                    maintenances_created_count += 1

            self.db.commit()

            return SpreadsheetImportResultResponse(
                success=True,
                total_rows=len(parsed.rows),
                created_count=created_count,
                updated_count=updated_count,
                catalogs_created_count=catalogs_created_count,
                tags_created_count=catalogs_created_count,
                maintenances_created_count=maintenances_created_count,
                errors=errors,
                message=f"Importação concluída: {created_count} novos equipamentos, {updated_count} atualizados e {catalogs_created_count} itens de catálogo cadastrados.",
            )
        except Exception:
            self.db.rollback()
            raise
