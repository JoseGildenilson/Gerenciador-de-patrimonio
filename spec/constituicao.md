# Constituição do Projeto

Este documento define a Constituição do Projeto de Gestão de Patrimônio e Suporte. Suas regras são soberanas e prevalecem sobre quaisquer especificações funcionais ou decisões técnicas secundárias.

---

## 1. Stack Técnica

- **Backend:** Python 3.13 + FastAPI.
- **Frontend:** React.js.
- **Banco de Dados:** PostgreSQL.
- **ORM / Database Toolkit:** SQLAlchemy 2.0.
- **Migrations:** Alembic.
- **Testes:** Pytest.
- **Gerenciamento de Pacotes:** `uv`.

---

## 2. Princípios de Código

1. **Simplificação Arquitetural:** Simplificações arquiteturais são permitidas quando reduzirem a complexidade sem comprometer a separação de responsabilidades. Exceções que introduzam acoplamento entre camadas devem ser explicitamente justificadas.
2. **Isolamento do Domínio:** O domínio pode utilizar bibliotecas de apoio à modelagem e validação, desde que essas bibliotecas não introduzam dependência de infraestrutura, transporte ou frameworks específicos.
3. **Seleção de Bibliotecas:** Não haverá uma lista fixa de bibliotecas permitidas ou proibidas. Uma biblioteca pode ser utilizada desde que seja considerada adequada e útil ao problema, após avaliação breve do desenvolvedor.
4. **Cobertura de Testes (100%):** Todo código executável DEVE possuir cobertura de testes automatizados de 100%, considerando linhas e branches. São isentos dessa exigência códigos puramente declarativos ou estruturais que não possuam comportamento próprio a ser validado, como schemas Pydantic e definições equivalentes. As exclusões de cobertura devem ser explícitas e justificadas.

---

## 3. Manutenção e Testes

- **Níveis de Teste:** Cada componente deve ser testado no nível arquitetural adequado ao seu comportamento. Regras de domínio e lógica de aplicação devem possuir testes unitários. Componentes que dependam de infraestrutura devem possuir testes de integração quando necessário. Interfaces HTTP devem possuir testes de API quando aplicável.
- **Exercício de Código:** Todo código executável deve ser exercitado por testes automatizados adequados.
- **Isolamento da Persistência nos Testes:** Testes de integração que envolvam persistência DEVEM utilizar uma instância isolada e descartável do mesmo sistema de banco de dados utilizado pela aplicação. O banco deve ser inicializado a partir das migrations do projeto antes da execução dos testes.
- **Testes de API:** Testes de API devem validar o comportamento exposto pelas interfaces HTTP e podem utilizar dependências reais ou isoladas conforme o comportamento que se pretende validar.

---

## 4. Banco de Dados e Persistência

- **Modelos de Persistência:** Entidades podem ser utilizadas diretamente como modelos de persistência quando o acoplamento ao SQLAlchemy não comprometer a separação das regras de negócio ou gerar dependências arquiteturais prejudiciais.
- **Uso do ORM/Core:** O projeto utilizará SQLAlchemy 2.0 para acesso ao banco de dados. O SQLAlchemy ORM será o padrão para persistência, enquanto o SQLAlchemy Core poderá ser utilizado quando oferecer uma solução mais adequada para operações específicas. SQL puro (raw SQL) não será utilizado.
- **Controle de Transação:** A transação deve ser controlada no nível da operação ou caso de uso. Repositories não devem executar `commit` ou `rollback` de forma independente. Operações que façam parte do mesmo caso de uso devem compartilhar a mesma transação e ser confirmadas ou revertidas conjuntamente.

---

## 5. Integração Contínua (CI)

- **Automação no GitHub Actions:** Os testes automatizados DEVEM ser executados automaticamente no GitHub Actions a cada push nas branches `develop` e `main`.
- **Validação de Pull Requests:** Os testes automatizados DEVEM ser executados automaticamente em pull requests direcionados da branch `develop` para a branch `main`.
- **Sincronia Spec x Testes:** Toda alteração nas especificações funcionais em `.spec/features/` DEVE vir acompanhada da atualização correspondente dos testes automatizados no mesmo Pull Request.
