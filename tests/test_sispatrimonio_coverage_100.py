"""Testes dedicados para cobertura completa de 100% de linhas e branches (Constituição)."""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.api.dependencies import require_tecnico_or_admin
from src.core.exceptions import NotFoundError, ConflictError
from src.domain.models import (
    User,
    Category,
    Location,
    Asset,
    PatrimonyHistory,
    AssetMovement,
    AssetMaintenance,
)
from src.domain.schemas import (
    CategoryCreate,
    CategoryUpdate,
    LocationCreate,
    LocationUpdate,
    AssetCreate,
    AssetUpdate,
    PatrimonyRenumberRequest,
    AssetMovementCreate,
    AssetMaintenanceCreate,
)
from src.infrastructure.repositories import (
    CategoryRepository,
    LocationRepository,
    AssetRepository,
    PatrimonyHistoryRepository,
    AssetMovementRepository,
    AssetMaintenanceRepository,
)
from src.use_cases.category_use_cases import CategoryUseCases
from src.use_cases.location_use_cases import LocationUseCases
from src.use_cases.asset_use_cases import AssetUseCases
from src.use_cases.movement_use_cases import AssetMovementUseCases
from src.use_cases.maintenance_use_cases import MaintenanceUseCases


def test_require_tecnico_or_admin_forbidden():
    """Valida rejeição com 403 quando o usuário não é técnico nem administrador."""
    colab = User(role="colaborador")
    with pytest.raises(HTTPException) as exc_info:
        require_tecnico_or_admin(current_user=colab)
    assert exc_info.value.status_code == 403

    admin = User(role="administrador")
    assert require_tecnico_or_admin(current_user=admin) == admin


def test_category_use_cases_and_repo_edge_branches(db_session: Session):
    """Cobre ramos de atualização de todos os atributos e tratamento de rollback em categorias."""
    cat = Category(
        name="Cat Inicial",
        useful_life_months=24,
        residual_value_rate=Decimal("5.00"),
        requires_serial_number=False,
    )
    db_session.add(cat)
    db_session.flush()

    use_case = CategoryUseCases(db_session)
    updated = use_case.update_category(
        cat.id,
        CategoryUpdate(
            name="Cat Modificada",
            useful_life_months=60,
            residual_value_rate=Decimal("15.00"),
            requires_serial_number=True,
        ),
    )
    assert updated.name == "Cat Modificada"
    assert updated.useful_life_months == 60
    assert updated.residual_value_rate == Decimal("15.00")
    assert updated.requires_serial_number is True

    # Testar rollbacks com falha simulada no commit
    mock_db = MagicMock(spec=Session)
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    mock_db.commit.side_effect = RuntimeError("Erro simulado")

    mock_use_case = CategoryUseCases(mock_db)
    with pytest.raises(RuntimeError):
        mock_use_case.create_category(CategoryCreate(name="Fail Cat"))
    mock_db.rollback.assert_called_once()

    mock_db.reset_mock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = cat
    mock_db.commit.side_effect = RuntimeError("Erro no update")
    with pytest.raises(RuntimeError):
        mock_use_case.update_category(cat.id, CategoryUpdate(name="Outro Nome"))
    mock_db.rollback.assert_called_once()


