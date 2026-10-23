# Phase 1 Data Model: Gerenciamento de Patrimônio

**Feature**: `001-gerenciamento-patrimonio`  
**Date**: 2026-10-22  
**Status**: Completed  

---

## 1. Enums do Domínio

### 1.1. `user_role`
Representa os níveis de privilégio de acesso ao SisPatrimonio:
- `administrador`: Gestão completa de usuários, categorias, configurações contábeis e todas as operações patrimoniais.
- `tecnico`: Cadastro, edição, movimentação, renumeração e lançamento de manutenções em ativos.
- `colaborador`: Consulta de ativos sob sua custódia e confirmação de aceite de termos de responsabilidade.

### 1.2. `asset_status`
Ciclo de vida operacional do ativo patrimonial:
- `disponivel`: Bem em estoque/almoxarifado pronto para alocação.
- `em_uso`: Ativo alocado em um setor/sala sob custódia de um colaborador.
- `em_manutencao`: Ativo em intervenção técnica preventiva ou corretiva.
- `baixado`: Ativo desincorporado, alienado ou descartado (fora de operação).

### 1.3. `maintenance_type`
Classificação da intervenção de manutenção:
- `preventiva`: Revisão periódica planejada.
- `corretiva`: Reparo de avaria ou restauração de funcionalidade com falha.

---

## 2. Entidades & Esquema Relacional

```mermaid
erDiagram
    User ||--o{ Asset : "assigned_custody"
    User ||--o{ PatrimonyHistory : "changed_by"
    User ||--o{ AssetMovement : "from_user"
    User ||--o{ AssetMovement : "to_user"
    User ||--o{ AssetMovement : "moved_by"
    User ||--o{ AssetMaintenance : "registered_by"

    Category ||--o{ Asset : "classifies"
    Location ||--o{ Asset : "houses"
    Location ||--o{ AssetMovement : "origin_location"
    Location ||--o{ AssetMovement : "dest_location"

    Asset ||--o{ PatrimonyHistory : "renumbered_via"
    Asset ||--o{ AssetMovement : "transferred_via"
    Asset ||--o{ AssetMaintenance : "maintained_via"

    User {
        int id PK
        string name "not null"
        string email "unique, not null, lower"
        string password_hash "not null"
        user_role role "default colaborador"
        boolean is_active "default true"
        datetime deleted_at "nullable"
        datetime created_at
        datetime updated_at
    }

    Location {
        int id PK
        string building "not null"
        string floor "not null"
        string sector "not null"
        string room_number "nullable"
        text description "nullable"
        datetime created_at
        datetime updated_at
    }

    Category {
        int id PK
        string name "unique, not null"
        int useful_life_months "nullable"
        numeric residual_value_rate "default 0.00 (0 a 100)"
        boolean requires_serial_number "default false"
        datetime created_at
        datetime updated_at
    }

    Asset {
        int id PK
        string patrimony_number "unique, not null"
        string serial_number "unique, nullable"
        string description "not null"
        int category_id FK
        int location_id FK
        int assigned_user_id FK "nullable"
        string brand "not null"
        string model "nullable"
        numeric purchase_cost "nullable, 12,2"
        date purchase_date "nullable"
        asset_status status "default disponivel"
        jsonb specs "not null, default {}"
        datetime deleted_at "nullable"
        datetime created_at
        datetime updated_at
    }

    PatrimonyHistory {
        int id PK
        int asset_id FK
        string old_patrimony_number "not null"
        string new_patrimony_number "not null"
        string reason "not null"
        int changed_by_id FK
        datetime changed_at "default now"
    }

    AssetMovement {
        int id PK
        int asset_id FK
        int origin_location_id FK
        int dest_location_id FK "nullable para baixa"
        int from_user_id FK "nullable"
        int to_user_id FK "nullable"
        int moved_by_id FK
        datetime term_accepted_at "nullable"
        datetime movement_date "not null, default now"
        text notes "nullable"
    }

    AssetMaintenance {
        int id PK
        int asset_id FK
        int registered_by_id FK
        maintenance_type maintenance_type "not null"
        string service_provider "nullable"
        text description "not null"
        numeric cost "nullable, 12,2"
        datetime maintenance_date "not null"
        datetime created_at
        datetime updated_at
    }
```

---

## 3. Regras de Negócio & Validações de Domínio

### 3.1. Validações da Entidade `Asset`
1. **Unicidade de Patrimônio**: `patrimony_number` é único e permanente no sistema.
2. **Número de Série Condicional**: Se a `Category` associada tiver `requires_serial_number == true`, a criação ou edição do `Asset` DEVE rejeitar payloads sem `serial_number`. Se fornecido, `serial_number` deve ser único.
3. **Custo de Aquisição**: `purchase_cost` deve ser `>= 0.00`.
4. **Alocação de Custodiante**: Se `assigned_user_id` for informado, o usuário deve possuir `is_active == true` e `deleted_at == null`.

### 3.2. Validações da Entidade `Location`
1. **Unicidade Física Composta**: A combinação `(building, floor, sector, room_number)` é única.

### 3.3. Validações da Entidade `Category`
1. **Taxa de Valor Residual**: `residual_value_rate` deve estar estritamente entre `0.00` e `100.00`.
2. **Vida Útil**: `useful_life_months` deve ser um inteiro positivo (`>= 1`).

### 3.4. Transições de Estado de Ativos
```mermaid
stateDiagram-v2
    [*] --> disponivel : Cadastro inicial
    disponivel --> em_uso : Movimentação para setor/usuário
    em_uso --> disponivel : Devolução ao almoxarifado
    em_uso --> em_manutencao : Abertura de manutenção
    disponivel --> em_manutencao : Abertura de manutenção
    em_manutencao --> disponivel : Conclusão da manutenção
    em_manutencao --> em_uso : Conclusão com retorno direto
    disponivel --> baixado : Baixa patrimonial (dest_location_id = NULL)
    em_uso --> baixado : Baixa patrimonial (dest_location_id = NULL)
    em_manutencao --> baixado : Baixa por inviabilidade técnica
    baixado --> [*]
```

### 3.5. Transação Atômica de Renumeração (`patrimony_history`)
Ao atualizar `assets.patrimony_number`:
1. Verifica se o novo patrimônio já está em uso por outro ativo.
2. Registra linha imutável em `patrimony_history` com `asset_id`, `old_patrimony_number`, `new_patrimony_number`, `reason`, `changed_by_id`, `changed_at`.
3. Atualiza `assets.patrimony_number` e `updated_at`.
4. Executa `commit` atômico conjunto na mesma transação.
