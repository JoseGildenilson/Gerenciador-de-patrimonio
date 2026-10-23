# Especificação: Gestão de Equipamentos (Patrimônio) - Versão Final e Atualizada

## Visão Geral
A funcionalidade de **Gestão de Equipamentos** centraliza todo o controle de patrimônio da organização. Permite exclusivamente aos usuários com papel de **Técnico** listar, filtrar por múltiplos critérios, ordenar, cadastrar, visualizar detalhes em tela única, editar dados cadastrais e gerenciar históricos de movimentações e manutenções (com inclusão de múltiplos itens, edição e exclusão).

---

## Regras de Negócio & Restrições

### 1. Listagem & Estrutura Visual dos Equipamentos
- **RN-EQ-01 (Paginação e Animação de Entrada):**
  - A listagem apresenta aproximadamente 25 equipamentos fixos por página.
  - Ao carregar a lista ou trocar de página, os blocos de equipamentos entram individualmente da direita para a esquerda (*staggered slide-in*), com uma sutil diferença de tempo entre eles, produzindo efeito fluido.
- **RN-EQ-02 (Layout Horizontal Limpo, Tipografia Refinada e Alto Contraste com o Fundo):**
  - Os equipamentos são exibidos em blocos empilhados com layout horizontal limpo, respiro interno em relação às bordas (`p-5 sm:px-6 sm:py-5`), espaçamento amplo entre cards (`space-y-4 sm:space-y-5`) e container de ícone balanceado (`p-3 shadow-inner`).
  - O nome/descrição do equipamento possui tipografia refinada e proporcional (`text-sm sm:text-base font-bold text-white`), acompanhado de tags e metadados inline legíveis (*Localização com Ícone*, *Situação com Ícone*, *Patrimônio*, *Nº Série*). A data de última manutenção é destacada no lado direito.
  - Os blocos possuem **bordas duplas espessas (`border-2 border-slate-700/90`)**, **sombras de alto relevo (`shadow-xl shadow-black/50`)** e **cores intercaladas (*zebra striping*)** entre itens pares (`bg-slate-900`) e ímpares (`bg-slate-900/60`), descolando os blocos com nitidez do fundo escuro (`bg-slate-950`).
  - O clique em qualquer região do bloco abre a tela dedicada de detalhes do equipamento.

### 2. Filtros de Pesquisa Avançados (Estilo Google Sheets & Seleção Múltipla)
- **RN-EQ-03 (Filtros Múltiplos):**
  - Todos os filtros de seleção (`Tipo`, `Localização`, `Situação`) e textuais (`Nº Patrimônio`, `Nº Série`, `Nº Produto`) aceitam múltiplos valores simultâneos.
  - A busca textual geral continua disponível para pesquisa por substring em múltiplos campos.
- **RN-EQ-04 (Componente de Filtro com Busca Interna & Desmarcar Tudo):**
  - Ao clicar em um filtro, um painel estilo Google Sheets é aberto contendo: campo de pesquisa interna, lista de opções com checkboxes, indicador de itens selecionados e o botão "Desmarcar tudo" (removendo seleções daquele filtro específico).
  - O cabeçalho do filtro exibe o contador/estado visual (ex: `Tipo (2)`).
  - Mantida a ação global "Limpar filtros" para zerar todas as seleções da barra.
- **RN-EQ-05 (Combinação Lógica de Filtros):**
  - Valores dentro do **mesmo filtro** utilizam lógica **OR** (ex.: `Tipo = Notebook OU Desktop`).
  - Filtros **diferentes** utilizam lógica **AND** (ex.: `(Notebook OU Desktop) E (Comunicação OU Rádio Produção)`).

### 3. Navegação
- **RN-EQ-06 (Fluxo de Navegação Claro):**
  - Na tela de listagem de equipamentos: botão **"← Voltar ao Dashboard"** direciona para o Dashboard principal (`/dashboard`).
  - Na tela de detalhes do equipamento: botão **"← Voltar para equipamentos"** direciona para a listagem (`/equipamentos`).

### 4. Tela de Detalhes em Única Tela & Modo de Edição em Lote
- **RN-EQ-07 (Tela Única sem Abas de Informação):**
  - Todas as informações do equipamento (Identificação, Estado Atual, Técnica/Licença e Históricos) são apresentadas em uma **única tela**, organizadas por seções verticais legíveis (sem abas para separar informações principais).
- **RN-EQ-08 (Modo de Edição em Lote):**
  - A tela de detalhes possui um único botão **"Editar equipamento"**.
  - Ao clicar, todos os campos editáveis entram em modo de edição simultaneamente, exibindo os botões **"Salvar alterações"** e **"Cancelar"**.
  - No cancelamento, os valores anteriores retornam. Ao salvar, as alterações são persistidas no banco e a tela volta ao modo de visualização.

### 5. Histórico de Manutenção Agrupado, Editável e Excluível
- **RN-EQ-09 (Sem Tipo de Manutenção e Suporte a Múltiplos Itens):**
  - O histórico não diferencia "tipo de manutenção" (como preventiva/corretiva), sendo identificado apenas como **Manutenção**.
  - Um único registro de manutenção permite cadastrar/agrupar uma lista de múltiplos itens realizados (ex.: `* Troca de SSD`, `* Limpeza interna`, `* Troca de pasta térmica`).