def test_location_use_cases_and_repo_edge_branches(db_session: Session):
    """Cobre ramos de atualização de descrição, sala nula e rollbacks em localizações."""
    loc = Location(building="Bld 1", floor="1", sector="TI", room_number="10", description="Desc")
    db_session.add(loc)
    db_session.flush()

    use_case = LocationUseCases(db_session)
    # Atualiza removendo sala e alterando descrição
    updated = use_case.update_location(
        loc.id,
        LocationUpdate(
            building="Bld 1",
            floor="1",
            sector="TI",
            room_number="",
            description="Nova Descricao",
        ),
    )
    assert updated.room_number is None
    assert updated.description == "Nova Descricao"

    # Atualiza sem alterar descrição
    updated2 = use_case.update_location(
        loc.id,
        LocationUpdate(description=None),
    )
    assert updated2.description == "Nova Descricao"

    # Rollback no create e update
    mock_db = MagicMock(spec=Session)
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    mock_db.commit.side_effect = RuntimeError("Commit fail")
    mock_use_case = LocationUseCases(mock_db)

    with pytest.raises(RuntimeError):
        mock_use_case.create_location(LocationCreate(building="A", floor="1", sector="B"))
    mock_db.rollback.assert_called_once()

    mock_db.reset_mock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = loc
    mock_db.commit.side_effect = RuntimeError("Update fail")
    with pytest.raises(RuntimeError):
        mock_use_case.update_location(loc.id, LocationUpdate(building="C"))
    mock_db.rollback.assert_called_once()


def test_asset_use_cases_and_repo_branches(db_session: Session, create_test_user):
    """Cobre ramos de busca com include_deleted, atualização completa de campos e rollbacks."""
    user = create_test_user(email="user_branches@empresa.com")
    cat = Category(name="Cat Branch", requires_serial_number=False)
    loc = Location(building="B", floor="1", sector="Sec")
    db_session.add_all([cat, loc])
    db_session.flush()

    repo = AssetRepository(db_session)
    asset = Asset(
        patrimony_number="PAT-BRANCH-01",
        serial_number="SN-BRANCH-01",
        description="Ativo para Branches",
        category_id=cat.id,
        location_id=loc.id,
        brand="Dell",
    )
    repo.create(asset)
    db_session.flush()

    # Busca com include_deleted
    repo.soft_delete(asset)
    db_session.flush()

    assert repo.get_by_id(asset.id, include_deleted=False) is None
    assert repo.get_by_id(asset.id, include_deleted=True) is not None
    assert repo.get_by_patrimony_number("PAT-BRANCH-01", include_deleted=False) is None
    assert repo.get_by_patrimony_number("PAT-BRANCH-01", include_deleted=True) is not None
    assert repo.get_by_serial_number("SN-BRANCH-01", include_deleted=False) is None
    assert repo.get_by_serial_number("SN-BRANCH-01", include_deleted=True) is not None

    asset.deleted_at = None
    db_session.flush()

    # Testar update_asset com todos os atributos opcionais
    use_case = AssetUseCases(db_session)
    updated = use_case.update_asset(
        asset.id,
        AssetUpdate(
            brand="Dell Technologies",
            model="Precision",
            purchase_cost=Decimal("7500.00"),
            purchase_date=date(2026, 4, 1),
            status="em_manutencao",
            specs={"gpu": "RTX A2000"},
            serial_number="",  # limpa serial
        ),
    )
    assert updated.brand == "Dell Technologies"
    assert updated.model == "Precision"
    assert updated.status == "em_manutencao"
    assert updated.specs["gpu"] == "RTX A2000"
    assert updated.serial_number is None

    # Histórico e Manutenções auxiliares no repo
    hist_repo = PatrimonyHistoryRepository(db_session)
    hist = hist_repo.create(
        PatrimonyHistory(
            asset_id=asset.id,
            old_patrimony_number="PAT-1",
            new_patrimony_number="PAT-2",
            reason="Troca",
            changed_by_id=user.id,
        )
    )
    db_session.flush()
    assert len(hist_repo.list_by_asset(asset.id)) == 1

    maint_repo = AssetMaintenanceRepository(db_session)
    maint = maint_repo.create(
        AssetMaintenance(
            asset_id=asset.id,
            registered_by_id=user.id,
            maintenance_type="preventiva",
            description="Manut",
            maintenance_date=datetime.now(timezone.utc),
        )
    )
    db_session.flush()
    assert maint_repo.get_by_id(maint.id) is not None

    # Rollbacks de asset_use_cases
    mock_db = MagicMock(spec=Session)
    mock_db.commit.side_effect = RuntimeError("Erro no commit de ativos")
    mock_use_case = AssetUseCases(mock_db)

    # Rollback no create
    mock_use_case.cat_repo.get_by_id = MagicMock(return_value=cat)
    mock_use_case.loc_repo.get_by_id = MagicMock(return_value=loc)
    mock_use_case.asset_repo.get_by_patrimony_number = MagicMock(return_value=None)
    with pytest.raises(RuntimeError):
        mock_use_case.create_asset(
            AssetCreate(
                patrimony_number="PAT-X",
                description="Desc",
                category_id=1,
                location_id=1,
                brand="Brand",
            )
        )
    mock_db.rollback.assert_called_once()

    # Rollback no update
    mock_db.reset_mock()
    mock_use_case.asset_repo.get_by_id = MagicMock(return_value=asset)
    with pytest.raises(RuntimeError):
        mock_use_case.update_asset(asset.id, AssetUpdate(brand="Nova"))
    mock_db.rollback.assert_called_once()

    # Rollback no renumber
    mock_db.reset_mock()
    with pytest.raises(RuntimeError):
        mock_use_case.renumber_patrimony(
            asset.id,
            PatrimonyRenumberRequest(new_patrimony_number="PAT-NOVO-ERR", reason="R"),
            changed_by_user_id=user.id,
        )
    mock_db.rollback.assert_called_once()

    # Rollback no delete
    mock_db.reset_mock()
    with pytest.raises(RuntimeError):
        mock_use_case.delete_asset(asset.id)
    mock_db.rollback.assert_called_once()


