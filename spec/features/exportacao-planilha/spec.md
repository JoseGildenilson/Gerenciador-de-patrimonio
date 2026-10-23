# Especificação: Exportação de Equipamentos em Planilha Excel (.xlsx)

## 1. Visão Geral

A funcionalidade de **Exportação de Equipamentos** permite que usuários com papel de **Técnico** exportem os dados cadastrais e históricos do inventário de patrimônio em formato de planilha Excel (`.xlsx`). O arquivo gerado segue rigorosamente o layout, ordenação de colunas e identidade visual do modelo corporativo (`PATRIMÔNIO CTM.xlsx`), com estilização profissional, larguras de coluna ajustadas, congelamento da linha de cabeçalho e consolidação cronológica de manutenções.

---

## 2. Regras de Negócio e Requisitos

### 2.1 Controle de Acesso (RBAC)
- **RN-EXP-01:** O endpoint e a ação de exportação são restritos exclusivamente a usuários autenticados com a role `tecnico`. Solicitações de usuários com perfil `colaborador` devem ser recusadas com `HTTP 403 Forbidden`.

### 2.2 Escopo dos Dados & Filtragem
- **RN-EXP-02:** A exportação deve respeitar os mesmos parâmetros de filtro aplicados na consulta/listagem de equipamentos (`types`, `locations`, `statuses`, `patrimony_numbers`, `serial_numbers`, `product_numbers`, `search`).
- **RN-EXP-03:** Caso nenhum filtro esteja ativo, a exportação conterá todos os equipamentos cadastrados no banco de dados.

### 2.3 Formato do Arquivo e Estrutura de Abas
- **RN-EXP-04:** O arquivo gerado deve ser no formato Microsoft Excel (`.xlsx`) com codificação padrão e conter uma única aba principal intitulada **`Patrimônio`**.
- **RN-EXP-05:** O nome do arquivo gerado no download deve seguir a convenção dinâmica: `PATRIMONIO_YYYY-MM-DD_HHMM.xlsx` (onde `YYYY-MM-DD_HHMM` corresponde ao timestamp do momento da geração).

### 2.4 Mapeamento e Ordem das Colunas (13 Colunas Canônicas)
- **RN-EXP-06:** O arquivo gerado deve conter exatamente as seguintes 13 colunas na ordem estabelecida:
  1. `TIPO`: tipo do equipamento (`equipment_type`).
  2. `LOCALIZAÇÃO`: localização atual (`location`).
  3. `SITUAÇÃO`: situação operacional (`status`).
  4. `DESCRIÇÃO`: descrição ou especificação do equipamento (`description`).
  5. `Nº PATRIMÔNIO`: número de patrimônio (`patrimony_number`), ou célula vazia se ausente.
  6. `Nº SÉRIE`: número de série (`serial_number`), ou célula vazia se ausente.
  7. `MARCA`: fabricante ou marca (`brand`), ou célula vazia se ausente.
  8. `ÚLTIMA MANUTENÇÃO`: data da última intervenção técnica (`last_maintenance_at`), formatada como data no padrão `DD/MM/YYYY` ou vazia se ausente.
  9. `CHAVE WINDOWS`: chave de ativação do Windows (`windows_key`), ou célula vazia se ausente.
  10. `Nº PRODUTO`: part number ou código do produto (`product_number`), ou célula vazia se ausente.
  11. `HISTÓRICO DE MOVIMENTAÇÕES`: histórico consolidado de intervenções técnicas (ver RN-EXP-07), ou célula vazia se ausente.
  12. `HOSTNAME`: nome de rede da máquina (`hostname`), ou célula vazia se ausente.
  13. `OBSERVAÇÕES`: observações gerais (`notes`), ou célula vazia se ausente.

### 2.5 Consolidação do Histórico de Manutenções
- **RN-EXP-07:** Para a coluna `HISTÓRICO DE MOVIMENTAÇÕES`:
  - As manutenções cadastradas para o equipamento devem ser ordenadas cronologicamente.
  - Cada atendimento deve ser formatado em linha única contendo a data e descrição, incluindo itens realizados quando houver (ex.: `21/03/2022: Atualização do s.o e softwares padrão` ou `18/09/2026: Troca de SSD, Limpeza interna`).
  - Múltiplas manutenções para o mesmo equipamento devem ser separadas por quebra de linha (`\n`) na mesma célula.

### 2.6 Estilização Visual e Formatação da Planilha
- **RN-EXP-08:** O cabeçalho (Linha 1) deve possuir:
  - Fundo preenchido com azul ciano `#4DD0E1` (RGB: `FF4DD0E1`).
  - Texto em caixa alta e fonte nítida.
  - Alinhamento centralizado verticalmente e horizontalmente com altura adequada.
