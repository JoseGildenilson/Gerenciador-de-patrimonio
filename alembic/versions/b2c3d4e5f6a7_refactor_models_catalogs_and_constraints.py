"""Refactor models catalogs soft delete and postgres constraints

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-14 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET, MACADDR

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Remover tabelas legadas
    op.execute("DROP TABLE IF EXISTS tickets CASCADE;")
    op.execute("DROP TABLE IF EXISTS equipment_tags CASCADE;")

    # 2. Criar tabelas de catálogos
    op.create_table(
        "equipment_types",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_equipment_types_name"),
    )

    op.create_table(
        "sectors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_sectors_name"),
    )

    op.create_table(
        "equipment_statuses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_equipment_statuses_name"),
    )

    op.create_table(
        "maintenance_types",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_maintenance_types_name"),
    )

    # 3. Limpeza de registros legados incompatíveis antes da reestruturação
    op.execute("TRUNCATE TABLE equipment_maintenances, equipment_movements, equipments CASCADE;")
    op.execute("TRUNCATE TABLE login_attempts;")
    op.execute("DELETE FROM users WHERE role <> 'tecnico';")

    # 4. Alterações na tabela users
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint("chk_users_role_tecnico", "users", "role = 'tecnico'")
    op.execute("DROP INDEX IF EXISTS ix_users_email;")
    op.execute("CREATE UNIQUE INDEX uq_users_email_lower ON users (LOWER(email));")

    # 5. Alterações na tabela login_attempts
    op.add_column("login_attempts", sa.Column("email_attempted", sa.String(length=255), nullable=False, server_default=""))
    op.execute("ALTER TABLE login_attempts ALTER COLUMN email_attempted DROP DEFAULT;")
    op.execute("ALTER TABLE login_attempts ALTER COLUMN ip_address TYPE inet USING ip_address::inet;")
    op.create_index("ix_login_attempts_ip_attempted_at", "login_attempts", ["ip_address", "attempted_at"])
    op.create_index("ix_login_attempts_email_attempted_at", "login_attempts", ["email_attempted", "attempted_at"])

    # 6. Alterações na tabela equipments
    op.execute("DROP INDEX IF EXISTS ix_equipments_equipment_type;")
    op.execute("DROP INDEX IF EXISTS ix_equipments_location;")
    op.execute("DROP INDEX IF EXISTS ix_equipments_status;")
    op.execute("DROP INDEX IF EXISTS ix_equipments_hostname;")
    op.execute("DROP INDEX IF EXISTS ix_equipments_patrimony_number;")
    op.execute("DROP INDEX IF EXISTS ix_equipments_serial_number;")

    op.drop_column("equipments", "equipment_type")
    op.drop_column("equipments", "location")
    op.drop_column("equipments", "status")
    op.drop_column("equipments", "windows_key")
    op.drop_column("equipments", "product_number")
    op.drop_column("equipments", "last_maintenance_at")

    op.add_column("equipments", sa.Column("model", sa.String(length=255), nullable=True))
    op.add_column("equipments", sa.Column("equipment_type_id", sa.Integer(), nullable=False))
    op.add_column("equipments", sa.Column("sector_id", sa.Integer(), nullable=False))
    op.add_column("equipments", sa.Column("status_id", sa.Integer(), nullable=False))
    op.add_column("equipments", sa.Column("ip_address", INET(), nullable=True))
    op.add_column("equipments", sa.Column("mac_address", MACADDR(), nullable=True))
    op.add_column("equipments", sa.Column("printer_identifier", sa.String(length=255), nullable=True))
    op.add_column("equipments", sa.Column("windows_product_key_encrypted", sa.Text(), nullable=True))
    op.add_column("equipments", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.add_column("equipments", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    op.alter_column("equipments", "description", existing_type=sa.Text(), nullable=True)
    op.alter_column("equipments", "patrimony_number", existing_type=sa.String(length=255), nullable=False)

    op.create_foreign_key("fk_equipments_equipment_type_id", "equipments", "equipment_types", ["equipment_type_id"], ["id"])
    op.create_foreign_key("fk_equipments_sector_id", "equipments", "sectors", ["sector_id"], ["id"])
    op.create_foreign_key("fk_equipments_status_id", "equipments", "equipment_statuses", ["status_id"], ["id"])

    # 7. Alterações na tabela equipment_movements
    op.drop_column("equipment_movements", "origin_location")
    op.drop_column("equipment_movements", "destination_location")

    op.add_column("equipment_movements", sa.Column("origin_sector_id", sa.Integer(), nullable=False))
    op.add_column("equipment_movements", sa.Column("destination_sector_id", sa.Integer(), nullable=False))
    op.add_column("equipment_movements", sa.Column("performed_by_user_id", sa.Integer(), nullable=False))
    op.add_column("equipment_movements", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))

    op.create_foreign_key("fk_equipment_movements_origin_sector_id", "equipment_movements", "sectors", ["origin_sector_id"], ["id"])
    op.create_foreign_key("fk_equipment_movements_destination_sector_id", "equipment_movements", "sectors", ["destination_sector_id"], ["id"])
    op.create_foreign_key("fk_equipment_movements_performed_by_user_id", "equipment_movements", "users", ["performed_by_user_id"], ["id"])

    # 8. Alterações na tabela equipment_maintenances
    op.drop_column("equipment_maintenances", "maintenance_date")
    op.drop_column("equipment_maintenances", "maintenance_type")

    op.add_column("equipment_maintenances", sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.add_column("equipment_maintenances", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("equipment_maintenances", sa.Column("maintenance_type_id", sa.Integer(), nullable=False))
    op.add_column("equipment_maintenances", sa.Column("performed_by_user_id", sa.Integer(), nullable=True))
    op.add_column("equipment_maintenances", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))

    op.alter_column("equipment_maintenances", "description", existing_type=sa.Text(), nullable=True)

    op.create_foreign_key("fk_equipment_maintenances_maintenance_type_id", "equipment_maintenances", "maintenance_types", ["maintenance_type_id"], ["id"])
    op.create_foreign_key("fk_equipment_maintenances_performed_by_user_id", "equipment_maintenances", "users", ["performed_by_user_id"], ["id"])

    # 9. Constraints CHECK
    op.create_check_constraint(
        "chk_equipments_ip_host_only",
        "equipments",
        "ip_address IS NULL OR (family(ip_address) = 4 AND masklen(ip_address) = 32) OR (family(ip_address) = 6 AND masklen(ip_address) = 128)",
    )
    op.create_check_constraint(
        "chk_movement_different_sectors",
        "equipment_movements",
        "origin_sector_id <> destination_sector_id",
    )
    op.create_check_constraint(
        "chk_movement_date_not_future",
        "equipment_movements",
        "movement_date <= (now() + interval '5 minutes')",
    )
    op.create_check_constraint(
        "chk_maintenance_completion_after_start",
        "equipment_maintenances",
        "completed_at IS NULL OR completed_at >= started_at",
    )

    # 10. Índices compostos, únicos funcionais e parciais
    op.create_index(
        "ix_equipment_movements_equipment_date_id",
        "equipment_movements",
        ["equipment_id", "movement_date", "id"],
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_equipment_maintenances_one_open_per_equipment "
        "ON equipment_maintenances (equipment_id) WHERE completed_at IS NULL;"
    )
    op.execute("CREATE UNIQUE INDEX uq_equipment_types_name_lower ON equipment_types (LOWER(name));")
    op.execute("CREATE UNIQUE INDEX uq_sectors_name_lower ON sectors (LOWER(name));")
    op.execute("CREATE UNIQUE INDEX uq_equipment_statuses_name_lower ON equipment_statuses (LOWER(name));")
    op.execute("CREATE UNIQUE INDEX uq_maintenance_types_name_lower ON maintenance_types (LOWER(name));")

    op.execute("CREATE UNIQUE INDEX uq_equipments_patrimony_number_lower ON equipments (LOWER(patrimony_number));")
    op.execute(
        "CREATE UNIQUE INDEX uq_equipments_serial_number_lower "
        "ON equipments (LOWER(serial_number)) WHERE serial_number IS NOT NULL;"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_equipments_hostname_active "
        "ON equipments (LOWER(hostname)) WHERE deleted_at IS NULL AND hostname IS NOT NULL;"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_equipments_ip_address_active "
        "ON equipments (ip_address) WHERE deleted_at IS NULL AND ip_address IS NOT NULL;"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_equipments_mac_address_active "
        "ON equipments (mac_address) WHERE deleted_at IS NULL AND mac_address IS NOT NULL;"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_equipments_printer_identifier_active "
        "ON equipments (LOWER(printer_identifier)) WHERE deleted_at IS NULL AND printer_identifier IS NOT NULL;"
    )

    # 11. PL/pgSQL Trigger function and triggers
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_equipments_updated_at
        BEFORE UPDATE ON equipments
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_equipment_movements_updated_at
        BEFORE UPDATE ON equipment_movements
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_equipment_maintenances_updated_at
        BEFORE UPDATE ON equipment_maintenances
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """
    )

    # 12. Carga inicial (Seeds)
    op.execute(
        """
        INSERT INTO equipment_statuses (name)
        VALUES
          ('Em uso'),
          ('Em manutenção'),
          ('Baixado'),
          ('Ocioso'),
          ('Aguardando recolhimento'),
          ('Alienação'),
          ('Exposição'),
          ('Acautelado')
        ON CONFLICT (name) DO NOTHING;
        """
    )
    op.execute(
        """
        INSERT INTO maintenance_types (name)
        VALUES
          ('Preventiva'),
          ('Corretiva')
        ON CONFLICT (name) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_equipment_maintenances_updated_at ON equipment_maintenances;")
    op.execute("DROP TRIGGER IF EXISTS trg_equipment_movements_updated_at ON equipment_movements;")
    op.execute("DROP TRIGGER IF EXISTS trg_equipments_updated_at ON equipments;")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")

    op.execute("DROP TABLE IF EXISTS equipment_maintenances CASCADE;")
    op.execute("DROP TABLE IF EXISTS equipment_movements CASCADE;")
    op.execute("DROP TABLE IF EXISTS equipments CASCADE;")
    op.execute("DROP TABLE IF EXISTS maintenance_types CASCADE;")
    op.execute("DROP TABLE IF EXISTS equipment_statuses CASCADE;")
    op.execute("DROP TABLE IF EXISTS sectors CASCADE;")
    op.execute("DROP TABLE IF EXISTS equipment_types CASCADE;")

    # Reverte alterações em login_attempts e users para o estado anterior
    op.drop_index("ix_login_attempts_email_attempted_at", table_name="login_attempts")
    op.drop_index("ix_login_attempts_ip_attempted_at", table_name="login_attempts")
    op.execute("ALTER TABLE login_attempts ALTER COLUMN ip_address TYPE varchar(45) USING ip_address::text;")
    op.drop_column("login_attempts", "email_attempted")

    op.execute("DROP INDEX IF EXISTS uq_users_email_lower;")
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.drop_constraint("chk_users_role_tecnico", "users", type_="check")
    op.drop_column("users", "deleted_at")
