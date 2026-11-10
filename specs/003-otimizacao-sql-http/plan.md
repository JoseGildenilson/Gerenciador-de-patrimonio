# Implementation Plan: Otimização de Consultas SQL e Requisições HTTP

**Feature Branch**: `003-otimizacao-sql-http`
**Created**: 2026-11-03
**Status**: In Progress

---

## 1. Linha de Base (Baseline Atual)

Medições realizadas antes de qualquer alteração no código:

| Cenário | Requisições HTTP (Front) | Queries SQL (Backend) | Detalhe das Queries |
| :--- | :---: | :---: | :--- |
| **1. Abertura da Listagem** (`/equipments`) | 3 req (6 em Dev com StrictMode) | 11 queries (22 em Dev) | `users` (auth x3) + `count` + `assets` + `categories` + `locations` + `users` + `asset_maintenances` + `categories` + `locations` |
| **2. Navegação na Listagem** (Mudar página) | 1 req | 7 queries | `users` (auth) + `count` + `assets` + `categories` + `locations` + `users` + `asset_maintenances` |
| **3. Abertura de Detalhe** (`/equipments/:id`) | 3 req | 13 queries | `users` (auth x3) + `assets` (detail com 8 queries separadas de histórico e users) + `categories` + `locations` |
| **4. Voltar para a Listagem** | 3 req (6 em Dev) | 11 queries (22 em Dev) | Sem cache: recarrega tudo novamente |
| **5. Abertura de Outro Detalhe** | 3 req | 13 queries | Sem cache: recarrega tags e ativo novamente |

---

## 2. Metas de Otimização (Pós-Implementação)

| Cenário | Requisições HTTP Alvo | Queries SQL Alvo | Redução Esperada |
| :--- | :---: | :---: | :---: |
| **1. Abertura da Listagem** | 3 req (deduplicadas em Dev) | 5 queries | **-54%** SQL queries |
| **2. Navegação na Listagem** | 1 req | 3 queries (`auth` + `count` + `assets_joined`) | **-57%** SQL queries |
| **3. Abertura de Detalhe** | 1 req (tags vêm do cache) | 5 queries (`auth` + `asset_joined` + `3 collections joined`) | **-61%** SQL queries, **-66%** HTTP req |
| **4. Voltar para a Listagem** | 1 req (tags do cache) | 3 queries | **-72%** SQL queries, **-66%** HTTP req |
| **5. Abertura de Outro Detalhe** | 1 req (tags do cache) | 5 queries | **-61%** SQL queries, **-66%** HTTP req |

---

## 3. Arquitetura da Solução

### 3.1 Frontend: Cache de Referência e Deduplicação (`equipmentApi.ts`)
- **Estratégia**: Cache em memória com TTL (5 minutos) e deduplicação de promises em trânsito (*in-flight promise sharing*).
- **Escopo**: `categories` e `locations`.
- **Deduplicação**: Se múltiplos componentes (ou `React.StrictMode`) solicitarem `/categories` ou `/locations` ao mesmo tempo, compartilham a mesma Promise HTTP ativa.
- **Invalidação Reativa**: Toda operação de escrita (`createCategory`, `updateCategory`, `deleteCategory`, `createLocation`, `updateLocation`, `deleteLocation`) limpa o cache correspondente.
- **API retrocompatível**: Suporte ao parâmetro `{ forceRefresh: true }` caso seja necessário contornar o cache.

### 3.2 Backend: Estratégia Híbrida de Carregamento SQLAlchemy (`repositories.py`)
- **Listagem de Ativos (`AssetRepository.list`)**:
  - `joinedload(Asset.category)`: 1:1, une na consulta principal sem produto cartesiano.
  - `joinedload(Asset.location)`: 1:1, une na consulta principal.
  - `joinedload(Asset.assigned_user)`: 1:1, une na consulta principal.
  - **Eliminação de `selectinload(Asset.maintenances)`**: Substituído por subquery escalar correlacionada:
    ```python
    last_maint_subq = (
        select(func.max(AssetMaintenance.maintenance_date))
        .where(AssetMaintenance.asset_id == Asset.id)
        .correlate(Asset)
        .scalar_subquery()
    )
    ```
    Carrega apenas a data mais recente no SELECT principal, sem instanciar centenas de objetos de manutenção.
- **Detalhe do Ativo (`AssetRepository.get_by_id`)**:
  - `joinedload` para entidades Many-to-One diretas (`category`, `location`, `assigned_user`).
  - `selectinload` para coleções 1:N (`maintenances`, `patrimony_histories`, `movements`) encadeado com `joinedload` para seus nós Many-to-One filhos.
  - Reduz de 14 para 4 consultas sem perigo de explosão cartesiana.
- **Autenticação (`UserRepository.get_by_id`)**:
  - Projeção estrita com `load_only(User.id, User.name, User.email, User.role, User.is_active, User.deleted_at)` para evitar carregamento desnecessário de `password_hash`.

---

## 4. Plano de Verificação e Testes

1. **Testes Unitários e de Integração**:
   - `tests/test_sql_optimization.py`: Testar contagem exata de queries geradas em `list_assets` e `get_asset`.
   - `frontend/src/__tests__/equipmentApi.test.ts`: Testar cache de categorias/localizações, deduplicação em voo e invalidação após mutações.
2. **Garantia de 100% de Cobertura**:
   - Manter cobertura total (linhas e branches) no backend e no frontend.
3. **Validação E2E e Comparação Final**:
   - Executar os 5 cenários com logging visual e aferir as métricas comparativas.
