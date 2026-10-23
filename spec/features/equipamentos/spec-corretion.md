# Especificação: Melhorias do Dashboard de Equipamentos

## 1. Objetivo

Esta especificação define as melhorias da tela de equipamentos após a implementação da primeira versão do sistema de patrimônio.

As melhorias têm como objetivo:

* tornar a pesquisa e filtragem mais eficiente;
* melhorar a hierarquia visual das informações;
* facilitar a leitura dos equipamentos;
* permitir edição completa dos dados;
* melhorar o gerenciamento do histórico de manutenções;
* aprimorar a tela de cadastro;
* melhorar a navegação entre Dashboard, equipamentos e detalhes.

As regras e comportamentos já definidos na especificação original permanecem válidos, salvo quando substituídos ou complementados neste documento.

---

# 2. Tela de equipamentos

## 2.1. Estrutura geral

A tela continuará sendo composta por:

* cabeçalho;
* botão para retornar ao Dashboard principal;
* barra de filtros sempre visível;
* ordenação;
* lista de equipamentos;
* paginação.

A lista continuará utilizando aproximadamente **25 equipamentos por página**, mantendo esse valor fixo.

---

# 3. Filtros de pesquisa

## 3.1. Filtros disponíveis

A tela deverá manter os seguintes filtros:

* Tipo;
* Localização;
* Situação;
* Nº Patrimônio;
* Nº Série;
* Nº Produto.

Além deles, continuará disponível uma **busca textual geral**.

---

## 3.2. Seleção múltipla

Todos os filtros deverão aceitar múltiplos valores.

Exemplo:

**Nº Série**

`[123 ×] [432 ×]`

O resultado deverá apresentar equipamentos que correspondam a qualquer um dos valores selecionados.

Exemplo:

`Nº Série = 123 OU 432`

O mesmo comportamento deverá existir para os demais campos.

---

## 3.3. Pesquisa dentro do filtro

Os filtros deverão utilizar comportamento semelhante ao Google Sheets.

Ao clicar em um filtro, será apresentado um componente de seleção contendo:

* campo de pesquisa;
* lista de opções;
* opções selecionadas;
* possibilidade de selecionar várias opções;
* opção de remover uma seleção;
* botão para desmarcar todas as opções.

Exemplo:

```text
┌──────────────────────────────┐
│ 🔎 Pesquisar...              │
├──────────────────────────────┤
│ ☑ Notebook                   │
│ ☑ Desktop                    │
│ ☐ Monitor                    │
│ ☐ Impressora                 │
│ ☐ Celular                    │
├──────────────────────────────┤
│ Limpar seleção               │
└──────────────────────────────┘
```

O usuário deverá poder pesquisar uma opção pelo nome e selecioná-la sem precisar percorrer toda a lista.

---

## 3.4. Estado dos filtros

Quando houver valores selecionados, o próprio filtro deverá informar visualmente que está ativo.

Exemplo:

`Tipo (2)`

ou:

`Tipo: Notebook, Desktop`

A interface deverá evitar ocupar espaço excessivo quando houver muitos valores selecionados.

---

## 3.5. Limpeza do filtro

Cada filtro deverá possuir uma ação:

**Desmarcar tudo**

Essa ação deverá remover somente as seleções daquele filtro.

Também poderá existir uma ação global:

**Limpar filtros**

que remove todas as seleções existentes na barra de filtros.

---

## 3.6. Combinação de filtros

Os filtros deverão funcionar com a seguinte lógica:

### Entre valores do mesmo filtro:

**OU**

### Entre filtros diferentes:

**E**

Exemplo:

**Tipo**

* Notebook
* Desktop

**Localização**

* Comunicação
* Rádio Produção

O resultado deverá ser:

> `(Notebook OU Desktop) E (Comunicação OU Rádio Produção)`

---

# 4. Bloco do equipamento

## 4.1. Estrutura

Os equipamentos continuarão sendo exibidos em **blocos empilhados verticalmente**, mantendo a proposta visual da primeira versão.

Cada bloco deverá apresentar uma estrutura consistente, organizada e previsível.

