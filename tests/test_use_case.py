"""Testes unitários do caso de uso AuthenticateUserUseCase."""

import pytest
from sqlalchemy.orm import Session
from src.infrastructure.repositories import LoginAttemptRepository, UserRepository
from src.use_cases.authenticate_user import (
    AuthenticateUserUseCase,
    InvalidCredentialsException,
    RateLimitExceededException,
)


def test_authenticate_user_success(db_session: Session, create_test_user):
    """Testa o caso de uso com credenciais válidas."""
    user = create_test_user(
        email="tecnico_uc1@empresa.com", password="SenhaSegura123!", role="tecnico"
    )
    use_case = AuthenticateUserUseCase(db_session)

    result = use_case.execute(
        email="tecnico_uc1@empresa.com",
        password="SenhaSegura123!",
        ip_address="127.0.0.1",
    )

    assert "access_token" in result
    assert "refresh_token" in result
    assert result["user"].id == user.id
    assert result["user"].role == "tecnico"


def test_authenticate_user_invalid_password(db_session: Session, create_test_user):
    """Testa a rejeição com senha incorreta e registro de falha."""
    create_test_user(email="tecnico_uc2@empresa.com", password="SenhaSegura123!")
    use_case = AuthenticateUserUseCase(db_session)
    test_ip = "192.168.0.1"

    with pytest.raises(InvalidCredentialsException):
        use_case.execute(
            email="tecnico_uc2@empresa.com",
            password="SenhaIncorreta",
            ip_address=test_ip,
        )

    # Verifica registro da falha por IP
    attempt_repo = LoginAttemptRepository(db_session)
    assert attempt_repo.count_recent_failed_attempts(test_ip) == 1


def test_authenticate_user_nonexistent_email(db_session: Session):
    """Testa a rejeição com email não cadastrado e mensagem genérica."""
    use_case = AuthenticateUserUseCase(db_session)

    with pytest.raises(InvalidCredentialsException):
        use_case.execute(
            email="inexistente@empresa.com",
            password="SenhaQualquer!",
            ip_address="127.0.0.1",
        )


def test_authenticate_user_inactive_user(db_session: Session, create_test_user):
    """Testa a rejeição quando o usuário está inativo."""
    create_test_user(email="inativo@empresa.com", password="SenhaSegura123!", is_active=False)
    use_case = AuthenticateUserUseCase(db_session)

    with pytest.raises(InvalidCredentialsException):
        use_case.execute(
            email="inativo@empresa.com",
            password="SenhaSegura123!",
            ip_address="127.0.0.1",
        )


def test_authenticate_user_rate_limit_exceeded(db_session: Session):
    """Testa a bloqueio imediato (Rate Limit) na 11ª tentativa de login a partir do mesmo IP."""
    use_case = AuthenticateUserUseCase(db_session)
    test_ip = "10.0.0.50"

    # Simula 10 falhas consecutivas para o mesmo IP com emails distintos
    for i in range(10):
        with pytest.raises(InvalidCredentialsException):
            use_case.execute(
                email=f"errado_{i}@empresa.com",
                password="SenhaIncorreta",
                ip_address=test_ip,
            )

    # A 11ª tentativa a partir do mesmo IP deve ser bloqueada por Rate Limit
    with pytest.raises(RateLimitExceededException):
        use_case.execute(
            email="qualquer@empresa.com",
            password="SenhaQualquer",
            ip_address=test_ip,
        )


def test_authenticate_user_account_rate_limit_exceeded(db_session: Session):
    """Testa bloqueio por conta após 5 tentativas consecutivas para o mesmo email (ISSUE-007)."""
    use_case = AuthenticateUserUseCase(db_session)
    email_alvo = "alvo@empresa.com"

    # Simula 5 falhas consecutivas de IPs diferentes
    for i in range(5):
        with pytest.raises(InvalidCredentialsException):
            use_case.execute(
                email=email_alvo,
                password="SenhaIncorreta",
                ip_address=f"192.168.1.{i + 10}",
            )

    # A 6ª tentativa para o mesmo email deve ser bloqueada
    with pytest.raises(RateLimitExceededException):
        use_case.execute(
            email=email_alvo,
            password="SenhaIncorreta",
            ip_address="192.168.1.99",
        )
