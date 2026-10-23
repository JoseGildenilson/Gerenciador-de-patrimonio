"""Fixtures do Pytest para isolamento e testes da aplicação no PostgreSQL com fallback SQLite."""

import os
import sqlite3
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import CheckConstraint
from alembic import command
from alembic.config import Config
from src.core.database import get_db, Base
from src.core.security import hash_password
from src.domain.models import User, EquipmentType, Sector, EquipmentStatus, MaintenanceType
from src.main import app


@compiles(CheckConstraint, "sqlite")
def compile_check_constraint_sqlite(element, compiler, **kw):
    """Ignora restrições específicas de dialeto PostgreSQL (interval, family) no SQLite de teste."""
    sqltext = str(element.sqltext)
    if "interval" in sqltext or "family(" in sqltext:
        return None
    return compiler.visit_check_constraint(element, **kw)


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/comunica_test"),
)

_use_sqlite = False
try:
    _pg_engine = create_engine(TEST_DATABASE_URL, poolclass=NullPool)
    with _pg_engine.connect() as _c:
        pass
    test_engine = _pg_engine
except Exception:
    _use_sqlite = True
    TEST_DATABASE_URL = "sqlite:///:memory:"
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL

from src.core.config import settings

settings.DATABASE_URL = TEST_DATABASE_URL

import src.core.database as core_db

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
core_db.engine = test_engine
core_db.SessionLocal = TestingSessionLocal


@pytest.fixture(scope="session")
def setup_test_database():
    """Executa as migrações no PostgreSQL ou create_all no SQLite."""
    if _use_sqlite:
        Base.metadata.create_all(bind=test_engine)
    else:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
        command.upgrade(alembic_cfg, "head")
    yield
    if _use_sqlite:
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
def db_session(setup_test_database):
    """Fornece uma sessão isolada para cada teste, revertendo alterações e limpando tabelas no SQLite."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        if _use_sqlite:
            with test_engine.begin() as conn:
                for table in reversed(Base.metadata.sorted_tables):
                    conn.execute(table.delete())


@pytest.fixture(scope="function")
async def client(db_session: Session):
    """Cliente HTTP assíncrono httpx.AsyncClient para os testes da API FastAPI."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest.fixture
def create_test_user(db_session: Session):
    """Fixture auxiliar para criar técnicos de teste (role restrita a 'tecnico' ou 'colaborador')."""

    def _create_user(
        email: str = "tecnico@empresa.com",
        password: str = "SenhaSegura123!",
        role: str = "tecnico",
        is_active: bool = True,
    ) -> User:
        hashed = hash_password(password)
        user = User(
            name="Test User",
            email=email,
            hashed_password=hashed,
            role=role,
            is_active=is_active,
        )
        db_session.add(user)
        db_session.flush()
        return user

    return _create_user


@pytest.fixture
def test_catalogs(db_session: Session):
    """Fixture auxiliar para obter ou criar registros de catálogo para testes."""

    def _get_or_create(model_cls, name: str):
        item = db_session.query(model_cls).filter(model_cls.name == name).first()
        if not item:
            item = model_cls(name=name)
            db_session.add(item)
            db_session.flush()
        return item

    eq_type = _get_or_create(EquipmentType, "Desktop")
    sector_ti = _get_or_create(Sector, "TI")
    sector_com = _get_or_create(Sector, "Comunicação")
    sector_dir = _get_or_create(Sector, "Diretoria")
    status_em_uso = _get_or_create(EquipmentStatus, "Em uso")
    status_em_manutencao = _get_or_create(EquipmentStatus, "Em manutenção")
    status_ocioso = _get_or_create(EquipmentStatus, "Ocioso")
    status_baixado = _get_or_create(EquipmentStatus, "Baixado")
    maint_prev = _get_or_create(MaintenanceType, "Preventiva")
    maint_corr = _get_or_create(MaintenanceType, "Corretiva")

    return {
        "type": eq_type,
        "sector_ti": sector_ti,
        "sector_com": sector_com,
        "sector_dir": sector_dir,
        "status_em_uso": status_em_uso,
        "status_em_manutencao": status_em_manutencao,
        "status_ocioso": status_ocioso,
        "status_baixado": status_baixado,
        "maint_prev": maint_prev,
        "maint_corr": maint_corr,
    }
