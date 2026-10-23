# Especificação: Redesign Visual & Design System (UI/UX Profissional)

## 1. Visão Geral & Diagnóstico

### 1.1. Contexto do Problema
O frontend atual implementa todas as regras de negócio de patrimônio, autenticação e suporte, porém sofre com padrões visuais e clichês característicos de interfaces geradas por IA genérica ("AI slop"):
- **Gradientes multicoloridos e espalhafatosos:** Botões com gradientes `from-blue-600 via-blue-500 to-indigo-600`, barras decorativas no topo de cards e gradientes de fundo sem função estrutural.
- **Esferas de luz e borrões excessivos:** Iluminações neon de fundo (`blur-[120px]`, `bg-blue-600/15`) na tela de login e dashboard que poluem a visão e reduzem o profissionalismo.
- **Sombras de brilho neon (*Glow Effects*):** `shadow-glow-brand`, `shadow-glow-error`, `shadow-blue-500/20` e bordas iluminadas que poluem o contraste visual.
- **Bordas duplas e *zebra striping* exagerado:** Contornos pesados (`border-2 border-slate-700/90`) que aumentam o ruído visual em vez de organizar os dados.
- **Excesso de badges e ícones coloridos:** Badges infladas e caixas de ícones em excesso que tiram o foco dos dados técnicos essenciais.

### 1.2. Objetivo do Redesign
Transformar o sistema em uma ferramenta de software corporativo de **alto nível de acabamento técnico**, inspirada nas melhores referências da indústria de tecnologia e ferramentas para desenvolvedores/TI (como *Linear*, *Vercel*, *Raycast*, *GitHub Enterprise* e *macOS Pro Utilities*):
- Estética sóbria, minimalista e funcional.
- Alta densidade de informação com hierarquia tipográfica precisa.
- Foco em dados técnicos com fontes monoespaçadas tabulares (`font-mono tabular-nums`) para números de patrimônio, séries, chaves e datas.
- Transições físicas rápidas, refinadas e táteis (150ms a 200ms) sem efeitos de brilho ou neon.
- Manutenção rigorosa de 100% das regras funcionais e cenários BDD existentes.

---

## 2. Princípios de Design & Diretrizes Anti-Clichê de IA

### 2.1. Eliminação dos Clichês de IA
1. **Zero Blurs Neon e Ambient Glow:** Nenhuma esfera de cor desfocada no fundo ou sombras com luzes coloridas artificiais.
2. **Zero Gradientes Decorativos em Ações e Textos:** Botões primários utilizarão acabamento de alto contraste sólido (ex: branco puro sobre fundo escuro `bg-zinc-100 text-zinc-950 hover:bg-white` ou azul técnico sólido `#2563eb`), com foco na legibilidade.
3. **Fim das Bordas Duplas Pesadas:** Substituição por bordas ultrafinas de 1px com transparência calculada (`border-zinc-800` ou `border-white/10`).
4. **Substituição de Badges Infladas por Indicadores Discretos (*Status Dots*):** Situações e status representados por pequenos pontos coloridos de 6px a 8px acompanhados de texto elegante, reduzindo o peso visual.
5. **Superfícies Táteis e Densidade:** Utilização de camadas de cinza neutro profundo (Zinc) com profundidade obtida por contraste sutil de superfícies e bordas de 1px, não por borrões coloridos.

### 2.2. Paleta de Cores e Tokens de Superfície (Dark Theme de Alta Precisão)
- **Background Principal:** `bg-zinc-950` (`#09090b`)
- **Superfície Secundária / Header:** `bg-zinc-900/80` (`#121215`) com `border-b border-zinc-800/80`
- **Cards e Painéis:** `bg-zinc-900/50` ou `bg-zinc-900/90` com `border border-zinc-800/80`
- **Bordas e Divisores:** `border-zinc-800` (`#27272a`) e `border-zinc-800/60`
- **Campos de Formulário (Inputs):** `bg-zinc-950 border-zinc-800 text-zinc-100 placeholder-zinc-500 focus:border-zinc-400 focus:ring-1 focus:ring-zinc-400`
- **Texto Principal:** `text-zinc-100` (`#f4f4f5`)
- **Texto Secundário / Metadados:** `text-zinc-400` (`#a1a1aa`)
- **Micro-labels / Auxiliares:** `text-zinc-500` (`#71717a`) com tipografia mono/semibold

