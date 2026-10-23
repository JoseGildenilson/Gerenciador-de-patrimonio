"""Testes complementares de cobertura para tags de equipamentos, catálogo e use cases."""

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError

from src.core.security import create_access_token
from src.domain.models import EquipmentType, Sector, EquipmentStatus, MaintenanceType, Equipment
from src.domain.schemas import (
    TagCreate,
    TagUpdate,
    CatalogItemCreate,
    CatalogItemUpdate,
    EquipmentCreate,
    EquipmentUpdate,
)
from src.use_cases.equipment_use_cases import (
    ManageCatalogsUseCase,
    CreateEquipmentUseCase,
    UpdateEquipmentUseCase,
    DeleteEquipmentUseCase,
    RestoreEquipmentUseCase,
    ConflictError,
)


@pytest.mark.anyio
async def test_equipment_tags_api_full_lifecycle(
    client: AsyncClient,
    create_test_user,
    test_catalogs,
):
    """Testa listagem, criação, edição e exclusão de tags via /api/v1/equipments/tags."""
    tecnico = create_test_user(email="tec_tags_test@empresa.com", role="tecnico")
    token = create_access_token(data={"sub": str(tecnico.id), "role": "tecnico"})
    client.cookies.set("access_token", token)

    # 1. Listagem completa
    res_list = await client.get("/api/v1/equipments/tags")
    assert res_list.status_code == 200
    tags = res_list.json()
    assert len(tags) >= 4
    categories = {t["category"] for t in tags}
    assert "tipo" in categories or "localizacao" in categories or "situacao" in categories

    # 2. Listagem filtrada por categoria
    res_tipo = await client.get("/api/v1/equipments/tags", params={"category": "tipo"})
    assert res_tipo.status_code == 200
    for t in res_tipo.json():
        assert t["category"] == "tipo"

    # Listagem com categoria inexistente
    res_empty = await client.get("/api/v1/equipments/tags", params={"category": "inexistente"})
    assert res_empty.status_code == 200
    assert res_empty.json() == []

    # 3. Criação de nova tag válida (tipo)
    res_create = await client.post(
        "/api/v1/equipments/tags",
        json={
            "category": "tipo",
            "name": "Tablet Profissional",
        },
    )
    assert res_create.status_code == 201
    created_tag = res_create.json()
    assert created_tag["name"] == "Tablet Profissional"
    assert created_tag["category"] == "tipo"
    tag_id = created_tag["id"]

    # Criação com categoria inválida -> 400
    res_invalid_cat = await client.post(
        "/api/v1/equipments/tags",
        json={
            "category": "invalida",
            "name": "Nome",
        },
    )
    assert res_invalid_cat.status_code == 400

    # Criação duplicada -> 400
    res_dup = await client.post(
        "/api/v1/equipments/tags",
        json={
            "category": "tipo",
            "name": "Tablet Profissional",
        },
    )
    assert res_dup.status_code == 400

    # 4. Atualização de tag existente
    res_update = await client.put(
        f"/api/v1/equipments/tags/{tag_id}",
        json={
            "name": "Tablet Corporativo",
        },
    )
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Tablet Corporativo"

    # Atualização para tag inexistente -> 404
    res_upd_404 = await client.put("/api/v1/equipments/tags/99999", json={"name": "X"})
    assert res_upd_404.status_code == 404

    # 5. Exclusão de tag existente
    res_del = await client.delete(f"/api/v1/equipments/tags/{tag_id}")
    assert res_del.status_code == 200
    assert "excluída com sucesso" in res_del.json()["message"]

    # Exclusão de tag inexistente -> 404
    res_del_404 = await client.delete("/api/v1/equipments/tags/99999")
    assert res_del_404.status_code == 404


