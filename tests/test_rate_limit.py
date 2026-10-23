"""Testes de integração do repositório de tentativas de login (Rate Limit e Auditoria)."""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from src.domain.models import LoginAttempt
from src.infrastructure.repositories import LoginAttemptRepository


def test_login_attempt_repository_counts(db_session: Session):
    """Testa a contagem de tentativas malsucedidas recentes por IP e gravação de email_attempted."""
    repo = LoginAttemptRepository(db_session)
    test_ip = "192.168.1.100"
    test_email = "tecnico@empresa.com"

    # Inicialmente 0 falhas
    assert repo.count_recent_failed_attempts(test_ip, window_minutes=15) == 0

    # Adiciona 5 falhas recentes
    for _ in range(5):
        repo.record_attempt(ip_address=test_ip, email_attempted=test_email, success=False)
    db_session.flush()

    assert repo.count_recent_failed_attempts(test_ip, window_minutes=15) == 5

    # Adiciona 1 tentativa de sucesso
    attempt = repo.record_attempt(ip_address=test_ip, email_attempted=test_email, success=True)
    db_session.flush()

    assert attempt.email_attempted == test_email
    assert str(attempt.ip_address) == test_ip
    assert attempt.success is True

    # Tentativa de sucesso não aumenta contagem de falhas
    assert repo.count_recent_failed_attempts(test_ip, window_minutes=15) == 5


def test_login_attempt_repository_ignores_old_attempts(db_session: Session):
    """Testa se o repositório ignora tentativas mais antigas que a janela de tempo (15 min)."""
    repo = LoginAttemptRepository(db_session)
    test_ip = "10.0.0.1"

    # Tentativa antiga (20 minutos atrás)
    old_attempt = LoginAttempt(
        ip_address=test_ip,
        email_attempted="admin@empresa.com",
        success=False,
        attempted_at=datetime.now(timezone.utc) - timedelta(minutes=20),
    )
    db_session.add(old_attempt)
    db_session.flush()

    # Deve ignorar a tentativa de 20 minutos atrás
    assert repo.count_recent_failed_attempts(test_ip, window_minutes=15) == 0
