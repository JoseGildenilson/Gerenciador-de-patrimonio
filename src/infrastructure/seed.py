"""Script para popular o banco de dados com dados iniciais (seed) e fictícios para testes."""

from datetime import datetime, timedelta, timezone
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
    """Insere dados fictícios ricos no banco de dados com idempotência."""
    db = SessionLocal()
    try:
        # 1. Catálogos
        catalogs = seed_catalogs(db)

        # 2. Usuários (Preservando os 3 usuários existentes)
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

        now = datetime.now(timezone.utc)

        # 3. Equipamentos (20 equipamentos completos e diversificados)
        equipments_data = [
            {
                "patrimony_number": "PAT-1001",
                "serial_number": "SN-DELL-3420",
                "description": "Notebook Dell Latitude 3420 Core i5 11ª Gen, 16GB RAM, 512GB SSD",
                "hostname": "note-ti-01",
                "brand": "Dell",
                "model": "Latitude 3420",
                "type": "Notebook",
                "sector": "TI",
                "status": "Em uso",
                "ip": "192.168.1.101",
                "mac": "00:1A:2B:3C:4D:5E",
                "win_key": "VK9X2-N8Y4R-W3M2T-K7P1Q-L9Z0A",
            },
            {
                "patrimony_number": "PAT-1002",
                "serial_number": "SN-LG-29-001",
                "description": "Monitor LG 29' Ultrawide IPS 75Hz Full HD com HDR10",
                "hostname": None,
                "brand": "LG",
                "model": "29WK600",
                "type": "Monitor",
                "sector": "Comunicação",
                "status": "Ocioso",
                "ip": None,
                "mac": None,
                "win_key": None,
            },
            {
                "patrimony_number": "PAT-1003",
                "serial_number": "SN-DELL-7090",
                "description": "Desktop Dell OptiPlex 7090 Core i7 10ª Gen, 16GB RAM, 1TB NVMe",
                "hostname": "desk-radio-01",
                "brand": "Dell",
                "model": "OptiPlex 7090",
                "type": "Desktop",
                "sector": "Rádio Produção",
                "status": "Em uso",
                "ip": "192.168.1.103",
                "mac": "00:1A:2B:3C:4D:6F",
                "win_key": "WM8R9-B2V4C-N5X7Z-K3P1L-J9Q0W",
            },
            {
                "patrimony_number": "PAT-1004",
                "serial_number": "SN-HP-M404DW",
                "description": "Impressora HP LaserJet Pro M404dw Laser Monocromática Duplex",
                "hostname": None,
                "brand": "HP",
                "model": "LaserJet Pro M404dw",
                "type": "Impressora",
                "sector": "TI",
                "status": "Em manutenção",
                "ip": "192.168.1.104",
                "mac": "00:1A:2B:3C:4D:7A",
                "printer_id": "PRN-TI-01",
                "win_key": None,
            },
            {
                "patrimony_number": "PAT-1005",
                "serial_number": "SN-LENOVO-T14",
                "description": "Notebook Lenovo ThinkPad T14 Gen 3 Ryzen 7 PRO, 32GB RAM",
                "hostname": "note-dir-01",
                "brand": "Lenovo",
                "model": "ThinkPad T14",
                "type": "Notebook",
                "sector": "Diretoria",
                "status": "Em uso",
                "ip": "192.168.1.105",
                "mac": "00:1A:2B:3C:4D:7B",
                "win_key": "T14G3-RYZ7P-32GBR-SSD1T-WIN11",
            },
            {
                "patrimony_number": "PAT-1006",
                "serial_number": "SN-DELL-U2723",
                "description": "Monitor Dell UltraSharp 27 4K IPS Black USB-C Hub U2723QE",
                "hostname": None,
                "brand": "Dell",
                "model": "U2723QE",
                "type": "Monitor",
                "sector": "Comunicação",
                "status": "Em uso",
                "ip": None,
                "mac": None,
                "win_key": None,
            },
            {
                "patrimony_number": "PAT-1007",
                "serial_number": "SN-LENOVO-M70Q",
                "description": "Desktop Lenovo ThinkCentre M70q Tiny Core i5 12ª Gen, 16GB",
                "hostname": "desk-ti-02",
                "brand": "Lenovo",
                "model": "ThinkCentre M70q",
                "type": "Desktop",
                "sector": "TI",
                "status": "Ocioso",
                "ip": "192.168.1.107",
                "mac": "00:1A:2B:3C:4D:7D",
                "win_key": "M70QT-I512G-16GBR-512SS-W11PR",
            },
            {
                "patrimony_number": "PAT-1008",
                "serial_number": "SN-DELL-INSP3511",
                "description": "Notebook Dell Inspiron 15 Core i5 8GB RAM 256GB SSD",
                "hostname": "note-almox-01",
                "brand": "Dell",
                "model": "Inspiron 15 3511",
                "type": "Notebook",
                "sector": "Almoxarifado",
                "status": "Aguardando recolhimento",
                "ip": "192.168.1.108",
                "mac": "00:1A:2B:3C:4D:7E",
                "win_key": None,
            },
            {
                "patrimony_number": "PAT-1009",
                "serial_number": "SN-BROTHER-L2540",
                "description": "Multifuncional Brother Laser Monocromática DCP-L2540DW Wi-Fi",
                "hostname": None,
                "brand": "Brother",
                "model": "DCP-L2540DW",
                "type": "Impressora",
                "sector": "Comunicação",
                "status": "Em uso",
                "ip": "192.168.1.109",
                "mac": "00:1A:2B:3C:4D:7F",
                "printer_id": "PRN-COM-01",
                "win_key": None,
            },
            {
                "patrimony_number": "PAT-1010",
                "serial_number": "SN-SAMSUNG-T350",
                "description": "Monitor Samsung 24 FHD 75Hz IPS Bordas Finas LF24T350",
                "hostname": None,
                "brand": "Samsung",
                "model": "LF24T350",
                "type": "Monitor",
                "sector": "Rádio Produção",
                "status": "Em uso",
                "ip": None,
                "mac": None,
                "win_key": None,
            },
            {
                "patrimony_number": "PAT-1011",
                "serial_number": "SN-HP-PD400",
                "description": "Desktop HP ProDesk 400 G6 Microtorre Core i5 10ª Gen",
                "hostname": "desk-dir-02",
                "brand": "HP",
                "model": "ProDesk 400 G6",
                "type": "Desktop",
                "sector": "Diretoria",
                "status": "Em uso",
                "ip": "192.168.1.111",
                "mac": "00:1A:2B:3C:4D:81",
                "win_key": "HPPD4-I510G-16RAM-512SS-W10PR",
            },
            {
                "patrimony_number": "PAT-1012",
                "serial_number": "SN-APPLE-MBP14",
                "description": "Notebook Apple MacBook Pro 14 M2 Pro 16GB 512GB SSD Cinza-Espacial",
                "hostname": "mac-dir-01",
                "brand": "Apple",
                "model": "MacBook Pro 14 M2",
                "type": "Notebook",
                "sector": "Diretoria",
                "status": "Acautelado",
                "ip": "192.168.1.112",
                "mac": "00:1A:2B:3C:4D:82",
                "win_key": None,
            },
            {
                "patrimony_number": "PAT-1013",
                "serial_number": "SN-DELL-OPT3080",
                "description": "Desktop Dell OptiPlex 3080 Core i3 8GB 256GB SSD",
                "hostname": "desk-old-01",
                "brand": "Dell",
                "model": "OptiPlex 3080",
                "type": "Desktop",
                "sector": "Almoxarifado",
                "status": "Baixado",
                "ip": "192.168.1.113",
                "mac": "00:1A:2B:3C:4D:83",
                "win_key": None,
            },
            {
                "patrimony_number": "PAT-1014",
                "serial_number": "SN-PHILIPS-221V",
                "description": "Monitor Philips 21.5 LED Full HD HDMI/VGA 221V8L",
                "hostname": None,
                "brand": "Philips",
                "model": "221V8L",
                "type": "Monitor",
                "sector": "Almoxarifado",
                "status": "Ocioso",
                "ip": None,
                "mac": None,
                "win_key": None,
            },
            {
                "patrimony_number": "PAT-1015",
                "serial_number": "SN-ZEBRA-ZD220",
                "description": "Impressora Térmica de Etiquetas Zebra ZD220 USB",
                "hostname": None,
                "brand": "Zebra",
                "model": "ZD220",
                "type": "Impressora",
                "sector": "Almoxarifado",
                "status": "Em uso",
                "ip": "192.168.1.115",
                "mac": "00:1A:2B:3C:4D:85",
                "printer_id": "PRN-ALMOX-01",
                "win_key": None,
            },
            {
                "patrimony_number": "PAT-1016",
                "serial_number": "SN-LENOVO-IP3",
                "description": "Notebook Lenovo IdeaPad 3 Ryzen 5 5500U 12GB RAM 256GB SSD",
                "hostname": "note-rad-01",
                "brand": "Lenovo",
                "model": "IdeaPad 3",
                "type": "Notebook",
                "sector": "Rádio Produção",
                "status": "Em uso",
                "ip": "192.168.1.116",
                "mac": "00:1A:2B:3C:4D:86",
                "win_key": "LNIP3-RYZ55-12RAM-256SS-W11HM",
            },
            {
                "patrimony_number": "PAT-1017",
                "serial_number": "SN-DELL-PREC3660",
                "description": "Workstation Dell Precision 3660 Core i7-12700K 32GB RTX A2000",
                "hostname": "work-rad-01",
                "brand": "Dell",
                "model": "Precision 3660",
                "type": "Desktop",
                "sector": "Rádio Produção",
                "status": "Em uso",
                "ip": "192.168.1.117",
                "mac": "00:1A:2B:3C:4D:87",
                "win_key": "DLPRC-I7127-32RAM-RTXA2-W11PR",
            },
            {
                "patrimony_number": "PAT-1018",
                "serial_number": "SN-LG-24MK430",
                "description": "Monitor LG 24 IPS Full HD 75Hz 24MK430H",
                "hostname": None,
                "brand": "LG",
                "model": "24MK430H",
                "type": "Monitor",
                "sector": "TI",
                "status": "Em uso",
                "ip": None,
                "mac": None,
                "win_key": None,
            },
            {
                "patrimony_number": "PAT-1019",
                "serial_number": "SN-EPSON-L3250",
                "description": "Impressora Multifuncional Tanque de Tinta Epson EcoTank L3250",
                "hostname": None,
                "brand": "Epson",
                "model": "EcoTank L3250",
                "type": "Impressora",
                "sector": "Diretoria",
                "status": "Em manutenção",
                "ip": "192.168.1.119",
                "mac": "00:1A:2B:3C:4D:89",
                "printer_id": "PRN-DIR-01",
                "win_key": None,
            },
            {
                "patrimony_number": "PAT-1020",
                "serial_number": "SN-DELL-LAT5430",
                "description": "Notebook Dell Latitude 5430 Core i7 12ª Gen 16GB 512GB SSD",
                "hostname": "note-ti-03",
                "brand": "Dell",
                "model": "Latitude 5430",
                "type": "Notebook",
                "sector": "TI",
                "status": "Acautelado",
                "ip": "192.168.1.120",
                "mac": "00:1A:2B:3C:4D:90",
                "win_key": "DLLAT-I712G-16RAM-512SS-W11PR",
            },
        ]

        eq_map = {}
        for data in equipments_data:
            eq = (
                db.query(Equipment)
                .filter(Equipment.patrimony_number == data["patrimony_number"])
                .first()
            )
            if not eq:
                eq = Equipment(
                    patrimony_number=data["patrimony_number"],
                    serial_number=data["serial_number"],
                    description=data["description"],
                    hostname=data.get("hostname"),
                    brand=data["brand"],
                    model=data["model"],
                    equipment_type_id=catalogs["types"][data["type"]].id,
                    sector_id=catalogs["sectors"][data["sector"]].id,
                    status_id=catalogs["statuses"][data["status"]].id,
                    ip_address=data.get("ip"),
                    mac_address=data.get("mac"),
                    printer_identifier=data.get("printer_id"),
                    windows_product_key_encrypted=(
                        encrypt_windows_product_key(data["win_key"])
                        if data.get("win_key")
                        else None
                    ),
                    created_at=now - timedelta(days=20),
                )
                db.add(eq)
                db.flush()
            eq_map[data["patrimony_number"]] = eq

        # 4. Movimentações de Equipamentos (Histórico diversificado)
        movements_data = [
            ("PAT-1001", "Almoxarifado", "TI", "Alocação inicial para equipe de suporte", 45),
            ("PAT-1003", "Almoxarifado", "Rádio Produção", "Instalação no estúdio de gravação", 30),
            ("PAT-1004", "TI", "Almoxarifado", "Recolhimento para substituição de peça", 10),
            ("PAT-1005", "Almoxarifado", "Diretoria", "Entrega de máquina executiva", 25),
            ("PAT-1007", "Comunicação", "TI", "Devolução por ociosidade", 15),
            ("PAT-1011", "Almoxarifado", "Diretoria", "Ativação no gabinete de gestão", 20),
            ("PAT-1016", "Almoxarifado", "Rádio Produção", "Atribuição a assistente de edição", 18),
            (
                "PAT-1017",
                "Almoxarifado",
                "Rádio Produção",
                "Montagem de ilha de renderização de vídeo",
                12,
            ),
            ("PAT-1019", "Diretoria", "TI", "Encaminhamento para manutenção preventiva", 5),
            ("PAT-1020", "TI", "Almoxarifado", "Guarda em custódia temporária", 2),
        ]

        for p_num, orig, dest, notes, days_ago in movements_data:
            eq = eq_map.get(p_num)
            if eq:
                has_mov = (
                    db.query(EquipmentMovement)
                    .filter(
                        EquipmentMovement.equipment_id == eq.id,
                        EquipmentMovement.notes == notes,
                    )
                    .first()
                )
                if not has_mov:
                    mov = EquipmentMovement(
                        equipment_id=eq.id,
                        origin_sector_id=catalogs["sectors"][orig].id,
                        destination_sector_id=catalogs["sectors"][dest].id,
                        performed_by_user_id=tecnico.id,
                        notes=notes,
                        movement_date=now - timedelta(days=days_ago),
                        created_at=now - timedelta(days=days_ago),
                    )
                    db.add(mov)

        # 5. Manutenções de Equipamentos (Preventivas e Corretivas)
        maintenances_data = [
            ("PAT-1004", "Corretiva", "Troca do conjunto de fusor e limpeza interna", 10, None),
            (
                "PAT-1001",
                "Preventiva",
                "Limpeza de coolers, ventoinhas e troca de pasta térmica",
                20,
                20,
            ),
            (
                "PAT-1003",
                "Preventiva",
                "Atualização de BIOS e inspeção de integridade do SSD",
                15,
                15,
            ),
            (
                "PAT-1013",
                "Corretiva",
                "Curto na placa-mãe sem viabilidade de reparo (baixado)",
                30,
                28,
            ),
            (
                "PAT-1019",
                "Corretiva",
                "Desobstrução do cabeçote de impressão e troca de almofada",
                4,
                None,
            ),
            ("PAT-1007", "Preventiva", "Reinstalação de imagem de SO e testes de estresse", 12, 12),
            (
                "PAT-1017",
                "Preventiva",
                "Calibração térmica dos ventiladores e testes da placa RTX",
                8,
                8,
            ),
        ]

        for p_num, m_type, desc, start_days, end_days in maintenances_data:
            eq = eq_map.get(p_num)
            if eq:
                if end_days is None:
                    has_open = (
                        db.query(EquipmentMaintenance)
                        .filter(
                            EquipmentMaintenance.equipment_id == eq.id,
                            EquipmentMaintenance.completed_at.is_(None),
                        )
                        .first()
                    )
                    if has_open:
                        continue
                has_maint = (
                    db.query(EquipmentMaintenance)
                    .filter(
                        EquipmentMaintenance.equipment_id == eq.id,
                        EquipmentMaintenance.description == desc,
                    )
                    .first()
                )
                if not has_maint:
                    start_dt = now - timedelta(days=start_days)
                    comp_dt = (start_dt + timedelta(hours=3)) if end_days is not None else None
                    maint = EquipmentMaintenance(
                        equipment_id=eq.id,
                        maintenance_type_id=catalogs["maintenance_types"][m_type].id,
                        performed_by_user_id=tecnico.id,
                        description=desc,
                        started_at=start_dt,
                        completed_at=comp_dt,
                        created_at=start_dt,
                    )
                    db.add(maint)

        # 6. Categorias SisPatrimonio
        categories_data = [
            ("Equipamentos de Informática", 60, 10.00, True),
            ("Mobiliário e Utensílios", 120, 5.00, False),
            ("Monitores e Displays", 60, 5.00, True),
            ("Servidores e Rede", 72, 15.00, True),
            ("Equipamentos de Impressão", 48, 8.00, True),
            ("Áudio e Vídeo", 60, 10.00, True),
        ]

        cat_map = {}
        for name, life, rate, req_serial in categories_data:
            cat = db.query(Category).filter(Category.name == name).first()
            if not cat:
                cat = Category(
                    name=name,
                    useful_life_months=life,
                    residual_value_rate=rate,
                    requires_serial_number=req_serial,
                )
                db.add(cat)
                db.flush()
            cat_map[name] = cat

        # 7. Localizações SisPatrimonio
        locations_data = [
            ("Prédio Central", "1º Andar", "TI", "101", "Sala de Suporte Técnico"),
            ("Bloco B", "Térreo", "Almoxarifado", None, "Depósito Geral e Logística"),
            (
                "Prédio Central",
                "2º Andar",
                "Coordenação Geral",
                "204",
                "Gabinete dos Coordenadores",
            ),
            (
                "Bloco de Laboratórios",
                "Térreo",
                "Lab de Banco de Dados",
                "Lab-01",
                "Laboratório Prático com 30 Bancadas",
            ),
            (
                "Bloco de Laboratórios",
                "1º Andar",
                "Lab de Redes",
                "Lab-104",
                "Rack de Roteadores, Switches e Patch Panels",
            ),
            (
                "Bloco Administrativo",
                "3º Andar",
                "Diretoria Executiva",
                "302",
                "Sala da Diretoria e Reuniões",
            ),
        ]

        loc_map = {}
        for building, floor, sector, room, desc in locations_data:
            loc = (
                db.query(Location)
                .filter(
                    Location.building == building,
                    Location.floor == floor,
                    Location.sector == sector,
                    Location.room_number == room,
                )
                .first()
            )
            if not loc:
                loc = Location(
                    building=building,
                    floor=floor,
                    sector=sector,
                    room_number=room,
                    description=desc,
                )
                db.add(loc)
                db.flush()
            loc_map[f"{building}-{sector}"] = loc

        loc_ti = loc_map["Prédio Central-TI"]
        loc_almox = loc_map["Bloco B-Almoxarifado"]
        loc_coord = loc_map["Prédio Central-Coordenação Geral"]
        loc_lab_bd = loc_map["Bloco de Laboratórios-Lab de Banco de Dados"]
        loc_lab_redes = loc_map["Bloco de Laboratórios-Lab de Redes"]
        loc_dir = loc_map["Bloco Administrativo-Diretoria Executiva"]

        # 8. Bens Patrimoniais SisPatrimonio (12 Ativos completos)
        assets_data = [
            {
                "patrimony_number": "SIS-0001",
                "serial_number": "SN-SIS-001",
                "description": "Workstation Dell Precision 3660 Core i7-12700 32GB 1TB NVMe",
                "cat": "Equipamentos de Informática",
                "loc": loc_ti,
                "user": tecnico,
                "brand": "Dell",
                "model": "Precision 3660",
                "cost": 8500.00,
                "status": "em_uso",
                "specs": {"cpu": "Intel Core i7-12700", "ram": "32GB", "storage": "1TB NVMe"},
            },
            {
                "patrimony_number": "SIS-0002",
                "serial_number": "SN-SIS-002",
                "description": "Notebook ThinkPad T14 Gen 3 Ryzen 7 PRO 16GB 512GB SSD",
                "cat": "Equipamentos de Informática",
                "loc": loc_coord,
                "user": colaborador,
                "brand": "Lenovo",
                "model": "ThinkPad T14",
                "cost": 6200.00,
                "status": "em_uso",
                "specs": {"cpu": "Ryzen 7 PRO", "ram": "16GB", "storage": "512GB SSD"},
            },
            {
                "patrimony_number": "SIS-0003",
                "serial_number": "SN-CISCO-2960",
                "description": "Switch Gerenciável Cisco Catalyst 2960X 48 Portas Gigabit PoE+",
                "cat": "Servidores e Rede",
                "loc": loc_lab_redes,
                "user": tecnico,
                "brand": "Cisco",
                "model": "Catalyst 2960X",
                "cost": 5400.00,
                "status": "em_uso",
                "specs": {"ports": 48, "throughput": "216 Gbps", "poe": "True"},
            },
            {
                "patrimony_number": "SIS-0004",
                "serial_number": "SN-DELL-R640",
                "description": "Servidor Dell PowerEdge R640 2x Xeon Silver 64GB RAM 4x1.2TB SAS",
                "cat": "Servidores e Rede",
                "loc": loc_lab_redes,
                "user": tecnico,
                "brand": "Dell",
                "model": "PowerEdge R640",
                "cost": 24500.00,
                "status": "em_uso",
                "specs": {
                    "cpu": "2x Intel Xeon Silver 4210",
                    "ram": "64GB ECC",
                    "raid": "PERC H730P",
                },
            },
            {
                "patrimony_number": "SIS-0005",
                "serial_number": "SN-LG-29WK",
                "description": "Monitor LG 29' Ultrawide IPS 75Hz Full HD HDR",
                "cat": "Monitores e Displays",
                "loc": loc_ti,
                "user": None,
                "brand": "LG",
                "model": "29WK600",
                "cost": 1450.00,
                "status": "disponivel",
                "specs": {"size": "29 pol", "resolution": "2560x1080", "panel": "IPS"},
            },
            {
                "patrimony_number": "SIS-0006",
                "serial_number": "SN-HP-M404",
                "description": "Impressora Laser HP LaserJet Pro M404dw Duplex Wi-Fi",
                "cat": "Equipamentos de Impressão",
                "loc": loc_ti,
                "user": tecnico,
                "brand": "HP",
                "model": "LaserJet Pro M404dw",
                "cost": 2100.00,
                "status": "em_manutencao",
                "specs": {"ppm": 40, "duplex": "True", "connectivity": "Ethernet/Wi-Fi"},
            },
            {
                "patrimony_number": "SIS-0007",
                "serial_number": None,
                "description": "Estação de Trabalho com Mesa em L 160x140cm e Calha para Cabos",
                "cat": "Mobiliário e Utensílios",
                "loc": loc_coord,
                "user": colaborador,
                "brand": "Flexform",
                "model": "WorkPro L-160",
                "cost": 1850.00,
                "status": "em_uso",
                "specs": {"material": "MDF 25mm", "structure": "Aço Carbono"},
            },
            {
                "patrimony_number": "SIS-0008",
                "serial_number": None,
                "description": "Cadeira Giratória Ergonômica Presidente NR17 com Ajustes 3D",
                "cat": "Mobiliário e Utensílios",
                "loc": loc_dir,
                "user": admin,
                "brand": "Cavaletti",
                "model": "Yon 40101",
                "cost": 1350.00,
                "status": "em_uso",
                "specs": {"standard": "NR17", "mechanism": "Syncron", "armrest": "3D"},
            },
            {
                "patrimony_number": "SIS-0009",
                "serial_number": "SN-APC-3000",
                "description": "Nobreak Senoidal APC Smart-UPS 3000VA Torre Bivolt",
                "cat": "Servidores e Rede",
                "loc": loc_lab_redes,
                "user": tecnico,
                "brand": "APC",
                "model": "SMT3000I",
                "cost": 8200.00,
                "status": "em_uso",
                "specs": {"power_va": 3000, "wave_type": "Senoidal Pura", "outlets": 8},
            },
            {
                "patrimony_number": "SIS-0010",
                "serial_number": "SN-DELL-LAT3420",
                "description": "Notebook Dell Latitude 3420 Core i5 16GB RAM 512GB SSD",
                "cat": "Equipamentos de Informática",
                "loc": loc_almox,
                "user": None,
                "brand": "Dell",
                "model": "Latitude 3420",
                "cost": 4600.00,
                "status": "disponivel",
                "specs": {"cpu": "Core i5-1135G7", "ram": "16GB", "storage": "512GB"},
            },
            {
                "patrimony_number": "SIS-0011",
                "serial_number": "SN-EPSON-W49",
                "description": "Projetor Multimídia Epson PowerLite W49 WXGA 3800 Lumens",
                "cat": "Áudio e Vídeo",
                "loc": loc_lab_bd,
                "user": None,
                "brand": "Epson",
                "model": "PowerLite W49",
                "cost": 3600.00,
                "status": "em_uso",
                "specs": {
                    "brightness_lumens": 3800,
                    "resolution": "WXGA 1280x800",
                    "lamp_life": "17000h",
                },
            },
            {
                "patrimony_number": "SIS-0012",
                "serial_number": "SN-DELL-OPT3050",
                "description": "Computador Desktop Dell OptiPlex 3050 Core i3 4GB RAM (Obsoleto)",
                "cat": "Equipamentos de Informática",
                "loc": loc_almox,
                "user": None,
                "brand": "Dell",
                "model": "OptiPlex 3050",
                "cost": 2200.00,
                "status": "baixado",
                "specs": {
                    "cpu": "Core i3-7100",
                    "ram": "4GB",
                    "condemnation_reason": "Falha na controladora",
                },
            },
        ]

        asset_map = {}
        for data in assets_data:
            ast = db.query(Asset).filter(Asset.patrimony_number == data["patrimony_number"]).first()
            if not ast:
                ast = Asset(
                    patrimony_number=data["patrimony_number"],
                    serial_number=data["serial_number"],
                    description=data["description"],
                    category_id=cat_map[data["cat"]].id,
                    location_id=data["loc"].id,
                    assigned_user_id=data["user"].id if data["user"] else None,
                    brand=data["brand"],
                    model=data["model"],
                    purchase_cost=data["cost"],
                    status=data["status"],
                    specs=data["specs"],
                    purchase_date=now.date() - timedelta(days=180),
                )
                db.add(ast)
                db.flush()
            asset_map[data["patrimony_number"]] = ast

        # 9. Histórico de Renumeração SisPatrimonio
        renumber_history = [
            (
                "SIS-0001",
                "SIS-0000-ANTIGO",
                "SIS-0001",
                "Substituição de plaqueta danificada na manutenção",
            ),
            (
                "SIS-0003",
                "REDE-SW-048",
                "SIS-0003",
                "Recadastramento e padronização no novo sistema",
            ),
            (
                "SIS-0004",
                "SRV-DELL-OLD",
                "SIS-0004",
                "Migração de código patrimonial legado para formato oficial",
            ),
        ]

        for p_num, old_num, new_num, reason in renumber_history:
            ast = asset_map.get(p_num)
            if ast:
                has_h = (
                    db.query(PatrimonyHistory)
                    .filter(
                        PatrimonyHistory.asset_id == ast.id,
                        PatrimonyHistory.new_patrimony_number == new_num,
                    )
                    .first()
                )
                if not has_h:
                    hist = PatrimonyHistory(
                        asset_id=ast.id,
                        old_patrimony_number=old_num,
                        new_patrimony_number=new_num,
                        reason=reason,
                        changed_by_id=tecnico.id,
                        changed_at=now - timedelta(days=40),
                    )
                    db.add(hist)

        # 10. Movimentações SisPatrimonio com Termos de Custódia
        asset_movements_data = [
            (
                "SIS-0001",
                loc_almox.id,
                loc_ti.id,
                None,
                tecnico.id,
                "Alocação do posto de trabalho técnico",
                50,
            ),
            (
                "SIS-0002",
                loc_almox.id,
                loc_coord.id,
                None,
                colaborador.id,
                "Entrega do notebook para o coordenador",
                35,
            ),
            (
                "SIS-0006",
                loc_coord.id,
                loc_ti.id,
                colaborador.id,
                tecnico.id,
                "Recolhimento para assistência técnica",
                10,
            ),
            (
                "SIS-0010",
                loc_ti.id,
                loc_almox.id,
                tecnico.id,
                None,
                "Devolução para estoque após encerramento de projeto",
                8,
            ),
            (
                "SIS-0011",
                loc_almox.id,
                loc_lab_bd.id,
                None,
                None,
                "Instalação no teto do laboratório de BD",
                25,
            ),
        ]

        for p_num, orig_id, dest_id, from_uid, to_uid, notes, days_ago in asset_movements_data:
            ast = asset_map.get(p_num)
            if ast:
                has_amov = (
                    db.query(AssetMovement)
                    .filter(
                        AssetMovement.asset_id == ast.id,
                        AssetMovement.notes == notes,
                    )
                    .first()
                )
                if not has_amov:
                    amov = AssetMovement(
                        asset_id=ast.id,
                        origin_location_id=orig_id,
                        dest_location_id=dest_id,
                        from_user_id=from_uid,
                        to_user_id=to_uid,
                        moved_by_id=tecnico.id,
                        notes=notes,
                        movement_date=now - timedelta(days=days_ago),
                        term_accepted_at=now - timedelta(days=days_ago - 1) if to_uid else None,
                    )
                    db.add(amov)

        # 11. Manutenções SisPatrimonio
        asset_maintenances_data = [
            (
                "SIS-0001",
                "preventiva",
                "Equipe Interna de TI",
                "Limpeza preventiva de coolers e diagnóstico de hardware",
                0.00,
                40,
            ),
            (
                "SIS-0004",
                "preventiva",
                "Dell ProSupport Enterprise",
                "Substituição preventiva de bateria da controladora RAID",
                450.00,
                20,
            ),
            (
                "SIS-0006",
                "corretiva",
                "Autorizada HP Care",
                "Troca da unidade de fusão e roletes de tração",
                580.00,
                5,
            ),
            (
                "SIS-0009",
                "preventiva",
                "Engenharia Elétrica Especializada",
                "Substituição preventiva do banco de baterias seladas",
                1200.00,
                15,
            ),
            (
                "SIS-0012",
                "corretiva",
                "Suporte Interno",
                "Perícia de queima de componentes elétricos da placa",
                0.00,
                60,
            ),
        ]

        for p_num, m_type, provider, desc, cost, days_ago in asset_maintenances_data:
            ast = asset_map.get(p_num)
            if ast:
                has_amaint = (
                    db.query(AssetMaintenance)
                    .filter(
                        AssetMaintenance.asset_id == ast.id,
                        AssetMaintenance.description == desc,
                    )
                    .first()
                )
                if not has_amaint:
                    amaint = AssetMaintenance(
                        asset_id=ast.id,
                        registered_by_id=tecnico.id,
                        maintenance_type=m_type,
                        service_provider=provider,
                        description=desc,
                        cost=cost,
                        maintenance_date=now - timedelta(days=days_ago),
                    )
                    db.add(amaint)

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
