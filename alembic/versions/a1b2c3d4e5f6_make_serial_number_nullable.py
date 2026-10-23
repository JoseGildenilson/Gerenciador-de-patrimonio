"""Make serial_number nullable on equipments table

Revision ID: a1b2c3d4e5f6
Revises: 97cfe449ece9
Create Date: 2026-08-23 18:35:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '97cfe449ece9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('equipments') as batch_op:
        batch_op.alter_column('serial_number',
                              existing_type=sa.String(length=255),
                              nullable=True)


def downgrade() -> None:
    # equipments may already be dropped by the b2c3d4e5f6a7 downgrade
    if 'equipments' not in sa.inspect(op.get_bind()).get_table_names():
        return
    with op.batch_alter_table('equipments') as batch_op:
        batch_op.alter_column('serial_number',
                              existing_type=sa.String(length=255),
                              nullable=False)
