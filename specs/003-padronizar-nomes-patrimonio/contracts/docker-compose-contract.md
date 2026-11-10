# Docker Compose Interface Contract

Este contrato define a estrutura obrigatória e os identificadores canônicos que devem ser obedecidos pelos arquivos `docker-compose.yml` e `docker-compose.prod.yml` do projeto **Gerenciador de Patrimônio**.

---

## 1. Contrato de Serviços

### 1.1 Serviço: `postgres`
- **Container Name (Dev)**: `patrimonio_postgres`
- **Container Name (Prod)**: `patrimonio_postgres_prod`
- **Database Name**: `${POSTGRES_DB:-patrimonio_db}`
- **Volumes Mount**: `patrimonio_data:/var/lib/postgresql/data`
- **Networks**:
  - `patrimonio_net`

### 1.2 Serviço: `backend`
- **Container Name (Dev)**: `patrimonio_backend`
- **Container Name (Prod)**: `patrimonio_backend_prod`
- **Database Connection**: `postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@postgres:5432/${POSTGRES_DB:-patrimonio_db}`
- **Networks**:
  - `patrimonio_net`

### 1.3 Serviço: `frontend`
- **Container Name (Dev)**: `patrimonio_frontend`
- **Container Name (Prod)**: `patrimonio_frontend_prod`
- **Proxy/Backend URL**: `http://backend:8000`
- **Networks**:
  - `patrimonio_net`

---

## 2. Contrato de Redes e Volumes

### 2.1 Rede: `patrimonio_net`
- **Key no compose**: `patrimonio_net`
- **Name**: `patrimonio_net` (em dev) / `patrimonio_net_prod` ou `patrimonio_net` (em prod)
- **Driver**: `bridge`

### 2.2 Volume: `patrimonio_data`
- **Key no compose**: `patrimonio_data`
- **Name**: `patrimonio_data` (em dev) / `patrimonio_postgres_prod_data` ou `patrimonio_data_prod` (em prod)
