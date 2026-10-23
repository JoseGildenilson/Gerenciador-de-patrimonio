# Lista de Tarefas: CRUD e Gerenciamento de Tags (Patrimônio)

## 1. Backend (Domínio, Repositório, Casos de Uso e API)
- [x] **1.1 DTOs / Schemas Pydantic:**
  - Adicionar `EquipmentTagUpdate` em `src/domain/schemas.py` com validação de campo `name` (min_length=1).
- [x] **1.2 Repositório de Tags (`EquipmentTagRepository`):**
  - Implementar método `get_by_id(tag_id: int) -> EquipmentTag | None` em `src/infrastructure/repositories.py`.
  - Implementar método `delete(tag: EquipmentTag) -> None`.
  - Implementar método `propagate_tag_rename(category: str, old_name: str, new_name: str) -> None` para atualizar em lote `equipment_type`, `location` ou `status` na tabela de equipamentos.
- [x] **1.3 Casos de Uso (`ManageTagsUseCase`):**
  - Atualizar `create_tag`: validar duplicidade e lançar `ValueError` em caso de conflito.
  - Implementar `update_tag(tag_id: int, new_name: str)`: validar existência, checar duplicidade na categoria, atualizar tag e propagar alteração nos equipamentos.
  - Implementar `delete_tag(tag_id: int)`: validar existência e remover a tag da sessão.
- [x] **1.4 Roteador HTTP (`src/api/equipment_routes.py`):**
  - Ajustar `POST /api/v1/equipments/tags` com tratamento de erro `HTTP 400 Bad Request`.
  - Adicionar `PUT /api/v1/equipments/tags/{id}` com `HTTP 200 OK`, `400 Bad Request` e `404 Not Found` (Role: Técnico).
  - Adicionar `DELETE /api/v1/equipments/tags/{id}` com `HTTP 200 OK` e `404 Not Found` (Role: Técnico).
- [x] **1.5 Testes Automatizados do Backend:**
  - Testes unitários para `ManageTagsUseCase` cobrindo criação, duplicidade, edição/propagação, e deleção com 100% de cobertura.
  - Testes de API para as rotas HTTP de tags (`GET`, `POST`, `PUT`, `DELETE`) incluindo validação de permissões RBAC (`tecnico` vs `colaborador`).

---

## 2. Frontend (API Client, Modais e Componentes)
- [x] **2.1 Cliente de API (`frontend/src/api/equipmentApi.ts`):**
  - Adicionar métodos `updateTag(id: number, name: string)` e `deleteTag(id: number)`.
- [x] **2.2 Modal de Gerenciamento Centralizado (`ManageTagsModal.tsx`):**
  - Criar componente `ManageTagsModal` com abas para as 3 categorias (`Tipo`, `Localização`, `Situação`).
  - Implementar listagem com badge contador de tags.
  - Implementar seletor de ícone estilo Iconize com busca rápida e biblioteca de ícones Lucide contextuais.
  - Desacoplar o formulário de adição em container estático (`z-20 overflow-visible`), mantendo a rolagem (`overflow-y-auto`) restrita à lista de tags para que o popover (`top-full mt-2 z-50`) fique 100% visível sobrepondo a lista sem ser recortado por overflow.
  - Exibir ícone associado no card da tag e persistir visualmente com fallback.
  - Implementar formulário de adição rápida de tag.
  - Implementar edição inline (botão editar -> input -> salvar/cancelar).
  - Implementar exclusão com confirmação visual.
- [x] **2.3 Ponto de Acesso no Menu Lateral (`SideMenu.tsx`):**
  - Adicionar item "Gerenciar Tags" com ícone de tag, visível para o perfil técnico, disparando a abertura do modal `ManageTagsModal`.
- [x] **2.4 Ponto de Acesso no Cabeçalho de Equipamentos (`EquipmentListPage.tsx`):**
  - Adicionar botão "Gerenciar Tags" no header ao lado de "Novo Equipamento", com callback para recarregar filtros e tags após alterações.
- [x] **2.5 Criação Rápida Inline no Modal de Movimentação (`MovementModal.tsx`):**
  - Adicionar botão de criação inline "Criar local" permitindo cadastrar nova localização diretamente durante a movimentação, com estilo aprimorado e sem duplo "+".
- [x] **2.6 Criação Rápida Inline nos Detalhes do Equipamento e Criação (`EquipmentDetailPage.tsx` / `NewEquipmentModal.tsx`):**
  - Adicionar botões "Criar tipo", "Criar local" e "Criar situação" com visual destacado e sem duplo "+".
- [x] **2.7 Testes Automatizados do Frontend:**
  - Testes do componente `ManageTagsModal` (listagem, adição, renomeação, exclusão).
  - Testes de integração de API `equipmentApi` para as novas rotas.
  - Testes de criação rápida inline no modal de movimentação e tela de detalhes.

---

## 3. Validação e Conclusão
- [x] Executar suíte de testes do backend (`pytest --cov=src --cov-branch`).
- [x] Executar suíte de testes do frontend (`npm run test`).
- [x] Validar conformidade de 100% com a especificação e a Constituição.