def test_manage_catalogs_use_case_edge_cases(db_session: Session):
    """Cobre métodos de soft-delete, restauração, referências ativas e exceções em ManageCatalogsUseCase."""
    uc = ManageCatalogsUseCase(db_session)

    item = uc.create_item(EquipmentType, CatalogItemCreate(name="Servidor Blade"))
    item_id = item.id

    # Busca por ID inexistente -> KeyError
    with pytest.raises(KeyError, match="não encontrado"):
        uc.get_item(EquipmentType, 99999)

    # Update item inexistente -> KeyError
    with pytest.raises(KeyError, match="não encontrado"):
        uc.update_item(EquipmentType, 99999, CatalogItemUpdate(name="Novo"))

    # Delete item inexistente -> KeyError
    with pytest.raises(KeyError, match="não encontrado"):
        uc.delete_item(EquipmentType, 99999)

    # Soft delete com sucesso
    uc.delete_item(EquipmentType, item_id)
    assert uc.get_item(EquipmentType, item_id).deleted_at is not None

    # Restaura item inexistente -> KeyError
    with pytest.raises(KeyError, match="não encontrado"):
        uc.restore_item(EquipmentType, 99999)

    # Restaura com sucesso
    restored = uc.restore_item(EquipmentType, item_id)
    assert restored.deleted_at is None

    # Teste de tentativa de exclusão de item com referência ativa (ISSUE-012)
    sector_item = uc.create_item(Sector, CatalogItemCreate(name="Setor Com Ativos"))
    status_item = uc.create_item(EquipmentStatus, CatalogItemCreate(name="Status Com Ativos"))
    eq = Equipment(
        patrimony_number="PAT-REF-ACTIVE-1",
        equipment_type_id=item_id,
        sector_id=sector_item.id,
        status_id=status_item.id,
    )
    db_session.add(eq)
    db_session.flush()

    with pytest.raises(ValueError, match="Não é possível excluir o item"):
        uc.delete_item(EquipmentType, item_id)

    with pytest.raises(ValueError, match="Não é possível excluir o item"):
        uc.delete_item(Sector, sector_item.id)

    with pytest.raises(ValueError, match="Não é possível excluir o item"):
        uc.delete_item(EquipmentStatus, status_item.id)

    # Rollback em erro no create_item
    mock_db = MagicMock()
    mock_db.commit.side_effect = IntegrityError("Unique violation", orig=Exception(), params=[])
    mock_repo_create = MagicMock()
    mock_repo_create.get_by_name_lower.return_value = None
    uc_mock = ManageCatalogsUseCase(mock_db, repo=mock_repo_create)
    with pytest.raises(ValueError, match="já está cadastrado"):
        uc_mock.create_item(EquipmentType, CatalogItemCreate(name="Item Falha"))
    mock_db.rollback.assert_called_once()

    # Rollback em erro genérico no delete_item
    mock_db_del = MagicMock()
    mock_db_del.query.return_value.filter.return_value.first.return_value = None
    mock_db_del.commit.side_effect = RuntimeError("Erro de banco")
    unused_item = EquipmentType(id=8888, name="Item Sem Uso", created_at=None, deleted_at=None)
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = unused_item
    uc_del = ManageCatalogsUseCase(mock_db_del, repo=mock_repo)
    with pytest.raises(RuntimeError):
        uc_del.delete_item(EquipmentType, unused_item.id)
    mock_db_del.rollback.assert_called_once()


def test_equipment_use_cases_rollback_and_stale_data(db_session: Session, test_catalogs):
    """Testa branches de exceção, rollback transacional e concorrência otimista (StaleDataError)."""
    create_uc = CreateEquipmentUseCase(db_session)

    eq = create_uc.execute(
        EquipmentCreate(
            patrimony_number="PAT-ROLLBACK-1",
            equipment_type_id=test_catalogs["type"].id,
            sector_id=test_catalogs["sector_ti"].id,
            status_id=test_catalogs["status_em_uso"].id,
        )
    )

    # 1. Simula StaleDataError no UpdateEquipmentUseCase
    mock_db = MagicMock()
    mock_db.commit.side_effect = StaleDataError("Concorrência detectada")
    mock_eq_repo = MagicMock()
    mock_eq_repo.get_by_id.return_value = eq
    uc_stale = UpdateEquipmentUseCase(mock_db, eq_repo=mock_eq_repo, cat_repo=MagicMock())

    with pytest.raises(ConflictError, match="modificado concorrentemente"):
        uc_stale.execute(eq.id, EquipmentUpdate(description="Alteração"))
    mock_db.rollback.assert_called_once()

    # 2. Simula IntegrityError no UpdateEquipmentUseCase
    mock_db_int = MagicMock()
    mock_db_int.commit.side_effect = IntegrityError("Unique violation", orig=Exception(), params=[])
    uc_integrity = UpdateEquipmentUseCase(mock_db_int, eq_repo=mock_eq_repo, cat_repo=MagicMock())

    with pytest.raises(ConflictError, match="Conflito de unicidade"):
        uc_integrity.execute(eq.id, EquipmentUpdate(description="Alteração"))
    mock_db_int.rollback.assert_called_once()

    # 3. Simula Exception no DeleteEquipmentUseCase
    mock_db_del = MagicMock()
    mock_db_del.commit.side_effect = RuntimeError("Falha de I/O no banco")
    uc_del = DeleteEquipmentUseCase(mock_db_del, eq_repo=mock_eq_repo)
    with pytest.raises(RuntimeError):
        uc_del.execute(eq.id)
    mock_db_del.rollback.assert_called_once()

    # 4. Simula Exception no RestoreEquipmentUseCase
    mock_db_res = MagicMock()
    mock_db_res.commit.side_effect = RuntimeError("Falha no commit de restore")
    eq_deleted = MagicMock()
    eq_deleted.deleted_at = "not None"
    mock_eq_repo_res = MagicMock()
    mock_eq_repo_res.get_by_id.return_value = eq_deleted
    mock_eq_repo_res.check_restoration_conflicts.return_value = []
    uc_res = RestoreEquipmentUseCase(mock_db_res, eq_repo=mock_eq_repo_res)
    with pytest.raises(RuntimeError):
        uc_res.execute(eq.id)
    mock_db_res.rollback.assert_called_once()