### 2.3. Tipografia e Escala
- **Fonte Principal:** `Inter`, com `font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11'` para renderização de caracteres nítidos e profissionais.
- **Fonte Monoespaçada:** `JetBrains Mono` / `ui-monospace` para todos os identificadores (Série, Patrimônio, Hostname, IPs, Windows Key, Datas e Contadores).
- **Tracking:**
  - Headings: `tracking-tight` (-0.02em)
  - Micro-labels: `tracking-wider uppercase text-[10px] font-semibold text-zinc-500`
  - Código/Monospace: `tracking-normal`

---

## 3. Regras de Negócio e UX para Cada Tela

### 3.1. Tela de Login (`LoginPage.tsx` & `LoginForm.tsx`)
- **RN-UI-01 (Autenticação Sóbria):**
  - Remover todas as luzes borradas de fundo e a linha superior com gradiente arco-íris.
  - Card central compacto e refinado com borda sutil de 1px (`border-zinc-800`), fundo `bg-zinc-900/90` e sombra discreta e natural (`shadow-2xl shadow-black/80`).
  - Identificador da marca técnico e elegante com ícone sóbrio em escala de cinza/acento único.
  - Botão "Entrar no Sistema" em acabamento sólido de alto contraste (`bg-zinc-100 text-zinc-900 font-semibold hover:bg-white transition-all active:scale-[0.99]`).
  - Alertas de erro (401 e 429) discretos, em forma de banners técnicos integrados com ícones monocromáticos e borda precisa.

### 3.2. Dashboard (`DashboardPage.tsx` & `SideMenu.tsx`)
- **RN-UI-02 (Command Center & Métricas Limpas):**
  - Remover gradientes no banner de boas-vindas; utilizar cabeçalho de seção estruturado e limpo.
  - Cards de métricas com layout de dashboard industrial:
    - Indicador numérico em destaque com `font-mono tabular-nums text-3xl font-bold text-zinc-100`.
    - Rótulo superior técnico com micro-ícone e status descritivo inferior.
    - Card de Equipamentos com sinalização de atalho clara e hover sutil (elevação mínima de borda e luminosidade, sem neon).
  - Menu lateral retrátil com visual de barra lateral técnica nativa (painel escuro com tipografia fina, divisor discreto de seções e perfil do usuário condensado).
  - O drawer do menu lateral deve ocupar a altura total da viewport (`h-screen min-h-screen top-0 bottom-0`) para evitar compactação vertical independente do elemento pai ou header em que o gatilho estiver posicionado.

### 3.3. Listagem de Equipamentos (`EquipmentListPage.tsx`)
- **RN-UI-03 (Tabela / Grid de Alta Densidade de Ativos):**
  - Remover bordas duplas espessas (`border-2`) e sombras pretas infladas.
  - Cada linha/item de equipamento terá layout horizontal fluido e denso:
    - Indicador de status por *Status Dot* (ex: verde para "Em uso", amarelo para "Em manutenção", cinza para "Estoque").
    - Nome/descrição em `text-sm font-semibold text-zinc-100`.
    - Metadados inline tabulares: `Patrimônio` e `SN` em `font-mono text-xs text-zinc-300`, com separadores sutis.
    - Tag de Tipo e Localização discretas em `bg-zinc-800/80 border border-zinc-700/50 text-zinc-300 text-[11px]`.
    - Data da última manutenção alinhada à direita em fonte monoespaçada legível.
    - Linhas com transição suave no hover (`hover:bg-zinc-900/80 hover:border-zinc-700`).
  - Barra de filtros estilo Google Sheets/Linear refinada com botões compactos de gatilho e popovers com busca interna instantânea.