def test_movement_and_maintenance_use_cases_rollbacks(db_session: Session, create_test_user):
    """Cobre rollbacks e ramos de movimento com from_user_id e maintenance."""
    user = create_test_user(email="user_mov_maint@empresa.com")
    cat = Category(name="Cat MM")
    loc1 = Location(building="B1", floor="1", sector="TI")
    loc2 = Location(building="B2", floor="2", sector="RH")
    db_session.add_all([cat, loc1, loc2])
    db_session.flush()

    asset = Asset(
        patrimony_number="PAT-MM-1",
        description="Equipamento MM",
        category_id=cat.id,
        location_id=loc1.id,
        brand="Dell",
    )
    db_session.add(asset)
    db_session.flush()

    # Movimento sem destino (baixa) com from_user_id
    mov_use_case = AssetMovementUseCases(db_session)
    mov = mov_use_case.create_movement(
        asset.id,
        AssetMovementCreate(
            origin_location_id=loc1.id,
            dest_location_id=None,
            from_user_id=user.id,
            notes="Baixa com responsável de devolução",
        ),
        moved_by_id=user.id,
    )
    assert mov.dest_location_id is None
    assert mov.from_user_id == user.id

    # Rollback no create_movement
    mock_db = MagicMock(spec=Session)
    mock_db.commit.side_effect = RuntimeError("Mov commit fail")
    mock_mov_uc = AssetMovementUseCases(mock_db)
    mock_mov_uc.asset_repo.get_by_id = MagicMock(return_value=asset)
    mock_mov_uc.location_repo.get_by_id = MagicMock(return_value=loc1)
    with pytest.raises(RuntimeError):
        mock_mov_uc.create_movement(
            asset.id,
            AssetMovementCreate(origin_location_id=1, dest_location_id=None),
            moved_by_id=user.id,
        )
    mock_db.rollback.assert_called_once()

    # Rollback no accept_custody_term
    mock_db.reset_mock()
    mock_mov = AssetMovement(id=1, asset_id=asset.id, origin_location_id=1, moved_by_id=1)
    mock_mov_uc.movement_repo.get_by_id = MagicMock(return_value=mock_mov)
    with pytest.raises(RuntimeError):
        mock_mov_uc.accept_custody_term(1)
    mock_db.rollback.assert_called_once()

    # Reset mock antes do create_maintenance
    mock_db.reset_mock()
    mock_maint_uc = MaintenanceUseCases(mock_db)
    mock_maint_uc.asset_repo.get_by_id = MagicMock(return_value=asset)
    mock_db.commit.side_effect = RuntimeError("Maint commit fail")
    with pytest.raises(RuntimeError):
        mock_maint_uc.create_maintenance(
            asset.id,
            AssetMaintenanceCreate(maintenance_type="corretiva", description="Reparo"),
            registered_by_id=user.id,
        )
    mock_db.rollback.assert_called_once()


