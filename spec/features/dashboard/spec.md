# Especificação: Dashboard

## Visão Geral
Após o login, o sistema redireciona para a tela de dashboard, que funciona como um portal central de acesso aos módulos do sistema corporativo (sem exibição de métricas numéricas nesta fase).
- O **Técnico** verá o card de acesso rápido ao módulo de **Patrimônio / Equipamentos** e status operacional do sistema.
- O **Colaborador** verá mensagem institucional e status do sistema.

## Regras de Negócio & Restrições
- **RN-01:** Deverá ter um menu lateral à esquerda retrátil (que pode ser aberto e fechado), que ao abrir o dashboard estará recolhido por padrão.
- **RN-02:** Um usuário deverá ver apenas as informações e módulos pertinentes ao seu cargo/role (Técnico vs Colaborador). As informações de e-mail e perfil do usuário ficam disponíveis no rodapé do menu lateral.
- **RN-03:** O dashboard deve ter um design sóbrio, limpo e corporativo (paleta neutra escura, sem métricas ou contadores numéricos).
- **RN-04:** O menu lateral conterá a opção "Patrimônio" (exclusiva para a role Técnico).
- **RN-05:** Ao clicar no card de acesso de Equipamentos ou no item "Patrimônio" do menu lateral, o técnico é redirecionado para a tela `/equipamentos`.

## Cenários de Aceitação (BDD)

### Cenário 1: Acesso Inicial e Estrutura Sóbria (Técnico e Colaborador)
- **Dado** que o login foi realizado com sucesso
- **Quando** for feito o redirecionamento para o dashboard
- **Então** a página deve apresentar a visão do portal sem métricas numéricas
- **E** o menu lateral deve estar disponível e fechado por padrão.

### Cenário 2: Acesso ao Painel de Patrimônio (Role: Técnico)
- **Dado** que o usuário (Técnico) esteja na tela de dashboard
- **Quando** ele efetuar um clique no card de acesso de Equipamentos ou no menu "Patrimônio"
- **Então** o usuário será redirecionado para a tela de listagem de equipamentos (`/equipamentos`).

### Cenário 3: Visão Limitada (Role: Colaborador)
- **Dado** que um usuário com a role "Colaborador" entra na tela de dashboard
- **Quando** ele visualiza a tela
- **Então** ele deve ver a visão institucional restrita do colaborador
- **E** não deve visualizar o card de controle global de Equipamentos
- **E** não deve haver a opção "Patrimônio" no menu lateral.

## Considerações de Borda & Invariantes
- Nunca deve ser possível o acesso de um usuário sem a role técnico ao painel de controle de patrimônio.
