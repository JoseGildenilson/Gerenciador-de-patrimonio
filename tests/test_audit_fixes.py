"""Testes automatizados de validação independente das correções de segurança e integridade."""

import pytest
from src.infrastructure.spreadsheet_exporter import _sanitize_formula
from src.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    revoke_token,
    is_token_revoked,
)
from src.core.config import Settings
from src.domain.models import User


def test_issue_005_csv_formula_injection_sanitization():
    """Valida se strings iniciadas por '=', '+', '-', '@' são prefixadas com aspas simples (CWE-1236)."""
    assert _sanitize_formula("=1+1") == "'=1+1"
    assert _sanitize_formula("+cmd|'/C calc'!A0") == "'+cmd|'/C calc'!A0"
    assert _sanitize_formula("-100") == "'-100"
    assert _sanitize_formula("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert _sanitize_formula("Dell Latitude 5420") == "Dell Latitude 5420"
    assert _sanitize_formula(None) is None


def test_issue_008_argon2_hashing_and_verification():
    """Valida se a biblioteca oficial argon2-cffi está ativa e validando senhas."""
    pwd = "MinhaSenhaForte@2026!"
    hashed = hash_password(pwd)
    assert hashed.startswith("$argon2id$")
    assert verify_password(pwd, hashed) is True
    assert verify_password("SenhaIncorreta", hashed) is False
    assert verify_password("", hashed) is False


def test_issue_008_issue_010_jwt_and_revocation():
    """Valida criação de JWT via PyJWT e invalidação de tokens revogados no logout."""
    payload = {"sub": "user@empresa.com", "role": "tecnico", "user_id": 1}
    token = create_access_token(payload)
    assert isinstance(token, str)
    assert not is_token_revoked(token)

    decoded = decode_token(token)
    assert decoded["sub"] == "user@empresa.com"
    assert decoded["role"] == "tecnico"

    # Revogação
    revoke_token(token)
    assert is_token_revoked(token)
    with pytest.raises(ValueError, match="Token revogado"):
        decode_token(token)


def test_issue_009_production_secret_key_enforcement():
    """Valida se a aplicação recusa iniciar em produção sem SECRET_KEY configurada."""
    with pytest.raises(
        RuntimeError, match="A variável de ambiente SECRET_KEY deve ser configurada"
    ):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="super-secret-key-change-in-production-1234567890",
        )

    # Com chave personalizada em produção, deve inicializar normalmente
    valid_prod = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="chave-de-producao-verdadeiramente-segura-e-longa-32-chars",
    )
    assert valid_prod.ENVIRONMENT == "production"


def test_issue_002_user_model_role_constraint_declaration():
    """Valida se a restrição de modelo aceita os papéis do DBML."""
    table_args = User.__table_args__
    check_constraints = [arg for arg in table_args if hasattr(arg, "sqltext")]
    assert len(check_constraints) >= 1
    constraint_sql = str(check_constraints[0].sqltext)
    assert "role IN ('administrador', 'tecnico', 'colaborador')" in constraint_sql