- **RN-EXP-09:** O cabeçalho deve ser fixado com congelamento da primeira linha (*Freeze Panes* em `A2`), permitindo que as colunas continuem visíveis ao rolar a página para baixo.
- **RN-EXP-10:** As larguras das colunas devem ser proporcionais e ajustadas para evitar que textos fiquem truncados (larguras mínimas: `TIPO: 16`, `LOCALIZAÇÃO: 20`, `SITUAÇÃO: 18`, `DESCRIÇÃO: 38`, `Nº PATRIMÔNIO: 16`, `Nº SÉRIE: 18`, `MARCA: 14`, `ÚLTIMA MANUTENÇÃO: 18`, `CHAVE WINDOWS: 32`, `Nº PRODUTO: 20`, `HISTÓRICO DE MOVIMENTAÇÕES: 45`, `HOSTNAME: 16`, `OBSERVAÇÕES: 45`).
- **RN-EXP-11:** As células devem ter quebra automática de texto (*Wrap Text*) habilitada e linhas de grade (*Gridlines*) visíveis.

### 2.7 Interface do Usuário (Frontend)
- **RN-EXP-12:** A tela de equipamentos (`/equipamentos`) deve exibir o botão **"Exportar Planilha"** no cabeçalho superior (ao lado dos botões *"Gerenciar Tags"* e *"Novo Equipamento"*).
- **RN-EXP-13:** O botão deve conter ícone representativo (ex.: `FileSpreadsheet` ou `Download`), exibir estado de desabilitado/carregando (*loading spinner*) durante a solicitação HTTP e disparar o download nativo do arquivo `.xlsx` no navegador com sucesso.

---

## 3. Contrato da API (Backend)

- **Endpoint:** `GET /api/v1/equipments/export`
- **Autenticação:** Exige Cookie HttpOnly `access_token` com role `tecnico`.
- **Query Parameters:**
  - `types`: `list[str]` (opcional)
  - `locations`: `list[str]` (opcional)
  - `statuses`: `list[str]` (opcional)
  - `patrimony_numbers`: `list[str]` (opcional)
  - `serial_numbers`: `list[str]` (opcional)
  - `product_numbers`: `list[str]` (opcional)
  - `search`: `str` (opcional)
  - `sort_by`: `str` (opcional, padrão: `created_at`)
  - `sort_order`: `str` (opcional, padrão: `desc`)
- **Headers de Resposta:**
  - `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  - `Content-Disposition: attachment; filename="PATRIMONIO_YYYY-MM-DD_HHMM.xlsx"`
- **Códigos de Resposta:**
  - `200 OK`: Stream binário da planilha gerada.
  - `401 Unauthorized`: Usuário não autenticado.
  - `403 Forbidden`: Usuário com role `colaborador`.

---

## 4. Cenários de Aceitação (BDD)

### Cenário 1: Exportação de todos os equipamentos sem filtros
- **Dado** que um usuário autenticado com perfil `tecnico` esteja na tela de equipamentos
- **E** nenhum filtro esteja selecionado
- **Quando** ele clicar no botão "Exportar Planilha"
- **Então** o sistema deve gerar um arquivo `.xlsx` contendo todos os equipamentos cadastrados no banco de dados
- **E** a planilha deve conter a aba "Patrimônio" com as 13 colunas estilizadas com fundo ciano `#4DD0E1` e congelamento na linha 1.

### Cenário 2: Exportação com filtros aplicados
- **Dado** que o técnico filtre a listagem por `Tipo: Notebook` e `Localização: TI`
- **Quando** ele clicar no botão "Exportar Planilha"
- **Então** o arquivo baixado deve conter apenas os equipamentos do tipo `Notebook` e localização `TI`
- **E** a contagem de linhas de dados deve coincidir com a quantidade filtrada.

### Cenário 3: Formatação correta do histórico de manutenções
- **Dado** que um equipamento possua 2 manutenções registradas:
  - 10/01/2023: "Troca de HD por SSD" (itens: "SSD 480GB")
  - 15/05/2024: "Limpeza interna e troca de pasta térmica"
- **Quando** a planilha for exportada
- **Então** a célula da coluna "HISTÓRICO DE MOVIMENTAÇÕES" desse equipamento deve conter as duas manutenções separadas por quebra de linha em ordem cronológica.

### Cenário 4: Bloqueio de acesso para Colaborador (RBAC)
- **Dado** que um usuário com a role `colaborador` tente acessar `GET /api/v1/equipments/export`
- **Então** a requisição deve ser rejeitada imediatamente com `HTTP 403 Forbidden`.

### Cenário 5: Interface e Feedback no Frontend
- **Dado** que o técnico clique em "Exportar Planilha"
- **Quando** a requisição estiver em andamento
- **Então** o botão deve apresentar estado de carregamento com spinner
- **E** ao concluir com sucesso, o download do arquivo `.xlsx` deve ser iniciado automaticamente no navegador.
