# Research & Decisions: Padronização de Nomenclatura e Conformidade Constitucional

Este documento consolida as decisões técnicas tomadas para padronização integral de nomenclaturas no projeto, eliminando qualquer vestígio de termos legados e alinhando configurações Docker com a Constituição do Projeto.

---

## 1. Padronização de Redes Docker (`patrimonio_net`)

### Decisão
Substituir a referência `patrimonio-net` (com hífen) por `patrimonio_net` (com sublinhado) em todas as declarações de rede nos arquivos `docker-compose.yml` e `docker-compose.prod.yml`, tanto nas seções de serviços (`backend`, `frontend`, `postgres`) quanto na seção global `networks`.

### Rationale
A Constituição do Projeto define explicitamente:
> **Rede e Volumes Docker:** `patrimonio_net`, `patrimonio_data`

O uso de hífen gera divergência entre a especificação normativa e o arquivo de infraestrutura, além de causar inconsistência em scripts de inspeção (`docker network ls`, `docker network inspect patrimonio_net`).

### Alternativas Consideradas
- **Manter `patrimonio-net` com alias interno `name: patrimonio_net`**: Rejeitado pois mantém a dissonância cognitiva no código do Compose e pode induzir novos desenvolvedores a utilizar a versão com hífen.

---

## 2. Padronização de Volumes Persistentes Docker (`patrimonio_data`)

### Decisão
Unificar a chave do volume de persistência do PostgreSQL para `patrimonio_data` no `docker-compose.yml` e `docker-compose.prod.yml`, substituindo a declaração legada `postgres_data`.

### Rationale
No `docker-compose.yml` atual, a chave interna ainda constava como `postgres_data:` com mapeamento para `name: patrimonio_data`. Ao renomear a chave interna diretamente para `patrimonio_data`, elimina-se o intermediário e estabelece-se identidade única em todo o arquivo.

### Alternativas Consideradas
- **Manter chave `postgres_data` apenas mapeando o nome externo**: Rejeitado por deixar resquício de nomenclatura genérica não-padronizada.

---

## 3. Tratamento de Menções Normativas a Nomes Legados

### Decisão
O termo proibido `internal_management` / `internal-management` deve permanecer **exclusivamente** nas cláusulas normativas de governança da Constituição (`GEMINI.md` e `spec/constituicao.md`) onde a proibição é taxativamente descrita, sendo terminantemente banido de todo código executável, scripts, variáveis de ambiente, nomes de arquivos e documentações de usuário.

### Rationale
Para que um instrumento de governança (Constituição) e os linters/testes possam auditar e proibir um identificador legado, é imprescindível enunciar formalmente qual termo está sob embargo. Não se trata de uso funcional, mas de definição da regra de auditoria.

### Alternativas Consideradas
- **Substituir o termo proibido por máscara regex ou pseudônimo na Constituição**: Rejeitado, pois tornaria o texto regulatório ambíguo e impediria ferramentas de análise estática de validar a regra contra termos literais.

---

## 4. Higiene em Docstrings de Migrações do Banco

### Decisão
Ajustar a docstring do arquivo de migração `alembic/versions/97cfe449ece9_add_equipment_management_models.py` para alinhar a terminologia com o domínio canônico do Gerenciador de Patrimônio, preservando rigorosamente o identificador de revisão, a estrutura das funções `upgrade()` / `downgrade()` e as constraints já migradas.

### Rationale
Ajustar o texto da docstring não altera o hash de revisão do Alembic nem a integridade estrutural do banco, garantindo consistência documental e de busca no repositório.

### Alternativas Consideradas
- **Ignorar arquivos de migração antigos**: Embora não quebre a execução, deixaria termos descritivos em desacordo com o padrão canônico do sistema.
