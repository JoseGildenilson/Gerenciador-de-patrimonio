# Especificação da Feature: Gerenciamento e CRUD de Tags (Patrimônio)

## Visão Geral
A funcionalidade de **Gerenciamento e CRUD de Tags** permite aos usuários com papel de **Técnico** criar, listar, renomear/editar e excluir tags dinâmicas do sistema em três categorias essenciais do patrimônio: **Tipos de Equipamento**, **Localizações** e **Situações (Status)**.

A funcionalidade conta com um **Gerenciador Centralizado de Tags** (modal com abas por categoria, edição inline e exclusão) e pontos de **Criação Rápida Inline** em todos os formulários do sistema onde tags são selecionadas.

---

## Regras de Negócio & Restrições

### 1. Categorias e Unicidade
- **RN-TAG-01 (Categorias Suportadas):** O sistema gerencia tags divididas em 3 categorias estruturais:
  - `tipo` (ex.: Desktop, Notebook, Monitor, Impressora)
  - `localizacao` (ex.: TI, Comunicação, Rádio Produção, Diretoria)
  - `situacao` (ex.: Em uso, Ocioso, Em manutenção, Aguardando recolhimento, Baixado)
- **RN-TAG-02 (Unicidade de Nome por Categoria):** Não é permitido cadastrar ou renomear duas tags com o mesmo nome na mesma categoria (case-insensitive ou exact match único no banco de dados). Em caso de tentativa de duplicidade, o sistema deve retornar `HTTP 400 Bad Request`.

### 2. Edição / Renomeação e Propagação
- **RN-TAG-03 (Renomeação de Tag):** O técnico pode renomear uma tag existente.
- **RN-TAG-04 (Propagação Automática para Equipamentos):** Ao renomear uma tag, todos os equipamentos vinculados àquele nome na categoria correspondente (`equipment_type`, `location` ou `status`) são atualizados automaticamente para o novo nome na mesma transação.

### 3. Exclusão de Tags
- **RN-TAG-05 (Exclusão da Lista de Tags Disponíveis):** Ao excluir uma tag, ela é removida da tabela de tags disponíveis para novas seleções e formulários futuros.
- **RN-TAG-06 (Preservação Histórica dos Ativos):** A exclusão de uma tag não altera os dados históricos dos equipamentos já cadastrados que a utilizavam.

### 4. Controle de Acesso (RBAC)
- **RN-TAG-07 (Restrição à Role Técnico):** Apenas usuários autenticados com a role `tecnico` possuem permissão para listar, criar, editar ou excluir tags (`HTTP 403 Forbidden` para colaboradores).

### 5. Interface do Usuário (UI/UX)
- **RN-TAG-08 (Gerenciador Centralizado de Tags):**
  - Acessível a partir do menu lateral (`SideMenu`) e por meio do botão `"Gerenciar Tags"` no cabeçalho da listagem de equipamentos (`/equipamentos`).
  - Apresenta abas ou seções para cada uma das 3 categorias (`Tipo`, `Localização`, `Situação`).
  - Exibe contador de tags por categoria.
  - Estrutura do modal dividida em cabeçalho, abas de categoria, container superior estático do formulário de adição (`px-6 pt-4 pb-2 z-20`) com `overflow-visible`, área de listagem de tags com rolagem independente (`overflow-y-auto px-6 pb-6`) e rodapé fixo.
  - O popover do seletor de ícones estilo Iconize abre para baixo (`top-full mt-2`) sobrepondo a lista de tags com `z-50`, permanecendo 100% visível sem ser recortado por overflow e sem colidir com o rodapé.
  - Exibe o ícone selecionado ao lado do nome de cada tag cadastrada.
  - Permite criação rápida via input + botão "+ Adicionar".
  - Cada item na lista possui ações de **Editar** (transforma o item em input com botões Salvar/Cancelar) e **Excluir** (com confirmação).
