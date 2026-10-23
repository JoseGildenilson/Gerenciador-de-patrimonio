# Especificação: Autocomplete nos Filtros de Patrimônio, Série e Produto

## Visão Geral
Os campos de filtro textual de **Nº Patrimônio**, **Nº Série** e **Nº Produto** na tela de listagem de equipamentos devem oferecer **sugestões em tempo real (autocomplete)** enquanto o usuário digita, exibindo valores existentes no banco de dados que correspondam ao prefixo digitado.

---

## Regras de Negócio & Restrições

### RN-AC-01 (Mínimo de caracteres para ativar sugestões)
- As sugestões só devem ser exibidas após o usuário digitar **pelo menos 2 caracteres**.

### RN-AC-02 (Busca por prefixo)
- A correspondência das sugestões deve ser por **prefixo** (o valor cadastrado começa com o texto digitado).
- A busca deve ser **case-insensitive**.

### RN-AC-03 (Limite de sugestões)
- O dropdown de sugestões deve exibir no máximo **10 itens** por consulta.

### RN-AC-04 (Seleção direta como chip)
- Ao clicar em uma sugestão, o valor deve ser **adicionado diretamente como chip/tag** no filtro ativo (mesmo comportamento do Enter atual).
- O campo de texto deve ser **limpo automaticamente** após a seleção, permitindo adicionar mais valores.

### RN-AC-05 (Entrada livre mantida)
- O comportamento atual de digitar um valor livre e pressionar **Enter** para adicioná-lo como chip deve ser **mantido como fallback**.
- O usuário pode adicionar valores que não aparecem nas sugestões.

### RN-AC-06 (Debounce)
- As requisições de sugestões devem respeitar um **debounce de 300ms** após a última tecla digitada para evitar sobrecarga na API.

### RN-AC-07 (Ocultação de valores já selecionados)
- Valores já adicionados como chips ativos no mesmo filtro **não devem aparecer** nas sugestões (evita duplicatas visuais).

### RN-AC-08 (Endpoint único de sugestões)
- O backend deve expor um **endpoint único** para sugestões:
  `GET /api/v1/equipments/suggestions?field={campo}&prefix={texto}&limit=10`
- O parâmetro `field` aceita os valores: `patrimony_number`, `serial_number`, `product_number`.
- O endpoint retorna uma lista de strings com os valores distintos correspondentes.
- O endpoint é restrito à role `tecnico` (RBAC).

### RN-AC-09 (Validação do campo)
- O endpoint deve retornar **HTTP 400** se o parâmetro `field` não for um dos campos válidos (`patrimony_number`, `serial_number`, `product_number`).
- O endpoint deve retornar **HTTP 400** se `prefix` não for informado ou tiver menos de 2 caracteres.

---

## Cenários de Aceitação (BDD)

### Cenário 1: Exibir sugestões ao digitar no filtro de Patrimônio
- **Dado** que existam equipamentos com patrimônios `PAT001`, `PAT002`, `PAT100` e `SER001`
- **Quando** o técnico digitar `PA` no campo de filtro de Patrimônio
- **Então** o dropdown de sugestões deve exibir `PAT001`, `PAT002` e `PAT100`
- **E** `SER001` **não** deve aparecer nas sugestões.

### Cenário 2: Não exibir sugestões com menos de 2 caracteres
- **Dado** que o técnico esteja no campo de filtro de Série
- **Quando** digitar apenas `S` (1 caractere)
- **Então** nenhuma sugestão deve ser exibida.

### Cenário 3: Adicionar sugestão como chip ao clicar
- **Dado** que o técnico digite `PAT` no campo de Patrimônio
- **E** as sugestões `PAT001` e `PAT002` sejam exibidas
- **Quando** o técnico clicar em `PAT001`
- **Então** `PAT001` deve ser adicionado como chip ativo no filtro de Patrimônio
- **E** o campo de texto deve ser limpo
- **E** a lista de equipamentos deve ser filtrada para incluir `PAT001`.

### Cenário 4: Ocultar valores já selecionados nas sugestões
- **Dado** que o técnico já tenha adicionado `PAT001` como chip no filtro de Patrimônio
- **Quando** digitar `PAT` novamente
- **Então** as sugestões devem exibir `PAT002` e `PAT100`
- **E** `PAT001` **não** deve aparecer nas sugestões.

### Cenário 5: Manter entrada livre via Enter
- **Dado** que o técnico digite `XYZ999` no campo de Produto
- **E** nenhuma sugestão seja exibida (valor não existe)
- **Quando** o técnico pressionar Enter
- **Então** `XYZ999` deve ser adicionado como chip ativo no filtro de Produto.

### Cenário 6: Backend retorna erro para campo inválido
- **Dado** que uma requisição seja feita para `GET /api/v1/equipments/suggestions?field=invalid_field&prefix=AB`
- **Então** o endpoint deve retornar HTTP 400 com mensagem de erro adequada.

### Cenário 7: Backend retorna erro para prefixo curto
- **Dado** que uma requisição seja feita para `GET /api/v1/equipments/suggestions?field=serial_number&prefix=A`
- **Então** o endpoint deve retornar HTTP 400 com mensagem de erro adequada.
