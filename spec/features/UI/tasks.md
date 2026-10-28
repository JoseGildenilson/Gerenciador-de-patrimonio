# Plano de Tarefas: Redesign Visual & Design System Anti-IA

Este documento detalha as etapas de implementação para o redesign do frontend, mapeando cada requisito definido em [`spec.md`](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/spec/features/UI/spec.md) e assegurando conformidade com a [`constituicao.md`](file:///home/gil/Projects/Gerenciador%20de%20patrimonio/spec/constituicao.md).

---

## Mapeamento de Requisitos da Especificação

| Requisito / Regra | Descrição | Tarefa Correspondente |
|---|---|---|
| **2.1 / 2.2** | Remoção de glow neon, blurs e gradientes arco-íris; Tokens Zinc neutros. | **TASK-UI-01**, **TASK-UI-02** |
| **2.3** | Tipografia profissional Inter + JetBrains Mono tabular para dados técnicos. | **TASK-UI-01**, **TASK-UI-04**, **TASK-UI-05** |
| **RN-UI-01** | Tela de Login sóbria, compacta, sem esferas de luz e botão sólido de alto contraste. | **TASK-UI-02**, **TASK-UI-03** |
| **RN-UI-02** | Dashboard estilo Command Center com números tabulares e cards sem gradientes. | **TASK-UI-04** |
| **RN-UI-03** | Listagem de equipamentos de alta densidade com Status Dot e filtros refinados. | **TASK-UI-05** |
| **RN-UI-04** | Tela de detalhes com quadrantes de 1px e timeline técnica para históricos. | **TASK-UI-06** |
| **RN-UI-05** | Modais e formulários com visual utilitário e foco nítido sem halos azuis. | **TASK-UI-07** |
| **Cenários 1-5** | Preservação de todos os comportamentos e passagem de 100% dos testes. | **TASK-UI-08** |

---

## Lista de Tarefas de Implementação

### Fase 1: Design System Base & Tokens Globais
- [x] **TASK-UI-01: Atualização de CSS Base e Tokens Globais (`index.css` & `tailwind.config.js`)**
  - [x] Remover classes e utilitários de sombras glow neon (`.btn-glow-transition`, `shadow-glow-brand`, `shadow-glow-error`, etc.).
  - [x] Configurar paleta de cores neutras e classes de foco nítido baseadas em tons de `zinc` / `slate` profundos.
  - [x] Definir keyframes de transição rápidos (150ms a 200ms) para micro-interações discretas, táteis e fluidas.

---

### Fase 2: Autenticação & Tela de Login
- [x] **TASK-UI-02: Redesign da Página de Login (`LoginPage.tsx`)**
  - [x] Remover luzes de fundo borradas (`blur-[120px]`) e linha de gradiente no topo do card.
  - [x] Aplicar card compacto em `bg-zinc-900/90` com borda fina `border-zinc-800` e sombra natural profunda.
  - [x] Refinar header da marca com tipografia precisa e ícone em escala de cinza/acento único.
- [x] **TASK-UI-03: Redesign do Formulário e Alertas (`LoginForm.tsx` & `AlertBanner.tsx`)**
  - [x] Botão de envio com acabamento sólido de alto contraste (`bg-zinc-100 text-zinc-900 font-semibold hover:bg-white`).
  - [x] Inputs com foco nítido `ring-1 ring-zinc-400 border-zinc-400`.
  - [x] Banners de alerta sóbrios com ícones monocromáticos integrados e bordas técnicas.

---

### Fase 3: Dashboard & Navegação
- [x] **TASK-UI-04: Redesign do Dashboard e Menu Lateral (`DashboardPage.tsx` & `SideMenu.tsx`)**
  - [x] Remover gradientes coloridos do banner de boas-vindas; adotar cabeçalho de seção estruturado e limpo.
  - [x] Redesenhar os cards de métricas (Tickets e Equipamentos) com números em `font-mono tabular-nums`.
  - [x] Refinar menu lateral (`SideMenu.tsx`) com gaveta escurecida de alta precisão e tipografia refinada.
  - [x] Garantir que o drawer do `SideMenu.tsx` ocupe a altura total da tela (`h-screen min-h-screen top-0 bottom-0`) para não compactar em headers.

---

### Fase 4: Gestão de Equipamentos (Patrimônio)
- [x] **TASK-UI-05: Redesign da Listagem e Filtros (`EquipmentListPage.tsx` & `MultiSelectFilterDropdown.tsx`)**
  - [x] Substituir bordas duplas grossas por linhas densas com divisores finos e hover sutil.
  - [x] Implementar *Status Dot* discreto para status do equipamento (Em uso, Manutenção, etc.).
  - [x] Formatar metadados (SN, Patrimônio, Datas) em `font-mono text-xs`.
  - [x] Refinar componente de filtro estilo Google Sheets/Linear com popover compacto e busca instantânea.
- [x] **TASK-UI-06: Redesign da Tela de Detalhes e Linha do Tempo (`EquipmentDetailPage.tsx`)**
  - [x] Estruturar seções técnicas com quadrantes limpos de 1px.
  - [x] Transformar os históricos de movimentações e manutenções em Timelines Técnicas limpas.
  - [x] Refinar botões de ação e modo de edição em lote.
- [x] **TASK-UI-07: Redesign dos Modais (`NewEquipmentModal.tsx`, `MaintenanceModal.tsx`, `EditMaintenanceModal.tsx`, `MovementModal.tsx`, `ManageTagsModal.tsx`)**
  - [x] Aplicar acabamento consistente com overlays limpos e formulários de alta densidade.
  - [x] Elevar o z-index de `ManageTagsModal.tsx` para `z-[60]` e renderizar via `createPortal(..., document.body)` para escapar do empilhamento/backdrop do header sticky e SideMenu.

---

### Fase 5: Validação & Auditoria de Testes
- [x] **TASK-UI-08: Execução e Validação dos Testes Automatizados**
  - [x] Executar suíte Vitest no frontend (`npm run test`) garantindo 28/28 testes aprovados.
  - [x] Verificar integridade da compilação TypeScript (`npm run build`).
