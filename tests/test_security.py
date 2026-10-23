"""Testes unitários para os serviços de segurança, Argon2id, JWT e criptografia de chaves Windows."""

from datetime import timedelta
import base64
import pytest
from src.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    create_token,
    _base64url_encode,
    encrypt_windows_product_key,
    decrypt_windows_product_key,
    mask_windows_product_key,
)


def test_password_hashing_and_verification():
    """Testa a geração de hash Argon2id e a verificação de senhas corretas e incorretas."""
    password = "MinhaSenhaSuperSegura123!"
    hashed = hash_password(password)

    assert hashed is not None
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("SenhaIncorreta", hashed) is False
    assert verify_password(password, "hash_invalido_corrompido") is False


def test_password_hashing_entropy_and_dynamic_salt():
    """Testa se senhas idênticas geram hashes distintos devido ao salt dinâmico (TASK-QA-02)."""
    password = "SenhaIdentica123!"
    h1 = hash_password(password)
    h2 = hash_password(password)

    assert h1 != h2
    assert verify_password(password, h1) is True
    assert verify_password(password, h2) is True
    assert verify_password("OutraSenhaErrada", h1) is False
    assert verify_password("OutraSenhaErrada", h2) is False


def test_verify_password_fallback_formats_and_exceptions():
    """Testa compatibilidade com hash com delimitador $, legado sem divisor $ e tratamento de exceções."""
    import hashlib

    salt = b"1234567890abcdef"
    salt_b64 = base64.b64encode(salt).decode().rstrip("=")
    derived = hashlib.scrypt(b"minhasenha", salt=salt, n=16384, r=8, p=1, dklen=32)
    derived_b64 = base64.b64encode(derived).decode().rstrip("=")

    # Formato com delimitador $
    hash_with_dollar = f"$argon2id$v=19$m=65536,t=3,p=4${salt_b64}${derived_b64}"
    assert verify_password("minhasenha", hash_with_dollar) is True
    assert verify_password("senhaerrada", hash_with_dollar) is False

    # Formato legado sem delimitador $
    hash_without_dollar = f"$argon2id$v=19$m=65536,t=3,p=4${salt_b64}{derived_b64}"
    assert verify_password("minhasenha", hash_without_dollar) is True
    assert verify_password("senhaerrada", hash_without_dollar) is False

    # Hash corrompido que dispara exceção dentro do bloco try
    broken_hash = "$argon2id$v=19$m=65536,t=3,p=4$===invalid_base64_salt===$$$"
    assert verify_password("minhasenha", broken_hash) is False

    # Entrada nula, não-string ou vazia
    assert verify_password("minhasenha", None) is False
    assert verify_password("minhasenha", 12345) is False
    assert verify_password("minhasenha", "") is False

    # Validação do formato padrão gerado por hash_password
    generated_hash = hash_password("minhasenha")
    assert generated_hash.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    assert generated_hash.count("$") == 5
    assert verify_password("minhasenha", generated_hash) is True


def test_jwt_access_token_lifecycle():
    """Testa a geração e decodificação de access token JWT."""
    payload = {"sub": "1", "email": "tecnico@empresa.com", "role": "tecnico"}
    token = create_access_token(data=payload)

    assert isinstance(token, str)
    decoded = decode_token(token)

    assert decoded["sub"] == "1"
    assert decoded["email"] == "tecnico@empresa.com"
    assert decoded["role"] == "tecnico"
    assert decoded["type"] == "access"
    assert "exp" in decoded
    assert "iat" in decoded


def test_jwt_refresh_token_lifecycle():
    """Testa a geração e decodificação de refresh token JWT."""
    payload = {"sub": "1"}
    token = create_refresh_token(data=payload)

    assert isinstance(token, str)
    decoded = decode_token(token)

    assert decoded["sub"] == "1"
    assert decoded["type"] == "refresh"


def test_jwt_expired_token():
    """Testa a rejeição de tokens expirados."""
    payload = {"sub": "1"}
    token = create_token(data=payload, expires_delta=timedelta(seconds=-10), token_type="access")

    with pytest.raises(ValueError, match="expirado"):
        decode_token(token)


def test_jwt_invalid_token_format_or_signature():
    """Testa a decodificação de tokens com formato ou assinatura inválida."""
    with pytest.raises(ValueError, match="malformado"):
        decode_token("token_invalido_sem_pontos")

    with pytest.raises(ValueError, match="Assinatura"):
        decode_token("header.payload.assinatura_falsa")


