"""Evolve database to sispatrimonio model

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-22 22:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update users table with name, updated_at, and password_hash
    op.add_column("users", sa.Column("name", sa.String(length=255), server_default="Usuário", nullable=False))
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), server_default="", nullable=False))
    op.execute("UPDATE users SET password_hash = hashed_password WHERE hashed_password IS NOT NULL")
    op.add_column("users", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    # Update check constraint on users.role to allow administrador
    op.drop_constraint("chk_users_role_valid", "users", type_="check")
    op.create_check_constraint(
        "chk_users_role_valid",
        "users",
        "role IN ('administrador', 'tecnico', 'colaborador')",
    )

    # 2. Create locations table
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("building", sa.String(length=100), nullable=False),
        sa.Column("floor", sa.String(length=50), nullable=False),
        sa.Column("sector", sa.String(length=100), nullable=False),
        sa.Column("room_number", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_locations_physical_space",
        "locations",
        ["building", "floor", "sector", "room_number"],
        unique=True,
    )

    # 3. Create categories table
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("useful_life_months", sa.Integer(), nullable=True),
        sa.Column("residual_value_rate", sa.Numeric(precision=5, scale=2), server_default="0.00", nullable=False),
        sa.Column("requires_serial_number", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_categories_name"),
    )

    # 4. Create assets table
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patrimony_number", sa.String(length=100), nullable=False),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("assigned_user_id", sa.Integer(), nullable=True),
        sa.Column("brand", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("purchase_cost", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="disponivel", nullable=False),
        sa.Column(
            "specs",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patrimony_number", name="uq_assets_patrimony_number"),
        sa.UniqueConstraint("serial_number", name="uq_assets_serial_number"),
    )

    # 5. Create patrimony_history table
    op.create_table(
        "patrimony_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("old_patrimony_number", sa.String(length=100), nullable=False),
        sa.Column("new_patrimony_number", sa.String(length=100), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("changed_by_id", sa.Integer(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 6. Create asset_movements table
    op.create_table(
        "asset_movements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("origin_location_id", sa.Integer(), nullable=False),
        sa.Column("dest_location_id", sa.Integer(), nullable=True),
        sa.Column("from_user_id", sa.Integer(), nullable=True),
        sa.Column("to_user_id", sa.Integer(), nullable=True),
        sa.Column("moved_by_id", sa.Integer(), nullable=False),
        sa.Column("term_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("movement_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["origin_location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["dest_location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["from_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["to_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["moved_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 7. Create asset_maintenances table
    op.create_table(
        "asset_maintenances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("registered_by_id", sa.Integer(), nullable=False),
        sa.Column("maintenance_type", sa.String(length=50), nullable=False),
        sa.Column("service_provider", sa.String(length=150), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("cost", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("maintenance_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["registered_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("asset_maintenances")
    op.drop_table("asset_movements")
    op.drop_table("patrimony_history")
    op.drop_table("assets")
    op.drop_table("categories")
    op.drop_index("uq_locations_physical_space", table_name="locations")
    op.drop_table("locations")

    op.drop_constraint("chk_users_role_valid", "users", type_="check")
    op.create_check_constraint("chk_users_role_valid", "users", "role IN ('tecnico', 'colaborador')")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "name")
