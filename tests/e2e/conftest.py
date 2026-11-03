"""Fixtures e utilitários compartilhados para os testes E2E no modelo canônico SisPatrimonio."""

import csv
import io
from decimal import Decimal
from typing import Any, List

import openpyxl
import pytest
from sqlalchemy.orm import Session

from src.core.security import _revoked_tokens, create_access_token, create_refresh_token, hash_password
from src.domain.models import Category, Location, User
from src.use_cases.authenticate_user import reset_rate_limits


@pytest.fixture(autouse=True)
def clean_rate_limits():
    """Limpa contadores de rate limiting e tokens revogados antes e depois de cada teste E2E."""
    reset_rate_limits()
    _revoked_tokens.clear()
    yield
    reset_rate_limits()
    _revoked_tokens.clear()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def e2e_users(db_session: Session):
    """Cria usuários padrão para testes E2E: administrador, técnico, colaborador e inativo."""
    password = "Password123!"
    hashed = hash_password(password)

    administrador = User(
        name="Admin E2E",
        email="admin_e2e@empresa.com",
        password_hash=hashed,
        role="administrador",
        is_active=True,
    )
    tecnico = User(
        name="Tecnico E2E",
        email="tecnico_e2e@empresa.com",
        password_hash=hashed,
        role="tecnico",
        is_active=True,
    )
    colaborador = User(
        name="Colaborador E2E",
        email="colaborador_e2e@empresa.com",
        password_hash=hashed,
        role="colaborador",
        is_active=True,
    )
    inativo = User(
        name="Inativo E2E",
        email="inativo_e2e@empresa.com",
        password_hash=hashed,
        role="tecnico",
        is_active=False,
    )

    default_category = Category(
        name="Notebook Padrao",
        useful_life_months=36,
        residual_value_rate=Decimal("10.00"),
        requires_serial_number=False,
    )
    default_location = Location(
        building="Sede",
        floor="1",
        sector="TI",
        room_number="101",
    )

    db_session.add_all(
        [administrador, tecnico, colaborador, inativo, default_category, default_location]
    )
    db_session.flush()
    for obj in [administrador, tecnico, colaborador, inativo, default_category, default_location]:
        db_session.refresh(obj)

    return {
        "administrador": administrador,
        "tecnico": tecnico,
        "colaborador": colaborador,
        "inativo": inativo,
        "raw_password": password,
        "default_category": default_category,
        "default_location": default_location,
    }


@pytest.fixture
def admin_tokens(e2e_users):
    """Gera tokens de acesso e refresh válidos para o usuário administrador."""
    user = e2e_users["administrador"]
    access = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id)})
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": user,
        "category_id": e2e_users["default_category"].id,
        "location_id": e2e_users["default_location"].id,
    }


@pytest.fixture
def tecnico_tokens(e2e_users):
    """Gera tokens de acesso e refresh válidos para o usuário técnico."""
    user = e2e_users["tecnico"]
    access = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id)})
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": user,
        "category_id": e2e_users["default_category"].id,
        "location_id": e2e_users["default_location"].id,
    }


@pytest.fixture
def colaborador_tokens(e2e_users):
    """Gera tokens de acesso e refresh válidos para o usuário colaborador."""
    user = e2e_users["colaborador"]
    access = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id)})
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": user,
        "category_id": e2e_users["default_category"].id,
        "location_id": e2e_users["default_location"].id,
    }


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
