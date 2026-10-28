"""Testes para utilitários de banco de dados e repositórios."""

from sqlalchemy.orm import Session
from src.core.database import get_db
from src.infrastructure.repositories import UserRepository
from src.domain.models import User


def test_get_db_generator():
    """Testa a injeção de dependência get_db."""
    db_gen = get_db()
    db = next(db_gen)
    assert isinstance(db, Session)
    try:
        next(db_gen)
    except StopIteration:
        pass


def test_user_repository_create_get_soft_delete_and_restore(db_session: Session):
    """Testa o repositório UserRepository (create, get_by_id, soft_delete e restore)."""
    repo = UserRepository(db_session)
    new_user = User(email="new_repo_user@empresa.com", password_hash="hash", role="tecnico")

    created = repo.create(new_user)
    db_session.flush()
    assert created.id is not None

    found = repo.get_by_id(created.id)
    assert found is not None
    assert found.email == "new_repo_user@empresa.com"

    # Soft delete
    repo.soft_delete(found)
    db_session.flush()

    assert repo.get_by_id(created.id) is None
    assert repo.get_by_id(created.id, include_deleted=True) is not None

    # Restore
    repo.restore(found)
    db_session.flush()
    assert repo.get_by_id(created.id) is not None

    not_found = repo.get_by_id(999999)
    assert not_found is None