def test_final_branch_coverage_completions(db_session: Session, create_test_user):
    """Cobre as últimas ramificações de if/else em Category, Asset e Movement."""
    user = create_test_user(email="user_branches_final@empresa.com")
    cat = Category(name="Cat Final")
    loc = Location(building="BFinal", floor="1", sector="TI")
    db_session.add_all([cat, loc])
    db_session.flush()

    asset = Asset(
        patrimony_number="PAT-FINAL-01",
        description="Ativo Final",
        category_id=cat.id,
        location_id=loc.id,
        brand="Dell",
    )
    db_session.add(asset)
    db_session.flush()

    # 1. CategoryUseCases: update com o mesmo nome exato (branch 56->62)
    cat_uc = CategoryUseCases(db_session)
    res_cat = cat_uc.update_category(cat.id, CategoryUpdate(name=cat.name))
    assert res_cat.name == cat.name

    # 2. AssetUseCases: update 404s para category, location e assigned_user
    asset_uc = AssetUseCases(db_session)
    with pytest.raises(NotFoundError):
        asset_uc.update_asset(asset.id, AssetUpdate(category_id=99999))
    with pytest.raises(NotFoundError):
        asset_uc.update_asset(asset.id, AssetUpdate(location_id=99999))
    with pytest.raises(NotFoundError):
        asset_uc.update_asset(asset.id, AssetUpdate(assigned_user_id=99999))

    # Update com serial válido não conflitante (branch 169->171) e relacionamentos válidos (linhas 151, 157, 163)
    res_up = asset_uc.update_asset(
        asset.id,
        AssetUpdate(
            category_id=cat.id,
            location_id=loc.id,
            assigned_user_id=user.id,
            serial_number="SN-NON-CONFLICT",
        ),
    )
    assert res_up.serial_number == "SN-NON-CONFLICT"
    assert res_up.category_id == cat.id
    assert res_up.location_id == loc.id
    assert res_up.assigned_user_id == user.id

    # 3. MovementUseCases: movimento com dest_location_id fornecido e to_user_id=None (branch 71->75)
    mov_uc = AssetMovementUseCases(db_session)
    mov = mov_uc.create_movement(
        asset.id,
        AssetMovementCreate(
            origin_location_id=loc.id,
            dest_location_id=loc.id,
            to_user_id=None,
        ),
        moved_by_id=user.id,
    )
    assert mov.dest_location_id == loc.id


@pytest.mark.anyio
async def test_auth_routes_coverage_revoked_and_logout(client, create_test_user):
    user = create_test_user(email="logout_cov@empresa.com", password="Password123!")
    from src.core.security import create_access_token, create_refresh_token, revoke_token

    access_tok = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    refresh_tok = create_refresh_token({"sub": str(user.id)})

    # Teste de refresh com token já revogado (linha 156)
    revoke_token(refresh_tok)
    client.cookies.set("refresh_token", refresh_tok)
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401
    assert "revogado" in resp.json()["detail"]

    # Teste de logout com Authorization Header e refresh cookie (linhas 214, 218, 220)
    client.cookies.clear()
    client.cookies.set("refresh_token", refresh_tok)
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_tok}"},
    )
    assert logout_resp.status_code == 200

    # Teste de logout com access_token em cookie (branch 211->215)
    client.cookies.set("access_token", access_tok)
    logout_resp2 = await client.post("/api/v1/auth/logout")
    assert logout_resp2.status_code == 200


