"""Dependências HTTP do FastAPI para autenticação e autorização."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.security import decode_token
from src.domain.models import User
from src.infrastructure.repositories import UserRepository


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Extrai e valida o token de acesso (a partir de Cookie HttpOnly ou header Authorization)."""
    token = request.cookies.get("access_token")

    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso ausente.",
        )

    try:
        payload = decode_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido ou expirado: {str(e)}",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido para autorização.",
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Payload de token inválido.",
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ID de usuário inválido no token.",
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo ou não encontrado.",
        )

    return user


def require_tecnico_role(current_user: User = Depends(get_current_user)) -> User:
    """Valida se o usuário autenticado possui a role 'tecnico' (RN-EQ-10)."""
    if current_user.role != "tecnico":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito exclusivamente a usuários com perfil técnico.",
        )
    return current_user


def require_tecnico_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Valida se o usuário autenticado possui a role 'tecnico' ou 'administrador'."""
    if current_user.role not in ("tecnico", "administrador"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito exclusivamente a usuários com perfil técnico ou administrador.",
        )
    return current_user
