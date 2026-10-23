# Quickstart & Verification Guide: Gerenciamento de Patrimônio — Modelo de Banco de Dados

**Feature**: `001-gerenciamento-patrimonio`  
**Date**: 2026-10-22  
**Purpose**: Procedimento de validação fim a fim do novo modelo de banco de dados e APIs do SisPatrimonio.

---

## 1. Pré-requisitos
- PostgreSQL 16 ativo (local ou container Docker).
- Python 3.13+ com `uv`.
- Migrações atualizadas até a revisão anterior (`c3d4e5f6a7b8`).

---

## 2. Passo a Passo de Execução e Verificação

### 2.1. Execução da Migração Alembic
```bash
# Aplica a nova migração do SisPatrimonio
uv run alembic upgrade head

# Verifica integridade de downgrade e upgrade (idempotência)
uv run pytest tests/test_migrations.py -k "test_alembic_migrations_lifecycle" -v
```

### 2.2. Validação da Criação de Catálogos e Espaço Físico
1. **Criar Categoria com Regra de Serial e Depreciação**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/categories \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Notebooks",
       "useful_life_months": 60,
       "residual_value_rate": 10.00,
       "requires_serial_number": true
     }'
   ```
2. **Criar Localização Física**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/locations \
     -H "Content-Type: application/json" \
     -d '{
       "building": "Bloco Central",
       "floor": "1",
       "sector": "Laboratório de Banco de Dados",
       "room_number": "Lab-01",
       "description": "Bancadas com computadores"
     }'
   ```
3. **Testar Bloqueio de Duplicidade Física**:
   - Reenviar o payload anterior idêntico.
   - **Resultado Esperado**: HTTP 409 Conflict (`uq_locations_physical_space`).

### 2.3. Validação do Ciclo de Vida do Ativo e Renumeração
1. **Cadastrar Ativo com JSONB**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/assets \
     -H "Content-Type: application/json" \
     -d '{
       "patrimony_number": "PAT-DB-001",
       "serial_number": "SN-DELL-9988",
       "description": "Dell Latitude 5420",
       "category_id": 1,
       "location_id": 1,
       "brand": "Dell",
       "model": "Latitude 5420",
       "purchase_cost": 5400.00,
       "purchase_date": "2026-02-15",
       "status": "disponivel",
       "specs": {
         "cpu": "Intel Core i7",
         "ram_gb": 16,
         "storage": "512GB NVMe",
         "os": "Ubuntu 24.04"
       }
     }'
   ```
2. **Testar Rejeição de Ativo sem Serial quando Categoria Exige**:
   - Tentar cadastrar novo ativo na categoria 1 sem `serial_number`.
   - **Resultado Esperado**: HTTP 400 Bad Request.
3. **Executar Renumeração com Histórico**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/assets/1/renumber \
     -H "Content-Type: application/json" \
     -d '{
       "new_patrimony_number": "PAT-DB-001-REV",
       "reason": "Substituição de plaqueta danificada por desgaste físico"
     }'
   ```
   - **Resultado Esperado**: HTTP 200 OK, gravando `patrimony_history` e atualizando `assets.patrimony_number`.

### 2.4. Validação de Movimentação e Manutenção
1. **Transferir Ativo para Colaborador e Novo Local**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/assets/1/movements \
     -H "Content-Type: application/json" \
     -d '{
       "origin_location_id": 1,
       "dest_location_id": 1,
       "to_user_id": 2,
       "movement_date": "2026-10-22T21:00:00Z",
       "notes": "Alocação para projeto acadêmico de banco de dados"
     }'
   ```
2. **Aceite do Termo de Responsabilidade**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/movements/1/accept-term
   ```
   - **Resultado Esperado**: `term_accepted_at` preenchido.
3. **Lançar Manutenção com Custo**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/assets/1/maintenances \
     -H "Content-Type: application/json" \
     -d '{
       "maintenance_type": "preventiva",
       "service_provider": "Suporte Técnico Interno",
       "description": "Limpeza interna e troca de pasta térmica",
       "cost": 85.00,
       "maintenance_date": "2026-10-22T21:30:00Z"
     }'
   ```

---

## 3. Validação da Cobertura de Testes (100% Quality Gate)
```bash
PYTHONPATH=. uv run --extra dev pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=100
```
- **Resultado Esperado**: 100% de cobertura em linhas e branches, zero falhas.
