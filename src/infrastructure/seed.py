"""Script para popular o banco de dados com dados iniciais (seed) do SisPatrimonio."""

from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.core.security import hash_password
from src.domain.models import (
    User,
    Category,
    Location,
    Asset,
    PatrimonyHistory,
    AssetMovement,
    AssetMaintenance,
)


def seed_database(db: Session | None = None) -> None:
    """Executa o povoamento completo das entidades canônicas do SisPatrimonio."""
    session = db or SessionLocal()
    try:
        # 1. Usuários
        admin = (
            session.query(User)
            .filter(func.lower(User.email) == "admin@sispatrimonio.edu.br")
            .first()
        )
        if not admin:
            admin = User(
                name="Administrador do Sistema",
                email="admin@sispatrimonio.edu.br",
                password_hash=hash_password("senha123"),
                role="administrador",
                is_active=True,
            )
            session.add(admin)

        tecnico = (
            session.query(User)
            .filter(func.lower(User.email) == "tecnico@sispatrimonio.edu.br")
            .first()
        )
        if not tecnico:
            tecnico = User(
                name="Carlos Henrique Técnico",
                email="tecnico@sispatrimonio.edu.br",
                password_hash=hash_password("senha123"),
                role="tecnico",
                is_active=True,
            )
            session.add(tecnico)

        colaborador = (
            session.query(User)
            .filter(func.lower(User.email) == "colaborador@sispatrimonio.edu.br")
            .first()
        )
        if not colaborador:
            colaborador = User(
                name="Mariana Souza Colaboradora",
                email="colaborador@sispatrimonio.edu.br",
                password_hash=hash_password("senha123"),
                role="colaborador",
                is_active=True,
            )
            session.add(colaborador)

        roberto = (
            session.query(User)
            .filter(func.lower(User.email) == "roberto.albuquerque@sispatrimonio.edu.br")
            .first()
        )
        if not roberto:
            roberto = User(
                name="Prof. Roberto Albuquerque",
                email="roberto.albuquerque@sispatrimonio.edu.br",
                password_hash=hash_password("senha123"),
                role="colaborador",
                is_active=True,
            )
            session.add(roberto)

        fernanda = (
            session.query(User)
            .filter(func.lower(User.email) == "fernanda.lima@sispatrimonio.edu.br")
            .first()
        )
        if not fernanda:
            fernanda = User(
                name="Fernanda Lima Coordenadora",
                email="fernanda.lima@sispatrimonio.edu.br",
                password_hash=hash_password("senha123"),
                role="colaborador",
                is_active=True,
            )
            session.add(fernanda)

        session.flush()

        # 2. Categorias
        categories_data = [
            ("Notebooks e Portáteis", 48, Decimal("10.00"), True),
            ("Computadores Desktop", 60, Decimal("5.00"), True),
            ("Monitores e Displays", 60, Decimal("5.00"), True),
            ("Servidores e Rede", 72, Decimal("15.00"), True),
            ("Mobiliário e Estações", 120, Decimal("20.00"), False),
            ("Equipamentos de Impressão", 48, Decimal("8.00"), True),
        ]
        cat_map = {}
        for name, life, rate, req_serial in categories_data:
            cat = session.query(Category).filter(func.lower(Category.name) == name.lower()).first()
            if not cat:
                cat = Category(
                    name=name,
                    useful_life_months=life,
                    residual_value_rate=rate,
                    requires_serial_number=req_serial,
                )
                session.add(cat)
                session.flush()
            cat_map[name] = cat

        # 3. Localizações Físicas
        locations_data = [
            (
                "Prédio Central",
                "1º Andar",
                "Departamento de TI",
                "Sala 101",
                "Setor de infraestrutura e suporte computacional",
            ),
            (
                "Prédio Central",
                "2º Andar",
                "Coordenação Geral",
                "Sala 204",
                "Gabinete dos coordenadores de curso",
            ),
            (
                "Bloco de Laboratórios",
                "Térreo",
                "Laboratório de Banco de Dados",
                "Lab-01",
                "Bancadas de aula prática com 30 computadores",
            ),
            (
                "Bloco de Laboratórios",
                "1º Andar",
                "Laboratório de Redes",
                "Lab-104",
                "Racks de roteamento e comutação",
            ),
            (
                "Bloco Administrativo",
                "Térreo",
                "Almoxarifado Central",
                None,
                "Depósito geral de patrimônio e estoque",
            ),
        ]
        loc_map = {}
        for bld, flr, sec, rm, desc in locations_data:
            loc = (
                session.query(Location)
                .filter(
                    func.lower(Location.building) == bld.lower(),
                    func.lower(Location.floor) == flr.lower(),
                    func.lower(Location.sector) == sec.lower(),
                )
                .first()
            )
            if not loc:
                loc = Location(
                    building=bld,
                    floor=flr,
                    sector=sec,
                    room_number=rm,
                    description=desc,
                )
                session.add(loc)
                session.flush()
            loc_map[sec] = loc

        # 4. Ativos (sincronizados com database/populate.sql)
        assets_data = [
            (
                "PAT-2026-0001",
                "SN-DELL-88210",
                "Dell Latitude 5430 Core i7 16GB",
                "Notebooks e Portáteis",
                "Departamento de TI",
                colaborador.id,
                "Dell",
                "Latitude 5430",
                Decimal("6500.00"),
                date(2026, 1, 15),
                "em_uso",
                {
                    "cpu": "Intel Core i7-1265U",
                    "ram_gb": 16,
                    "storage": "512GB NVMe SSD",
                    "os": "Ubuntu 24.04 LTS",
                },
            ),
            (
                "PAT-2026-0002",
                "SN-LENOVO-9941",
                "ThinkPad T14 Gen 3 Ryzen 7 32GB",
                "Notebooks e Portáteis",
                "Coordenação Geral",
                fernanda.id,
                "Lenovo",
                "ThinkPad T14 Gen 3",
                Decimal("7200.00"),
                date(2026, 2, 10),
                "em_uso",
                {
                    "cpu": "AMD Ryzen 7 PRO 6850U",
                    "ram_gb": 32,
                    "storage": "1TB SSD",
                    "os": "Windows 11 Pro",
                },
            ),
            (
                "PAT-2026-0003",
                "SN-DELL-OPT-01",
                "Desktop Dell OptiPlex 7000 Torre",
                "Computadores Desktop",
                "Laboratório de Banco de Dados",
                roberto.id,
                "Dell",
                "OptiPlex 7000",
                Decimal("4800.00"),
                date(2025, 11, 20),
                "em_uso",
                {
                    "cpu": "Intel Core i5-12500",
                    "ram_gb": 16,
                    "storage": "512GB SSD",
                    "gpu": "Intel UHD 770",
                },
            ),
            (
                "PAT-2026-0004",
                "SN-SAMS-M778",
                "Monitor Samsung Odyssey 27 IPS 165Hz",
                "Monitores e Displays",
                "Laboratório de Banco de Dados",
                roberto.id,
                "Samsung",
                "Odyssey G4",
                Decimal("1650.00"),
                date(2025, 11, 20),
                "em_uso",
                {
                    "screen_size_inch": 27,
                    "resolution": "1920x1080",
                    "refresh_rate_hz": 165,
                    "panel": "IPS",
                },
            ),
            (
                "PAT-2026-0005",
                "SN-DELL-R750-01",
                "Servidor Dell PowerEdge R750 2U Rack",
                "Servidores e Rede",
                "Laboratório de Redes",
                tecnico.id,
                "Dell",
                "PowerEdge R750",
                Decimal("38500.00"),
                date(2025, 8, 10),
                "em_uso",
                {
                    "dual_cpu": "2x Xeon Gold 6330",
                    "ram_gb": 128,
                    "storage_tb": "4x 2TB SAS SSD RAID 10",
                    "power_redundant": True,
                },
            ),
            (
                "PAT-2026-0006",
                None,
                "Mesa de Trabalho Ergonômica 160x80cm",
                "Mobiliário e Estações",
                "Departamento de TI",
                None,
                "Cavaletti",
                "Start 160",
                Decimal("1100.00"),
                date(2026, 3, 1),
                "disponivel",
                {
                    "dimensions_cm": "160x80x75",
                    "color": "Cinza e Grafite",
                    "cable_pass": True,
                },
            ),
            (
                "PAT-2026-0007",
                "SN-BROTHER-L5652",
                "Multifuncional Brother Laser Monocromática",
                "Equipamentos de Impressão",
                "Almoxarifado Central",
                None,
                "Brother",
                "DCP-L5652DN",
                Decimal("3200.00"),
                date(2024, 5, 18),
                "em_manutencao",
                {
                    "print_speed_ppm": 42,
                    "duplex": True,
                    "network_interface": "Gigabit Ethernet",
                },
            ),
            (
                "PAT-2026-0008",
                "SN-HP-M404DW",
                "Impressora HP LaserJet Pro M404dw",
                "Equipamentos de Impressão",
                "Almoxarifado Central",
                None,
                "HP",
                "M404dw",
                Decimal("1800.00"),
                date(2023, 2, 14),
                "baixado",
                {
                    "print_speed_ppm": 40,
                    "duplex": True,
                    "decommission_reason": "Queima irreversível da placa lógica",
                },
            ),
        ]
        asset_map = {}
        for (
            pat_num,
            ser_num,
            desc,
            cat_name,
            loc_sec,
            user_id,
            brand,
            model,
            cost,
            p_date,
            status_val,
            specs_val,
        ) in assets_data:
            asset = session.query(Asset).filter(Asset.patrimony_number == pat_num).first()
            if not asset:
                asset = Asset(
                    patrimony_number=pat_num,
                    serial_number=ser_num,
                    description=desc,
                    category_id=cat_map[cat_name].id,
                    location_id=loc_map[loc_sec].id,
                    assigned_user_id=user_id,
                    brand=brand,
                    model=model,
                    purchase_cost=cost,
                    purchase_date=p_date,
                    status=status_val,
                    specs=specs_val,
                )
                session.add(asset)
                session.flush()
            asset_map[pat_num] = asset

        asset1 = asset_map["PAT-2026-0001"]
        asset3 = asset_map["PAT-2026-0003"]
        asset5 = asset_map["PAT-2026-0005"]
        asset7 = asset_map["PAT-2026-0007"]
        asset8 = asset_map["PAT-2026-0008"]

        # 5. Histórico de Renumeração
        hist = (
            session.query(PatrimonyHistory).filter(PatrimonyHistory.asset_id == asset1.id).first()
        )
        if not hist:
            hist = PatrimonyHistory(
                asset_id=asset1.id,
                old_patrimony_number="PAT-LEGACY-904",
                new_patrimony_number="PAT-2026-0001",
                reason="Substituição de plaqueta danificada e padronização do novo formato universitário",
                changed_by_id=tecnico.id,
            )
            session.add(hist)

        # 6. Movimentações Físicas
        movements_data = [
            (
                asset1,
                loc_map["Almoxarifado Central"].id,
                loc_map["Departamento de TI"].id,
                None,
                colaborador.id,
                tecnico.id,
                datetime.now(timezone.utc) - timedelta(days=20),
                datetime.now(timezone.utc) - timedelta(days=21),
                "Entrega inicial do notebook com assinatura digital do termo de responsabilidade",
            ),
            (
                asset7,
                loc_map["Coordenação Geral"].id,
                loc_map["Almoxarifado Central"].id,
                fernanda.id,
                None,
                tecnico.id,
                None,
                datetime.now(timezone.utc) - timedelta(days=3),
                "Recolhimento para o almoxarifado após barulho no fusor; aguarda orçamento de peça",
            ),
            (
                asset8,
                loc_map["Almoxarifado Central"].id,
                None,
                None,
                None,
                admin.id,
                datetime.now(timezone.utc) - timedelta(days=15),
                datetime.now(timezone.utc) - timedelta(days=15),
                "Baixa definitiva por desincorporação patrimonial com laudo técnico nº 84/2026",
            ),
        ]
        for (
            target_asset,
            orig_id,
            dest_id,
            from_uid,
            to_uid,
            by_uid,
            term_dt,
            mov_dt,
            notes_txt,
        ) in movements_data:
            mov = (
                session.query(AssetMovement)
                .filter(AssetMovement.asset_id == target_asset.id)
                .first()
            )
            if not mov:
                mov = AssetMovement(
                    asset_id=target_asset.id,
                    origin_location_id=orig_id,
                    dest_location_id=dest_id,
                    from_user_id=from_uid,
                    to_user_id=to_uid,
                    moved_by_id=by_uid,
                    term_accepted_at=term_dt,
                    movement_date=mov_dt,
                    notes=notes_txt,
                )
                session.add(mov)

        # 7. Manutenções
        maintenances_data = [
            (
                asset3,
                tecnico.id,
                "preventiva",
                "Equipe Interna de TI",
                "Limpeza preventiva de poeira nos coolers, troca de pasta térmica e verificação de integridade do SSD SMART",
                Decimal("0.00"),
                datetime.now(timezone.utc) - timedelta(days=40),
            ),
            (
                asset7,
                tecnico.id,
                "corretiva",
                "LaserTech Manutenções e Peças Ltda",
                "Substituição do rolo pressor e conjunto da película de fusão que apresentavam desgaste térmico acentuado",
                Decimal("485.50"),
                datetime.now(timezone.utc) - timedelta(days=2),
            ),
            (
                asset5,
                tecnico.id,
                "preventiva",
                "Dell ProSupport Enterprise",
                "Atualização sem interrupção de firmware iDRAC9 e diagnóstico preditivo dos módulos de memória ECC",
                Decimal("1200.00"),
                datetime.now(timezone.utc) - timedelta(days=90),
            ),
        ]
        for (
            target_asset,
            reg_uid,
            m_type,
            provider,
            m_desc,
            m_cost,
            m_dt,
        ) in maintenances_data:
            maint = (
                session.query(AssetMaintenance)
                .filter(AssetMaintenance.asset_id == target_asset.id)
                .first()
            )
            if not maint:
                maint = AssetMaintenance(
                    asset_id=target_asset.id,
                    registered_by_id=reg_uid,
                    maintenance_type=m_type,
                    service_provider=provider,
                    description=m_desc,
                    cost=m_cost,
                    maintenance_date=m_dt,
                )
                session.add(maint)

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if db is None:
            session.close()


def main() -> None:  # pragma: no cover
    print("Iniciando povoamento do banco de dados...")
    seed_database()
    print("Banco de dados populado com sucesso!")


if __name__ == "__main__":  # pragma: no cover
    main()