As informações serão apresentadas dentro de pequenos blocos internos, com pouco destaque visual, apenas o suficiente para facilitar a leitura.

---

## 4.2. Hierarquia das informações

O nome do equipamento continuará sendo o elemento de maior destaque.

Exemplo:

**💻 ThinkPad T480**

Abaixo dele, as informações principais serão distribuídas em pequenos blocos:

```text
┌───────────────┐  ┌───────────────┐  ┌──────────────────┐
│ PATRIMÔNIO    │  │ Nº SÉRIE      │  │ TIPO             │
│ 10342         │  │ PF123456      │  │ Notebook         │
└───────────────┘  └───────────────┘  └──────────────────┘
```

Outros dados:

```text
┌───────────────┐  ┌───────────────┐  ┌──────────────────┐
│ LOCALIZAÇÃO   │  │ SITUAÇÃO      │  │ ÚLTIMA MANUT.   │
│ Rádio Prod.   │  │ Em uso        │  │ 18/09/2026      │
└───────────────┘  └───────────────┘  └──────────────────┘
```

---

## 4.3. Tamanho fixo dos blocos internos

Os blocos internos deverão possuir dimensões e espaçamentos consistentes.

O tamanho não deverá variar significativamente de acordo com o tamanho do conteúdo.

Exemplo:

Um Nº Patrimônio curto:

`10342`

e um número de série maior:

`PF123456789AB`

deverão continuar respeitando a mesma estrutura visual.

O objetivo é criar uma leitura organizada e previsível independentemente do conteúdo.

---

## 4.4. Tipografia

Os nomes dos campos deverão possuir maior peso visual ou tamanho ligeiramente maior do que os valores, mas sem criar excesso de contraste.

Exemplo:

**PATRIMÔNIO**
10342

**Nº SÉRIE**
PF123456

A hierarquia tipográfica deverá facilitar a identificação rápida da informação sem transformar cada campo em um grande card.

---

## 4.5. Clique no equipamento

O clique em qualquer região do bloco deverá abrir a **tela dedicada de detalhes do equipamento**.

---

# 5. Dropdowns e Selects

## 5.1. Aparência

Os componentes de seleção deverão receber uma melhoria visual, mantendo uma aparência consistente com a aplicação.

Devem possuir:

* área de clique clara;
* indicação visual de abertura;
* busca interna quando houver muitas opções;
* lista organizada;
* estado selecionado;
* opção de criação de nova tag quando aplicável.

---

## 5.2. Seleção em filtros

Nos filtros, os Selects deverão permitir múltiplas seleções.

Nos formulários de cadastro e edição, os campos categóricos continuarão podendo utilizar seleção de uma única tag, conforme sua finalidade.

---

# 6. Navegação

## 6.1. Tela de equipamentos

A tela de equipamentos deverá possuir:

**← Voltar ao Dashboard**

Esse botão deverá levar diretamente ao Dashboard principal.

---

## 6.2. Tela de detalhes

A tela de detalhes deverá possuir:

**← Voltar para equipamentos**

O botão deverá levar o usuário novamente para a listagem de equipamentos.

A navegação não deverá levar diretamente ao Dashboard a partir da tela de detalhes.

---

# 7. Tela de detalhes do equipamento

## 7.1. Visualização

Todas as informações continuarão sendo apresentadas em **uma única aba/tela**.

Não haverá separação em abas como:

* Informações;
* Manutenções;
* Movimentações.

Os conteúdos serão organizados em seções dentro da mesma tela.

---

## 7.2. Hierarquia visual

As informações deverão possuir maior tamanho e visibilidade do que na tela de listagem.

Os nomes dos campos deverão utilizar:

* fonte mais grossa;
* tamanho ligeiramente maior;
* espaçamento adequado.

Os valores deverão permanecer claramente legíveis.

Exemplo:

**Nº PATRIMÔNIO**

# 10342

**Nº SÉRIE**

PF123456

**LOCALIZAÇÃO**

Rádio Produção

---

## 7.3. Edição do equipamento

A tela deverá possuir um único botão:

**Editar equipamento**

Ao clicar, todos os campos editáveis da tela deverão entrar em modo de edição simultaneamente.