- **RN-EQ-10 (Edição e Exclusão de Manutenções):**
  - Cada registro de manutenção no histórico possui opções para **Editar** (alterar data, itens realizados, descrição e observações) e **Excluir** (remover o registro do histórico).
- **RN-EQ-11 (Última Manutenção Automática e Independente):**
  - O cadastro ou edição de uma manutenção atualiza automaticamente o campo "Última manutenção" para a data informada.
  - O campo "Última manutenção" permanece editável de forma independente para correções históricas pontuais.
- **RN-EQ-12 (Independência da Situação):**
  - Nenhuma manutenção ou movimentação altera automaticamente a situação do equipamento (ex: `Em uso`). A alteração de situação só ocorre por ação manual explícita do Técnico.

### 6. Tela de Cadastro Ampla & Licenciamento
- **RN-EQ-13 (Formulário de Cadastro Amplo):**
  - A tela/modal de novo equipamento utiliza áreas úteis maiores (labels maiores, inputs mais amplos, espaçamentos generosos), organizados em seções lógicas: Identificação, Localização/Situação, Rede, Licenciamento, Manutenção e Observações.
- **RN-EQ-14 (Proteção da Chave Windows):**
  - Exibida mascarada (`••••••••••••••••`) com botão "Mostrar/Ocultar" para revelação temporária.

### 7. Constraints DB & RBAC
- **RN-EQ-15 (Unicidade no DB):**
  - `serial_number`, `patrimony_number` (se informado) e `hostname` (se informado) devem ser estritamente únicos (HTTP `400 Bad Request` em duplicidade).
- **RN-EQ-16 (Controle de Acesso RBAC):**
  - Módulo restrito exclusivamente à role `tecnico` (HTTP `403 Forbidden` para colaboradores).

---

## Cenários de Aceitação (BDD)

### Cenário 1: Selecionar múltiplos valores em um filtro com busca interna
- **Dado** que o técnico abra o painel do filtro de `Nº Série`
- **Quando** pesquisar pelo valor `123` e selecioná-lo
- **E** pesquisar pelo valor `432` e selecioná-lo
- **Então** o filtro deve exibir o indicador visual `Nº Série (2)`
- **E** a lista deve exibir equipamentos que possuam o Nº Série `123` OU `432`.

### Cenário 2: Utilizar múltiplos filtros simultaneamente (Lógica OR e AND)
- **Dado** que o técnico selecione `Notebook` e `Desktop` em Tipo
- **E** selecione `Comunicação` e `Rádio Produção` em Localização
- **Então** o sistema deve retornar equipamentos que sejam `(Notebook OU Desktop) E (Comunicação OU Rádio Produção)`.

### Cenário 3: Desmarcar filtro individual
- **Dado** que o filtro de `Tipo` possua 3 opções selecionadas
- **Quando** o técnico clicar em `Desmarcar tudo` dentro do dropdown de `Tipo`
- **Então** todas as seleções de `Tipo` devem ser removidas
- **E** os demais filtros (ex: `Localização`) devem permanecer intactos.

### Cenário 4: Visualização limpa com nomes proporcionais, respiro interno e alto contraste
- **Dado** que a listagem seja carregada
- **Quando** os blocos de equipamentos forem exibidos
- **Então** cada bloco deve apresentar layout horizontal com nomes em tamanho proporcional (`text-sm sm:text-base font-bold`), respiro interno em relação às bordas (`p-5 sm:px-6 sm:py-5`), alto contraste com o fundo escuro (`border-2 border-slate-700/90`) e cores alternadas (*zebra striping*).

### Cenário 5: Edição completa em modo único na tela de detalhes
- **Dado** que o técnico esteja visualizando os detalhes de um equipamento em tela única
- **Quando** clicar em `Editar equipamento`
- **Então** todos os campos editáveis devem entrar em modo de edição simultaneamente
- **E** ao clicar em `Salvar alterações`, os novos dados devem ser persistidos e a tela voltar ao modo de visualização.

### Cenário 6: Registrar manutenção com múltiplos itens agrupados
- **Dado** que o técnico cadastre uma manutenção para o equipamento
- **Quando** inserir a data `18/09/2026` e a lista de itens `Troca de SSD`, `Limpeza interna` e `Troca de pasta térmica`
- **Então** deve ser criado um único registro no histórico agrupando todos os itens
- **E** a data de "Última manutenção" do equipamento deve ser atualizada para `18/09/2026`.

### Cenário 7: Editar e excluir registro de manutenção no histórico
- **Dado** que exista uma manutenção cadastrada no histórico do equipamento
- **Quando** o técnico clicar em `Editar` naquele registro
- **Então** ele deve poder alterar os itens e a data da manutenção
- **E** ao clicar em `Excluir`, o registro deve ser removido do histórico do equipamento.

### Cenário 8: Navegação explícita
- **Dado** que o técnico esteja na tela de equipamentos, ao clicar em `← Voltar ao Dashboard` deve navegar para `/dashboard`
- **Dado** que o técnico esteja na tela de detalhes, ao clicar em `← Voltar para equipamentos` deve navegar para `/equipamentos`.
