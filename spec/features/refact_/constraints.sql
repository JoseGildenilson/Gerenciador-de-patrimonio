-- Complementos PostgreSQL que não são expressos de forma portável em DBML.
-- Executar após criar as tabelas a partir de Comunica_Patrimonio.dbml.

-- 1. Regras de domínio (CHECK constraints)

-- Nesta versão só existe a role tecnico.
ALTER TABLE users
  ADD CONSTRAINT chk_users_role_tecnico
  CHECK (role = 'tecnico');

-- Garante que ip_address armazene apenas endereços de host (/32 em IPv4 ou /128 em IPv6), sem máscara de sub-rede.
ALTER TABLE equipments
  ADD CONSTRAINT chk_equipments_ip_host_only
  CHECK (
    ip_address IS NULL
    OR (family(ip_address) = 4 AND masklen(ip_address) = 32)
    OR (family(ip_address) = 6 AND masklen(ip_address) = 128)
  );

-- Não faz sentido registrar uma transferência para o mesmo setor.
ALTER TABLE equipment_movements
  ADD CONSTRAINT chk_movement_different_sectors
  CHECK (origin_sector_id <> destination_sector_id);

-- Impede datas futuras nas movimentações (com margem de 5 minutos para evitar falsos positivos por Clock Skew entre containers).
ALTER TABLE equipment_movements
  ADD CONSTRAINT chk_movement_date_not_future
  CHECK (movement_date <= (now() + interval '5 minutes'));

-- A conclusão não pode preceder o início da manutenção.
ALTER TABLE equipment_maintenances
  ADD CONSTRAINT chk_maintenance_completion_after_start
  CHECK (completed_at IS NULL OR completed_at >= started_at);


-- 2. Índices parciais e funcionais de unicidade (Case-Insensitive e Soft Delete)

-- No máximo uma manutenção aberta por equipamento.
CREATE UNIQUE INDEX uq_equipment_maintenances_one_open_per_equipment
  ON equipment_maintenances (equipment_id)
  WHERE completed_at IS NULL;

-- Unicidade case-insensitive permanente (mesmo após soft delete) para usuários, catálogos e identificadores fixos.
CREATE UNIQUE INDEX uq_users_email_lower
  ON users (LOWER(email));

CREATE UNIQUE INDEX uq_equipment_types_name_lower
  ON equipment_types (LOWER(name));

CREATE UNIQUE INDEX uq_sectors_name_lower
  ON sectors (LOWER(name));

CREATE UNIQUE INDEX uq_equipment_statuses_name_lower
  ON equipment_statuses (LOWER(name));

CREATE UNIQUE INDEX uq_maintenance_types_name_lower
  ON maintenance_types (LOWER(name));

CREATE UNIQUE INDEX uq_equipments_patrimony_number_lower
  ON equipments (LOWER(patrimony_number));

CREATE UNIQUE INDEX uq_equipments_serial_number_lower
  ON equipments (LOWER(serial_number))
  WHERE serial_number IS NOT NULL;

-- Unicidade apenas entre equipamentos ativos (não excluídos logicamente).
-- Colunas textuais usam LOWER() para evitar duplicatas por diferença de caixa; inet e macaddr já possuem comparação canônica nativa.
CREATE UNIQUE INDEX uq_equipments_hostname_active
  ON equipments (LOWER(hostname))
  WHERE deleted_at IS NULL AND hostname IS NOT NULL;

CREATE UNIQUE INDEX uq_equipments_ip_address_active
  ON equipments (ip_address)
  WHERE deleted_at IS NULL AND ip_address IS NOT NULL;

CREATE UNIQUE INDEX uq_equipments_mac_address_active
  ON equipments (mac_address)
  WHERE deleted_at IS NULL AND mac_address IS NOT NULL;

CREATE UNIQUE INDEX uq_equipments_printer_identifier_active
  ON equipments (LOWER(printer_identifier))
  WHERE deleted_at IS NULL AND printer_identifier IS NOT NULL;


-- 3. Função e Triggers genéricas para atualização automática de updated_at

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_equipments_updated_at
BEFORE UPDATE ON equipments
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_equipment_movements_updated_at
BEFORE UPDATE ON equipment_movements
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_equipment_maintenances_updated_at
BEFORE UPDATE ON equipment_maintenances
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


-- 4. Carga inicial (Seed) de catálogos obrigatórios

-- Valores iniciais de situações patrimoniais.
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

-- Valores iniciais de tipos de manutenção.
INSERT INTO maintenance_types (name)
VALUES
  ('Preventiva'),
  ('Corretiva')
ON CONFLICT (name) DO NOTHING;