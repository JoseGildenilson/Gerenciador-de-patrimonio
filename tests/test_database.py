"""Testes para utilitários de banco de dados e repositórios."""

import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from src.core.config import Settings, settings
from src.core.database import (
    get_db,
    sanitize_sql_params,
    extract_and_sanitize_params,
    register_sql_logging_listeners,
)
from src.infrastructure.repositories import UserRepository
from src.domain.models import User


def test_get_db_generator():
    """Testa a injeção de dependência get_db."""
    db_gen = get_db()
    db = next(db_gen)
    assert isinstance(db, Session)
    try:
        next(db_gen)
    except StopIteration:
        pass


def test_user_repository_create_get_soft_delete_and_restore(db_session: Session):
    """Testa o repositório UserRepository (create, get_by_id, soft_delete e restore)."""
    repo = UserRepository(db_session)
    new_user = User(email="new_repo_user@empresa.com", password_hash="hash", role="tecnico")

    created = repo.create(new_user)
    db_session.flush()
    assert created.id is not None

    found = repo.get_by_id(created.id)
    assert found is not None
    assert found.email == "new_repo_user@empresa.com"

    # Soft delete
    repo.soft_delete(found)
    db_session.flush()

    assert repo.get_by_id(created.id) is None
    assert repo.get_by_id(created.id, include_deleted=True) is not None

    # Restore
    repo.restore(found)
    db_session.flush()
    assert repo.get_by_id(created.id) is not None

    not_found = repo.get_by_id(999999)
    assert not_found is None


def test_sanitize_sql_params():
    """Valida higienização de parâmetros sensíveis."""
    assert sanitize_sql_params(None) is None
    assert sanitize_sql_params({}) == {}
    assert sanitize_sql_params([]) == []
    assert sanitize_sql_params("raw_scalar") == "raw_scalar"
    assert sanitize_sql_params((1, 2, 3)) == (1, 2, 3)

    params = {
        "email": "user@test.com",
        "password_hash": "argon2$secret",
        "token": "jwt-token-val",
        "api_key": "secret-api-key",
        "normal_field": 123,
    }
    sanitized = sanitize_sql_params(params)
    assert sanitized["email"] == "user@test.com"
    assert sanitized["normal_field"] == 123
    assert sanitized["password_hash"] == "[REDACTED]"
    assert sanitized["token"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"

    # Test list of dicts (executemany)
    list_params = [
        {"id": 1, "password": "pass1"},
        {"id": 2, "password": "pass2"},
    ]
    sanitized_list = sanitize_sql_params(list_params)
    assert sanitized_list[0]["password"] == "[REDACTED]"
    assert sanitized_list[1]["password"] == "[REDACTED]"


def test_extract_and_sanitize_params():
    """Valida extração de parâmetros compilados e fallbacks."""
    # Context nulo
    assert extract_and_sanitize_params(None, {"password": "123"}) == {"password": "[REDACTED]"}

    # Context com execution_context
    class DummyExecutionContext:
        compiled_parameters = [{"token": "jwt_secret"}]

    class DummyContextWithEC:
        execution_context = DummyExecutionContext()

    res = extract_and_sanitize_params(DummyContextWithEC(), None)
    assert res == {"token": "[REDACTED]"}

    # Context com multiplos itens compilados (bulk)
    class DummyContextBulk:
        compiled_parameters = [{"password": "p1"}, {"password": "p2"}]

    res_bulk = extract_and_sanitize_params(DummyContextBulk(), None)
    assert len(res_bulk) == 2
    assert res_bulk[0]["password"] == "[REDACTED]"
    assert res_bulk[1]["password"] == "[REDACTED]"


def test_settings_log_sql_statements():
    """Valida configurações de ativação do LOG_SQL_STATEMENTS."""
    s1 = Settings(LOG_SQL_STATEMENTS=True)
    assert s1.LOG_SQL_STATEMENTS is True
    s2 = Settings(LOG_SQL_STATEMENTS=False)
    assert s2.LOG_SQL_STATEMENTS is False

    s_dev = Settings(ENVIRONMENT="development")
    assert s_dev.LOG_SQL_STATEMENTS is True

    s_prod = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="chave-de-producao-verdadeiramente-segura-e-longa-32-chars",
    )
    assert s_prod.LOG_SQL_STATEMENTS is False

    old_env = os.environ.get("LOG_SQL_STATEMENTS")
    try:
        os.environ["LOG_SQL_STATEMENTS"] = "true"
        s_env_true = Settings(
            ENVIRONMENT="production",
            SECRET_KEY="chave-de-producao-verdadeiramente-segura-e-longa-32-chars",
        )
        assert s_env_true.LOG_SQL_STATEMENTS is True

        os.environ["LOG_SQL_STATEMENTS"] = "false"
        s_env_false = Settings(ENVIRONMENT="development")
        assert s_env_false.LOG_SQL_STATEMENTS is False
    finally:
        if old_env is not None:
            os.environ["LOG_SQL_STATEMENTS"] = old_env
        else:
            os.environ.pop("LOG_SQL_STATEMENTS", None)


