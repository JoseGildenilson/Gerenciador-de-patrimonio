"""Script para popular o banco de dados com dados iniciais (seed) e fictícios para testes."""

from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.core.security import hash_password, encrypt_windows_product_key
from src.domain.models import (
    User,
    Equipment,
    EquipmentType,
    Sector,
    EquipmentStatus,
    MaintenanceType,
    EquipmentMovement,
    EquipmentMaintenance,
    Category,
    Location,
    Asset,
    PatrimonyHistory,
    AssetMovement,
    AssetMaintenance,
)

DEFAULT_TYPES = ["Desktop", "Notebook", "Monitor", "Impressora"]
DEFAULT_SECTORS = ["TI", "Comunicação", "Rádio Produção", "Diretoria", "Almoxarifado"]
DEFAULT_STATUSES = [
    "Em uso",
    "Em manutenção",
    "Baixado",
    "Ocioso",
    "Aguardando recolhimento",
    "Alienação",
    "Exposição",
    "Acautelado",
]
DEFAULT_MAINTENANCE_TYPES = ["Preventiva", "Corretiva"]


def seed_catalogs(db: Session) -> dict:
    """Insere os catálogos padrão no banco de dados se ainda não existirem."""
    types_map = {}
    for name in DEFAULT_TYPES:
        item = (
            db.query(EquipmentType).filter(func.lower(EquipmentType.name) == name.lower()).first()
        )
        if not item:
            item = EquipmentType(name=name)
            db.add(item)
            db.flush()
        types_map[name] = item

    sectors_map = {}
    for name in DEFAULT_SECTORS:
        item = db.query(Sector).filter(func.lower(Sector.name) == name.lower()).first()
        if not item:
            item = Sector(name=name)
            db.add(item)
            db.flush()
        sectors_map[name] = item

    statuses_map = {}
    for name in DEFAULT_STATUSES:
        item = (
            db.query(EquipmentStatus)
            .filter(func.lower(EquipmentStatus.name) == name.lower())
            .first()
        )
        if not item:
            item = EquipmentStatus(name=name)
            db.add(item)
            db.flush()
        statuses_map[name] = item

    maint_types_map = {}
    for name in DEFAULT_MAINTENANCE_TYPES:
        item = (
            db.query(MaintenanceType)
            .filter(func.lower(MaintenanceType.name) == name.lower())
            .first()
        )
        if not item:
            item = MaintenanceType(name=name)
            db.add(item)
            db.flush()
        maint_types_map[name] = item

    return {
        "types": types_map,
        "sectors": sectors_map,
        "statuses": statuses_map,
        "maintenance_types": maint_types_map,
    }


