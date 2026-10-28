"""Testes automatizados de validação independente das correções (ISSUE-001 a ISSUE-017)."""

import pytest
from datetime import datetime, timezone
from src.infrastructure.spreadsheet_exporter import (
    _sanitize_formula_value,
    generate_equipments_excel,
)
from src.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    revoke_token,
    is_token_revoked,
)
from src.core.config import Settings
from src.domain.models import User, Equipment, IPAddressType, MACAddressType
from src.domain.schemas import TagResponse, TagCreate, TagUpdate


def test_issue_005_csv_formula_injection_sanitization():
    """Valida se strings iniciadas por '=', '+', '-', '@' são prefixadas com aspas simples (CWE-1236)."""
    assert _sanitize_formula_value("=1+1") == "'=1+1"
    assert _sanitize_formula_value("+cmd|'/C calc'!A0") == "'+cmd|'/C calc'!A0"
    assert _sanitize_formula_value("-100") == "'-100"
    assert _sanitize_formula_value("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert _sanitize_formula_value("Dell Latitude 5420") == "Dell Latitude 5420"
    assert _sanitize_formula_value(None) == ""


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
    """Valida se a restrição de modelo aceita tanto 'tecnico' quanto 'colaborador'."""
    table_args = User.__table_args__
    check_constraints = [arg for arg in table_args if hasattr(arg, "sqltext")]
    assert len(check_constraints) >= 1
    constraint_sql = str(check_constraints[0].sqltext)
    assert "role IN ('administrador', 'tecnico', 'colaborador')" in constraint_sql


def test_issue_014_ip_and_mac_dialect_agnostic_types():
    """Valida se os TypeDecorators agnósticos para IP e MAC estão declarados."""
    from unittest.mock import MagicMock

    ip_type = IPAddressType()
    mac_type = MACAddressType()
    assert ip_type.process_bind_param("192.168.1.10", None) == "192.168.1.10"
    assert ip_type.process_bind_param(None, None) is None
    assert mac_type.process_bind_param("AA:BB:CC:DD:EE:FF", None) == "AA:BB:CC:DD:EE:FF"
    assert mac_type.process_bind_param(None, None) is None

    # Valida fallback de dialeto não-PostgreSQL (SQLite/genérico)
    mock_dialect = MagicMock()
    mock_dialect.name = "sqlite"
    mock_dialect.type_descriptor = lambda t: t
    assert ip_type.load_dialect_impl(mock_dialect) is not None
    assert mac_type.load_dialect_impl(mock_dialect) is not None


def test_issue_001_tag_schemas():
    """Valida se os schemas TagResponse, TagCreate e TagUpdate funcionam para contratos de tag."""
    t_create = TagCreate(category="tipo", name="Notebook")
    assert t_create.category == "tipo"
    assert t_create.name == "Notebook"

    t_resp = TagResponse(
        id=1, category="tipo", name="Notebook", created_at=datetime.now(timezone.utc)
    )
    assert t_resp.id == 1
    assert t_resp.name == "Notebook"
