# Relatório de Code Review — Gestão de Patrimônio e Suporte

**Data:** 17/08/2026  
**Escopo:** Backend (FastAPI / SQLAlchemy 2.0) e Frontend (React / TypeScript / Tailwind CSS)  
**Status do Review:** **NEEDS CHANGES** (Requer correção dos itens impeditivos antes do merge)

---

## 1. MUST FIX (Bloqueia Merge / Impeditivos)

### [BUG] Impossibilidade de limpar `patrimony_number` e `hostname` na atualização de Equipamento
- **Localização:** [`src/use_cases/equipment_use_cases.py`](file:///home/gil/code/internal_management/src/use_cases/equipment_use_cases.py#L141-L150) (linhas 141 a 150)
- **Problema:** No método `UpdateEquipmentUseCase.execute`, os campos `patrimony_number` e `hostname` só são atribuídos caso avaliem como *truthy* (`if data.patrimony_number and ...`). Se o usuário ou o frontend tentar limpar um número de patrimônio ou hostname previamente preenchido (enviando `None` ou `""`), os campos são ignorados e continuam com o valor anterior no banco de dados, ao contrário dos demais campos opcionais (`brand`, `product_number`, `windows_key`, `notes`).
- **Solução recomendada:** Tratar explicitamente `if data.patrimony_number is not None: equipment.patrimony_number = data.patrimony_number.strip() or None`, executando a validação de unicidade apenas quando o novo valor for uma string não nula e diferente do valor atual. O mesmo tratamento deve ser aplicado para `hostname`.

### [SEC] Vulnerabilidade de Salt Estático no Fallback de Criptografia de Senhas
- **Localização:** [`src/core/security.py`](file:///home/gil/code/internal_management/src/core/security.py#L24-L29) (linhas 24 a 29)
- **Problema:** Quando a biblioteca `argon2-cffi` não está instalada e o sistema recorre ao fallback com `scrypt`, o *salt* utilizado é gerado deterministicamente a partir da `SECRET_KEY` (`salt = hashlib.sha256(settings.SECRET_KEY.encode()).digest()[:16]`). Isso faz com que todos os usuários compartilhem exatamente o mesmo salt, tornando os hashes vulneráveis a ataques de dicionário pré-computados e *rainbow tables* em caso de vazamento do banco de dados.
- **Solução recomendada:** Gerar um salt criptograficamente aleatório e único para cada senha (`os.urandom(16)`), armazená-lo codificado na string do hash e extraí-lo dinamicamente na função `verify_password`.

### [SEC] Possibilidade de Bypass de Rate Limiting por Spoofing de Cabeçalho `X-Forwarded-For`
- **Localização:** [`src/api/routes.py`](file:///home/gil/code/internal_management/src/api/routes.py#L20-L30) (linhas 20 a 30)
- **Problema:** A função `_extract_client_ip` confia diretamente nos cabeçalhos `X-Forwarded-For` e `X-Real-IP` sem validar se a requisição é proveniente de um *reverse proxy* confiável. Um atacante pode contornar completamente o bloqueio de força bruta de 10 tentativas (`AuthenticateUserUseCase`) apenas alternando IPs arbitrários no cabeçalho `X-Forwarded-For` a cada requisição.
- **Solução recomendada:** Validar a confiança do proxy reverso ou utilizar estritamente `request.client.host` caso a aplicação não esteja configurada com um middleware de proxy confiável explícito.

---

## 2. SHOULD FIX (Importantes, mas não bloqueantes)

### [PERF] Potencial Consulta N+1 no Endpoint de Listagem de Equipamentos
- **Localização:** [`src/domain/schemas.py`](file:///home/gil/code/internal_management/src/domain/schemas.py#L141-L169) (linhas 141 a 169) e [`src/use_cases/equipment_use_cases.py`](file:///home/gil/code/internal_management/src/use_cases/equipment_use_cases.py#L99) (linha 99)
- **Problema:** O schema `EquipmentListResponse` reutiliza o DTO `EquipmentResponse`, que inclui as listas aninhadas completas de `movements` e `maintenances`. Ao listar 25 equipamentos por página, a serialização executa consultas individuais *lazy-load* para cada linha do banco (gerando até 50 queries adicionais por requisição).
- **Solução recomendada:** Criar um schema leve de listagem `EquipmentListItemResponse` sem os históricos detalhados ou configurar carregamento explícito via *eager loading* (`selectinload(Equipment.movements)`, `selectinload(Equipment.maintenances)`) no repositório.

### [BUG] Vulnerabilidade a Exceção SQL em Parâmetro `sort_by` Não Validado
- **Localização:** [`src/infrastructure/repositories.py`](file:///home/gil/code/internal_management/src/infrastructure/repositories.py#L187) (linha 187)
- **Problema:** A linha `sort_column = getattr(Equipment, sort_by, Equipment.created_at)` permite consultar atributos que não sejam colunas escalares (como relacionamentos `movements`, `maintenances` ou propriedades internas do modelo SQLAlchemy), o que pode disparar um erro HTTP 500 não tratado.
- **Solução recomendada:** Validar `sort_by` contra uma *whitelist* de colunas permitidas (`created_at`, `last_maintenance_at`, `serial_number`, `patrimony_number`, `equipment_type`, `location`, `status`, etc.).

### [BUG] Potencial Erro de Comparação de Datas com Fuso Horário Diferente (*Naive* vs *Aware*)
- **Localização:** [`src/use_cases/equipment_use_cases.py`](file:///home/gil/code/internal_management/src/use_cases/equipment_use_cases.py#L267) (linhas 267 e 295)
- **Problema:** A expressão `max((m.maintenance_date for m in remaining), default=None)` lançará `TypeError: can't compare offset-naive and offset-aware datetimes` se houver divergência no fuso horário das datas salvas.
- **Solução recomendada:** Garantir a normalização de todas as instâncias de data para `timezone.utc`.

### [DEAD CODE] Protótipos e Componentes Obsoletos no Frontend
- **Localização:** [`frontend/src/prototypes/equipment-modal/`](file:///home/gil/code/internal_management/frontend/src/prototypes/), [`frontend/src/components/AnimatedCounter.tsx`](file:///home/gil/code/internal_management/frontend/src/components/AnimatedCounter.tsx), [`frontend/src/api/dashboardApi.ts`](file:///home/gil/code/internal_management/frontend/src/api/dashboardApi.ts)
- **Problema:** O diretório `prototypes/` (~1.500 linhas) e o componente `AnimatedCounter.tsx` não são mais utilizados após o redesenho corporativo escuro, derrubando a cobertura global de testes do frontend para ~50%.
- **Solução recomendada:** Mover os protótipos para uma pasta fora de `frontend/src/` (ou removê-los) e limpar arquivos não utilizados.

---

## 3. CONSIDER (Sugestões de Melhoria e Boas Práticas)

### [CONFIG] Validação de `SECRET_KEY` em Ambiente de Produção
- **Localização:** [`src/core/config.py`](file:///home/gil/code/internal_management/src/core/config.py#L9) (linha 9)
- **Sugestão:** Evitar valores padrão estáticos em produção; disparar um alerta ou erro de inicialização se `SECRET_KEY` não for configurada via variável de ambiente.

### [UX / PERF] Debounce no Campo de Busca Global de Equipamentos
- **Localização:** [`frontend/src/pages/EquipmentListPage.tsx`](file:///home/gil/code/internal_management/frontend/src/pages/EquipmentListPage.tsx#L374) (linha 374)
- **Sugestão:** Adicionar um *debounce* (ex: 300ms) no input de pesquisa global para evitar disparar uma requisição HTTP a cada caractere digitado.

### [STYLE / TS] Tipagem Segura nos Tratamentos de Erro do Frontend
- **Localização:** [`frontend/src/pages/EquipmentDetailPage.tsx`](file:///home/gil/code/internal_management/frontend/src/pages/EquipmentDetailPage.tsx#L110) (linhas 110, 177, 192)
- **Sugestão:** Substituir `catch (err: any)` por `catch (err: unknown)` com a checagem `if (axios.isAxiosError(err))`.

---

## 4. PONTOS FORTES IDENTIFICADOS (Looks Good)

- **Conformidade com a Constituição e SDD:** Controle de transação estritamente gerenciado no nível de casos de uso/rotas sem commits autônomos nos repositórios; especificações BDD em `spec/` documentadas e mapeadas.
- **Cobertura de Testes no Backend:** 100% de cobertura de linhas e branches no Pytest (63 testes executados com sucesso).
- **Segurança de Autenticação:** Cookies HttpOnly para JWTs, suporte a Argon2id e controle de acesso por papel (RBAC com `require_tecnico_role`).
- **Interface e Usabilidade:** Design corporativo sóbrio em paleta escura (#121212, #1E1E1E), layout horizontal de alta densidade e modais integrados.

---

**Veredito:** **NEEDS CHANGES** (Corrigir itens *MUST FIX* antes de liberar para produção).
