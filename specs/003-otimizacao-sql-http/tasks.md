# Tasks: Otimização de Consultas SQL e Requisições HTTP

**Feature Branch**: `003-otimizacao-sql-http`
**Status**: In Progress

---

## Phase 1: Baseline & Setup

- [x] **T106**: Registrar linha de base (baseline) do comportamento atual: quantidade de requisições HTTP e consultas SQL nos 5 cenários descritos na especificação.

---

## Phase 2: Frontend Cache & In-Flight Deduplication

- [x] **T107**: Implementar cache em memória com TTL (5 min), deduplicação de promises em trânsito e suporte a invalidação em `frontend/src/api/equipmentApi.ts`.
- [x] **T108**: Atualizar chamadas em `EquipmentListPage.tsx`, `EquipmentDetailPage.tsx`, `NewEquipmentModal.tsx` e `ManageTagsModal.tsx` para aproveitar o cache e disparar invalidação em operações de mutação.
- [x] **T109**: Adicionar testes unitários no frontend validando o funcionamento do cache de categorias e localizações, deduplicação em requisições paralelas e invalidação após escrita em `frontend/src/__tests__/equipmentApi.test.ts`.

---

## Phase 3: Backend SQLAlchemy Query Optimization

- [x] **T110**: Otimizar `UserRepository.get_by_id` com `load_only(User.id, User.name, User.email, User.role, User.is_active, User.deleted_at)` em `src/infrastructure/repositories.py` para não trafegar `password_hash` durante autenticação.
- [x] **T111**: Otimizar `AssetRepository.list` e `list_for_export` em `src/infrastructure/repositories.py`, substituindo o carregamento da coleção inteira `selectinload(Asset.maintenances)` por subquery escalar correlacionada de `last_maintenance_at`, e utilizando `joinedload` para `category`, `location` e `assigned_user`.
- [x] **T112**: Otimizar `AssetRepository.get_by_id` em `src/infrastructure/repositories.py` com `joinedload` para entidades Many-to-One e `selectinload` encadeado com `joinedload` para nós filhos de coleções (`maintenances`, `patrimony_histories`, `movements`).
- [x] **T113**: Atualizar `AssetUseCases._to_asset_response` em `src/use_cases/asset_use_cases.py` para receber a data da última manutenção projetada pela subquery ou entidade, sem acionar consultas adicionais.

---

## Phase 4: Testes Automatizados e 100% de Cobertura

- [x] **T114**: Criar testes automatizados de observabilidade e assert de contagem de queries SQL em `tests/test_sql_optimization.py`.
- [x] **T115**: Executar suíte completa de testes de regressão e cobertura: backend (`uv run pytest --cov=src --cov-branch --cov-fail-under=100`, `uv run ruff check .`) e frontend (`npm test -- --run`, `npx tsc --noEmit`).

---

## Phase 5: Medição Comparativa e Relatório Final

- [x] **T116**: Executar medição pós-otimização nos 5 cenários, comparar com a baseline e redigir o relatório final detalhado com confirmação de não alteração do modelo do banco de dados.
