-- ==============================================================================
-- SisPatrimonio: Script DML de Povoamento de Dados PostgreSQL 16
-- Disciplina: Banco de Dados
-- Projeto: Gerenciador de Patrimônio (sispatrimonio)
-- ==============================================================================

-- 1. Inserção de Usuários
-- Senhas criptografadas padrão: 'senha123'
INSERT INTO users (id, name, email, password_hash, role, is_active, created_at, updated_at)
VALUES
    (1, 'Administrador do Sistema', 'admin@sispatrimonio.edu.br', '$argon2id$v=19$m=65536,t=3,p=4$qN8kY3eU1w$sK7m9x0w7Z3b5r2q1...', 'administrador', true, NOW(), NOW()),
    (2, 'Carlos Henrique Técnico', 'tecnico@sispatrimonio.edu.br', '$argon2id$v=19$m=65536,t=3,p=4$qN8kY3eU1w$sK7m9x0w7Z3b5r2q1...', 'tecnico', true, NOW(), NOW()),
    (3, 'Mariana Souza Silva', 'mariana.souza@sispatrimonio.edu.br', '$argon2id$v=19$m=65536,t=3,p=4$qN8kY3eU1w$sK7m9x0w7Z3b5r2q1...', 'colaborador', true, NOW(), NOW()),
    (4, 'Prof. Roberto Albuquerque', 'roberto.albuquerque@sispatrimonio.edu.br', '$argon2id$v=19$m=65536,t=3,p=4$qN8kY3eU1w$sK7m9x0w7Z3b5r2q1...', 'colaborador', true, NOW(), NOW()),
    (5, 'Fernanda Lima Coordenadora', 'fernanda.lima@sispatrimonio.edu.br', '$argon2id$v=19$m=65536,t=3,p=4$qN8kY3eU1w$sK7m9x0w7Z3b5r2q1...', 'colaborador', true, NOW(), NOW())
ON CONFLICT (email) DO NOTHING;

SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));

