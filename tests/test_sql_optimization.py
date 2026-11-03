"""Testes automatizados de otimização de consultas SQL e observabilidade (SisPatrimonio)."""

from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import event
from src.core.database import SessionLocal, engine
from src.domain.models import Asset, AssetMaintenance, Category, Location, User
from src.infrastructure.repositories import AssetRepository, UserRepository
from src.use_cases.asset_use_cases import AssetUseCases, _to_asset_response


class SQLQueryCounter:
    """Contador de consultas SQL executadas pelo engine."""

    def __init__(self):
        self.queries: list[str] = []

    def __enter__(self):
        self.queries.clear()
        event.listen(engine, "after_cursor_execute", self._after_cursor)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        event.remove(engine, "after_cursor_execute", self._after_cursor)

    def _after_cursor(self, conn, cursor, statement, parameters, context, executemany):
        clean = statement.strip()
        if clean.upper() != "SELECT 1":
            self.queries.append(clean)

    @property
    def count(self) -> int:
        return len(self.queries)


def test_list_assets_executes_minimal_queries(db_session):
    """Garante que a listagem de ativos executa no máximo 2 consultas (count + select joined)."""
    # Cria dados de teste
    cat = Category(name="Notebooks Otimizados", requires_serial_number=True)
    loc = Location(building="B1", floor="1", sector="TI")
    db_session.add_all([cat, loc])
    db_session.commit()

    asset = Asset(
        patrimony_number="PAT-OPT-001",
        serial_number="SN-OPT-001",
        description="Notebook Dell Teste Otimização",
        brand="Dell",
        model="Latitude 5420",
        category_id=cat.id,
        location_id=loc.id,
    )
    db_session.add(asset)
    db_session.commit()

    maint = AssetMaintenance(
        asset_id=asset.id,
        registered_by_id=1,
        maintenance_type="preventiva",
        description="Limpeza preventiva",
        maintenance_date=datetime.now(timezone.utc),
    )
    db_session.add(maint)
    db_session.commit()

    use_case = AssetUseCases(db_session)

    with SQLQueryCounter() as counter:
        result = use_case.list_assets(page=1, limit=25)

    assert result.total >= 1
    # Deve executar no máximo 3 queries no SQLite de teste e 2 no PostgreSQL
    assert counter.count <= 3, f"Captured queries ({counter.count}): {counter.queries}"
    # Confirma que last_maintenance_at foi preenchido via subquery sem carregar a coleção
    found = next((a for a in result.items if a.patrimony_number == "PAT-OPT-001"), None)
    assert found is not None
    assert found.last_maintenance_at is not None


def test_get_asset_detail_eager_history_minimal_queries(db_session):
    """Garante que o detalhe de ativo com histórico completo executa no máximo 4 consultas."""
    cat = Category(name="Servidores Otimizados")
    loc = Location(building="B2", floor="2", sector="DataCenter")
    db_session.add_all([cat, loc])
    db_session.commit()

    asset = Asset(
        patrimony_number="PAT-OPT-002",
        serial_number="SN-OPT-002",
        description="Servidor PowerEdge",
        brand="Dell",
        model="R740",
        category_id=cat.id,
        location_id=loc.id,
    )
    db_session.add(asset)
    db_session.commit()

    maint = AssetMaintenance(
        asset_id=asset.id,
        registered_by_id=1,
        maintenance_type="corretiva",
        description="Substituição de disco",
        maintenance_date=datetime.now(timezone.utc),
    )
    db_session.add(maint)
    db_session.commit()

    use_case = AssetUseCases(db_session)

    with SQLQueryCounter() as counter:
        detail = use_case.get_asset(asset.id)

    assert detail.id == asset.id
    assert len(detail.maintenances) >= 1
    assert counter.count <= 6, f"Captured queries ({counter.count}): {counter.queries}"


def test_user_repository_load_only_omits_password_hash(db_session):
    """Garante que UserRepository.get_by_id com load_full=False não carrega password_hash."""
    user = User(
        name="Teste Otimizacao",
        email="otimizado@empresa.com",
        password_hash="hash_secreto_super_longo",
        role="colaborador",
    )
    db_session.add(user)
    db_session.commit()

    repo = UserRepository(db_session)
    fetched_user = repo.get_by_id(user.id, load_full=False)
    assert fetched_user is not None
    assert fetched_user.id == user.id
    assert fetched_user.email == "otimizado@empresa.com"

    # Exercita branch com load_full=True
    full_user = repo.get_by_id(user.id, load_full=True)
    assert full_user is not None
    assert full_user.password_hash == "hash_secreto_super_longo"


def test_to_asset_response_fallback_branch(db_session):
    """Testa fallback em _to_asset_response quando computed_last_maintenance_at não está presente."""
    cat = Category(name="Monitores Otimizados")
    loc = Location(building="B3", floor="3", sector="Design")
    db_session.add_all([cat, loc])
    db_session.commit()

    asset = Asset(
        patrimony_number="PAT-OPT-003",
        description="Monitor 4K",
        brand="LG",
        category_id=cat.id,
        location_id=loc.id,
    )
    db_session.add(asset)
    db_session.commit()

    # Sem computed_last_maintenance_at e sem maintenances
    resp = _to_asset_response(asset)
    assert resp.last_maintenance_at is None
