# Plano de Tarefas: Autenticação de Usuário

Este documento especifica o plano detalhado de implementação para a funcionalidade de **Autenticação de Usuário**, mapeando cada requisito da especificação [`spec.md`](file:///home/gil/code/internal_management/spec/features/autenticacao/spec.md) e cumprindo os princípios da [`constituicao.md`](file:///home/gil/code/internal_management/spec/constituicao.md).

---

## Mapeamento de Requisitos da Especificação

| Requisito / Regra | Descrição | Tarefa Correspondente |
|---|---|---|
| **RN-01** | Acesso Restrito via JWT em Cookie HttpOnly (`access_token` 15 min, `refresh_token` 24h). | **TASK-03**, **TASK-06**, **TASK-07**, **TASK-09** |
| **RN-02** | Bloqueio por IP (Rate Limit) após 10 falhas em 15 min via tabela PostgreSQL (HTTP 429). | **TASK-02**, **TASK-04**, **TASK-05**, **TASK-06** |
| **RN-03** | Validação obrigatória de formulário (Email e Senha). | **TASK-05**, **TASK-08** |
| **RN-04** | Prevenção de duplo envio durante processamento ativo no frontend. | **TASK-08** |
| **RN-05** | Mensagem de erro genérica em falhas de credenciais (HTTP 401 sem revelar campo). | **TASK-05**, **TASK-06**, **TASK-08** |
| **RN-06** | Claim `role` (`"tecnico"` \| `"colaborador"`) inclusa no payload do token JWT. | **TASK-02**, **TASK-03**, **TASK-05** |
| **RN-07** | Criptografia de senhas obrigatoriamente via algoritmo **Argon2id**. | **TASK-01**, **TASK-03** |
| **Cenário 1** | Login com credenciais válidas, Cookies HttpOnly e claim `role`. | **TASK-03**, **TASK-05**, **TASK-06** |
| **Cenário 2** | Tentativa com credenciais inválidas + resposta 401 genérica + registro de falha por IP no DB. | **TASK-04**, **TASK-05**, **TASK-06**, **TASK-08** |
| **Cenário 3** | Prevenção de reenvio no frontend durante processamento. | **TASK-08** |
| **Cenário 4** | Bloqueio por excesso de tentativas por IP (11ª tentativa bloqueada com HTTP 429). | **TASK-04**, **TASK-05**, **TASK-06**, **TASK-08** |
| **Cenário 5** | Renovação de sessão via `POST /api/v1/auth/refresh` emitindo novo `access_token`. | **TASK-03**, **TASK-06**, **TASK-09** |

---

## Lista de Tarefas de Implementação

### Fase 1: Infraestrutura e Configuração Base (Backend)
- [x] **TASK-01: Configuração do ambiente e dependências do Backend**
  - [x] Configurar `pyproject.toml` com FastAPI, Uvicorn, SQLAlchemy 2.0, Alembic, Pytest, Pytest-cov, Argon2id (`pwdlib[argon2]` / `passlib[argon2]`), PyJWT / `python-jose` e `uv`.
  - [x] Configurar estrutura básica de diretórios (`src/core`, `src/domain`, `src/infrastructure`, `src/api`).
  - [x] Configurar ambiente de testes no `tests/conftest.py` com suporte a banco de dados PostgreSQL descartável/isolado.
  - *Critério de Aceite:* `uv run pytest` executa com sucesso na estrutura inicial.

- [x] **TASK-02: Entidade de Usuário e Tabela de Tentativas de Login (`login_attempts`)**
  - [x] Criar modelo SQLAlchemy para a tabela `users` (`id`, `email`, `hashed_password`, `role`, `is_active`, `created_at`).
  - [x] Criar modelo SQLAlchemy para a tabela `login_attempts` (`id`, `ip_address`, `attempted_at`, `success`).
  - [x] Criar migration inicial via Alembic para criar as tabelas no PostgreSQL.
  - *Critério de Aceite:* Migration executa e reverte sem erros.

---

### Fase 2: Regras de Negócio e Serviços do Domínio (Backend)
- [x] **TASK-03: Criptografia com Argon2id e Serviço de Tokens JWT (Access 15min / Refresh 24h)**
  - [x] Criar módulo de hash de senha utilizando **Argon2id** (`hash_password` e `verify_password`).
  - [x] Criar serviço JWT (`create_access_token` com TTL de 15 minutos e claim `role`; `create_refresh_token` com TTL de 24 horas; e `decode_token`).
  - [x] **Testes Unitários:** 100% de cobertura para hash Argon2id e emissão/validação de JWTs.

- [x] **TASK-04: Serviço de Proteção contra Força Bruta por IP no PostgreSQL (RN-02)**
  - [x] Criar serviço para consultar a quantidade de tentativas malsucedidas nos últimos 15 minutos por endereço IP (`ip_address`) na tabela `login_attempts`.
  - [x] Criar função para registrar tentativa de login (sucesso/falha) associada ao IP.
  - [x] **Testes Unitários & Integração:** Cobertura 100% demonstrando bloqueio por IP exatamente na 11ª tentativa e liberação após a janela de 15 minutos.

- [x] **TASK-05: Caso de Uso de Autenticação (`AuthenticateUser`)**
  - [x] Validar que email e senha foram informados (RN-03).
  - [x] Verificar se o IP solicitante está temporariamente bloqueado por rate limit no banco (RN-02 / Cenário 4).
  - [x] Lançar exceção de bloqueio por rate limit (HTTP 429) se excedido.
  - [x] Validar existência do usuário e comparar a hash da senha (Argon2id).
  - [x] Registrar tentativa malsucedida no banco para o IP e lançar exceção genérica se credenciais forem inválidas (HTTP 401 / RN-05 / Cenário 2).
  - [x] Registrar tentativa bem-sucedida e retornar payload do usuário com tokens (Cenário 1 e RN-06).
  - [x] **Testes Unitários:** 100% de cobertura para todos os cenários e ramos condicionais.

---

### Fase 3: Interface de API HTTP (FastAPI)
- [x] **TASK-06: Endpoints HTTP de Autenticação e Cookies HttpOnly (`/login` e `/refresh`)**
  - [x] Criar Pydantic schemas (`LoginRequest`, `TokenResponse`, `UserResponse`, `ErrorResponse`).
  - [x] Implementar `POST /api/v1/auth/login` capturando o IP do cliente e definindo cookies `HttpOnly` seguros para `access_token` e `refresh_token`.
  - [x] Implementar `POST /api/v1/auth/refresh` para renovação do `access_token` a partir do `refresh_token` via Cookie.
  - [x] Implementar `POST /api/v1/auth/logout` limpando os cookies HttpOnly.
  - [x] Tratar exceção de credenciais inválidas retornando HTTP `401 Unauthorized` genérico.
  - [x] Tratar bloqueio por rate limit retornando HTTP `429 Too Many Requests`.
  - [x] **Testes de API:** Testar requisições HTTP para cenários 1, 2, 4 e 5 (cobertura 100%).

- [x] **TASK-07: Proteção de Rotas com Middleware/Dependency HTTP (RN-01)**
  - [x] Implementar dependência FastAPI (`get_current_user`) extraindo o `access_token` a partir do Cookie HttpOnly (ou header `Authorization`).
  - [x] Validar a presença e integridade do token e injetar as permissões (`role`).
  - [x] Criar endpoint de teste de rota protegida (`GET /api/v1/auth/me`).
  - [x] **Testes de API:** Validar acesso negado sem token (401), com token expirado (401) e aceito com token válido (200).

---

### Fase 4: Frontend (React.js)
- [x] **TASK-08: Componente do Formulário de Login (RN-03, RN-04, RN-05)**
  - [x] Criar formulário de login com campos para Email e Senha (RN-03).
  - [x] Adicionar estado de submissão `isSubmitting` que desabilita os campos e o botão durante o envio (RN-04 / Cenário 3).
  - [x] Exibir mensagem de erro genérica em resposta a HTTP 401 (RN-05 / Cenário 2).
  - [x] Exibir mensagem de alerta de bloqueio temporário em resposta a HTTP 429 (Cenário 4).
  - [x] **Testes de Componente:** Testar interações, prevenção de duplo clique/envio e renderização de mensagens de erro.

- [x] **TASK-09: Gerenciamento de Sessão com Cookies HttpOnly e Interceptor HTTP (RN-01)**
  - [x] Configurar cliente HTTP (ex.: Axios / Fetch wrapper) com `withCredentials: true` para tráfego de Cookies HttpOnly.
  - [x] Implementar renovação automática de token no interceptor ao receber erro de token expirado (usando o endpoint `/refresh`).
  - [x] Redirecionar para a tela de login ao capturar falha definitiva de autenticação nas rotas protegidas.

---

### Fase 5: Cobertura de Testes e Validação Final
- [x] **TASK-10: Auditoria de Cobertura de Testes (100% Lines e Branches)**
  - [x] Rodar suíte de testes com Pytest (`uv run pytest --cov=src --cov-branch --cov-report=term-missing`).
  - [x] Garantir 100% de cobertura em código executável no backend.
  - [x] Validar execução de testes em ambiente limpo de PostgreSQL.
