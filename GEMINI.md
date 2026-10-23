# Instruções para o Gemini / Antigravity

## 1. Modo de Operação — SDD

Este projeto segue a metodologia **Spec-Driven Development (Spec-Anchored)**.

As especificações são a fonte de verdade para o comportamento esperado do sistema.

### Regras obrigatórias
- NUNCA implemente uma feature sem uma especificação correspondente.
- NUNCA pule a criação ou atualização do `spec.md`.
- NUNCA pule a criação ou atualização do `tasks.md`.
- Antes de implementar uma feature, verifique se `spec.md` e `tasks.md` estão consistentes com a Constituição do Projeto.
- Se uma especificação entrar em conflito com este arquivo, a este arquivo deve prevalecer, e o conflito deve ser identificado antes da implementação.
- Não invente requisitos funcionais que não estejam definidos na especificação. Quando houver ambiguidade, questione antes de implementar.
- Ao identificar uma decisão técnica que possa afetar as regras da Constituição, sinalize a necessidade de revisão antes de introduzir uma nova convenção.

### Fluxo esperado

Para uma nova feature ou alteração significativa:

1. Consultar a especificação existente da feature em `.spec/features/`.
2. Criar ou atualizar `spec.md` utilizando BDD quando aplicável.
3. Criar ou atualizar `tasks.md`.
4. Implementar a feature seguindo as especificações e a Constituição.
5. Criar ou atualizar os testes automatizados correspondentes.
6. Executar a suíte de testes.
7. Confirmar que a implementação atende às especificações antes de considerá-la concluída.

---

# 2. Visão do Projeto

## Gestão de Patrimônio e Suporte

### Problema

O controle atual de equipamentos, como computadores, monitores e periféricos, é realizado por meio de Google Sheets.

Esse processo dificulta:

- rastreamento do histórico de manutenção;
- controle estruturado dos ativos;
- preservação das informações;
- acompanhamento das intervenções técnicas;
- formalização das solicitações de suporte.

### Objetivo

Centralizar o inventário de ativos e o histórico de intervenções técnicas em um sistema web estruturado, reduzindo a dependência de planilhas e processos informais.

### Escopo inicial

- **Fase 1 — MVP:** Gestão e cadastro de patrimônio, incluindo ativos, localização, status e histórico de manutenção.
- **Fase 2 — Futuro:** Módulo de chamados/tickets integrado ao sistema.
- **Fase 3 — Futuro:** Importação em lote por CSV e dashboard.

### Usuários-alvo

- **Técnicos de TI:** gerenciam o inventário e registram manutenções.
- **Colaboradores:** consultam seus equipamentos e podem realizar solicitações de suporte.

---

# 3. Constituição do Projeto

## Stack Técnica

- **Backend:** Python 3.13 + FastAPI.
- **Frontend:** React.js.
- **Banco de dados:** PostgreSQL.
- **ORM/Database Toolkit:** SQLAlchemy 2.0.
- **Migrations:** Alembic.
- **Testes:** Pytest.
- **Gerenciamento de pacotes:** uv.

## Princípios de Código

1. Simplificações arquiteturais são permitidas quando reduzirem complexidade sem comprometer a separação de responsabilidades. Exceções que introduzam acoplamento entre camadas devem ser explicitamente justificadas.
2. O domínio pode utilizar bibliotecas de apoio à modelagem e validação, desde que essas bibliotecas não introduzam dependência de infraestrutura, transporte ou frameworks específicos.
3. Não haverá uma lista fixa de bibliotecas permitidas ou proibidas. Uma biblioteca pode ser utilizada desde que seja considerada adequada e útil ao problema, após avaliação breve do desenvolvedor.
4. Todo código executável DEVE possuir cobertura de testes automatizados de 100%, considerando linhas e branches. São isentos dessa exigência códigos puramente declarativos ou estruturais que não possuam comportamento próprio a ser validado, como schemas Pydantic e definições equivalentes. As exclusões de cobertura devem ser explícitas e justificadas.

## Manutenção

- Cada componente deve ser testado no nível arquitetural adequado ao seu comportamento. Regras de domínio e lógica de aplicação devem possuir testes unitários. Componentes que dependam de infraestrutura devem possuir testes de integração quando necessário. Interfaces HTTP devem possuir testes de API quando aplicável.
- Todo código executável deve ser exercitado por testes automatizados adequados.
- Testes de integração que envolvam persistência DEVEM utilizar uma instância isolada e descartável do mesmo sistema de banco de dados utilizado pela aplicação. O banco deve ser inicializado a partir das migrations do projeto antes da execução dos testes.
- Testes de API devem validar o comportamento exposto pelas interfaces HTTP e podem utilizar dependências reais ou isoladas conforme o comportamento que se pretende validar.

## Banco de Dados

- Entidades podem ser utilizadas diretamente como modelos de persistência quando o acoplamento ao SQLAlchemy não comprometer a separação das regras de negócio ou gerar dependências arquiteturais prejudiciais.
- O projeto utilizará SQLAlchemy 2.0 para acesso ao banco de dados. O SQLAlchemy ORM será o padrão para persistência, enquanto o SQLAlchemy Core poderá ser utilizado quando oferecer uma solução mais adequada para operações específicas. SQL puro (raw SQL) não será utilizado.
- A transação deve ser controlada no nível da operação ou caso de uso. Repositories não devem executar `commit` ou `rollback` de forma independente. Operações que façam parte do mesmo caso de uso devem compartilhar a mesma transação e ser confirmadas ou revertidas conjuntamente.

## Integração Contínua

- Os testes automatizados DEVEM ser executados automaticamente no GitHub Actions a cada push nas branches `develop` e `main`.
- Os testes automatizados DEVEM ser executados automaticamente em pull requests direcionados da branch `develop` para a branch `main`.
- Toda alteração nas especificações funcionais em `.spec/features/` DEVE vir acompanhada da atualização correspondente dos testes automatizados no mesmo Pull Request.