-- 2. Inserção de Categorias Patrimoniais
INSERT INTO categories (id, name, useful_life_months, residual_value_rate, requires_serial_number, created_at, updated_at)
VALUES
    (1, 'Notebooks e Portáteis', 48, 10.00, true, NOW(), NOW()),
    (2, 'Computadores Desktop', 60, 5.00, true, NOW(), NOW()),
    (3, 'Monitores e Displays', 60, 5.00, true, NOW(), NOW()),
    (4, 'Servidores e Rede', 72, 15.00, true, NOW(), NOW()),
    (5, 'Mobiliário e Estações', 120, 20.00, false, NOW(), NOW()),
    (6, 'Equipamentos de Impressão', 48, 8.00, true, NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET
    useful_life_months = EXCLUDED.useful_life_months,
    residual_value_rate = EXCLUDED.residual_value_rate,
    requires_serial_number = EXCLUDED.requires_serial_number;

SELECT setval('categories_id_seq', (SELECT COALESCE(MAX(id), 1) FROM categories));

-- 3. Inserção de Localizações Físicas
INSERT INTO locations (id, building, floor, sector, room_number, description, created_at, updated_at)
VALUES
    (1, 'Prédio Central', '1º Andar', 'Departamento de TI', 'Sala 101', 'Setor de infraestrutura e suporte computacional', NOW(), NOW()),
    (2, 'Prédio Central', '2º Andar', 'Coordenação Geral', 'Sala 204', 'Gabinete dos coordenadores de curso', NOW(), NOW()),
    (3, 'Bloco de Laboratórios', 'Térreo', 'Laboratório de Banco de Dados', 'Lab-01', 'Bancadas de aula prática com 30 computadores', NOW(), NOW()),
    (4, 'Bloco de Laboratórios', '1º Andar', 'Laboratório de Redes', 'Lab-104', 'Racks de roteamento e comutação', NOW(), NOW()),
    (5, 'Bloco Administrativo', 'Térreo', 'Almoxarifado Central', NULL, 'Depósito geral de patrimônio e estoque', NOW(), NOW())
ON CONFLICT (building, floor, sector, room_number) DO NOTHING;

SELECT setval('locations_id_seq', (SELECT COALESCE(MAX(id), 1) FROM locations));

-- 4. Inserção de Bens Patrimoniais (Ativos)
INSERT INTO assets (
    id, patrimony_number, serial_number, description, category_id, location_id,
    assigned_user_id, brand, model, purchase_cost, purchase_date, status, specs, created_at, updated_at
)
VALUES
    (
        1,
        'PAT-2026-0001',
        'SN-DELL-88210',
        'Dell Latitude 5430 Core i7 16GB',
        1,
        1,
        3,
        'Dell',
        'Latitude 5430',
        6500.00,
        '2026-01-15',
        'em_uso',
        '{"cpu": "Intel Core i7-1265U", "ram_gb": 16, "storage": "512GB NVMe SSD", "os": "Ubuntu 24.04 LTS"}'::jsonb,
        NOW(),
        NOW()
    ),
    (
        2,
        'PAT-2026-0002',
        'SN-LENOVO-9941',
        'ThinkPad T14 Gen 3 Ryzen 7 32GB',
        1,
        2,
        5,
        'Lenovo',
        'ThinkPad T14 Gen 3',
        7200.00,
        '2026-02-10',
        'em_uso',
        '{"cpu": "AMD Ryzen 7 PRO 6850U", "ram_gb": 32, "storage": "1TB SSD", "os": "Windows 11 Pro"}'::jsonb,
        NOW(),
        NOW()
    ),
    (
        3,
        'PAT-2026-0003',
        'SN-DELL-OPT-01',
        'Desktop Dell OptiPlex 7000 Torre',
        2,
        3,
        4,
        'Dell',
        'OptiPlex 7000',
        4800.00,
        '2025-11-20',
        'em_uso',
        '{"cpu": "Intel Core i5-12500", "ram_gb": 16, "storage": "512GB SSD", "gpu": "Intel UHD 770"}'::jsonb,
        NOW(),
        NOW()
    ),
    (
        4,
        'PAT-2026-0004',
        'SN-SAMS-M778',
        'Monitor Samsung Odyssey 27 IPS 165Hz',
        3,
        3,
        4,
        'Samsung',
        'Odyssey G4',
        1650.00,
        '2025-11-20',
        'em_uso',
        '{"screen_size_inch": 27, "resolution": "1920x1080", "refresh_rate_hz": 165, "panel": "IPS"}'::jsonb,
        NOW(),
        NOW()
    ),
    (
        5,
        'PAT-2026-0005',
        'SN-DELL-R750-01',
        'Servidor Dell PowerEdge R750 2U Rack',
        4,
        4,
        2,
        'Dell',
        'PowerEdge R750',
        38500.00,
        '2025-08-10',
        'em_uso',
        '{"dual_cpu": "2x Xeon Gold 6330", "ram_gb": 128, "storage_tb": "4x 2TB SAS SSD RAID 10", "power_redundant": true}'::jsonb,
        NOW(),
        NOW()
    ),
    (
        6,
        'PAT-2026-0006',
        NULL,
        'Mesa de Trabalho Ergonômica 160x80cm',
        5,
        1,
        NULL,
        'Cavaletti',
        'Start 160',
        1100.00,
        '2026-03-01',
        'disponivel',
        '{"dimensions_cm": "160x80x75", "color": "Cinza e Grafite", "cable_pass": true}'::jsonb,
        NOW(),
        NOW()
    ),
    (
        7,
        'PAT-2026-0007',
        'SN-BROTHER-L5652',
        'Multifuncional Brother Laser Monocromática',
        6,
        5,
        NULL,
        'Brother',
        'DCP-L5652DN',
        3200.00,
        '2024-05-18',
        'em_manutencao',
        '{"print_speed_ppm": 42, "duplex": true, "network_interface": "Gigabit Ethernet"}'::jsonb,
        NOW(),
        NOW()
    ),
    (
        8,
        'PAT-2026-0008',
        'SN-HP-M404DW',
        'Impressora HP LaserJet Pro M404dw',
        6,
        5,
        NULL,
        'HP',
        'M404dw',
        1800.00,
        '2023-02-14',
        'baixado',
        '{"print_speed_ppm": 40, "duplex": true, "decommission_reason": "Queima irreversível da placa lógica"}'::jsonb,
        NOW(),
        NOW()
    )
ON CONFLICT (patrimony_number) DO NOTHING;

SELECT setval('assets_id_seq', (SELECT COALESCE(MAX(id), 1) FROM assets));

-- 5. Inserção de Histórico de Renumeração de Patrimônio
INSERT INTO patrimony_history (id, asset_id, old_patrimony_number, new_patrimony_number, reason, changed_by_id, changed_at)
VALUES
    (1, 1, 'PAT-LEGACY-904', 'PAT-2026-0001', 'Substituição de plaqueta danificada e padronização do novo formato universitário', 2, NOW() - INTERVAL '10 days')
ON CONFLICT (id) DO NOTHING;

SELECT setval('patrimony_history_id_seq', (SELECT COALESCE(MAX(id), 1) FROM patrimony_history));

-- 6. Inserção de Movimentações Físicas e Transferência de Custódia
INSERT INTO asset_movements (
    id, asset_id, origin_location_id, dest_location_id, from_user_id, to_user_id,
    moved_by_id, term_accepted_at, movement_date, notes
)
VALUES
    (
        1,
        1,
        5,
        1,
        NULL,
        3,
        2,
        NOW() - INTERVAL '20 days',
        NOW() - INTERVAL '21 days',
        'Entrega inicial do notebook com assinatura digital do termo de responsabilidade'
    ),
    (
        2,
        7,
        2,
        5,
        5,
        NULL,
        2,
        NULL,
        NOW() - INTERVAL '3 days',
        'Recolhimento para o almoxarifado após barulho no fusor; aguarda orçamento de peça'
    ),
    (
        3,
        8,
        5,
        NULL,
        NULL,
        NULL,
        1,
        NOW() - INTERVAL '15 days',
        NOW() - INTERVAL '15 days',
        'Baixa definitiva por desincorporação patrimonial com laudo técnico nº 84/2026'
    )
ON CONFLICT (id) DO NOTHING;

SELECT setval('asset_movements_id_seq', (SELECT COALESCE(MAX(id), 1) FROM asset_movements));

-- 7. Inserção de Manutenções Técnicas
INSERT INTO asset_maintenances (
    id, asset_id, registered_by_id, maintenance_type, service_provider, description, cost, maintenance_date, created_at, updated_at
)
VALUES
    (
        1,
        3,
        2,
        'preventiva',
        'Equipe Interna de TI',
        'Limpeza preventiva de poeira nos coolers, troca de pasta térmica e verificação de integridade do SSD SMART',
        0.00,
        NOW() - INTERVAL '40 days',
        NOW(),
        NOW()
    ),
    (
        2,
        7,
        2,
        'corretiva',
        'LaserTech Manutenções e Peças Ltda',
        'Substituição do rolo pressor e conjunto da película de fusão que apresentavam desgaste térmico acentuado',
        485.50,
        NOW() - INTERVAL '2 days',
        NOW(),
        NOW()
    ),
    (
        3,
        5,
        2,
        'preventiva',
        'Dell ProSupport Enterprise',
        'Atualização sem interrupção de firmware iDRAC9 e diagnóstico preditivo dos módulos de memória ECC',
        1200.00,
        NOW() - INTERVAL '90 days',
        NOW(),
        NOW()
    )
ON CONFLICT (id) DO NOTHING;

SELECT setval('asset_maintenances_id_seq', (SELECT COALESCE(MAX(id), 1) FROM asset_maintenances));
