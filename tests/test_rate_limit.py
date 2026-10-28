"""Testes de rate limiting e auditoria em memória."""

from datetime import datetime, timedelta, timezone
from src.use_cases.authenticate_user import (
    _cleanup_and_count_attempts,
    _record_failed_attempt,
    _record_success,
)


def test_in_memory_rate_limit_cleanup_and_count():
    """Valida se o controle de taxa em memória filtra tentativas fora da janela."""
    attempts = {}
    ip = "192.168.1.50"

    assert _cleanup_and_count_attempts(attempts, ip, window_minutes=15) == 0

    # 3 falhas recentes
    for _ in range(3):
        _record_failed_attempt(attempts, ip)

    assert _cleanup_and_count_attempts(attempts, ip, window_minutes=15) == 3

    # Tentativa antiga (20 minutos atrás)
    attempts[ip].append(datetime.now(timezone.utc) - timedelta(minutes=20))
    # Deve limpar a tentativa antiga
    assert _cleanup_and_count_attempts(attempts, ip, window_minutes=15) == 3

    # Sucesso limpa o registro
    _record_success(ip, "user@empresa.com", ip_map=attempts)
    assert _cleanup_and_count_attempts(attempts, ip, window_minutes=15) == 0
