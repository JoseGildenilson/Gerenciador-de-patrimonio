"""Configuração da engine do SQLAlchemy 2.0 e gerenciamento de sessões."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from src.core.config import settings

# Garante suporte a SQLite (connect_args) e PostgreSQL
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):  # pragma: no cover
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """Classe base declarativa para os modelos ORM SQLAlchemy."""

    pass


def get_db() -> Generator[Session, None, None]:
    """Injeção de dependência da sessão de banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