@pytest.mark.anyio
async def test_catalog_and_equipment_api_error_branches(
    client: AsyncClient,
    create_test_user,
    test_catalogs,
    db_session: Session,
):
    """Testa branches de erro 400 e 409 em catalog_routes e equipment_routes."""
    tecnico = create_test_user(email="tec_cat_eq_errors@empresa.com", role="tecnico")
    token = create_access_token(data={"sub": str(tecnico.id), "role": "tecnico"})
    client.cookies.set("access_token", token)

    # 1. DELETE /api/v1/equipment-types/{id} quando o item está em uso por equipamento ativo -> 400
    eq_in_use = Equipment(
        patrimony_number="PAT-CAT-ERR-1",
        equipment_type_id=test_catalogs["type"].id,
        sector_id=test_catalogs["sector_ti"].id,
        status_id=test_catalogs["status_em_uso"].id,
    )
    db_session.add(eq_in_use)
    db_session.commit()

    res_del_in_use = await client.delete(f"/api/v1/equipment-types/{test_catalogs['type'].id}")
    assert res_del_in_use.status_code == 400
    assert "Não é possível excluir o item" in res_del_in_use.json()["detail"]

    # 2. POST /api/v1/equipment-types/{id}/restore quando o item NÃO está deletado -> 400
    res_restore_active = await client.post(
        f"/api/v1/equipment-types/{test_catalogs['type'].id}/restore"
    )
    assert res_restore_active.status_code == 400
    assert "já está ativo" in res_restore_active.json()["detail"]

    # 3. PUT /api/v1/equipments/tags/{id} com nome duplicado na mesma categoria -> 400
    res_tag_other = await client.post(
        "/api/v1/equipments/tags",
        json={"category": "tipo", "name": "Tipo Outro"},
    )
    assert res_tag_other.status_code == 201
    other_tag_id = res_tag_other.json()["id"]

    res_upd_tag_dup = await client.put(
        f"/api/v1/equipments/tags/{other_tag_id}",
        json={"name": test_catalogs["type"].name},
    )
    assert res_upd_tag_dup.status_code == 400
    assert "já está cadastrado" in res_upd_tag_dup.json()["detail"]

    # 4. DELETE /api/v1/equipments/tags/{id} quando a tag está em uso -> 400
    res_del_tag_in_use = await client.delete(f"/api/v1/equipments/tags/{test_catalogs['type'].id}")
    assert res_del_tag_in_use.status_code == 400
    assert "Não é possível excluir" in res_del_tag_in_use.json()["detail"]

    # 5. POST /api/v1/equipments com patrimônio duplicado -> 400
    res_create_dup = await client.post(
        "/api/v1/equipments",
        json={
            "patrimony_number": "PAT-CAT-ERR-1",
            "equipment_type_id": test_catalogs["type"].id,
            "sector_id": test_catalogs["sector_ti"].id,
            "status_id": test_catalogs["status_em_uso"].id,
        },
    )
    assert res_create_dup.status_code == 400
    assert "já está cadastrado" in res_create_dup.json()["detail"]

    # 6. POST /api/v1/equipments com ConflictError concorrente -> 409 (cobre linha 103 de equipment_routes)
    from unittest.mock import patch

    with patch(
        "src.api.equipment_routes.CreateEquipmentUseCase.execute",
        side_effect=ConflictError("Conflito concorrente"),
    ):
        res_create_conflict = await client.post(
            "/api/v1/equipments",
            json={
                "patrimony_number": "PAT-CONCURRENT-1",
                "equipment_type_id": test_catalogs["type"].id,
                "sector_id": test_catalogs["sector_ti"].id,
                "status_id": test_catalogs["status_em_uso"].id,
            },
        )
        assert res_create_conflict.status_code == 409

    # 7. PUT /api/v1/equipments/{id} com ConflictError concorrente -> 409 (cobre linha 312 de equipment_routes)
    with patch(
        "src.api.equipment_routes.UpdateEquipmentUseCase.execute",
        side_effect=ConflictError("Conflito de unicidade"),
    ):
        res_put_conflict = await client.put(
            f"/api/v1/equipments/{eq_in_use.id}",
            json={"description": "Nova desc"},
        )
        assert res_put_conflict.status_code == 409


