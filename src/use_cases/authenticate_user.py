"""Caso de uso para autenticação de usuário com controle de rate limit e auditoria em memória."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import threading
from sqlalchemy.orm import Session
from src.core.security import verify_password, create_access_token, create_refresh_token
from src.domain.models import User
from src.infrastructure.repositories import UserRepository

_rate_limit_lock = threading.Lock()
_failed_ip_attempts: dict[str, list[datetime]] = {}
_failed_email_attempts: dict[str, list[datetime]] = {}


def _cleanup_and_count_attempts(
    attempts_map: dict[str, list[datetime]], key: str, window_minutes: int = 15
) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    if key not in attempts_map:
        return 0
    # Mantém apenas tentativas dentro da janela
    valid_attempts = [ts for ts in attempts_map[key] if ts >= cutoff]
    attempts_map[key] = valid_attempts
    return len(valid_attempts)


def _record_failed_attempt(attempts_map: dict[str, list[datetime]], key: str) -> None:
    now = datetime.now(timezone.utc)
    if key not in attempts_map:
        attempts_map[key] = []
    attempts_map[key].append(now)


def _record_success(
    ip: str,
    email: str,
    ip_map: dict[str, list[datetime]] | None = None,
    email_map: dict[str, list[datetime]] | None = None,
) -> None:
    target_ip_map = _failed_ip_attempts if ip_map is None else ip_map
    target_email_map = _failed_email_attempts if email_map is None else email_map
    if ip in target_ip_map:
        target_ip_map[ip] = []
    normalized_email = email.strip().lower()
    if normalized_email in target_email_map:
        target_email_map[normalized_email] = []


def reset_rate_limits() -> None:
    """Limpa todas as tentativas registradas em memória (usado para isolamento entre testes)."""
    with _rate_limit_lock:
        _failed_ip_attempts.clear()
        _failed_email_attempts.clear()


class RateLimitExceededException(Exception):
    """Exceção lançada quando o limite de tentativas de login é excedido por IP ou conta (HTTP 429)."""

    def __init__(
        self,
        message: str = "Acesso temporariamente bloqueado por motivos de segurança devido ao excesso de tentativas malsucedidas.",
    ):
        self.message = message
        super().__init__(self.message)


class InvalidCredentialsException(Exception):
    """Exceção genérica lançada quando as credenciais fornecidas são inválidas (HTTP 401)."""

    def __init__(self, message: str = "Credenciais de acesso inválidas."):
        self.message = message
        super().__init__(self.message)


class AuthenticateUserUseCase:
    """Caso de uso de autenticação de usuário com controle de taxa e hash seguro de senha."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def execute(self, email: str, password: str, ip_address: str) -> Dict[str, Any]:
        """Executa validação, rate limiting e autenticação no login."""
        normalized_email = email.strip().lower()

        with _rate_limit_lock:
            # 1. Verifica taxa de tentativas malsucedidas por IP e por conta
            failed_ip_count = _cleanup_and_count_attempts(
                _failed_ip_attempts, ip_address, window_minutes=15
            )
            if failed_ip_count >= 10:
                raise RateLimitExceededException()

            failed_email_count = _cleanup_and_count_attempts(
                _failed_email_attempts, normalized_email, window_minutes=15
            )
            if failed_email_count >= 5:
                raise RateLimitExceededException(
                    "Acesso temporariamente bloqueado por motivos de segurança devido ao excesso de tentativas malsucedidas."
                )

        # 2. Busca usuário por email (case-insensitive e deleted_at IS NULL)
        user = self.user_repo.get_by_email(email)

        # 3. Valida credenciais (existência do usuário, ativo, não deletado e senha correta)
        is_valid = (
            user is not None
            and user.is_active
            and user.deleted_at is None
            and verify_password(password, user.password_hash)
        )

        if not is_valid:
            with _rate_limit_lock:
                _record_failed_attempt(_failed_ip_attempts, ip_address)
                _record_failed_attempt(_failed_email_attempts, normalized_email)
            raise InvalidCredentialsException()

        with _rate_limit_lock:
            _record_success(ip_address, email)

        # 4. Gera tokens JWT
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user,
        }
