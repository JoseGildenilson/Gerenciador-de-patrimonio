# Naming Policy & Repository Integrity Contract

Este contrato estabelece as regras de integridade léxica e validação de nomenclatura para o repositório **Gerenciador de Patrimônio**.

---

## 1. Regra de Ocorrência Zero para Nomes Legados

- **Termos Embargados**: `internal_management`, `internal-management`
- **Validação**: Nenhuma ocorrência desses termos é admitida no repositório, com a única exceção dos arquivos normativos onde a regra de proibição é formalizada:
  - `GEMINI.md`
  - `spec/constituicao.md`
  - `.specify/memory/constitution.md`
  - Registros de tarefas históricas já concluídas (ex.: `specs/001-gerenciamento-patrimonio/tasks.md` onde relata a exclusão do arquivo legadodb).
- **Proibição Absoluta**: É terminantemente proibido o aparecimento dos termos embargados em:
  - Arquivos de código (`src/**/*.py`)
  - Testes (`tests/**/*.py`, `frontend/src/**/*.test.tsx`)
  - Arquivos de infraestrutura (`Dockerfile*`, `docker-compose*.yml`, `nginx.conf`)
  - Configurações de pacotes (`pyproject.toml`, `package.json`)
  - Variáveis de ambiente (`.env*`)

---

## 2. Padrões de Identificadores Oficiais

| Escopo | Padrão Válido | Padrão Inválido |
|--------|---------------|-----------------|
| Rede Docker | `patrimonio_net` | `patrimonio-net`, `internal-net`, `app-network` |
| Volume Docker | `patrimonio_data` | `postgres_data`, `data_volume` |
| Pacote Python | `gerenciador_patrimonio` | `internal_management`, `app`, `sis_patrimonio` |
| Pacote Frontend | `patrimonio-frontend` | `internal-management-ui`, `frontend` |
| Banco de Dados Principal | `patrimonio_db` | `internal_management_db`, `patrimonio` |
| Banco de Testes | `test_patrimonio_db` | `test_db`, `internal_test_db` |