- **RN-TAG-09 (Criação Rápida Inline):**
  - Mantida no modal de **Novo Equipamento** (`NewEquipmentModal`).
  - Disponível no modal de **Movimentação** (`MovementModal`) para criar nova localização de destino sem sair do fluxo.
  - Disponível na tela de **Detalhes do Equipamento** (`EquipmentDetailPage`) durante o modo de edição em lote para Tipo, Localização e Situação.

---

## Contrato da API (Backend)

### Endpoints
- `GET /api/v1/equipments/tags`
  - Query Params: `category` (opcional: `tipo`, `localizacao`, `situacao`)
  - Status: `200 OK`
  - Resposta: `list[EquipmentTagResponse]`
- `POST /api/v1/equipments/tags`
  - Body: `EquipmentTagCreate` (`category`, `name`)
  - Status: `201 Created`
  - Resposta: `EquipmentTagResponse`
  - Erros: `400 Bad Request` (nome vazio ou duplicado), `403 Forbidden`
- `PUT /api/v1/equipments/tags/{id}`
  - Body: `EquipmentTagUpdate` (`name`)
  - Status: `200 OK`
  - Resposta: `EquipmentTagResponse`
  - Erros: `400 Bad Request` (nome vazio ou duplicado), `404 Not Found`, `403 Forbidden`
- `DELETE /api/v1/equipments/tags/{id}`
  - Status: `200 OK`
  - Resposta: `MessageResponse` (`{"message": "Tag excluída com sucesso."}`)
  - Erros: `404 Not Found`, `403 Forbidden`

---

## Cenários de Aceitação (BDD)

### Cenário 1: Listar tags filtradas por categoria
- **Dado** que o técnico acesse o gerenciador de tags
- **Quando** selecionar a aba "Localização"
- **Então** o sistema deve listar apenas as tags pertencentes à categoria `localizacao`.

### Cenário 2: Criar nova tag com sucesso
- **Dado** que o técnico esteja na categoria "Tipo de Equipamento"
- **Quando** preencher o nome `"Tablet"` e clicar em "Adicionar"
- **Então** a tag `"Tablet"` deve ser persistida no banco com a categoria `tipo`
- **E** passar a ser exibida imediatamente na lista e nos dropdowns de seleção.

### Cenário 3: Impedir criação de tag duplicada na mesma categoria
- **Dado** que já exista uma tag `"TI"` na categoria `localizacao`
- **Quando** o técnico tentar cadastrar outra tag `"TI"` na categoria `localizacao`
- **Então** o sistema deve retornar erro indicando duplicidade (`HTTP 400`) e manter os dados íntegros.

### Cenário 4: Renomear tag existente com propagação para os equipamentos
- **Dado** que exista a tag `"TI"` na categoria `localizacao` e equipamentos vinculados à localização `"TI"`
- **Quando** o técnico renomear a tag `"TI"` para `"Tecnologia da Informação"`
- **Então** a tag deve ter seu nome atualizado na tabela de tags
- **E** todos os equipamentos que tinham a localização `"TI"` devem passar a ter `"Tecnologia da Informação"`.

### Cenário 5: Excluir tag existente
- **Dado** que exista a tag `"Ocioso"` na categoria `situacao`
- **Quando** o técnico clicar em "Excluir" e confirmar
- **Então** a tag `"Ocioso"` deve ser removida da tabela de tags
- **E** equipamentos previamente cadastrados com `"Ocioso"` continuam com o valor preservado em seu registro.

### Cenário 6: Criar nova tag inline no modal de movimentação
- **Dado** que o técnico abra o modal de movimentação de um equipamento
- **Quando** clicar em "Criar local", digitar `"Almoxarifado B"` e confirmar
- **Então** a nova tag de localização `"Almoxarifado B"` deve ser criada no banco
- **E** selecionada automaticamente como o destino da movimentação.

### Cenário 7: Bloqueio de acesso para colaborador (RBAC)
- **Dado** que um usuário autenticado com a role `colaborador` tente acessar as rotas de criação, edição ou exclusão de tags
- **Então** a requisição deve ser rejeitada com `HTTP 403 Forbidden`.
