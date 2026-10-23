# Plano de Tarefas: Tela de Login (Frontend React)

Este documento especifica o plano detalhado de implementação para a **Tela de Login** no Frontend React, mapeando cada requisito da especificação [`spec.md`](file:///home/gil/code/internal_management/spec/features/tela-de-login/spec.md) e cumprindo os princípios da [`constituicao.md`](file:///home/gil/code/internal_management/spec/constituicao.md).

---

## Mapeamento de Requisitos da Especificação

| Requisito / Regra | Descrição | Tarefa Correspondente |
|---|---|---|
| **RN-UI-01** | Design moderno, responsivo e adaptado para temas elegantes (Inter font, dark/light mode). | **TASK-UI-01**, **TASK-UI-03**, **TASK-UI-05** |
| **RN-UI-02** | Validação client-side dos campos Email e Senha (RN-03). | **TASK-UI-03** |
| **RN-UI-03** | Prevenção de duplo envio (`isSubmitting` com spinner) (RN-04). | **TASK-UI-03**, **TASK-UI-05** |
| **RN-UI-04** | Exibição de mensagem genérica para HTTP 401 (RN-05). | **TASK-UI-04**, **TASK-UI-05** |
| **RN-UI-05** | Alerta visual em destaque para bloqueio HTTP 429 por força bruta (RN-02). | **TASK-UI-04**, **TASK-UI-05** |
| **RN-UI-06** | Atualização do `AuthContext` e redirecionamento para `/dashboard` (RN-01). | **TASK-UI-02**, **TASK-UI-05** |
| **RN-UI-07** | Micro-interações, efeitos de brilho (*glow*), transições suaves no hover do botão e animação de entrada da tela. | **TASK-UI-01**, **TASK-UI-03** |

---

## Lista de Tarefas de Implementação

### Fase 1: Infraestrutura e Estado Global do Frontend
- [x] **TASK-UI-01: Configuração do ambiente Frontend React e Design System Base**
  - [x] Configurar estrutura do projeto React (Vite / React + TypeScript ou JavaScript, Tailwind ou Vanilla CSS conforme convenção).
  - [x] Definir tokens de design e animações (`index.css` com variáveis de cores, sombras de brilho `box-shadow: 0 0 15px ...`, transições suaves `transition: all 0.2s ease` e keyframes de `fadeIn`/`scaleUp`).
  - [x] *Critério de Aceite:* Estilos base, sombras de brilho e animações aplicados corretamente.

- [x] **TASK-UI-02: Cliente HTTP de API e Contexto de Autenticação (`AuthContext`)**
  - [x] Implementar cliente HTTP (Axios / Fetch Wrapper) com `withCredentials: true` / `credentials: 'include'` para envio dos Cookies HttpOnly.
  - [x] Criar `AuthContext` e hook `useAuth` gerenciando estado `user` (`id`, `email`, `role`), estado de carregamento e funções `login`, `logout` e `checkAuth`.
  - [x] *Critério de Aceite:* `useAuth` responde aos estados de autenticação e injeta dados no aplicativo.

---

### Fase 2: Componentes da Interface de Login
- [x] **TASK-UI-03: Componente do Formulário de Login (`LoginForm` com Micro-interações)**
  - [x] Criar campos de entrada com anel de foco (*ring/glow*) animado ao selecionar.
  - [x] Criar botão "Entrar" com efeito hover fluido (mudança de gradiente, elevação suave e iluminação *glow*).
  - [x] Adicionar suporte a estado `isSubmitting` (exibindo spinner de carregamento e desabilitando os campos).
  - [x] *Critério de Aceite:* Botão reage suavemente ao passar o mouse e valida entradas prevenindo reenvios.

- [x] **TASK-UI-04: Componente de Alerta de Erro e Bloqueio (`AlertBanner`)**
  - [x] Criar banner de mensagem para HTTP 401 ("Credenciais inválidas. Verifique seu email e senha.").
  - [x] Criar banner de destaque para HTTP 429 ("Acesso temporariamente bloqueado por motivos de segurança. Tente novamente em 15 minutos.").
  - [x] *Critério de Aceite:* Alertas renderizam com ícones e estilos apropriados de erro/aviso.

- [x] **TASK-UI-05: Integração da Página de Login (`LoginPage`)**
  - [x] Criar layout centralizado e responsivo da página de login com animação de entrada (*fade-in / scale-up*), marca da empresa, card elevado e formulário.
  - [x] Conectar o formulário à chamada `login(email, password)` da API e tratar redirecionamento para `/dashboard`.
  - [x] *Critério de Aceite:* Login bem-sucedido direciona para dashboard; falhas exibem alertas correspondentes.

---

### Fase 3: Suíte de Testes de Componentes e Integração Frontend
- [x] **TASK-UI-06: Suíte de Testes Frontend (React Testing Library / Vitest)**
  - [x] Criar testes cobrindo os 6 cenários BDD da especificação.
  - [x] Testar estados de validação, clique no botão de envio, prevenção de duplo clique, exibição de alerta 401 e 429.
  - [x] *Critério de Aceite:* 100% de cobertura nos componentes de login do frontend.