def seed_database():
    """Insere dados fictícios no banco de dados se ainda não existirem."""
    db = SessionLocal()
    try:
        # Seed catálogos
        catalogs = seed_catalogs(db)

        # Seed técnico
        tecnico = db.query(User).filter(User.email == "tecnico@empresa.com").first()
        if not tecnico:
            tecnico = User(
                name="Técnico de TI",
                email="tecnico@empresa.com",
                password_hash=hash_password("senha123"),
                role="tecnico",
                is_active=True,
            )
            db.add(tecnico)
            db.flush()

        # Seed colaborador
        colaborador = db.query(User).filter(User.email == "colaborador@empresa.com").first()
        if not colaborador:
            colaborador = User(
                name="Colaborador Exemplo",
                email="colaborador@empresa.com",
                password_hash=hash_password("senha123"),
                role="colaborador",
                is_active=True,
            )
            db.add(colaborador)
            db.flush()

        # Equipamentos
        if db.query(Equipment).count() == 0:
            eq1 = Equipment(
                description="Notebook Dell Latitude 3420 Core i5, 16GB RAM",
                serial_number="SN-DELL-3420",
                patrimony_number="PAT-1001",
                hostname="note-ti-01",
                brand="Dell",
                model="Latitude 3420",
                equipment_type_id=catalogs["types"]["Notebook"].id,
                sector_id=catalogs["sectors"]["TI"].id,
                status_id=catalogs["statuses"]["Em uso"].id,
                ip_address="192.168.1.101",
                mac_address="00:1A:2B:3C:4D:5E",
                windows_product_key_encrypted=encrypt_windows_product_key(
                    "VK9X2-N8Y4R-W3M2T-K7P1Q-L9Z0A"
                ),
            )
            eq2 = Equipment(
                description="Monitor LG 29' Ultrawide IPS 75Hz",
                serial_number="SN-LG-29-001",
                patrimony_number="PAT-1002",
                brand="LG",
                model="29WK600",
                equipment_type_id=catalogs["types"]["Monitor"].id,
                sector_id=catalogs["sectors"]["Comunicação"].id,
                status_id=catalogs["statuses"]["Ocioso"].id,
            )
            eq3 = Equipment(
                description="Desktop OptiPlex 7090",
                serial_number="SN-DELL-7090",
                patrimony_number="PAT-1003",
                hostname="desk-radio-01",
                brand="Dell",
                model="OptiPlex 7090",
                equipment_type_id=catalogs["types"]["Desktop"].id,
                sector_id=catalogs["sectors"]["Rádio Produção"].id,
                status_id=catalogs["statuses"]["Em uso"].id,
                ip_address="192.168.1.103",
                mac_address="00:1A:2B:3C:4D:6F",
                windows_product_key_encrypted=encrypt_windows_product_key(
                    "WM8R9-B2V4C-N5X7Z-K3P1L-J9Q0W"
                ),
            )
            eq4 = Equipment(
                description="Impressora HP LaserJet Pro M404dw",
                serial_number="SN-HP-M404DW",
                patrimony_number="PAT-1004",
                brand="HP",
                model="LaserJet Pro M404dw",
                printer_identifier="PRN-TI-01",
                equipment_type_id=catalogs["types"]["Impressora"].id,
                sector_id=catalogs["sectors"]["TI"].id,
                status_id=catalogs["statuses"]["Em manutenção"].id,
                ip_address="192.168.1.104",
            )
            db.add_all([eq1, eq2, eq3, eq4])
            db.flush()

            # Histórico de transferências para eq1: Almoxarifado -> TI
            mov = EquipmentMovement(
                equipment_id=eq1.id,
                origin_sector_id=catalogs["sectors"]["Almoxarifado"].id,
                destination_sector_id=catalogs["sectors"]["TI"].id,
                performed_by_user_id=tecnico.id,
                notes="Alocação inicial",
            )
            db.add(mov)

            # Manutenção para eq4 (Em manutenção)
            maint = EquipmentMaintenance(
                equipment_id=eq4.id,
                maintenance_type_id=catalogs["maintenance_types"]["Corretiva"].id,
                performed_by_user_id=tecnico.id,
                description="Troca de fusor danificado",
            )
            db.add(maint)

        # Categorias SisPatrimonio
        cat_info = db.query(Category).filter(Category.name == "Equipamentos de Informática").first()
        if not cat_info:
            cat_info = Category(
                name="Equipamentos de Informática",
                useful_life_months=60,
                residual_value_rate=10.00,
                requires_serial_number=True,
            )
            db.add(cat_info)
            db.flush()

        cat_mob = db.query(Category).filter(Category.name == "Mobiliário e Utensílios").first()
        if not cat_mob:
            cat_mob = Category(
                name="Mobiliário e Utensílios",
                useful_life_months=120,
                residual_value_rate=5.00,
                requires_serial_number=False,
            )
            db.add(cat_mob)
            db.flush()

        # Localizações SisPatrimonio
        loc1 = (
            db.query(Location)
            .filter(
                Location.building == "Prédio Central",
                Location.floor == "1º Andar",
                Location.sector == "TI",
                Location.room_number == "101",
            )
            .first()
        )
        if not loc1:
            loc1 = Location(
                building="Prédio Central",
                floor="1º Andar",
                sector="TI",
                room_number="101",
                description="Sala de Suporte Técnico",
            )
            db.add(loc1)
            db.flush()

        loc2 = (
            db.query(Location)
            .filter(
                Location.building == "Bloco B",
                Location.floor == "Térreo",
                Location.sector == "Almoxarifado",
                Location.room_number.is_(None),
            )
            .first()
        )
        if not loc2:
            loc2 = Location(
                building="Bloco B",
                floor="Térreo",
                sector="Almoxarifado",
                room_number=None,
                description="Depósito Geral",
            )
            db.add(loc2)
            db.flush()

        # Usuário Administrador SisPatrimonio
        admin = db.query(User).filter(User.email == "admin@sispatrimonio.edu.br").first()
        if not admin:
            admin = User(
                name="Administrador do Sistema",
                email="admin@sispatrimonio.edu.br",
                password_hash=hash_password("senha123"),
                role="administrador",
                is_active=True,
            )
            db.add(admin)
            db.flush()

        # Ativo inicial SisPatrimonio
        if db.query(Asset).count() == 0:
            asset1 = Asset(
                patrimony_number="SIS-0001",
                serial_number="SN-SIS-001",
                description="Workstation Dell Precision 3660",
                category_id=cat_info.id,
                location_id=loc1.id,
                assigned_user_id=tecnico.id,
                brand="Dell",
                model="Precision 3660",
                purchase_cost=8500.00,
                status="em_uso",
                specs={"cpu": "Intel Core i7-12700", "ram": "32GB", "storage": "1TB NVMe"},
            )
            db.add(asset1)
            db.flush()

            asset2 = Asset(
                patrimony_number="SIS-0002",
                serial_number="SN-SIS-002",
                description="Notebook ThinkPad T14 Gen 3",
                category_id=cat_info.id,
                location_id=loc1.id,
                assigned_user_id=colaborador.id,
                brand="Lenovo",
                model="ThinkPad T14",
                purchase_cost=6200.00,
                status="em_uso",
                specs={"cpu": "Ryzen 7 PRO", "ram": "16GB", "storage": "512GB SSD"},
            )
            db.add(asset2)
            db.flush()

            # Histórico de renumeração para asset1
            hist = PatrimonyHistory(
                asset_id=asset1.id,
                old_patrimony_number="SIS-0000-ANTIGO",
                new_patrimony_number="SIS-0001",
                reason="Substituição de plaqueta danificada",
                changed_by_id=tecnico.id,
            )
            db.add(hist)

            # Movimentação física e custódia para asset2
            mov = AssetMovement(
                asset_id=asset2.id,
                origin_location_id=loc2.id,
                dest_location_id=loc1.id,
                from_user_id=None,
                to_user_id=colaborador.id,
                moved_by_id=tecnico.id,
                notes="Alocação inicial do equipamento de trabalho",
            )
            db.add(mov)

            # Manutenção técnica para asset1
            maint = AssetMaintenance(
                asset_id=asset1.id,
                registered_by_id=tecnico.id,
                maintenance_type="preventiva",
                service_provider="Equipe Interna de TI",
                description="Limpeza preventiva de coolers e diagnóstico de hardware",
                cost=0.00,
                maintenance_date=datetime.now(timezone.utc),
            )
            db.add(maint)

        db.commit()
        print("Banco de dados semeado com sucesso!")
    except Exception as e:
        db.rollback()
        print(f"Erro ao semear banco de dados: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
