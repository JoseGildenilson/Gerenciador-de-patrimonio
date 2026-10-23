"""Fixtures e utilitários compartilhados para os testes E2E."""

import csv
import io
from typing import Any, List

import openpyxl
import pytest
from sqlalchemy.orm import Session

from src.core.security import create_access_token, create_refresh_token, hash_password
from src.domain.models import User


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def e2e_users(db_session: Session):
    """Cria usuários padrão para testes E2E: técnico, colaborador e inativo."""
    password = "Password123!"
    hashed = hash_password(password)

    tecnico = User(
        email="tecnico_e2e@empresa.com",
        hashed_password=hashed,
        role="tecnico",
        is_active=True,
    )
    colaborador = User(
        id=998,
        email="colaborador_e2e@empresa.com",
        hashed_password=hashed,
        role="colaborador",
        is_active=True,
    )
    inativo = User(
        email="inativo_e2e@empresa.com",
        hashed_password=hashed,
        role="tecnico",
        is_active=False,
    )

    db_session.add_all([tecnico, inativo])
    db_session.flush()
    db_session.refresh(tecnico)
    db_session.refresh(inativo)

    return {
        "tecnico": tecnico,
        "colaborador": colaborador,
        "inativo": inativo,
        "raw_password": password,
    }


@pytest.fixture
def tecnico_tokens(e2e_users):
    """Gera tokens de acesso e refresh válidos para o usuário técnico."""
    user = e2e_users["tecnico"]
    access = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id)})
    return {"access_token": access, "refresh_token": refresh, "user": user}


@pytest.fixture
def colaborador_tokens(e2e_users):
    """Gera tokens de acesso e refresh válidos para o usuário colaborador."""
    from src.api.dependencies import get_current_user
    from src.main import app

    user = e2e_users["colaborador"]
    access = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id)})
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        yield {"access_token": access, "refresh_token": refresh, "user": user}
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def make_excel_bytes():
    """Helper factory para gerar binários .xlsx válidos em memória."""

    def _create(
        rows: List[List[Any]],
        headers: List[str] | None = None,
        sheet_name: str = "Patrimônio",
    ) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name
        if headers:
            ws.append(headers)
        for r in rows:
            ws.append(r)
        bio = io.BytesIO()
        wb.save(bio)
        return bio.getvalue()

    return _create


@pytest.fixture
def make_csv_bytes():
    """Helper factory para gerar arquivos CSV em memória com delimitador customizável."""

    def _create(
        rows: List[List[Any]],
        headers: List[str] | None = None,
        delimiter: str = ";",
        encoding: str = "utf-8",
    ) -> bytes:
        sio = io.StringIO()
        writer = csv.writer(sio, delimiter=delimiter)
        if headers:
            writer.writerow(headers)
        for r in rows:
            writer.writerow(r)
        return sio.getvalue().encode(encoding)

    return _create
