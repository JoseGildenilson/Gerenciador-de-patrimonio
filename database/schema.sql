-- ==============================================================================
-- SisPatrimonio: Script DDL de Criação do Banco de Dados PostgreSQL 16
-- Disciplina: Banco de Dados
-- Projeto: Gerenciador de Patrimônio (sispatrimonio)
-- ==============================================================================

-- 1. Criação dos Tipos Enumerados (ENUMs)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('administrador', 'tecnico', 'colaborador');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'asset_status') THEN
        CREATE TYPE asset_status AS ENUM ('disponivel', 'em_uso', 'em_manutencao', 'baixado');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'maintenance_type') THEN
        CREATE TYPE maintenance_type AS ENUM ('preventiva', 'corretiva');
    END IF;
END $$;

-- 2. Tabela de Usuários (users)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'colaborador',
    is_active BOOLEAN NOT NULL DEFAULT true,
    deleted_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Tabela de Localizações Físicas (locations)
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    building VARCHAR(100) NOT NULL,
    floor VARCHAR(50) NOT NULL,
    sector VARCHAR(100) NOT NULL,
    room_number VARCHAR(50) NULL,
    description TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_locations_physical_space UNIQUE NULLS NOT DISTINCT (building, floor, sector, room_number)
);

-- 4. Tabela de Categorias Patrimoniais (categories)
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    useful_life_months INTEGER NULL CHECK (useful_life_months IS NULL OR useful_life_months > 0),
    residual_value_rate NUMERIC(5,2) NOT NULL DEFAULT 0.00 CHECK (residual_value_rate >= 0.00 AND residual_value_rate <= 100.00),
    requires_serial_number BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Tabela de Bens Patrimoniais / Ativos (assets)
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    patrimony_number VARCHAR(100) UNIQUE NOT NULL,
    serial_number VARCHAR(100) UNIQUE NULL,
    description VARCHAR(255) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE RESTRICT,
    assigned_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(100) NULL,
    purchase_cost NUMERIC(12,2) NULL CHECK (purchase_cost IS NULL OR purchase_cost >= 0.00),
    purchase_date DATE NULL,
    status asset_status NOT NULL DEFAULT 'disponivel',
    specs JSONB NOT NULL DEFAULT '{}'::jsonb,
    deleted_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Tabela de Histórico de Renumeração de Patrimônio (patrimony_history)
CREATE TABLE IF NOT EXISTS patrimony_history (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    old_patrimony_number VARCHAR(100) NOT NULL,
    new_patrimony_number VARCHAR(100) NOT NULL,
    reason VARCHAR(255) NOT NULL,
    changed_by_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Tabela de Movimentações Físicas e Custódia (asset_movements)
CREATE TABLE IF NOT EXISTS asset_movements (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    origin_location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE RESTRICT,
    dest_location_id INTEGER NULL REFERENCES locations(id) ON DELETE RESTRICT,
    from_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    to_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    moved_by_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    term_accepted_at TIMESTAMPTZ NULL,
    movement_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT NULL
);

-- 8. Tabela de Manutenções Técnicas (asset_maintenances)
CREATE TABLE IF NOT EXISTS asset_maintenances (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    registered_by_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    maintenance_type maintenance_type NOT NULL,
    service_provider VARCHAR(150) NULL,
    description TEXT NOT NULL,
    cost NUMERIC(12,2) NULL CHECK (cost IS NULL OR cost >= 0.00),
    maintenance_date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. Índices de Otimização e Desempenho
CREATE INDEX IF NOT EXISTS idx_assets_category_id ON assets(category_id);
CREATE INDEX IF NOT EXISTS idx_assets_location_id ON assets(location_id);
CREATE INDEX IF NOT EXISTS idx_assets_assigned_user_id ON assets(assigned_user_id);
CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
CREATE INDEX IF NOT EXISTS idx_asset_movements_asset_id ON asset_movements(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_maintenances_asset_id ON asset_maintenances(asset_id);
CREATE INDEX IF NOT EXISTS idx_patrimony_history_asset_id ON patrimony_history(asset_id);