O usuário poderá alterar qualquer informação permitida.

Exemplo:

```text
[ Editar equipamento ]
```

Ao entrar no modo de edição:

```text
[ Salvar alterações ] [ Cancelar ]
```

---

## 7.4. Cancelamento

Ao cancelar:

* nenhuma alteração deverá ser persistida;
* os valores originais deverão retornar;
* a tela deverá voltar ao modo de visualização.

---

## 7.5. Salvar alterações

Ao salvar:

* os dados deverão ser atualizados;
* a tela deverá voltar ao modo de visualização;
* os novos valores deverão aparecer imediatamente.

---

# 8. Histórico de manutenções

## 8.1. Conceito

O histórico continuará separado do histórico de movimentações.

A manutenção não deverá ser tratada como uma movimentação.

---

## 8.2. Registro de manutenção

Cada registro de manutenção deverá possuir:

* data;
* descrição da manutenção;
* itens realizados;
* observações, quando necessário.

Não será necessário manter um campo de "tipo de manutenção", como "preventiva" ou "corretiva".

O registro deverá ser simplesmente identificado como:

**Manutenção**

---

## 8.3. Vários itens na mesma manutenção

Uma única manutenção deverá permitir que o usuário registre vários itens realizados.

Exemplo:

### 18/09/2026 — Manutenção

* Troca de SSD;
* Limpeza interna;
* Troca de pasta térmica;
* Teste de memória RAM.

Assim, atividades realizadas no mesmo atendimento poderão ficar concentradas em um único registro.

---

## 8.4. Registros no mesmo dia

O sistema não deverá obrigatoriamente criar vários registros isolados para atividades feitas durante a mesma manutenção.

O usuário poderá utilizar um único registro para agrupar várias ações realizadas no mesmo atendimento.

O agrupamento deverá ser controlado pelo usuário, e não exclusivamente pela data.

Exemplo:

### 18/09/2026 — Manutenção

* Troca de SSD.

### 18/09/2026 — Manutenção

* Troca de teclado.

Esses dois registros ainda poderão existir separadamente caso representem atendimentos diferentes.

---

# 9. Edição do histórico

## 9.1. Editar manutenção

Todo registro de manutenção deverá possuir uma ação:

**Editar**

O usuário poderá alterar qualquer campo do registro.

Isso inclui:

* data;
* itens realizados;
* descrição;
* observações.

---

## 9.2. Exclusão

O usuário poderá excluir um registro de manutenção.

A exclusão deverá remover o registro do histórico daquele equipamento.

---

## 9.3. Última manutenção

Ao cadastrar uma nova manutenção, a data do registro deverá atualizar automaticamente:

**Última manutenção**

para a data daquela manutenção.

Exemplo:

`18/09/2026 — Manutenção`

Resultado:

`Última manutenção = 18/09/2026`

---

## 9.4. Edição independente da última manutenção

O campo **Última manutenção** continuará sendo editável separadamente.

Isso significa que o usuário poderá corrigir manualmente a data sem precisar alterar os registros do histórico.

---

# 10. Situação do equipamento

As regras anteriores permanecem:

O cadastro, edição ou exclusão de uma manutenção não deverá alterar automaticamente a situação do equipamento.

Exemplo:

`Situação = Em uso`

Após registrar uma manutenção:

`Situação = Em uso`

A situação somente mudará quando um usuário alterar manualmente o campo.

---

# 11. Movimentações

As regras existentes para movimentação permanecem.

Uma movimentação deverá registrar, quando aplicável:

* origem;
* destino;
* data;
* observação.

Ao salvar uma movimentação, a localização atual do equipamento deverá ser atualizada para o destino informado.

A movimentação não deverá alterar automaticamente a situação.

---

# 12. Tela de novo equipamento

## 12.1. Estrutura visual

A tela deverá apresentar o formulário ocupando a maior parte da área útil disponível.

Deverá existir uma margem externa suficiente para manter a percepção de que o formulário está dentro da própria aplicação, evitando que o conteúdo fique encostado nas bordas da tela.

---

## 12.2. Tamanho

