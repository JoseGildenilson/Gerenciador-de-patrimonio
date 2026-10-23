# Especificação: Importação de Equipamentos via Planilha (.xlsx / .csv)

## 1. Visão Geral

Permite que técnicos de TI realizem a carga inicial ou atualizações em lote do inventário de equipamentos a partir de arquivos de planilha (`.xlsx`, `.xls` ou `.csv`). O sistema processa os dados de forma tolerante a inconsistências de formatação, sanitiza cabeçalhos e textos, preenche automaticamente tags dinâmicas e consolida notas e históricos de manutenção.

---

## 2. Regras de Negócio e Requisitos

### 2.1 Permissões e Acesso (RBAC)
- A funcionalidade e seus endpoints são de acesso exclusivo para usuários com perfil `tecnico`.
- Usuários com perfil `colaborador` recebem `HTTP 403 Forbidden` e não visualizam a opção de importação na navegação.

### 2.2 Estrutura e Sanitização dos Dados
- O importador deve ler a aba `Patrimônio` (quando em formato Excel com múltiplas abas) ou a primeira aba disponível / arquivo CSV.
- Cabeçalhos aceitos (com tolerância a espaços antes/depois, maiúsculas/minúsculas e acentuação):
  - `TIPO`: mapeado para `equipment_type` (ex: DESKTOP, COMPUTADOR, MONITOR, etc.).
  - `LOCALIZAÇÃO`: mapeado para `location` (ex: CTM, TV PRODUÇÃO, etc.).
  - `SITUAÇÃO`: mapeado para `status` (ex: EM USO, OCIOSO, ALIENAÇÃO, etc.).
  - `DESCRIÇÃO`: mapeado para `description`. Se vazio, preencher com o `TIPO` ou texto descritivo padrão.
  - `Nº PATRIMÔNIO`: mapeado para `patrimony_number`. Se não informado, permanece `None` (vazio).
  - `Nº SÉRIE`: mapeado para `serial_number`. Se não informado, permanece `None` (vazio). O campo no banco de dados é `nullable=True`.
  - `MARCA`: mapeado para `brand`.
  - `ÚLTIMA MANUTENÇÃO`: data de referência da última intervenção. Aceita objeto datetime ou formatos textuais de data comuns (ex: `DD/MM/YYYY`, `YYYY-MM-DD`). Se ausente ou inválida, utiliza a data corrente.
  - `CHAVE WINDOWS`: mapeado para `windows_key`.
  - `Nº PRODUTO`: mapeado para `product_number`.
  - `HISTÓRICO DE MOVIMENTAÇÕES`: mapeado para registro de manutenção.
  - `HOSTNAME`: mapeado para `hostname`.
  - `OBSERVAÇÕES`: mapeado para o campo `notes` do equipamento.

### 2.3 Identificação e Lógica de Upsert
- O sistema verifica a existência prévia do equipamento:
  1. Primeiro pelo `patrimony_number` (se preenchido e não vazio).
  2. Caso não encontre ou não haja patrimônio, busca pelo `serial_number` (se preenchido e não vazio).
- **Se o equipamento já existir:** Seus dados cadastrais (`description`, `equipment_type`, `location`, `status`, `brand`, `hostname`, `windows_key`, `product_number`, `notes`) são atualizados.
- **Se o equipamento não existir:** Um novo registro é inserido no banco com os identificadores disponíveis (ou `None` para os campos ausentes).

### 2.4 Histórico de Manutenção Consolidado
- Para cada equipamento que possuir conteúdo na coluna `HISTÓRICO DE MOVIMENTAÇÕES`:
  - É criado 1 registro único na tabela `equipment_maintenances`.
  - `description`: Conteúdo textual de `HISTÓRICO DE MOVIMENTAÇÕES`.
  - `maintenance_type`: `"Histórico Importado"`.
  - `maintenance_date`: Data extraída de `ÚLTIMA MANUTENÇÃO` ou data atual se vazia.
  - `Equipment.last_maintenance_at`: Atualizado com a referida data.

