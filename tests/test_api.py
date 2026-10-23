"""Testes de API HTTP utilizando httpx.AsyncClient para os endpoints de autenticação e rotas protegidas."""

from datetime import timedelta
from unittest.mock import MagicMock
import pytest
from httpx import AsyncClient
from src.api.routes import _extract_client_ip
from src.core.security import create_access_token, create_refresh_token, create_token
from src.main import lifespan, app


@pytest.mark.anyio
async def test_app_lifespan():
    """Testa o evento de ciclo de vida (lifespan) da aplicação FastAPI."""
    async with lifespan(app):
        pass


@pytest.mark.anyio
async def test_health_check_endpoint(client: AsyncClient):
    """Testa o endpoint de verificação de saúde da aplicação."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_login_success(client: AsyncClient, create_test_user):
    """Testa o login bem-sucedido via HTTP POST /login com verificação de cookies HttpOnly."""
    create_test_user(email="tecnico@empresa.com", password="SenhaSegura123!", role="tecnico")

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "tecnico@empresa.com", "password": "SenhaSegura123!"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "tecnico@empresa.com"
    assert data["user"]["role"] == "tecnico"

    # Verifica definição dos cookies HttpOnly
    cookies = response.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies


@pytest.mark.anyio
async def test_login_with_proxy_headers(client: AsyncClient, create_test_user):
    """Testa a captura de IP com cabeçalhos X-Forwarded-For e X-Real-IP."""
    create_test_user(email="tecnico2@empresa.com", password="SenhaSegura123!")

    # Teste com X-Forwarded-For
    res1 = await client.post(
        "/api/v1/auth/login",
        json={"email": "tecnico2@empresa.com", "password": "SenhaSegura123!"},
        headers={"X-Forwarded-For": "203.0.113.195, 70.41.3.18"},
    )
    assert res1.status_code == 200

    # Teste com X-Real-IP
    res2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "tecnico2@empresa.com", "password": "SenhaSegura123!"},
        headers={"X-Real-IP": "198.51.100.1"},
    )
    assert res2.status_code == 200


def test_extract_client_ip_fallback():
    """Testa o fallback para 127.0.0.1 caso o request não possua client."""
    mock_request = MagicMock()
    mock_request.headers.get.return_value = None
    mock_request.client = None

    ip = _extract_client_ip(mock_request)
    assert ip == "127.0.0.1"


@pytest.mark.anyio
async def test_login_invalid_credentials(client: AsyncClient, create_test_user):
    """Testa o envio de credenciais incorretas retornando HTTP 401."""
    create_test_user(email="tecnico@empresa.com", password="SenhaSegura123!")

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "tecnico@empresa.com", "password": "SenhaIncorreta!"},
    )

    assert response.status_code == 401
    assert "Credenciais de acesso inválidas" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_rate_limit_exceeded(client: AsyncClient):
    """Testa o bloqueio por excesso de tentativas (Rate Limit) com retorno HTTP 429."""
    for i in range(10):
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": f"errado_{i}@empresa.com", "password": "SenhaIncorreta!"},
        )
        assert res.status_code == 401

    # 11ª tentativa de login a partir do mesmo IP
    res11 = await client.post(
        "/api/v1/auth/login",
        json={"email": "tecnico@empresa.com", "password": "SenhaSegura123!"},
    )
    assert res11.status_code == 429
    assert "temporariamente bloqueado" in res11.json()["detail"]


@pytest.mark.anyio
async def test_refresh_token_success(client: AsyncClient, create_test_user):
    """Testa a renovação da sessão via POST /refresh."""
    user = create_test_user(email="tecnico@empresa.com", password="SenhaSegura123!")
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    client.cookies.set("refresh_token", refresh_token)
    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "tecnico@empresa.com"
    assert "access_token" in response.cookies


@pytest.mark.anyio
async def test_refresh_token_failures(client: AsyncClient, create_test_user):
    """Testa falhas na renovação de token (ausente, inválido, tipo incorreto)."""
    # Ausente
    client.cookies.clear()
    res1 = await client.post("/api/v1/auth/refresh")
    assert res1.status_code == 401

    # Inválido
    client.cookies.set("refresh_token", "invalid_token_str")
    res2 = await client.post("/api/v1/auth/refresh")
    assert res2.status_code == 401

    # Tipo incorreto (access_token enviado onde se espera refresh_token)
    user = create_test_user(email="user2@empresa.com", password="SenhaSegura123!")
    access_as_refresh = create_access_token(data={"sub": str(user.id)})
    client.cookies.set("refresh_token", access_as_refresh)
    res3 = await client.post("/api/v1/auth/refresh")
    assert res3.status_code == 401

    # Usuário inexistente
    fake_refresh = create_refresh_token(data={"sub": "99999"})
    client.cookies.set("refresh_token", fake_refresh)
    res4 = await client.post("/api/v1/auth/refresh")
    assert res4.status_code == 401


@pytest.mark.anyio
async def test_logout_endpoint(client: AsyncClient):
    """Testa o encerramento de sessão via POST /logout."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logout realizado com sucesso."


@pytest.mark.anyio
async def test_get_me_protected_route(client: AsyncClient, create_test_user):
    """Testa o acesso à rota protegida GET /me com e sem token de acesso."""
    user = create_test_user(email="tecnico@empresa.com", password="SenhaSegura123!", role="tecnico")

    # Acesso negado sem token
    res_no_token = await client.get("/api/v1/auth/me")
    assert res_no_token.status_code == 401

    # Acesso aceito via Cookie HttpOnly
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )
    client.cookies.set("access_token", access_token)
    res_cookie = await client.get("/api/v1/auth/me")
    assert res_cookie.status_code == 200
    assert res_cookie.json()["email"] == "tecnico@empresa.com"
    assert res_cookie.json()["role"] == "tecnico"

    # Acesso aceito via Header Authorization Bearer
    client.cookies.clear()
    res_header = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert res_header.status_code == 200
    assert res_header.json()["email"] == "tecnico@empresa.com"


@pytest.mark.anyio
async def test_get_me_invalid_tokens(client: AsyncClient, create_test_user):
    """Testa casos de erro no middleware get_current_user."""
    user = create_test_user(email="user3@empresa.com", password="SenhaSegura123!")

    # Token com formato/assinatura inválidos
    res_corrupt = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer token_corrompido.abc.xyz"}
    )
    assert res_corrupt.status_code == 401

    # Tipo de token incorreto (refresh token enviado no lugar de access_token)
    refresh_tok = create_refresh_token(data={"sub": str(user.id)})
    res1 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh_tok}"})
    assert res1.status_code == 401

    # Token sem sub (sub ausente/None)
    no_sub_tok = create_token(
        data={"email": "a@b.com"}, expires_delta=timedelta(minutes=15), token_type="access"
    )
    res2 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {no_sub_tok}"})
    assert res2.status_code == 401

    # Token com sub string vazia
    empty_sub_tok = create_token(
        data={"sub": ""}, expires_delta=timedelta(minutes=15), token_type="access"
    )
    res2_empty = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {empty_sub_tok}"}
    )
    assert res2_empty.status_code == 401

    # Sub não numérico
    invalid_sub_tok = create_access_token(data={"sub": "not_an_int"})
    res3 = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {invalid_sub_tok}"}
    )
    assert res3.status_code == 401

    # Usuário inexistente
    nonexistent_user_tok = create_access_token(data={"sub": "99999"})
    res4 = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {nonexistent_user_tok}"}
    )
    assert res4.status_code == 401