### 3.4. Tela de Detalhes do Equipamento (`EquipmentDetailPage.tsx`)
- **RN-UI-04 (Prontuário Técnico e Timeline):**
  - Layout organizado em 3 quadrantes técnicos superiores (Identificação, Localização/Rede, Licenciamento/Manutenção) com bordas precisas de 1px.
  - Exibição da Chave Windows com máscara pontilhada precisa e botão discreto de alternância de visualização.
  - Histórico de Manutenções e Histórico de Movimentações apresentados como **Timelines Técnicas** (linha vertical sutil conectando os eventos, datas no topo e lista limpa de itens realizados com marcadores minimalistas).
  - Ações no cabeçalho ("Editar equipamento", "Movimentar", "Manutenção") com hierarquia clara (botão primário sólido para manutenção/edição e botões secundários com borda sutil).

### 3.5. Modais e Formulários (`NewEquipmentModal.tsx`, `MaintenanceModal.tsx`, etc.)
- **RN-UI-05 (Formulários Utilitários de Alta Eficiência):**
  - Modais com overlay escuro limpo (`bg-black/70 backdrop-blur-sm`).
  - O modal do Gerenciador de Tags (`ManageTagsModal.tsx`) e modais globais devem ser renderizados via Portal (`createPortal(..., document.body)`) com camada de empilhamento elevada (`z-[60]` ou superior) para evitar que fiquem presos ou abaixo de elementos pais que possuem `backdrop-filter`, `transform` ou `z-index` local (como headers sticky e drawers laterais).
  - Estrutura de abas ou seções bem delineadas com títulos técnicos claros.
  - Inputs com foco limpo (`ring-1 ring-zinc-400 border-zinc-400`), eliminando halos azuis desfocados.
  - Botões de confirmação e cancelamento consistentes e bem alinhados.

---

## 4. Cenários de Aceitação (BDD)

### Cenário 1: Visualização da Tela de Login sem Clichês de IA
- **Dado** que um usuário acesse a rota `/login`
- **Quando** a tela for renderizada
- **Então** o fundo não deve conter esferas de luz ou gradientes borrados
- **E** o card central deve exibir borda fina de 1px e tipografia nítida
- **E** o botão "Entrar no Sistema" deve apresentar visual sólido e de alto contraste sem gradiente azul/roxo.

### Cenário 2: Visualização do Dashboard Corporativo
- **Dado** que o usuário autenticado esteja no `/dashboard`
- **Quando** visualizar os indicadores
- **Então** os valores numéricos devem ser apresentados em fonte monoespaçada tabular (`font-mono tabular-nums`)
- **E** os cards devem possuir bordas e superfícies neutras em tons de Zinc, sem gradientes de preenchimento chamativos.

### Cenário 3: Navegação na Lista de Equipamentos de Alta Densidade
- **Dado** que o técnico acesse `/equipamentos`
- **Quando** a lista for carregada
- **Então** os equipamentos devem ser dispostos em linhas/blocos elegantes de alta densidade
- **E** a situação do equipamento deve ser identificada por um *Status Dot* discreto junto ao texto
- **E** os identificadores (Série e Patrimônio) devem estar em fonte monoespaçada legível
- **E** a animação de entrada deve ser rápida, suave e sem atrasos artificiais perceptíveis.

### Cenário 4: Visualização dos Detalhes e Linha do Tempo Técnica
- **Dado** que o técnico acesse `/equipamentos/:id`
- **Quando** visualizar o histórico de movimentações e manutenções
- **Então** os eventos devem ser estruturados em formato de timeline técnica com linha conectora vertical
- **E** os itens de manutenção devem ser listados de forma clara e limpa.

### Cenário 5: Preservação de Testes e Funcionalidades
- **Dado** que as modificações de design sejam implementadas
- **Quando** a suíte de testes automatizados do frontend for executada
- **Então** todos os testes (28/28) devem continuar passando com 100% de sucesso
- **E** nenhum fluxo de navegação, autenticação ou mutação de dados deve ser quebrado.

---

## 5. Invariantes de Integridade
- Todas as rotas (`/login`, `/dashboard`, `/equipamentos`, `/equipamentos/:id`) mantêm seus comportamentos e proteções de acesso por perfil intactos.
- Os seletores de teste (`data-testid`) e textos de botão essenciais para os testes existentes permanecem inalterados.
- Nenhum comportamento da API é alterado.
