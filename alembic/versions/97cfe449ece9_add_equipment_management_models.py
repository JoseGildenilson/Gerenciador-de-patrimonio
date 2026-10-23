"""Add equipment management models

Revision ID: 97cfe449ece9
Revises: '53b2fa2ee904'
Create Date: 2026-08-13 15:56:07.355743
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97cfe449ece9'
down_revision: Union[str, None] = '53b2fa2ee904'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Atualizações na tabela equipments
    op.add_column('equipments', sa.Column('serial_number', sa.String(length=255), nullable=False))
    op.add_column('equipments', sa.Column('patrimony_number', sa.String(length=255), nullable=True))
    op.add_column('equipments', sa.Column('hostname', sa.String(length=255), nullable=True))
    op.add_column('equipments', sa.Column('brand', sa.String(length=255), nullable=True))
    op.add_column('equipments', sa.Column('product_number', sa.String(length=255), nullable=True))
    op.add_column('equipments', sa.Column('equipment_type', sa.String(length=100), nullable=False))
    op.add_column('equipments', sa.Column('location', sa.String(length=100), nullable=False))
    op.add_column('equipments', sa.Column('windows_key', sa.String(length=255), nullable=True))
    op.add_column('equipments', sa.Column('last_maintenance_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('equipments', sa.Column('notes', sa.Text(), nullable=True))
    op.alter_column('equipments', 'description', existing_type=sa.TEXT(), nullable=False)
    op.alter_column('equipments', 'status', existing_type=sa.VARCHAR(length=50), type_=sa.String(length=100), existing_nullable=False)
    
    op.create_index(op.f('ix_equipments_equipment_type'), 'equipments', ['equipment_type'], unique=False)
    op.create_index(op.f('ix_equipments_hostname'), 'equipments', ['hostname'], unique=True)
    op.create_index(op.f('ix_equipments_location'), 'equipments', ['location'], unique=False)
    op.create_index(op.f('ix_equipments_patrimony_number'), 'equipments', ['patrimony_number'], unique=True)
    op.create_index(op.f('ix_equipments_serial_number'), 'equipments', ['serial_number'], unique=True)
    op.create_index(op.f('ix_equipments_status'), 'equipments', ['status'], unique=False)
    if op.get_bind().dialect.name != 'sqlite':
        op.drop_column('equipments', 'name')

    # 2. Tabela equipment_tags
    op.create_table(
        'equipment_tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category', 'name', name='uq_equipment_tag_category_name')
    )
    op.create_index(op.f('ix_equipment_tags_category'), 'equipment_tags', ['category'], unique=False)

    # 3. Tabela equipment_movements
    op.create_table(
        'equipment_movements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=False),
        sa.Column('origin_location', sa.String(length=100), nullable=False),
        sa.Column('destination_location', sa.String(length=100), nullable=False),
        sa.Column('movement_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_equipment_movements_equipment_id'), 'equipment_movements', ['equipment_id'], unique=False)

    # 4. Tabela equipment_maintenances
    op.create_table(
        'equipment_maintenances',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=False),
        sa.Column('maintenance_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('maintenance_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_equipment_maintenances_equipment_id'), 'equipment_maintenances', ['equipment_id'], unique=False)


def downgrade() -> None:
    # equipments may already be dropped by the b2c3d4e5f6a7 downgrade
    if 'equipments' not in sa.inspect(op.get_bind()).get_table_names():
        return
    op.drop_index(op.f('ix_equipment_maintenances_equipment_id'), table_name='equipment_maintenances')
    op.drop_table('equipment_maintenances')
    op.drop_index(op.f('ix_equipment_movements_equipment_id'), table_name='equipment_movements')
    op.drop_table('equipment_movements')
    op.drop_index(op.f('ix_equipment_tags_category'), table_name='equipment_tags')
    op.drop_table('equipment_tags')

    op.drop_index(op.f('ix_equipment_status'), table_name='equipments')
    op.drop_index(op.f('ix_equipment_serial_number'), table_name='equipments')
    op.drop_index(op.f('ix_equipment_patrimony_number'), table_name='equipments')
    op.drop_index(op.f('ix_equipment_location'), table_name='equipments')
    op.drop_index(op.f('ix_equipment_hostname'), table_name='equipments')
    op.drop_index(op.f('ix_equipment_equipment_type'), table_name='equipments')
    op.alter_column('equipments', 'status', existing_type=sa.String(length=100), type_=sa.VARCHAR(length=50), existing_nullable=False)
    op.alter_column('equipments', 'description', existing_type=sa.TEXT(), nullable=True)
    op.drop_column('equipments', 'notes')
    op.drop_column('equipments', 'last_maintenance_at')
    op.drop_column('equipments', 'windows_key')
    op.drop_column('equipments', 'location')
    op.drop_column('equipments', 'equipment_type')
    op.drop_column('equipments', 'product_number')
    op.drop_column('equipments', 'brand')
    op.drop_column('equipments', 'hostname')
    op.drop_column('equipments', 'patrimony_number')
    op.drop_column('equipments', 'serial_number')