def test_jwt_invalid_payload_json():
    """Testa o tratamento de exceção em tokens com payload corrompido/não-JSON."""
    import hmac, hashlib
    from src.core.config import settings

    header_b64 = _base64url_encode(b'{"alg":"HS256","typ":"JWT"}')
    invalid_payload_b64 = _base64url_encode(b"not_a_json_string")
    signing_input = f"{header_b64}.{invalid_payload_b64}".encode()
    signature = hmac.new(settings.SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    bad_token = f"{header_b64}.{invalid_payload_b64}.{sig_b64}"

    with pytest.raises(ValueError, match="Payload inválido"):
        decode_token(bad_token)


def test_extract_client_ip_trusted_and_untrusted():
    """Testa a extração de IP garantindo que apenas proxies confiáveis tenham cabeçalhos aceitos (TASK-QA-03)."""
    from starlette.requests import Request
    from src.api.routes import _extract_client_ip

    def build_req(client_host, headers=None):
        raw_headers = []
        for k, v in (headers or {}).items():
            raw_headers.append((k.lower().encode("latin-1"), v.encode("latin-1")))
        scope = {
            "type": "http",
            "client": (client_host, 12345) if client_host is not None else None,
            "headers": raw_headers,
        }
        return Request(scope)

    # 1. Host não confiável tenta forjar X-Forwarded-For e X-Real-IP -> cabeçalhos devem ser ignorados
    untrusted_req = build_req(
        "198.51.100.2", {"X-Forwarded-For": "203.0.113.1", "X-Real-IP": "203.0.113.2"}
    )
    assert _extract_client_ip(untrusted_req) == "198.51.100.2"

    # 2. Proxy confiável (127.0.0.1) com X-Forwarded-For contendo múltiplos IPs -> extrai o primeiro
    trusted_req_xff = build_req("127.0.0.1", {"X-Forwarded-For": "203.0.113.195, 10.0.0.1"})
    assert _extract_client_ip(trusted_req_xff) == "203.0.113.195"

    # 3. Proxy confiável (testserver) com X-Real-IP -> extrai X-Real-IP
    trusted_req_real_ip = build_req("testserver", {"X-Real-IP": "198.51.100.77"})
    assert _extract_client_ip(trusted_req_real_ip) == "198.51.100.77"

    # 4. Proxy confiável sem nenhum cabeçalho de proxy -> retorna o próprio host
    trusted_req_direct = build_req("localhost")
    assert _extract_client_ip(trusted_req_direct) == "localhost"

    # 5. Request sem client -> fallback seguro para 127.0.0.1
    no_client_req = build_req(None)
    assert _extract_client_ip(no_client_req) == "127.0.0.1"

    # 6. Proxy confiável Docker bridge (172.20.0.3) com X-Real-IP -> extrai X-Real-IP
    docker_req_real_ip = build_req("172.20.0.3", {"X-Real-IP": "203.0.113.50"})
    assert _extract_client_ip(docker_req_real_ip) == "203.0.113.50"

    # 7. Proxy confiável (172.20.0.3) com X-Forwarded-For contendo prefixo forjado -> extrai o IP real do cliente (à direita)
    docker_req_spoofed = build_req("172.20.0.3", {"X-Forwarded-For": "10.99.0.1, 1.2.3.4"})
    assert _extract_client_ip(docker_req_spoofed) == "1.2.3.4"

    # 8. Proxy confiável onde todos os IPs em X-Forwarded-For são privados -> retorna o IP original interno (primeiro)
    internal_chain_req = build_req("172.20.0.3", {"X-Forwarded-For": "10.0.0.1, 10.0.0.2"})
    assert _extract_client_ip(internal_chain_req) == "10.0.0.1"

    # 9. Proxy confiável com X-Real-IP contendo apenas espaços -> cai para X-Forwarded-For ou host
    empty_real_ip_req = build_req(
        "127.0.0.1", {"X-Real-IP": "   ", "X-Forwarded-For": "203.0.113.77"}
    )
    assert _extract_client_ip(empty_real_ip_req) == "203.0.113.77"

    # 10. Proxy confiável com X-Forwarded-For contendo apenas espaços -> cai para client_host
    empty_xff_req = build_req("127.0.0.1", {"X-Forwarded-For": "   "})
    assert _extract_client_ip(empty_xff_req) == "127.0.0.1"

    # 11. Host não resolvível / inválido -> não é proxy confiável e não dispara exceção
    invalid_host_req = build_req("invalid_hostname_format", {"X-Real-IP": "1.2.3.4"})
    assert _extract_client_ip(invalid_host_req) == "invalid_hostname_format"

    # 12. Validação direta do helper _is_trusted_proxy
    from src.api.routes import _is_trusted_proxy

    assert _is_trusted_proxy("") is False
    assert _is_trusted_proxy(None) is False
    assert _is_trusted_proxy("127.0.0.1") is True
    assert _is_trusted_proxy("::1") is True
    assert _is_trusted_proxy("localhost") is True
    assert _is_trusted_proxy("testserver") is True
    assert _is_trusted_proxy("172.20.0.5") is True
    assert _is_trusted_proxy("10.10.10.10") is True
    assert _is_trusted_proxy("192.168.1.1") is True
    assert _is_trusted_proxy("203.0.113.1") is False
    assert _is_trusted_proxy("not-an-ip") is False


def test_login_rate_limiting_blocks_spoofed_x_forwarded_for(db_session):
    """Testa que atacante com host não confiável não consegue burlar rate limit rotacionando X-Forwarded-For (CRIT-02)."""
    from starlette.testclient import TestClient
    from src.main import app
    from src.core.database import get_db

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        untrusted_client = TestClient(app, client=("198.51.100.99", 54321))

        # Executa 10 tentativas falhas com cabeçalhos X-Forwarded-For diferentes
        for i in range(10):
            resp = untrusted_client.post(
                "/api/v1/auth/login",
                json={"email": f"attacker_{i}@example.com", "password": "wrongpassword"},
                headers={"X-Forwarded-For": f"10.200.0.{i}"},
            )
            assert resp.status_code == 401

        # A 11ª tentativa originada do mesmo host não confiável deve ser bloqueada com 429
        blocked_resp = untrusted_client.post(
            "/api/v1/auth/login",
            json={"email": "attacker_final@example.com", "password": "wrongpassword"},
            headers={"X-Forwarded-For": "10.200.0.99"},
        )
        assert blocked_resp.status_code == 429
        assert "bloqueado" in blocked_resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_login_rate_limiting_blocks_spoofed_x_forwarded_for_through_trusted_proxy(db_session):
    """Testa que atacante enviando requisições através de proxy confiável não burla rate limit com prefixo XFF rotacionado."""
    from starlette.testclient import TestClient
    from src.main import app
    from src.core.database import get_db

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        # Simula requisições passando por proxy Docker confiável (172.20.0.2)
        trusted_proxy_client = TestClient(app, client=("172.20.0.2", 50000))

        # Atacante conecta com IP real 198.51.100.99 e tenta forjar prefixos X-Forwarded-For diferentes
        for i in range(10):
            resp = trusted_proxy_client.post(
                "/api/v1/auth/login",
                json={"email": f"attacker_{i}@example.com", "password": "wrongpassword"},
                headers={"X-Forwarded-For": f"10.99.0.{i}, 198.51.100.99"},
            )
            assert resp.status_code == 401

        # A 11ª tentativa deve ser bloqueada com 429
        blocked_resp = trusted_proxy_client.post(
            "/api/v1/auth/login",
            json={"email": "attacker_final@example.com", "password": "wrongpassword"},
            headers={"X-Forwarded-For": "10.99.0.99, 198.51.100.99"},
        )
        assert blocked_resp.status_code == 429
        assert "bloqueado" in blocked_resp.json()["detail"].lower()

        # Usuário legítimo de outro IP através do mesmo proxy NÃO deve ser bloqueado (evita DoS global)
        legit_resp = trusted_proxy_client.post(
            "/api/v1/auth/login",
            json={"email": "legit@example.com", "password": "anypassword"},
            headers={"X-Forwarded-For": "203.0.113.5"},
        )
        assert legit_resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_windows_product_key_encryption_decryption_and_masking():
    """Testa encriptação Fernet, decriptação fiel e mascaramento de chaves Windows."""
    raw_key = "VK9X2-N8Y4R-W3M2T-K7P1Q-L9Z0A"

    # Encriptação e decriptação válidas
    encrypted = encrypt_windows_product_key(raw_key)
    assert encrypted is not None
    assert encrypted != raw_key
    assert len(encrypted) > 20

    decrypted = decrypt_windows_product_key(encrypted)
    assert decrypted == raw_key

    # Mascaramento
    assert mask_windows_product_key(encrypted) == "••••••••••••••••"
    assert mask_windows_product_key(raw_key) == "••••••••••••••••"
    assert mask_windows_product_key(None) is None
    assert mask_windows_product_key("") is None
    assert mask_windows_product_key("   ") is None

    # Entradas vazias na encriptação e decriptação
    assert encrypt_windows_product_key(None) is None
    assert encrypt_windows_product_key("") is None
    assert encrypt_windows_product_key("   ") is None

    assert decrypt_windows_product_key(None) is None
    assert decrypt_windows_product_key("") is None
    assert decrypt_windows_product_key("   ") is None
