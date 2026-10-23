"""Allow colaborador role and add optimistic lock version_id to equipments

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-10-15 13:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ajuste da constraint de role de usuários para permitir colaborador (ISSUE-002)
    op.drop_constraint("chk_users_role_tecnico", "users", type_="check")
    op.create_check_constraint("chk_users_role_valid", "users", "role IN ('tecnico', 'colaborador')")

    # 2. Adicionar version_id para controle de lock otimista em equipments (ISSUE-011)
    op.add_column(
        "equipments",
        sa.Column("version_id", sa.Integer(), server_default="1", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("equipments", "version_id")
    op.drop_constraint("chk_users_role_valid", "users", type_="check")
    op.create_check_constraint("chk_users_role_tecnico", "users", "role = 'tecnico'")