O formulário deverá utilizar:

* labels maiores;
* campos maiores;
* espaçamento maior entre seções;
* maior área útil horizontal;
* maior área útil vertical.

O objetivo é melhorar a leitura e reduzir a sensação de formulário comprimido.

---

## 12.3. Estrutura

O formulário deverá continuar dividido em seções lógicas:

### Identificação

* Tipo;
* Descrição;
* Marca;
* Nº Produto;
* Nº Patrimônio;
* Nº Série.

### Localização

* Localização;
* Situação.

### Rede

* Hostname.

### Licenciamento

* Chave Windows.

### Manutenção

* Última manutenção.

### Observações

* Observações.

---

# 13. Chave Windows

A chave Windows continuará sendo exibida de forma mascarada.

Exemplo:

`••••••••••••••••••••`

Com botão:

**Mostrar**

Ao clicar, a chave será temporariamente exibida.

---

# 14. Paginação

A paginação continuará utilizando:

**25 equipamentos por página**

A quantidade será fixa nesta versão.

Ao trocar de página, os novos equipamentos deverão repetir a animação definida anteriormente.

---

# 15. Animação dos equipamentos

Ao carregar a lista:

* os equipamentos deverão entrar individualmente;
* a animação será da direita para a esquerda;
* haverá uma pequena diferença de tempo entre os blocos;
* a animação deverá ser suave;
* o efeito não deverá prejudicar a velocidade percebida da aplicação.

O mesmo comportamento deverá ocorrer ao trocar de página.

---

# 16. Regras de negócio adicionadas

### RN-09 — Filtro múltiplo

Todos os filtros deverão permitir múltiplos valores selecionados simultaneamente.

### RN-10 — Busca em filtros

Os filtros deverão permitir pesquisa textual das opções disponíveis antes da seleção.

### RN-11 — Desmarcar filtro

Cada filtro deverá possuir uma ação para remover todas as opções selecionadas naquele filtro.

### RN-12 — Combinação de filtros

Valores dentro do mesmo filtro deverão utilizar lógica OR, enquanto filtros diferentes deverão utilizar lógica AND.

### RN-13 — Estrutura visual dos equipamentos

Os blocos de equipamentos deverão utilizar uma estrutura interna padronizada, mantendo espaçamento e dimensões consistentes independentemente do tamanho dos valores.

### RN-14 — Edição completa

A tela de detalhes deverá permitir a edição dos campos do equipamento por meio de um único modo de edição.

### RN-15 — Manutenção agrupada

Um registro de manutenção poderá conter múltiplos itens realizados durante o mesmo atendimento.

### RN-16 — Edição de manutenção

Registros de manutenção deverão permitir edição completa após o cadastro.

### RN-17 — Exclusão de manutenção

Registros de manutenção poderão ser excluídos pelo usuário.

### RN-18 — Atualização automática da última manutenção

O cadastro de uma manutenção deverá atualizar automaticamente a data de última manutenção.

### RN-19 — Última manutenção independente

A data de última manutenção poderá ser alterada manualmente sem modificar o histórico.

### RN-20 — Navegação

A tela de equipamentos deverá possuir retorno para o Dashboard, enquanto a tela de detalhes deverá possuir retorno para a listagem de equipamentos.

### RN-21 — Situação manual

Nenhuma manutenção ou movimentação deverá alterar automaticamente a situação do equipamento.

---

# 17. Cenários de aceitação — BDD

## Cenário 1: Selecionar múltiplos valores em um filtro

**Dado** que o usuário esteja na tela de equipamentos
**Quando** abrir o filtro de Nº Série
**E** pesquisar pelo valor `123`
**E** selecionar `123`
**E** pesquisar pelo valor `432`
**E** selecionar `432`
**Então** o filtro deverá apresentar os dois valores selecionados
**E** a lista deverá exibir equipamentos com Nº Série `123` ou `432`.

---

## Cenário 2: Utilizar múltiplos filtros simultaneamente