def test_security_and_repo_edge_branches(db_session: Session, monkeypatch):
    from src.core.security import revoke_token, is_token_revoked, decode_token, create_access_token
    from src.infrastructure.repositories import UserRepository

    # Linha 24->exit e 31
    revoke_token("")
    assert is_token_revoked("") is True
    assert is_token_revoked(None) is True

    # Linhas 136-137: decode_token quando jwt.decode falha (fallback payload)
    import jwt

    valid_token = create_access_token({"sub": "user_fallback_123"})
    monkeypatch.setattr(
        jwt,
        "decode",
        lambda *args, **kwargs: (_ for _ in ()).throw(jwt.PyJWTError("Simulated decode failure")),
    )
    decoded = decode_token(valid_token)
    assert decoded["sub"] == "user_fallback_123"

    # Repositório branch 30->32
    user_repo = UserRepository(db_session)
    u = User(
        email="del_user@teste.com",
        role="tecnico",
        password_hash="hash",
        deleted_at=datetime.now(timezone.utc),
    )
    user_repo.create(u)
    db_session.flush()
    assert user_repo.get_by_email("del_user@teste.com", include_deleted=True) is not None
    assert user_repo.get_by_email("del_user@teste.com", include_deleted=False) is None

    # AuthenticateUserUseCase linha 45: _record_success limpa email em failed_email_attempts
    from src.use_cases.authenticate_user import (
        _record_failed_attempt,
        _record_success,
        _cleanup_and_count_attempts,
    )

    email_map = {}
    _record_failed_attempt(email_map, "test@clean.com")
    assert _cleanup_and_count_attempts(email_map, "test@clean.com") == 1
    _record_success("1.2.3.4", "test@clean.com", email_map=email_map)
    assert _cleanup_and_count_attempts(email_map, "test@clean.com") == 0


def test_import_spreadsheet_remaining_branches(db_session: Session, monkeypatch):
    from src.use_cases.import_spreadsheet_use_cases import ExecuteSpreadsheetImportUseCase
    from src.infrastructure.spreadsheet_parser import ParsedSpreadsheet, ParsedSpreadsheetRow

    cat_repo = CategoryRepository(db_session)
    loc_repo = LocationRepository(db_session)
    asset_repo = AssetRepository(db_session)

    cat = Category(name="Geral")
    cat_repo.create(cat)
    loc = Location(building="Prédio Central", floor="1º Andar", sector="Recepcao")
    loc_repo.create(loc)
    db_session.flush()

    asset = Asset(
        patrimony_number="PAT-MOB-01",
        description="Mesa de Escritorio",
        category_id=cat.id,
        location_id=loc.id,
        brand="Kappesberg",
        model="Original",
        status="disponivel",
    )
    asset_repo.create(asset)
    db_session.flush()

    # Linha com status None (branch 136->145) e description, brand, model None ao atualizar (branch 166->168)
    mock_parsed = ParsedSpreadsheet(
        filename="mob.xlsx",
        headers=["TIPO"],
        detected_sheet="Planilha",
        rows=[
            ParsedSpreadsheetRow(
                row_number=1,
                equipment_type="Geral",
                location="Recepcao",
                status=None,
                description=None,
                patrimony_number="PAT-MOB-01",
                serial_number=None,
                brand=None,
                model=None,
            )
        ],
    )
    monkeypatch.setattr(
        "src.use_cases.import_spreadsheet_use_cases.parse_spreadsheet",
        lambda *args, **kwargs: mock_parsed,
    )

    uc = ExecuteSpreadsheetImportUseCase(db_session)
    res = uc.execute(b"dummy", "mob.xlsx")
    assert res.updated_count == 1
    db_session.refresh(asset)
    assert asset.description == "Mesa de Escritorio"
    assert asset.status == "disponivel"
    assert asset.brand == "Kappesberg"
    assert asset.model == "Original"
