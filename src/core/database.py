"""Configuração da engine do SQLAlchemy 2.0 e gerenciamento de sessões."""

import time
from typing import Any, Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from src.core.config import settings

SENSITIVE_FIELD_NAMES = ("password", "hash", "token", "secret", "key")


def sanitize_sql_params(parameters: Any) -> Any:
    """Higieniza parâmetros SQL sensíveis substituindo por [REDACTED]."""
    if not parameters:
        return parameters
    if isinstance(parameters, dict):
        sanitized = {}
        for k, v in parameters.items():
            if any(s in str(k).lower() for s in SENSITIVE_FIELD_NAMES):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = v
        return sanitized
    if isinstance(parameters, (list, tuple)):
        if parameters and isinstance(parameters[0], dict):
            return [sanitize_sql_params(p) for p in parameters]
        return parameters
    return parameters


def extract_and_sanitize_params(context: Any, raw_parameters: Any) -> Any:
    """Extrai parâmetros compilados ou brutos e aplica higienização."""
    compiled = getattr(context, "compiled_parameters", None)
    if not compiled and hasattr(context, "execution_context"):
        compiled = getattr(context.execution_context, "compiled_parameters", None)

    if compiled and isinstance(compiled, list):
        if len(compiled) == 1 and isinstance(compiled[0], dict):
            return sanitize_sql_params(compiled[0])
        return [sanitize_sql_params(p) for p in compiled]

    return sanitize_sql_params(raw_parameters)


_OP_BADGES = {
    "INSERT": ("\033[1;32m🟢 [SQL QUERY] [INSERT]\033[0m", "\033[32m"),
    "SELECT": ("\033[1;36m🔵 [SQL QUERY] [SELECT]\033[0m", "\033[36m"),
    "UPDATE": ("\033[1;33m🟡 [SQL QUERY] [UPDATE]\033[0m", "\033[33m"),
    "DELETE": ("\033[1;31m🔴 [SQL QUERY] [DELETE]\033[0m", "\033[31m"),
}


def register_sql_logging_listeners(target_engine: Any) -> None:
    """Registra listeners de SQL para observabilidade e logs visuais de queries no terminal."""

    @event.listens_for(target_engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if context is not None:
            context._query_start_time = time.perf_counter()

    @event.listens_for(target_engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if not getattr(settings, "LOG_SQL_STATEMENTS", False):
            return

        clean_stmt = statement.strip().rstrip(";")
        if clean_stmt.upper() == "SELECT 1":
            return

        start_time = getattr(context, "_query_start_time", None) if context else None
        duration_ms = (time.perf_counter() - start_time) * 1000 if start_time else 0.0
        sanitized = extract_and_sanitize_params(context, parameters)

        op = (clean_stmt.split() + ["QUERY"])[0].upper()
        badge, stmt_color = _OP_BADGES.get(
            op, (f"\033[1;35m🟣 [SQL QUERY] [{op}]\033[0m", "\033[35m")
        )

        header = f"\033[90m┌──\033[0m {badge} \033[1;33m⏱️ {duration_ms:.2f}ms\033[0m \033[90m──────────────────────────────────────────\033[0m"
        body = f"\033[90m│\033[0m \033[1mSQL:\033[0m {stmt_color}{clean_stmt}\033[0m"
        if sanitized:
            body += f"\n\033[90m│\033[0m \033[1m📦 PARAMS:\033[0m {sanitized}"
        footer = "\033[90m└─────────────────────────────────────────────────────────────\033[0m"

        print(f"{header}\n{body}\n{footer}", flush=True)


@compiles(CheckConstraint, "sqlite")
def _compile_check_constraint_sqlite(element, compiler, **kw):  # pragma: no cover
    sqltext = str(element.sqltext)
    if "interval" in sqltext or "family(" in sqltext:
        return None
    return compiler.visit_check_constraint(element, **kw)


# Garante suporte a SQLite (connect_args) e PostgreSQL
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):  # pragma: no cover
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    future=True,
)
register_sql_logging_listeners(engine)

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
