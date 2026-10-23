# Phase 0 Research: Gerenciamento de Patrimônio — Modelo de Banco de Dados

**Feature**: `001-gerenciamento-patrimonio`  
**Date**: 2026-10-22  
**Status**: Completed  

---

## 1. Pesquisa & Decisões Arquiteturais

### 1.1. Tratamento de Enums Nativos do PostgreSQL vs SQLite de Teste
- **Contexto**: O DBML define 3 enums: `user_role` (`administrador`, `tecnico`, `colaborador`), `asset_status` (`disponivel`, `em_uso`, `em_manutencao`, `baixado`) e `maintenance_type` (`preventiva`, `corretiva`).
- **Decisão**: Utilizar `sa.Enum` nativo do SQLAlchemy com classes Python `enum.StrEnum` (ou `enum.Enum` com `values_callable=lambda x: [e.value for e in x]`).
- **Configuração**:
  - Declarar `create_type=True` e `name='user_role'` para PostgreSQL.
  - Para o SQLite in-memory de testes, o SQLAlchemy mapeia automaticamente `Enum` como `VARCHAR` com `CHECK constraint`, garantindo paridade funcional sem quebras no fallback de teste.
- **Alternativas Consideradas**:
  - Tabelas de catálogo separadas (como na versão anterior): Rejeitado porque o modelo fornecido pelo usuário e a matéria de banco de dados exigem expressamente Enums PostgreSQL (`Enum user_role`, `Enum asset_status`, `Enum maintenance_type`).

---

### 1.2. Mapeamento de Coluna `specs` (JSONB)
- **Contexto**: A tabela `assets` possui o campo `specs jsonb [not null, default: '{}']` para armazenar especificações flexíveis de equipamentos de TI e outros bens.
- **Decisão**: Mapear como `sa.JSON().with_variant(postgresql.JSONB, "postgresql")` com `server_default=sa.text("'{}'::jsonb")` no PostgreSQL e `server_default=sa.text("'{}'")` no SQLite. Em Python, tipado como `Mapped[dict[str, Any]] = mapped_column(..., default=dict)`.
- **Alternativas Consideradas**:
  - Colunas normais EAV (Entity-Attribute-Value): Rejeitado por complexidade desnecessária e divergência do DBML fornecido.
  - Coluna `Text` com serialização manual: Rejeitado porque o PostgreSQL oferece operadores indexáveis (`->`, `->>`, `@>`) e validação de sintaxe JSON em runtime com `JSONB`.

---

### 1.3. Estratégia de Unicidade Composta em `locations` com Coluna Nullable
- **Contexto**: `locations` possui a restrição `uq_locations_physical_space` sobre `(building, floor, sector, room_number)`. `room_number` é opcional (`null`).
- **Decisão**:
  - No PostgreSQL 15+, restrições únicas com colunas nulas podem utilizar `UNIQUE NULLS NOT DISTINCT (building, floor, sector, room_number)` ou índice funcional com `COALESCE(room_number, '')`.
  - Para garantir portabilidade transparente com o SQLite de testes (que trata cada `NULL` como distinto no índice único padrão), implementar a constraint formal `Index("uq_locations_physical_space", building, floor, sector, func.coalesce(room_number, ""), unique=True)` ou `UNIQUE NULLS NOT DISTINCT` com fallback de teste.
- **Alternativas Consideradas**:
  - Transformar `room_number` em NOT NULL com valor vazio `""`: Rejeitado para preservar a especificação fiel do DBML (`room_number varchar(50) [null]`).

---

### 1.4. Campos Financeiros e Taxas (`numeric(12,2)` e `numeric(5,2)`)
- **Contexto**: `purchase_cost` e `asset_maintenances.cost` utilizam `numeric(12,2)`. `residual_value_rate` utiliza `numeric(5,2)`.
- **Decisão**: No SQLAlchemy, mapear com `sa.Numeric(precision=12, scale=2)` e `sa.Numeric(precision=5, scale=2)`. No Pydantic v2 e domínio, tipar com `Decimal` do módulo nativo `decimal`, validando `residual_value_rate >= 0.00` e `<= 100.00`.
- **Alternativas Consideradas**:
  - `Float`: Rejeitado sumariamente por causar imprecisão de arredondamento em cálculos fiscais e de depreciação.

---

### 1.5. Estratégia de Migração no Alembic
- **Contexto**: A aplicação possui tabelas existentes (`equipments`, `sectors`, `equipment_types`, `equipment_statuses`, etc.). A nova especificação substitui a estrutura pelo projeto `sispatrimonio`.
- **Decisão**: Criar nova migração formal `d4e5f6a7b8c9_evolve_to_sispatrimonio_model.py`:
  1. Cria os novos enums (`user_role`, `asset_status`, `maintenance_type`).
  2. Ajusta `users` para suportar `name`, renomear `hashed_password` para `password_hash` e incluir `administrador` na role.
  3. Cria as novas tabelas: `categories`, `locations`, `assets`, `patrimony_history`, `asset_movements`, `asset_maintenances`.
  4. Migra dados existentes de compatibilidade onde aplicável (ou substitui tabelas legadas garantindo idempotência com `downgrade()`).
- **Alternativas Consideradas**:
  - Alterar migrações antigas retroativamente: Rejeitado pela Constituição do Projeto (migrações passadas são imutáveis e já estão commitadas).

---

## 2. Resumo de Decisões Prontas para Fase 1

| Componente | Decisão Final | Rationale |
|---|---|---|
| **Enums** | `sa.Enum(..., native_enum=True)` | Fidelidade estrita ao DBML `sispatrimonio` e otimização de espaço no PG. |
| **JSONB** | `sa.JSON().with_variant(postgresql.JSONB, "postgresql")` | Compatibilidade híbrida PG 16 e SQLite de testes. |
| **Índice de Localização** | `uq_locations_physical_space` | Unicidade de espaço físico prevenindo duplicatas de salas/setores. |
| **Depreciação** | `Decimal` com `Numeric(5,2)` | Precisão contábil para vida útil e valor residual. |
| **Renumeração** | Transação atômica em `patrimony_history` | Rastreabilidade total exigida na auditoria patrimonial. |