@pytest.mark.anyio
async def test_auth_routes_refresh_and_logout_edges(
    client: AsyncClient,
    create_test_user,
):
    """Testa caminhos adicionais de autenticação, refresh com token revogado e logout com header Bearer."""
    user = create_test_user(email="auth_edges_test@empresa.com", role="tecnico")
    from src.core.security import create_refresh_token, revoke_token

    access_tok = create_access_token(data={"sub": str(user.id), "role": "tecnico"})
    refresh_tok = create_refresh_token(data={"sub": str(user.id)})

    # 1. Refresh com token revogado -> 401
    revoke_token(refresh_tok)
    client.cookies.set("refresh_token", refresh_tok)
    res_ref_revoked = await client.post("/api/v1/auth/refresh")
    assert res_ref_revoked.status_code == 401
    assert "revogado" in res_ref_revoked.json()["detail"]

    # 2. Logout com Authorization Bearer header e refresh_token em cookie
    fresh_access = create_access_token(data={"sub": str(user.id), "role": "tecnico"})
    fresh_refresh = create_refresh_token(data={"sub": str(user.id)})
    client.cookies.set("refresh_token", fresh_refresh)
    client.headers["Authorization"] = f"Bearer {fresh_access}"

    res_logout = await client.post("/api/v1/auth/logout")
    assert res_logout.status_code == 200
    assert "Logout realizado com sucesso" in res_logout.json()["message"]


def test_core_security_and_repositories_edges(db_session: Session):
    """Cobre branches de revoke/is_revoked, decode_token fallback, repositories e type decorators."""
    from src.core.security import revoke_token, is_token_revoked, decode_token
    from src.infrastructure.repositories import LoginAttemptRepository
    from src.domain.models import IPAddressType, MACAddressType

    # 1. Revoke / is_token_revoked com strings vazias / None
    revoke_token("")
    assert is_token_revoked("") is True
    assert is_token_revoked(None) is True
    assert is_token_revoked("unknown_token_xyz") is False

    # 2. decode_token fallback quando jwt.decode falha mas decode básico funcionou
    from unittest.mock import patch
    import jwt

    token = create_access_token(data={"sub": "123", "role": "tecnico"})
    with patch("jwt.decode", side_effect=jwt.InvalidTokenError("Mock fail")):
        payload = decode_token(token)
        assert payload["sub"] == "123"

    # 3. LoginAttemptRepository com email vazio
    repo = LoginAttemptRepository(db_session)
    assert repo.count_recent_failed_attempts_by_email("") == 0

    # 4. IPAddressType e MACAddressType em dialeto PostgreSQL
    mock_pg = MagicMock()
    mock_pg.name = "postgresql"
    ip_type = IPAddressType()
    mac_type = MACAddressType()
    ip_impl = ip_type.load_dialect_impl(mock_pg)
    mac_impl = mac_type.load_dialect_impl(mock_pg)
    assert mock_pg.type_descriptor.call_count >= 2