**Dado** que existam filtros Tipo e Localização
**Quando** o usuário selecionar `Notebook` e `Desktop` em Tipo
**E** selecionar `Comunicação` e `Rádio Produção` em Localização
**Então** o sistema deverá retornar equipamentos que sejam Notebook ou Desktop
**E** estejam localizados em Comunicação ou Rádio Produção.

---

## Cenário 3: Limpar um filtro

**Dado** que um filtro possua múltiplos valores selecionados
**Quando** o usuário clicar em `Desmarcar tudo`
**Então** todas as seleções daquele filtro deverão ser removidas
**E** os demais filtros deverão permanecer inalterados.

---

## Cenário 4: Visualização do bloco do equipamento

**Dado** que existam equipamentos cadastrados
**Quando** a tela de equipamentos carregar
**Então** os equipamentos deverão aparecer em blocos empilhados
**E** cada bloco deverá apresentar seus principais dados em pequenos blocos internos
**E** os espaçamentos deverão permanecer consistentes independentemente do tamanho das informações.

---

## Cenário 5: Abrir detalhes do equipamento

**Dado** que o usuário esteja na tela de equipamentos
**Quando** clicar em um bloco de equipamento
**Então** deverá ser aberta a tela dedicada daquele equipamento
**E** todas as informações deverão estar disponíveis na mesma tela.

---

## Cenário 6: Editar equipamento

**Dado** que o usuário esteja nos detalhes de um equipamento
**Quando** clicar em `Editar equipamento`
**Então** todos os campos editáveis deverão entrar em modo de edição
**E** o usuário deverá poder alterar qualquer informação permitida
**E** deverá existir a opção de salvar ou cancelar.

---

## Cenário 7: Cancelar edição

**Dado** que o usuário tenha alterado informações de um equipamento
**Quando** clicar em `Cancelar`
**Então** as alterações não deverão ser persistidas
**E** os valores anteriores deverão permanecer.

---

## Cenário 8: Salvar edição

**Dado** que o usuário tenha alterado informações
**Quando** clicar em `Salvar alterações`
**Então** as alterações deverão ser persistidas
**E** a tela deverá retornar ao modo de visualização.

---

## Cenário 9: Registrar manutenção com vários itens

**Dado** que o usuário esteja no histórico de um equipamento
**Quando** cadastrar uma manutenção em `18/09/2026`
**E** adicionar os itens `Troca de SSD`, `Limpeza interna` e `Troca de pasta térmica`
**Então** deverá ser criado um único registro de manutenção contendo todos os itens.

---

## Cenário 10: Atualizar última manutenção

**Dado** que o equipamento possua última manutenção em `05/08/2026`
**Quando** o usuário cadastrar uma nova manutenção em `18/09/2026`
**Então** a data de última manutenção deverá passar para `18/09/2026`.

---

## Cenário 11: Editar manutenção

**Dado** que exista uma manutenção cadastrada
**Quando** o usuário clicar em `Editar`
**Então** deverá ser possível alterar qualquer informação do registro
**E** salvar a alteração.

---

## Cenário 12: Excluir manutenção

**Dado** que exista uma manutenção cadastrada
**Quando** o usuário selecionar `Excluir`
**Então** o registro deverá ser removido do histórico do equipamento.

---

## Cenário 13: Situação não alterada automaticamente

**Dado** que o equipamento esteja com situação `Em uso`
**Quando** uma manutenção for registrada
**Então** a situação deverá continuar como `Em uso`.

---

## Cenário 14: Voltar para equipamentos

**Dado** que o usuário esteja na tela de detalhes
**Quando** clicar em `Voltar para equipamentos`
**Então** deverá retornar para a listagem de equipamentos.

---

## Cenário 15: Voltar para Dashboard

**Dado** que o usuário esteja na tela de equipamentos
**Quando** clicar em `Voltar ao Dashboard`
**Então** deverá retornar ao Dashboard principal.

---

## Cenário 16: Entrada dos equipamentos

**Dado** que a tela de equipamentos seja carregada
**Quando** os resultados forem exibidos
**Então** os blocos deverão aparecer individualmente da direita para a esquerda
**E** deverá existir uma pequena diferença temporal entre as entradas
**E** o mesmo comportamento deverá ocorrer ao trocar de página.
