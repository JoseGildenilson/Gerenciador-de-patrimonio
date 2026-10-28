"""Purge legacy database tables and columns outside DBML

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-28 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop dependent maintenance and movement tables
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    legacy_tables_ordered = [
        "equipment_maintenances",
        "equipment_movements",
        "equipments",
        "equipment_statuses",
        "maintenance_types",
        "sectors",
        "equipment_types",
        "login_attempts",
    ]

    for table_name in legacy_tables_ordered:
        if table_name in existing_tables:
            op.drop_table(table_name)

    # 2. Drop obsolete hashed_password column on users table if it exists
    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "hashed_password" in user_columns:
        op.drop_column("users", "hashed_password")


def downgrade() -> None:
    # Recreate obsolete hashed_password column
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "hashed_password" not in user_columns:
        op.add_column("users", sa.Column("hashed_password", sa.String(length=255), nullable=True))

    # Recreate minimal legacy tables to allow reversible downgrade
    existing_tables = set(inspector.get_table_names())

    if "login_attempts" not in existing_tables:
        op.create_table(
            "login_attempts",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("email_attempted", sa.String(length=255), nullable=False),
            sa.Column("ip_address", sa.String(length=45), nullable=False),
            sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("success", sa.Boolean(), nullable=False, default=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if "equipment_types" not in existing_tables:
        op.create_table(
            "equipment_types",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )

    if "sectors" not in existing_tables:
        op.create_table(
            "sectors",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )

    if "equipment_statuses" not in existing_tables:
        op.create_table(
            "equipment_statuses",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )

    if "maintenance_types" not in existing_tables:
        op.create_table(
            "maintenance_types",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )
