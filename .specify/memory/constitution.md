<!--
Sync Impact Report:
- Version change: 0.1.0 (unratified template) → 1.0.0 (ratified Spec Kit constitution)
- Modified principles: Formalized existing constitutional principles from GEMINI.md and spec/constituicao.md, reinforced with empirical findings from the repository audit.
- Added sections:
  * Core Principles (I. Preservação de Contratos Públicos, II. Arquitetura em Camadas e Desacoplamento Limpo, III. Persistência Exclusiva com SQLAlchemy 2.0 e Banimento de Raw SQL, IV. Controle Transacional Delimitado no Caso de Uso, V. Governança Estrita do Banco de Dados via Migrações Alembic, VI. Cobertura de Código de 100% e Quality Gates, VII. Escopo Estrito e Proibição de Refatorações Especulativas)
  * Stack Tecnológica e Padrões de Persistência
  * Procedimentos de Testes, Validação e CI/CD
  * Governance
- Removed sections: Template generic example placeholders.
- Follow-up TODOs: None. All principles and constraints are confirmed by code, tests, and repository configurations.
-->

# Comunica — Gestão de Patrimônio e Suporte Constitution

## Core Principles

### I. Preservação de Contratos Públicos e Compatibilidade Retroativa
Os contratos públicos da API HTTP (`/api/v1/`), payloads de resposta, esquemas DTO de validação e comportamentos de rotas existentes DEVEM ser preservados e mantidos retrocompatíveis. Nenhuma alteração de campos existentes, rotas ou contratos de autenticação (Cookies HttpOnly `access_token` / `refresh_token` e suporte a Bearer token) pode ser introduzida sem que uma especificação funcional prévia formalmente aprovada em `.spec/features/` justifique e oriente a mudança.
*Rationale:* Protege a estabilidade da aplicação cliente SPA React, evita quebras de integração e garante que as funcionalidades já entregues permaneçam operacionais.

### II. Arquitetura em Camadas e Desacoplamento Limpo
O sistema organiza-se estritamente em camadas com separação clara de responsabilidades:
1. `src/api/`: Adaptadores primários HTTP (FastAPI), roteamento, injeção de dependências e controle de acesso RBAC.
2. `src/use_cases/`: Casos de uso de negócio orquestrando fluxos, transações atômicas e regras de aplicação.
3. `src/domain/`: Modelos de dados e schemas de validação (Pydantic v2).
4. `src/infrastructure/`: Adaptadores secundários de persistência (Repositórios SQLAlchemy 2.0), exportadores de arquivos, parsers de planilhas e sementes de dados.
5. `src/core/`: Configurações centralizadas, conexões de banco e módulo de segurança criptográfica.

O domínio e os casos de uso NUNCA devem importar bibliotecas ou tipos de transporte HTTP (`fastapi`, `starlette`, `httpx`). Simplificações arquiteturais são aceitas apenas quando reduzem complexidade sem gerar acoplamento prejudicial entre camadas.
*Rationale:* Garante manutenibilidade, testabilidade unitária sem necessidade de mocks de infraestrutura e portabilidade dos componentes centrais.

### III. Persistência Exclusiva com SQLAlchemy 2.0 e Banimento de Raw SQL
O acesso e manipulação de dados no banco DEVE ocorrer exclusivamente por meio da API idiomática do SQLAlchemy 2.0 (ORM e Core declarativo). É ESTRITAMENTE PROIBIDO o uso de SQL puro (*raw SQL* via `text()`, `cursor.execute()` ou comandos DDL/DML em strings literais) no código da aplicação.
Entidades podem atuar diretamente como modelos de persistência. Para tipos de dados de rede, devem ser utilizados tipos abstratos e agnósticos a dialeto (`IPAddressType`, `MACAddressType` em `src/domain/models.py`) que compilam nativamente para `INET` e `MACADDR` no PostgreSQL e recaem com segurança para `String` em bancos de teste.
*Rationale:* Previne vulnerabilidades de injeção de SQL, viabiliza checagem estática de integridade relacional e assegura compatibilidade entre ambientes.

### IV. Controle Transacional Delimitado no Caso de Uso
O ciclo de vida da transação de banco de dados (`commit` e `rollback`) DEVE ser controlado unicamente no nível da operação, caso de uso ou rota HTTP.
Os repositórios (`src/infrastructure/repositories.py`) NUNCA devem executar `commit()` ou `rollback()` de forma autônoma. Seu papel restringe-se a compor consultas e registrar alterações na sessão ativa (`db.add()`, `db.flush()`). Operações que integrem um mesmo fluxo lógico (ex.: importação em lote com upsert de equipamentos, criação dinâmica de catálogos e registro de manutenções) DEVEM compartilhar a mesma transação e ser confirmadas ou revertidas conjuntamente em caso de erro.
*Rationale:* Evita persistências parciais, estados inconsistentes e preserva a atomicidade de regras de negócio complexas.

### V. Governança Estrita do Banco de Dados via Migrações Alembic
Toda alteração estrutural no banco de dados (criação de tabelas, exclusão de colunas, constraints e índices) DEVE ser implementada obrigatoriamente através de migrações versionadas no Alembic (`alembic/versions/`). É vedado o uso de `Base.metadata.create_all()` para atualizar esquemas em ambientes persistidos.
Toda migração DEVE ser idempotente e conter tanto a função `upgrade()` quanto a função `downgrade()`. As convenções de indexação existentes DEVEM ser seguidas:
- Unicidade permanente *case-insensitive* (`LOWER(col)`) para identificadores canônicos que permanecem reservados mesmo após soft delete (`patrimony_number`, `serial_number`, catálogos).
- Unicidade condicional parcial (`WHERE deleted_at IS NULL`) para identificadores operacionais reutilizáveis (`hostname`, `ip_address`, `mac_address`, `printer_identifier`).
- Bloqueio de concorrência otimista via coluna `version_id` em `Equipment`.
*Rationale:* Assegura reprodutibilidade, auditabilidade de histórico de schema e alinhamento transparente entre desenvolvimento, CI e produção.

### VI. Cobertura de Código de 100% e Quality Gates Inegociáveis
Todo código executável no backend DEVE possuir cobertura de testes automatizados de 100%, considerando linhas e branches (`--cov=src --cov-branch --cov-fail-under=100`).
São isentos dessa exigência códigos puramente declarativos ou estruturais sem lógica própria, como schemas Pydantic básicos. Quaisquer omissões de cobertura no `pyproject.toml` ou `vite.config.ts` DEVEM ser explícitas e formalmente justificadas com comentários. O pipeline de Integração Contínua (CI) do GitHub Actions bloqueia qualquer alteração que reduza a cobertura ou quebre tipagens estáticas (`tsc --noEmit`).
*Rationale:* Garante a sustentabilidade do código a longo prazo, protege fluxos críticos de autenticação e patrimônio contra regressões e assegura previsibilidade nos deploys.

### VII. Escopo Estrito e Proibição de Refatorações Especulativas
Qualquer implementação ou modificação deve ater-se com rigor ao escopo delimitado da tarefa ou especificação ativa.
É TERMINANTEMENTE PROIBIDO realizar refatorações amplas não solicitadas, deletar ou renomear arquivos e módulos fora do escopo, ou introduzir tecnologias e convenções novas sem fundamentação e aprovação prévia. Não inventar regras de negócio, tabelas de banco ou abstrações antecipadas (YAGNI).
*Rationale:* Reduz riscos de efeitos colaterais em módulos estáveis e foca o esforço técnico estritamente nas demandas priorizadas.

## Stack Tecnológica e Padrões de Persistência

A base técnica do projeto é padronizada e deve ser rigorosamente respeitada:

- **Backend:** Python 3.13+, FastAPI, SQLAlchemy 2.0 (ORM/Core), Alembic, Pydantic v2, uv, openpyxl, psycopg2-binary, Argon2-cffi (hashing de senhas), PyJWT (autenticação JWT) e Cryptography Fernet (para encriptação simétrica de dados sensíveis como `windows_product_key`).
- **Frontend:** React 18, TypeScript 5+, Vite, Tailwind CSS 3, Lucide React, Axios (configurado com `withCredentials: true`), React Router v7.
- **Banco de Dados:** PostgreSQL 16 (padrão obrigatório para desenvolvimento, homologação e produção). Instância SQLite in-memory é admitida única e exclusivamente como contingência rápida para execução de testes unitários locais onde o PostgreSQL não estiver acessível.
- **DevSecOps e Segurança de Execução:**
  - Build multi-stage enxuto em Dockerfiles.
  - Execução sob usuários não-privilegiados (`appuser` UID 10001 no backend e `nginx-unprivileged` porta 8080 no frontend).
  - Em produção, isolamento total das portas do banco (`5432`) e da API (`8000`) dentro da rede interna do Docker (`internal-net`), expondo unicamente o Nginx.
  - Sanitização obrigatória de entradas em planilhas para prevenir ataques de Formula Injection (CWE-1236).

## Procedimentos de Testes, Validação e CI/CD

O repositório opera sob a pirâmide de testes e validação contínua:

1. **Níveis de Teste:**
   - **Testes Unitários:** Validação exaustiva de regras de negócio, algoritmos de parser/exportação, validações de domínio e segurança em `tests/`.
   - **Testes de Integração e API:** Executados contra as rotas FastAPI utilizando `httpx.AsyncClient` e fixtures de isolamento transacional por savepoint.
   - **Testes End-to-End (E2E):** Suíte estruturada em 4 Tiers (`tests/e2e/`), executável através de `tests/e2e_runner.py`.
   - **Testes de Frontend:** Testes de componentes, hooks e fluxos com Vitest e React Testing Library (`frontend/src/__tests__/`), complementados por compilação TypeScript estrita (`npx tsc --noEmit`).
2. **Automação no GitHub Actions:**
   - O pipeline em `.github/workflows/ci.yml` executa automaticamente a cada `push` e em todo `pull_request` direcionado às branches `main` e `develop`.
   - Os jobs englobam: checagem de linter e formatação Backend (`ruff`), migrações Alembic no PostgreSQL 16, suíte Pytest com exigência de 100% de cobertura, checagem TypeScript e testes Vitest no Frontend, e compilação de imagens Docker.
3. **Sincronia Spec x Testes:**
   - Toda alteração ou introdução de especificação funcional em `.spec/features/` DEVE obrigatoriamente vir acompanhada da implementação dos testes automatizados correspondentes no mesmo ciclo de entrega.

## Governance

A Constituição do Projeto é o documento de maior hierarquia normativa e técnica do repositório:

1. **Soberania:** As diretrizes aqui firmadas sobrepõem-se a quaisquer especificações funcionais, planos de tarefas ou opiniões contextuais. Nenhum caso de uso pode violar os princípios constitucionais.
2. **Processo de Emenda:** Alterações nestes princípios exigem justificativa fundamentada, comprovação de que não há regressão de arquitetura e incremento semântico de versão da constituição:
   - **MAJOR:** Remoção ou quebra substancial de princípio de arquitetura, stack ou segurança.
   - **MINOR:** Adição de novo princípio, módulo ou ampliação de diretrizes técnicas.
   - **PATCH:** Esclarecimentos de redação, correção de tipografias ou ajustes não-normativos.
3. **Verificação Mandatória (Spec Kit):** Todo plano de implementação gerado pelo Spec Kit (`plan.md`) e todo conjunto de tarefas (`tasks.md`) DEVE ser auditado contra esta Constituição antes do início da codificação.
4. **Resolução de Conflitos:** Ao identificar conflito entre uma demanda funcional em `.spec/features/` e os princípios constitucionais, a implementação deve ser pausada e a divergência apontada formalmente para resolução antes de prosseguir.

**Version**: 1.0.0 | **Ratified**: 2026-08-13 | **Last Amended**: 2026-10-22