def test_sql_logging_listeners_lifecycle(capsys):
    """Testa o listener de SQL no SQLAlchemy (queries, binds, healthchecks e erros)."""
    test_eng = create_engine("sqlite:///:memory:")
    register_sql_logging_listeners(test_eng)

    original_setting = settings.LOG_SQL_STATEMENTS
    try:
        settings.LOG_SQL_STATEMENTS = True

        with test_eng.connect() as conn:
            # 1. Healthcheck SELECT 1 deve ser filtrado
            conn.execute(text("SELECT 1;"))
            captured = capsys.readouterr().out
            assert "[SQL QUERY]" not in captured
            assert "SELECT 1" not in captured

            # 2. Query normal sem params
            conn.execute(text("SELECT 100 AS num;"))
            captured = capsys.readouterr().out
            assert "[SQL QUERY]" in captured
            assert "SELECT 100 AS num" in captured

            # 3. Query com parâmetros e mascaramento
            conn.execute(
                text("SELECT :user AS u, :password_hash AS p;"),
                {"user": "admin", "password_hash": "segredo_123"},
            )
            captured = capsys.readouterr().out
            assert "[SQL QUERY]" in captured
            assert "'user': 'admin'" in captured
            assert "'password_hash': '[REDACTED]'" in captured
            assert "segredo_123" not in captured

        settings.LOG_SQL_STATEMENTS = False
        with test_eng.connect() as conn:
            conn.execute(text("SELECT 200 AS num;"))
            captured = capsys.readouterr().out
            assert "[SQL QUERY]" not in captured
            assert captured == ""

    finally:
        settings.LOG_SQL_STATEMENTS = original_setting


def test_sql_logging_listeners_edge_cases(capsys):
    """Testa casos de borda com context nulo ou sem start time."""
    test_eng = create_engine("sqlite:///:memory:")
    register_sql_logging_listeners(test_eng)

    before_fn = list(test_eng.dispatch.before_cursor_execute)[0]
    after_fn = list(test_eng.dispatch.after_cursor_execute)[0]

    original_setting = settings.LOG_SQL_STATEMENTS
    try:
        settings.LOG_SQL_STATEMENTS = True

        # context is None em before e after
        before_fn(None, None, "SELECT 1", None, None, False)
        after_fn(None, None, "SELECT 42", None, None, False)
        captured = capsys.readouterr().out
        assert "[SQL QUERY]" in captured
        assert "SELECT 42" in captured

        # after com SELECT 1 deve ser ignorado
        after_fn(None, None, "SELECT 1;", None, None, False)
        captured = capsys.readouterr().out
        assert captured == ""

    finally:
        settings.LOG_SQL_STATEMENTS = original_setting


