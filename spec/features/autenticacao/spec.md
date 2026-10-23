# Especificação: Autenticação de Usuário

## Visão Geral
O sistema deve permitir que usuários registrados se autentiquem de forma segura utilizando email e senha, garantindo a proteção contra ataques de força bruta através de rate limit por IP e o acesso restrito às funcionalidades do sistema via tokens JWT armazenados em Cookies HttpOnly.

## Regras de Negócio & Restrições
- **RN-01 (Acesso Restrito & Tokens JWT):** Rotas protegidas exigem um token de acesso JWT válido (`access_token` com TTL de 15 minutos). O token é transmitido e armazenado no navegador através de `HttpOnly Cookie`. A renovação da sessão é realizada através de um `refresh_token` (TTL de 24 horas / 1 dia).
- **RN-02 (Proteção contra Força Bruta por IP):** O sistema deve bloquear temporariamente solicitações de login após 10 tentativas malsucedidas associadas ao mesmo **endereço IP** em um intervalo de 15 minutos. Quando bloqueado, o sistema responde imediatamente com `HTTP 429 Too Many Requests`. O histórico de tentativas é mantido em tabela no banco de dados.
- **RN-03 (Validação de Formulário):** Solicitações de login só podem ser enviadas se email e senha forem fornecidos.
- **RN-04 (Prevenção de Duplo Envio):** O sistema deve ignorar ou desabilitar novas submissões enquanto uma validação de credencial já estiver em processamento no frontend.
- **RN-05 (Mensagem de Erro Genérica):** Por razões de segurança, falhas de autenticação não devem revelar se o erro foi no email ou na senha.
- **RN-06 (Perfil de Acesso - Role):** O payload do token JWT deve obrigatoriamente conter a claim `role` (`"tecnico"` | `"colaborador"`) do usuário autenticado para ser utilizada nos middlewares de autorização.
- **RN-07 (Criptografia de Senha):** As senhas dos usuários devem ser armazenadas obrigatoriamente utilizando o algoritmo hash **Argon2id**.

## Cenários de Aceitação (BDD)

### Cenário 1: Login com credenciais válidas
- **Dado** que o usuário forneça o email "tecnico@empresa.com" e a senha correta
- **Quando** a solicitação de autenticação for processada
- **Então** o sistema deve confirmar a autenticação com sucesso
- **E** definir cookies seguros `HttpOnly` com o `access_token` (15 min, contendo claim `role`) e o `refresh_token` (24h)
- **E** permitir acesso às rotas protegidas.

### Cenário 2: Tentativa de login com credenciais inválidas
- **Dado** que o usuário forneça um email ou senha incorretos
- **Quando** a solicitação de autenticação for processada
- **Então** a autenticação deve ser recusada com status HTTP 401
- **E** o sistema deve retornar uma mensagem genérica de credenciais inválidas sem especificar qual campo falhou
- **E** registrar a tentativa malsucedida associada ao IP do cliente no banco de dados.

### Cenário 3: Prevenção de reenvio durante processamento
- **Dado** que uma solicitação de autenticação esteja em andamento
- **Quando** o usuário tentar submeter o formulário novamente
- **Então** o sistema não deve disparar uma nova requisição até que a anterior seja concluída.

### Cenário 4: Bloqueio por excesso de tentativas por IP (Rate Limit - HTTP 429)
- **Dado** que foram registradas 10 tentativas malsucedidas vindas do mesmo endereço IP nos últimos 15 minutos
- **Quando** for feita a 11ª tentativa de login a partir desse mesmo IP
- **Então** o sistema deve recusar a operação imediatamente com status **HTTP 429 Too Many Requests**
- **E** retornar uma mensagem informando que o acesso está temporariamente bloqueado por motivos de segurança.

### Cenário 5: Renovação de sessão com Refresh Token
- **Dado** que um usuário possui um `refresh_token` válido armazenado em Cookie HttpOnly e um `access_token` expirado
- **Quando** for feita uma solicitação ao endpoint de renovação (`POST /api/v1/auth/refresh`)
- **Então** o sistema deve validar o `refresh_token` e emitir um novo `access_token` com TTL de 15 minutos em Cookie HttpOnly.