### 2.5 Criação Automática de Tags Dinâmicas
- Todo valor não-vazio encontrado para `equipment_type`, `location` e `status` é automaticamente verificado na tabela `equipment_tags` nas respectivas categorias (`tipo`, `localizacao`, `situacao`).
- Se a tag não existir, ela é inserida no banco, ficando disponível para os filtros e dropdowns do sistema.

### 2.6 Transacionalidade e Retorno
- Toda a importação é executada dentro de uma única transação de banco de dados (`Unit of Work`).
- O retorno detalha:
  - `total_rows`: total de linhas com dados processadas.
  - `created_count`: novos equipamentos cadastrados.
  - `updated_count`: equipamentos existentes atualizados.
  - `tags_created_count`: novas tags cadastradas.
  - `errors`: lista de linhas ignoradas ou com alertas, se houver.

---

## 3. Cenários BDD (Gherkin)

### Cenário 1: Técnico envia planilha para pré-visualização (Preview)
- **Dado** que um usuário autenticado com perfil `tecnico` acessa a rota de importação
- **Quando** ele envia um arquivo `.xlsx` ou `.csv` válido
- **Então** o sistema responde com `HTTP 200`
- **E** retorna o total de registros identificados e uma prévia das primeiras linhas estruturadas sem persistir no banco.

### Cenário 2: Confirmação de importação com sucesso e upsert
- **Dado** que a planilha contém equipamentos novos e equipamentos já cadastrados no banco
- **Quando** o técnico confirma a importação
- **Então** o sistema executa a transação no banco de dados
- **E** cria os novos equipamentos, atualiza os existentes, insere as tags dinâmicas e vincula o histórico de manutenção
- **E** retorna o sumário com `created_count` e `updated_count`.

### Cenário 3: Importação de equipamentos sem serial ou sem patrimônio
- **Dado** que a planilha contém linhas com a coluna `Nº SÉRIE` ou `Nº PATRIMÔNIO` vazias
- **Quando** o técnico executa a importação
- **Então** o sistema salva o equipamento mantendo os campos correspondentes como `None` (vazio)
- **E** não gera identificadores artificiais nem bloqueia a importação.

### Cenário 4: Consolidação de manutenção e observações
- **Dado** uma linha com `ÚLTIMA MANUTENÇÃO = 21/03/2022`, `HISTÓRICO DE MOVIMENTAÇÕES = Atualização de SO` e `OBSERVAÇÕES = TV Redação`
- **Quando** o equipamento é importado
- **Então** é gerado um registro em `equipment_maintenances` com data `2022-03-21` e descrição `"Atualização de SO"`
- **E** o campo `notes` do equipamento recebe `"TV Redação"`.

### Cenário 5: Usuário colaborador tenta acessar a importação
- **Dado** que um usuário autenticado possui perfil `colaborador`
- **Quando** ele tenta submeter um arquivo para pré-visualização ou importação
- **Então** o sistema rejeita a requisição com `HTTP 403 Forbidden`.

### Cenário 6: Envio de arquivo inválido ou sem dados
- **Dado** que o técnico envia um arquivo corrompido ou sem as colunas esperadas
- **Quando** a requisição de pré-visualização é processada
- **Então** o sistema retorna `HTTP 400 Bad Request` com mensagem amigável detalhando o problema.

### Cenário 7: Interface do Frontend (Aba Importação)
- **Dado** que o técnico acessa o sistema
- **Então** o menu lateral exibe o item **"Importação"**
- **Quando** ele clica no item, visualiza a tela com área de drag-and-drop
- **E** ao carregar um arquivo, visualiza os contadores, a tabela de pré-visualização e o botão "Confirmar Importação"
- **E** após confirmação, vê a mensagem de sucesso e o resumo dos dados importados.
