# API Contracts: SisPatrimonio Canonical Endpoints

**Feature**: `002-purge-legacy-database` | **Date**: 2026-10-28

All APIs operate exclusively on the canonical DBML entities under `/api/v1/`.

---

## 1. Authentication (`/api/v1/auth`)

### `POST /api/v1/auth/login`
Authenticates a user with email and password.
- **Request Body**:
  ```json
  {
    "email": "admin@sispatrimonio.edu.br",
    "password": "senha123"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "jwt_token_string",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "name": "Administrador",
      "email": "admin@sispatrimonio.edu.br",
      "role": "administrador",
      "is_active": true
    }
  }
  ```

---

## 2. Categories (`/api/v1/categories`)

### `GET /api/v1/categories`
Lists all asset categories.
- **Response `200 OK`**:
  ```json
  [
    {
      "id": 1,
      "name": "Notebooks e Portáteis",
      "useful_life_months": 48,
      "residual_value_rate": 10.00,
      "requires_serial_number": true
    }
  ]
  ```

### `POST /api/v1/categories`
Creates a new asset category.
- **Request Body**:
  ```json
  {
    "name": "Servidores",
    "useful_life_months": 72,
    "residual_value_rate": 15.00,
    "requires_serial_number": true
  }
  ```
- **Response `201 Created`**: Returns created Category object.

---

## 3. Locations (`/api/v1/locations`)

### `GET /api/v1/locations`
Lists all physical locations.
- **Response `200 OK`**:
  ```json
  [
    {
      "id": 1,
      "building": "Prédio Central",
      "floor": "1º Andar",
      "sector": "Departamento de TI",
      "room_number": "Sala 101",
      "description": "Setor de infraestrutura"
    }
  ]
  ```

### `POST /api/v1/locations`
Creates a new physical location.
- **Request Body**:
  ```json
  {
    "building": "Prédio Central",
    "floor": "2º Andar",
    "sector": "Biblioteca",
    "room_number": "Sala 201",
    "description": "Acervo e computadores de pesquisa"
  }
  ```
- **Response `201 Created`**: Returns created Location object.

---

## 4. Assets (`/api/v1/assets`)

### `GET /api/v1/assets`
Lists assets with pagination and filters (`category_id`, `location_id`, `status`, `search`).
- **Response `200 OK`**:
  ```json
  {
    "items": [
      {
        "id": 1,
        "patrimony_number": "PAT-2026-0001",
        "serial_number": "SN-DELL-88210",
        "description": "Dell Latitude 5430 Core i7 16GB",
        "category_id": 1,
        "location_id": 1,
        "assigned_user_id": 3,
        "brand": "Dell",
        "model": "Latitude 5430",
        "purchase_cost": 6500.00,
        "purchase_date": "2026-01-15",
        "status": "em_uso",
        "specs": {"cpu": "Core i7", "ram_gb": 16}
      }
    ],
    "total": 1,
    "page": 1,
    "limit": 50,
    "pages": 1
  }
  ```

### `POST /api/v1/assets`
Registers a new asset.
- **Request Body**:
  ```json
  {
    "patrimony_number": "PAT-2026-0002",
    "serial_number": "SN-LENOVO-9941",
    "description": "ThinkPad T14",
    "category_id": 1,
    "location_id": 1,
    "assigned_user_id": null,
    "brand": "Lenovo",
    "model": "ThinkPad T14 Gen 3",
    "purchase_cost": 7200.00,
    "purchase_date": "2026-02-10",
    "status": "disponivel",
    "specs": {}
  }
  ```
- **Response `201 Created`**: Returns created Asset object.

### `POST /api/v1/assets/{id}/renumber`
Audited renumbering of an asset.
- **Request Body**:
  ```json
  {
    "new_patrimony_number": "PAT-2026-0099",
    "reason": "Troca de plaqueta danificada"
  }
  ```
- **Response `200 OK`**: Returns updated Asset with audit history entry.

---

## 5. Movements & Maintenances (`/api/v1/assets/{id}/...`)

### `POST /api/v1/assets/{id}/movements`
Records physical/custodian transfer.
- **Request Body**:
  ```json
  {
    "origin_location_id": 1,
    "dest_location_id": 2,
    "from_user_id": 3,
    "to_user_id": 4,
    "notes": "Transferência de sala e responsável"
  }
  ```
- **Response `201 Created`**: Movement record.

### `POST /api/v1/assets/{id}/maintenances`
Records technical maintenance.
- **Request Body**:
  ```json
  {
    "maintenance_type": "preventiva",
    "service_provider": "Dell Suporte Pro",
    "description": "Limpeza preventiva e troca de pasta térmica",
    "cost": 350.00,
    "maintenance_date": "2026-10-28T10:00:00Z"
  }
  ```
- **Response `201 Created`**: Maintenance record.
