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
        admin = session.query(User).filter(func.lower(User.email) == "admin@sispatrimonio.edu.br").first()
        if not admin:
            admin = User(
                name="Administrador do Sistema",
                email="admin@sispatrimonio.edu.br",
                password_hash=hash_password("senha123"),
                role="administrador",
                is_active=True,
            )
            session.add(admin)

        tecnico = session.query(User).filter(func.lower(User.email) == "tecnico@sispatrimonio.edu.br").first()
        if not tecnico:
            tecnico = User(
                name="Carlos Henrique Técnico",
                email="tecnico@sispatrimonio.edu.br",
                password_hash=hash_password("senha123"),
                role="tecnico",
                is_active=True,
            )
            session.add(tecnico)

        colaborador = session.query(User).filter(func.lower(User.email) == "colaborador@sispatrimonio.edu.br").first()
        if not colaborador:
            colaborador = User(
                name="Mariana Souza Colaboradora",
                email="colaborador@sispatrimonio.edu.br",
                password_hash=hash_password("senha123"),
                role="colaborador",
                is_active=True,
            )
            session.add(colaborador)

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
            ("Prédio Central", "1º Andar", "Departamento de TI", "Sala 101", "Setor de infraestrutura"),
            ("Prédio Central", "2º Andar", "Coordenação Geral", "Sala 204", "Gabinete dos coordenadores"),
            ("Bloco de Laboratórios", "Térreo", "Laboratório de Banco de Dados", "Lab-01", "30 computadores de aula"),
            ("Bloco Administrativo", "Térreo", "Almoxarifado Central", None, "Depósito geral de estoque"),
        ]
        loc_map = {}
        for bld, flr, sec, rm, desc in locations_data:
            loc = session.query(Location).filter(
                func.lower(Location.building) == bld.lower(),
                func.lower(Location.floor) == flr.lower(),
                func.lower(Location.sector) == sec.lower(),
            ).first()
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

        # 4. Ativos
        asset1 = session.query(Asset).filter(Asset.patrimony_number == "PAT-2026-0001").first()
        if not asset1:
            asset1 = Asset(
                patrimony_number="PAT-2026-0001",
                serial_number="SN-DELL-88210",
                description="Dell Latitude 5430 Core i7 16GB",
                category_id=cat_map["Notebooks e Portáteis"].id,
                location_id=loc_map["Departamento de TI"].id,
                assigned_user_id=colaborador.id,
                brand="Dell",
                model="Latitude 5430",
                purchase_cost=Decimal("6500.00"),
                purchase_date=date(2026, 1, 15),
                status="em_uso",
                specs={"cpu": "Core i7", "ram_gb": 16, "os": "Ubuntu 24.04 LTS"},
            )
            session.add(asset1)
            session.flush()

        asset2 = session.query(Asset).filter(Asset.patrimony_number == "PAT-2026-0002").first()
        if not asset2:
            asset2 = Asset(
                patrimony_number="PAT-2026-0002",
                serial_number="SN-LENOVO-9941",
                description="ThinkPad T14 Gen 3 Ryzen 7 32GB",
                category_id=cat_map["Notebooks e Portáteis"].id,
                location_id=loc_map["Coordenação Geral"].id,
                assigned_user_id=None,
                brand="Lenovo",
                model="ThinkPad T14 Gen 3",
                purchase_cost=Decimal("7200.00"),
                purchase_date=date(2026, 2, 10),
                status="disponivel",
                specs={"cpu": "Ryzen 7", "ram_gb": 32, "os": "Windows 11 Pro"},
            )
            session.add(asset2)
            session.flush()

        # 5. Histórico de Renumeração
        hist = session.query(PatrimonyHistory).filter(PatrimonyHistory.asset_id == asset1.id).first()
        if not hist:
            hist = PatrimonyHistory(
                asset_id=asset1.id,
                old_patrimony_number="PAT-LEGACY-904",
                new_patrimony_number="PAT-2026-0001",
                reason="Padronização de plaqueta patrimonial",
                changed_by_id=tecnico.id,
            )
            session.add(hist)

        # 6. Movimentação Física
        mov = session.query(AssetMovement).filter(AssetMovement.asset_id == asset1.id).first()
        if not mov:
            mov = AssetMovement(
                asset_id=asset1.id,
                origin_location_id=loc_map["Almoxarifado Central"].id,
                dest_location_id=loc_map["Departamento de TI"].id,
                from_user_id=None,
                to_user_id=colaborador.id,
                moved_by_id=tecnico.id,
                term_accepted_at=datetime.now(timezone.utc),
                notes="Entrega de equipamento com termo de responsabilidade assinado",
            )
            session.add(mov)

        # 7. Manutenções
        maint = session.query(AssetMaintenance).filter(AssetMaintenance.asset_id == asset1.id).first()
        if not maint:
            maint = AssetMaintenance(
                asset_id=asset1.id,
                registered_by_id=tecnico.id,
                maintenance_type="preventiva",
                service_provider="Equipe Interna de TI",
                description="Revisão preventiva periódica de hardware",
                cost=Decimal("0.00"),
                maintenance_date=datetime.now(timezone.utc) - timedelta(days=5),
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
