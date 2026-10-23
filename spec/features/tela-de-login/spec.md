# Especificação: Tela de Login (Frontend React)

## Visão Geral
A funcionalidade de **Tela de Login** consiste na interface de usuário web (React.js) para autenticação no sistema de Gestão de Patrimônio e Suporte. Ela provê um formulário moderno, fluido, responsivo e seguro que consome a API de autenticação em `/api/v1/auth/login`, lida com validações client-side, previne envios duplos e gerencia o estado da sessão do usuário com Cookies HttpOnly.

## Regras de Negócio e UX (User Experience)
- **RN-UI-01 (Design Moderno & Responsivo):** A tela deve possuir estética moderna e profissional (dark/light mode ajustado, tipografia Inter/Outfit, gradientes suaves e micro-animações de entrada e foco).
- **RN-UI-02 (Validação Client-Side - RN-03):** O formulário deve validar a presença do email (em formato válido) e da senha. O botão "Entrar" deve permanecer desabilitado se os campos forem inválidos.
- **RN-UI-03 (Prevenção de Duplo Envio - RN-04 / Cenário 3):** Durante o processamento da requisição HTTP (`isSubmitting === true`), os campos de entrada e o botão de envio devem ser desabilitados e o botão deve exibir um indicador visual de carregamento (spinner).
- **RN-UI-04 (Tratamento de Credenciais Inválidas - RN-05 / Cenário 2):** Respostas HTTP `401 Unauthorized` devem exibir um alerta de erro amigável e genérico ("Credenciais inválidas. Verifique seu email e senha.").
- **RN-UI-05 (Tratamento de Rate Limit - RN-02 / Cenário 4):** Respostas HTTP `429 Too Many Requests` devem exibir um alerta em destaque avisando que o acesso a partir do IP está temporariamente bloqueado por motivos de segurança (tentar novamente em 15 minutos).
- **RN-UI-06 (Gerenciamento de Sessão & Redirecionamento - RN-01 / Cenário 1):** Em caso de resposta HTTP `200 OK`, a aplicação atualiza o estado global de autenticação (`AuthContext`) com os dados do usuário autenticado (`id`, `email`, `role`) e redireciona o usuário para o dashboard principal (`/dashboard`).
- **RN-UI-07 (Micro-interações e Fluidez Visual):** O botão de submissão e os campos interativos devem possuir transições físicas suaves (`transition: all 0.2s ease-in-out`). Ao passar o mouse (`:hover`), o botão de ação deve sofrer alteração sutil de tom/gradiente com efeito de brilho (*glow effect / box-shadow*) e leve elevação (*scale/translateY*), tornando a experiência de uso fluida e agradável. Os campos de texto devem exibir anel de foco (*ring/glow*) animado ao serem selecionados.

## Cenários de Aceitação (BDD)

### Cenário 1: Renderização inicial e animação da tela de login
- **Dado** que um usuário não autenticado navegue até a rota `/login`
- **Quando** a página for carregada
- **Então** a tela deve surgir com uma transição suave de entrada (*fade-in / scale-up*)
- **E** o formulário de login deve ser exibido centralizado com os campos limpos e foco inicial no campo de Email.

### Cenário 2: Validação de campos obrigatórios no frontend
- **Dado** que o usuário esteja na tela de login
- **Quando** o usuário tentar submeter o formulário sem preencher o email ou a senha
- **Então** a submissão deve ser bloqueada
- **E** mensagens de validação visual ("Email é obrigatório" / "Senha é obrigatória") devem ser apresentadas abaixo dos respectivos campos.

### Cenário 3: Interação visual no hover do botão de login
- **Dado** que o usuário esteja com o formulário válido
- **Quando** o ponteiro do mouse for posicionado sobre o botão "Entrar"
- **Então** o botão deve transicionar suavemente exibindo alteração de tom, elevação sutil e um efeito de brilho suave (*glow*), retornando ao estado normal ao sair.

### Cenário 4: Submissão bem-sucedida de login
- **Dado** que o usuário preencha um email e senha válidos
- **Quando** o usuário clicar em "Entrar"
- **Então** o estado `isSubmitting` deve ser ativado, desabilitando o formulário e exibindo um spinner
- **E** ao receber HTTP 200 da API, o contexto de autenticação deve ser atualizado e o usuário redirecionado para `/dashboard`.

### Cenário 5: Exibição de erro por credenciais inválidas (HTTP 401)
- **Dado** que o usuário envie credenciais incorretas
- **Quando** a API retornar HTTP 401
- **Então** o formulário deve ser reabilitado
- **E** uma mensagem de erro genérica ("Credenciais inválidas. Verifique seu email e senha.") deve ser exibida na tela.

### Cenário 6: Exibição de alerta de bloqueio por força bruta (HTTP 429)
- **Dado** que o IP do usuário tenha atingido o limite de 10 tentativas falhas
- **Quando** o usuário tentar realizar o login e a API retornar HTTP 429
- **Então** o formulário deve ser reabilitado
- **E** um banner de alerta vermelho/amarelo deve ser exibido informando sobre o bloqueio temporário por motivos de segurança.