@pytest.mark.anyio
async def test_sql_logging_during_api_request(client, create_test_user, capsys):
    """Valida emissão de logs SQL (SELECT, INSERT, UPDATE e soft-delete) em 100% das rotas da API."""
    original_setting = settings.LOG_SQL_STATEMENTS
    try:
        settings.LOG_SQL_STATEMENTS = True
        capsys.readouterr()

        # 0. Criação de usuário (INSERT em users com password_hash mascarado como [REDACTED])
        user = create_test_user(
            email="sql_audit_admin@sispatrimonio.edu.br",
            password="SenhaAudit123!",
            role="administrador",
        )
        out_user = capsys.readouterr().out
        assert "[SQL QUERY]" in out_user
        assert "INSERT INTO users" in out_user
        assert "[REDACTED]" in out_user
        assert "SenhaAudit123!" not in out_user

        # 1. Healthcheck e Login (POST /api/v1/auth/login -> SELECT em users)
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "sql_audit_admin@sispatrimonio.edu.br", "password": "SenhaAudit123!"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        out_login = capsys.readouterr().out
        assert "[SQL QUERY]" in out_login
        assert "SELECT" in out_login and "FROM users" in out_login
        assert "SELECT 1" not in out_login

        # 2. Categorias: POST e GET (/api/v1/categories -> INSERT e SELECT)
        cat_post = await client.post(
            "/api/v1/categories",
            json={
                "name": "Audit Notebooks",
                "useful_life_months": 48,
                "residual_value_rate": "10.00",
                "requires_serial_number": True,
            },
            headers=headers,
        )
        assert cat_post.status_code == 201
        cat_id = cat_post.json()["id"]
        out_cat_post = capsys.readouterr().out
        assert "INSERT INTO categories" in out_cat_post

        cat_get = await client.get("/api/v1/categories", headers=headers)
        assert cat_get.status_code == 200
        out_cat_get = capsys.readouterr().out
        assert "SELECT" in out_cat_get and "FROM categories" in out_cat_get

        # 3. Localizações: POST e GET (/api/v1/locations -> INSERT e SELECT)
        loc_post = await client.post(
            "/api/v1/locations",
            json={
                "building": "Bloco Audit",
                "floor": "1º Andar",
                "sector": "Auditoria SQL",
                "room_number": "101",
            },
            headers=headers,
        )
        assert loc_post.status_code == 201
        loc_id = loc_post.json()["id"]
        out_loc_post = capsys.readouterr().out
        assert "INSERT INTO locations" in out_loc_post

        loc_get = await client.get("/api/v1/locations", headers=headers)
        assert loc_get.status_code == 200
        out_loc_get = capsys.readouterr().out
        assert "SELECT" in out_loc_get and "FROM locations" in out_loc_get

        # 4. Ativos: POST, GET, PUT/PATCH, Renumber e DELETE (/api/v1/assets)
        asset_post = await client.post(
            "/api/v1/assets",
            json={
                "patrimony_number": "PAT-AUDIT-001",
                "serial_number": "SN-AUDIT-001",
                "description": "Notebook de Auditoria SQL",
                "category_id": cat_id,
                "location_id": loc_id,
                "brand": "Dell",
                "model": "Latitude",
                "status": "disponivel",
                "specs": {"ram": "16GB"},
            },
            headers=headers,
        )
        assert asset_post.status_code == 201
        asset_id = asset_post.json()["id"]
        out_asset_post = capsys.readouterr().out
        assert "INSERT INTO assets" in out_asset_post

        asset_list = await client.get("/api/v1/assets", headers=headers)
        assert asset_list.status_code == 200
        out_asset_list = capsys.readouterr().out
        assert "SELECT" in out_asset_list and "FROM assets" in out_asset_list

        asset_put = await client.put(
            f"/api/v1/assets/{asset_id}",
            json={"description": "Notebook de Auditoria SQL Atualizado", "status": "em_uso"},
            headers=headers,
        )
        assert asset_put.status_code == 200
        out_asset_put = capsys.readouterr().out
        assert "UPDATE assets" in out_asset_put

        # 5. Movimentações e Manutenções (/api/v1/assets/{id}/movements e maintenances)
        mov_post = await client.post(
            f"/api/v1/assets/{asset_id}/movements",
            json={
                "origin_location_id": loc_id,
                "dest_location_id": loc_id,
                "to_user_id": user.id,
                "notes": "Movimentação auditada",
            },
            headers=headers,
        )
        assert mov_post.status_code == 201
        out_mov = capsys.readouterr().out
        assert "INSERT INTO asset_movements" in out_mov

        maint_post = await client.post(
            f"/api/v1/assets/{asset_id}/maintenances",
            json={
                "maintenance_type": "preventiva",
                "description": "Manutenção auditada",
                "cost": "100.00",
            },
            headers=headers,
        )
        assert maint_post.status_code == 201
        out_maint = capsys.readouterr().out
        assert "INSERT INTO asset_maintenances" in out_maint

        # 6. Dashboard (/api/v1/dashboard/metrics -> SELECT agregações)
        dash_get = await client.get("/api/v1/dashboard/metrics", headers=headers)
        assert dash_get.status_code == 200
        out_dash = capsys.readouterr().out
        assert "SELECT count(assets.id)" in out_dash

        # 7. Soft-delete de Ativo (DELETE /api/v1/assets/{id} -> UPDATE assets SET deleted_at)
        asset_del = await client.delete(f"/api/v1/assets/{asset_id}", headers=headers)
        assert asset_del.status_code in (200, 204)
        out_del = capsys.readouterr().out
        assert "UPDATE assets" in out_del and "deleted_at" in out_del
    finally:
        settings.LOG_SQL_STATEMENTS = original_setting