def test_use_cases_exception_rollback_all_handlers(test_catalogs):
    """Garante que todos os blocos `except Exception: self.db.rollback(); raise` são exercitados."""
    from src.domain.schemas import (
        EquipmentMovementCreate,
        EquipmentMaintenanceStart,
        EquipmentMaintenanceComplete,
        EquipmentMaintenanceUpdate,
    )
    from src.use_cases.equipment_use_cases import (
        MovementsUseCase,
        MaintenancesUseCase,
    )
    from datetime import datetime, timezone

    # 1. ManageCatalogsUseCase update_item Exception rollback
    mock_db = MagicMock()
    mock_db.commit.side_effect = RuntimeError("DB Fail")
    mock_repo = MagicMock()
    item = EquipmentType(id=1, name="Tipo Teste", created_at=None, deleted_at=None)
    mock_repo.get_by_id.return_value = item
    mock_repo.get_by_name_lower.return_value = None
    uc_cat = ManageCatalogsUseCase(mock_db, repo=mock_repo)

    with pytest.raises(RuntimeError):
        uc_cat.update_item(EquipmentType, 1, CatalogItemUpdate(name="Novo Nome"))
    mock_db.rollback.assert_called_once()

    # 2. ManageCatalogsUseCase restore_item Exception rollback
    mock_db_res = MagicMock()
    mock_db_res.commit.side_effect = RuntimeError("DB Fail")
    item_del = EquipmentType(
        id=2, name="Deletado", created_at=None, deleted_at=datetime.now(timezone.utc)
    )
    mock_repo_res = MagicMock()
    mock_repo_res.get_by_id.return_value = item_del
    mock_repo_res.get_by_name_lower.return_value = None
    uc_cat_res = ManageCatalogsUseCase(mock_db_res, repo=mock_repo_res)

    with pytest.raises(RuntimeError):
        uc_cat_res.restore_item(EquipmentType, 2)
    mock_db_res.rollback.assert_called_once()

    # 3. CreateEquipmentUseCase Exception rollback
    mock_db_create = MagicMock()
    mock_db_create.commit.side_effect = RuntimeError("DB Fail")
    mock_cat = MagicMock()
    mock_cat.get_by_id.return_value = MagicMock(deleted_at=None)
    mock_eq_create = MagicMock()
    mock_eq_create.get_by_patrimony_number.return_value = None
    mock_eq_create.get_by_serial_number.return_value = None
    mock_eq_create.get_active_by_hostname.return_value = None
    mock_eq_create.get_active_by_ip.return_value = None
    mock_eq_create.get_active_by_mac.return_value = None
    mock_eq_create.get_active_by_printer_identifier.return_value = None
    uc_create = CreateEquipmentUseCase(mock_db_create, eq_repo=mock_eq_create, cat_repo=mock_cat)

    with pytest.raises(RuntimeError):
        uc_create.execute(
            EquipmentCreate(
                patrimony_number="PAT-EXC-1",
                equipment_type_id=1,
                sector_id=1,
                status_id=1,
            )
        )
    mock_db_create.rollback.assert_called_once()

    # 4. MovementsUseCase record_movement Exception rollback
    mock_db_mov = MagicMock()
    mock_db_mov.commit.side_effect = RuntimeError("DB Fail")
    mock_eq = MagicMock(deleted_at=None, sector_id=1)
    mock_eq_repo = MagicMock()
    mock_eq_repo.get_by_id.return_value = mock_eq
    mock_mov_repo = MagicMock()
    mock_mov_repo.get_last_movement.return_value = None
    mock_mov_repo.get_ordered_movements.return_value = []
    uc_mov = MovementsUseCase(
        mock_db_mov, eq_repo=mock_eq_repo, mov_repo=mock_mov_repo, cat_repo=mock_cat
    )

    with pytest.raises(RuntimeError):
        uc_mov.record_movement(
            1,
            EquipmentMovementCreate(
                origin_sector_id=1,
                destination_sector_id=2,
                responsible_name="Resp",
                reason="Motivo",
                movement_date=datetime.now(timezone.utc),
            ),
            performed_by_user_id=1,
        )
    mock_db_mov.rollback.assert_called_once()

    # 5. MaintenancesUseCase start_maintenance Exception rollback
    mock_db_maint = MagicMock()
    mock_db_maint.commit.side_effect = RuntimeError("DB Fail")
    mock_maint_repo = MagicMock()
    mock_maint_repo.get_open_maintenance.return_value = None
    status_em_manut = MagicMock(id=5, name="Em manutenção", deleted_at=None)
    mock_cat.get_by_name_lower.return_value = status_em_manut
    uc_maint = MaintenancesUseCase(
        mock_db_maint, eq_repo=mock_eq_repo, maint_repo=mock_maint_repo, cat_repo=mock_cat
    )

    with pytest.raises(RuntimeError):
        uc_maint.start_maintenance(
            1,
            EquipmentMaintenanceStart(
                maintenance_type_id=1,
                description="Manut",
                started_at=datetime.now(timezone.utc),
            ),
            performed_by_user_id=1,
        )
    mock_db_maint.rollback.assert_called_once()

    # 6. MaintenancesUseCase complete_maintenance Exception rollback & tz-aware started_at branch
    mock_db_comp = MagicMock()
    mock_db_comp.commit.side_effect = RuntimeError("DB Fail")
    open_maint = MagicMock(
        equipment_id=1,
        completed_at=None,
        started_at=datetime.now(timezone.utc),  # Aware datetime (covers line 879->882)
    )
    mock_maint_repo.get_by_id.return_value = open_maint
    mock_cat.get_by_id.return_value = MagicMock(name="Disponível", deleted_at=None)
    uc_comp = MaintenancesUseCase(
        mock_db_comp, eq_repo=mock_eq_repo, maint_repo=mock_maint_repo, cat_repo=mock_cat
    )

    with pytest.raises(RuntimeError):
        uc_comp.complete_maintenance(
            1,
            10,
            EquipmentMaintenanceComplete(
                new_status_id=3,
                completed_at=datetime.now(timezone.utc),
            ),
        )
    mock_db_comp.rollback.assert_called_once()

    # 7. MaintenancesUseCase update_maintenance Exception rollback
    mock_db_upd_maint = MagicMock()
    mock_db_upd_maint.commit.side_effect = RuntimeError("DB Fail")
    mock_maint_repo.get_by_id.return_value = open_maint
    uc_upd_maint = MaintenancesUseCase(
        mock_db_upd_maint, maint_repo=mock_maint_repo, cat_repo=mock_cat
    )

    with pytest.raises(RuntimeError):
        uc_upd_maint.update_maintenance(1, 10, EquipmentMaintenanceUpdate(description="Nova desc"))
    mock_db_upd_maint.rollback.assert_called_once()

    # 8. ManageCatalogsUseCase create_item Exception rollback (lines 94-96)
    mock_db_create_cat = MagicMock()
    mock_db_create_cat.commit.side_effect = RuntimeError("Generic DB Fail")
    mock_cat_repo = MagicMock()
    mock_cat_repo.get_by_name_lower.return_value = None
    uc_cat_create = ManageCatalogsUseCase(mock_db_create_cat, repo=mock_cat_repo)
    with pytest.raises(RuntimeError):
        uc_cat_create.create_item(EquipmentType, CatalogItemCreate(name="Fail Item"))
    mock_db_create_cat.rollback.assert_called_once()

    # 9. ManageCatalogsUseCase update_item IntegrityError rollback (lines 111-112)
    mock_db_upd_int = MagicMock()
    mock_db_upd_int.commit.side_effect = IntegrityError(
        "Unique violation", orig=Exception(), params=[]
    )
    mock_cat_repo_upd = MagicMock()
    mock_cat_repo_upd.get_by_id.return_value = item
    mock_cat_repo_upd.get_by_name_lower.return_value = None
    uc_cat_upd_int = ManageCatalogsUseCase(mock_db_upd_int, repo=mock_cat_repo_upd)
    with pytest.raises(ValueError, match="já está cadastrado"):
        uc_cat_upd_int.update_item(EquipmentType, 1, CatalogItemUpdate(name="Novo Nome"))
    mock_db_upd_int.rollback.assert_called_once()

    # 10. ManageCatalogsUseCase delete_item with MaintenanceType active ref (lines 143-144)
    mock_db_maint_ref = MagicMock()
    mock_db_maint_ref.query.return_value.filter.return_value.first.return_value = MagicMock()
    mock_cat_maint_ref = MagicMock()
    mock_cat_maint_ref.get_by_id.return_value = MaintenanceType(
        id=99, name="Corretiva", created_at=None, deleted_at=None
    )
    uc_cat_maint_ref = ManageCatalogsUseCase(mock_db_maint_ref, repo=mock_cat_maint_ref)
    with pytest.raises(ValueError, match="Não é possível excluir o item"):
        uc_cat_maint_ref.delete_item(MaintenanceType, 99)

    # 10b. ManageCatalogsUseCase delete_item with arbitrary class (branch 143->151)
    class OtherCatalog:
        pass

    mock_db_other = MagicMock()
    mock_cat_other = MagicMock()
    mock_cat_other.get_by_id.return_value = MagicMock(name="Item Outro")
    uc_cat_other = ManageCatalogsUseCase(mock_db_other, repo=mock_cat_other)
    uc_cat_other.delete_item(OtherCatalog, 123)
    mock_db_other.commit.assert_called_once()

    # 11. CreateEquipmentUseCase IntegrityError raises ConflictError (lines 268-269)
    mock_db_eq_int = MagicMock()
    mock_db_eq_int.commit.side_effect = IntegrityError("Unique error", orig=Exception(), params=[])
    uc_create_int = CreateEquipmentUseCase(
        mock_db_eq_int, eq_repo=mock_eq_create, cat_repo=mock_cat
    )
    with pytest.raises(ConflictError, match="Conflito de unicidade"):
        uc_create_int.execute(
            EquipmentCreate(
                patrimony_number="PAT-INT-1",
                equipment_type_id=1,
                sector_id=1,
                status_id=1,
            )
        )
    mock_db_eq_int.rollback.assert_called_once()

    # 12. UpdateEquipmentUseCase generic Exception rollback (lines 572-574)
    mock_db_upd_exc = MagicMock()
    mock_db_upd_exc.commit.side_effect = RuntimeError("Update Fail")
    mock_eq_upd_exc = MagicMock()
    mock_eq_upd_exc.get_by_id.return_value = mock_eq
    uc_upd_exc = UpdateEquipmentUseCase(mock_db_upd_exc, eq_repo=mock_eq_upd_exc, cat_repo=mock_cat)
    with pytest.raises(RuntimeError):
        uc_upd_exc.execute(1, EquipmentUpdate(description="Alteração"))
    mock_db_upd_exc.rollback.assert_called_once()

    # 13. RestoreEquipmentUseCase IntegrityError raises ConflictError (lines 621-622)
    mock_db_res_int = MagicMock()
    mock_db_res_int.commit.side_effect = IntegrityError(
        "Unique restore conflict", orig=Exception(), params=[]
    )
    mock_eq_deleted = MagicMock(deleted_at=datetime.now(timezone.utc))
    mock_eq_repo_res = MagicMock()
    mock_eq_repo_res.get_by_id.return_value = mock_eq_deleted
    mock_eq_repo_res.check_restoration_conflicts.return_value = []
    uc_res_int = RestoreEquipmentUseCase(mock_db_res_int, eq_repo=mock_eq_repo_res)
    with pytest.raises(ConflictError, match="Conflito de unicidade"):
        uc_res_int.execute(1)
    mock_db_res_int.rollback.assert_called_once()

    # 14. MaintenancesUseCase start_maintenance IntegrityError raises ConflictError (lines 856-857)
    mock_db_maint_int = MagicMock()
    mock_db_maint_int.commit.side_effect = IntegrityError(
        "Unique active maint conflict", orig=Exception(), params=[]
    )
    uc_maint_int = MaintenancesUseCase(
        mock_db_maint_int, eq_repo=mock_eq_repo, maint_repo=mock_maint_repo, cat_repo=mock_cat
    )
    with pytest.raises(ConflictError, match="Já existe uma manutenção"):
        uc_maint_int.start_maintenance(
            1,
            EquipmentMaintenanceStart(
                maintenance_type_id=1,
                description="Manut",
                started_at=datetime.now(timezone.utc),
            ),
            performed_by_user_id=1,
        )
    mock_db_maint_int.rollback.assert_called_once()


@pytest.mark.anyio
async def test_logout_with_access_token_in_cookies_branch(client: AsyncClient, create_test_user):
    """Cobre branch 211->215 de routes.py: logout com access_token diretamente nos cookies."""
    user = create_test_user(email="logout_cookie@empresa.com", role="tecnico")
    tok = create_access_token(data={"sub": str(user.id), "role": "tecnico"})
    client.cookies.set("access_token", tok)
    if "Authorization" in client.headers:
        del client.headers["Authorization"]

    res = await client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    assert "Logout realizado com sucesso" in res.json()["message"]
