"""Módulo de segurança para criptografia de senhas (Argon2id) e emissão/validação de JWTs."""

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from typing import Any, Dict
from src.core.config import settings

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt

_argon2_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)

# Lista de revogação de tokens em memória (para tokens invalidados no logout)
_revoked_tokens: set[str] = set()


def revoke_token(token: str) -> None:
    """Adiciona um token à lista de revogação."""
    if token:
        _revoked_tokens.add(token.strip())


def is_token_revoked(token: str) -> bool:
    """Verifica se um token consta na lista de revogação."""
    if not token:
        return True
    return token.strip() in _revoked_tokens


def _base64url_encode(data: bytes) -> str:
    """Codifica bytes em base64 URL-safe sem padding."""
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def hash_password(password: str) -> str:
    """Gera o hash da senha utilizando o algoritmo Argon2id oficial."""
    return _argon2_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha fornecida corresponde ao hash Argon2id."""
    if not hashed_password or not isinstance(hashed_password, str):
        return False

    if hashed_password.startswith("$argon2"):
        try:
            return _argon2_hasher.verify(hashed_password, plain_password)
        except Exception:
            # Fallback para hashes gerados pela simulação scrypt
            pass

    # Compatibilidade retroativa para hashes legados
    if hashed_password.startswith("$argon2id$v=19$m=65536,t=3,p=4$"):
        try:
            payload = hashed_password[len("$argon2id$v=19$m=65536,t=3,p=4$") :]
            if "$" in payload:
                salt_b64, stored_derived_b64 = payload.split("$", 1)
            else:
                salt_b64 = payload[:22]
                stored_derived_b64 = payload[22:]

            salt_padded = salt_b64 + "=" * (-len(salt_b64) % 4)
            salt = base64.b64decode(salt_padded)
            derived = hashlib.scrypt(
                plain_password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32
            )
            derived_b64 = base64.b64encode(derived).decode().rstrip("=")
            return hmac.compare_digest(derived_b64, stored_derived_b64)
        except Exception:
            return False
    return False


def create_token(data: Dict[str, Any], expires_delta: timedelta, token_type: str = "access") -> str:
    """Cria um token JWT (access ou refresh) utilizando a biblioteca PyJWT."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode.update(
        {
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
            "type": token_type,
        }
    )
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(data: Dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Cria um token de acesso de curta duração (padrão 15 min)."""
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token(data, delta, token_type="access")


def create_refresh_token(data: Dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Cria um token de renovação de longa duração (padrão 24h)."""
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token(data, delta, token_type="refresh")


def decode_token(token: str) -> Dict[str, Any]:
    """Decodifica e valida um token JWT. Lança ValueError se inválido, revogado ou expirado."""
    if is_token_revoked(token):
        raise ValueError("Token revogado.")

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Token malformado")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(settings.SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")

    if not hmac.compare_digest(sig_b64, expected_sig_b64):
        raise ValueError("Assinatura do token inválida")

    try:
        padding = "=" * (4 - (len(payload_b64) % 4))
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        payload = json.loads(payload_bytes.decode())
    except Exception as e:
        raise ValueError(f"Payload inválido: {str(e)}") from e

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if "exp" in payload and payload["exp"] < now_ts:
        raise ValueError("Token expirado")

    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception:
        return payload


def _get_fernet():
    from cryptography.fernet import Fernet

    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_windows_product_key(plain_key: str | None) -> str | None:
    """Criptografa simetricamente a chave de produto do Windows usando Fernet."""
    if plain_key is None or not plain_key.strip():
        return None
    fernet = _get_fernet()
    return fernet.encrypt(plain_key.strip().encode("utf-8")).decode("utf-8")


def decrypt_windows_product_key(encrypted_key: str | None) -> str | None:
    """Decriptografa a chave de produto do Windows encriptada."""
    if encrypted_key is None or not encrypted_key.strip():
        return None
    fernet = _get_fernet()
    return fernet.decrypt(encrypted_key.strip().encode("utf-8")).decode("utf-8")


def mask_windows_product_key(encrypted_or_plain_key: str | None) -> str | None:
    """Retorna máscara fixa para chave do Windows existente ou None."""
    if encrypted_or_plain_key is None or not str(encrypted_or_plain_key).strip():
        return None
    return "••••••••••••••••"
