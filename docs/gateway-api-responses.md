# Gateway API Response Formats

Documentation of real Gateway API responses for each endpoint used in synchronization.
Source of truth: Actual responses from `https://efko-gateway-production.up.railway.app/api`

---

## Authentication

### POST /auth/login

**Path:** `/auth/login`  
**Method:** `POST`  
**Query Parameters:** None  
**Body:**
```json
{
  "email": "admin@efko.local",
  "password": "Efko2024!"
}
```

**Response (200):**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4OTc1MTE5OC01OTYwLTQ1NTQtYmZkMC01YWQ5NDcwY2E5NmUiLCJlbWFpbCI6ImFkbWluQGVma28ubG9jYWwiLCJyb2xlIjoiYWRtaW4iLCJmdWxsTmFtZSI6ItCT0YPRgdC10LIg0JPRgNC40LPQvtGA0LjQuSDQodGC0LXQv9Cw0L3QvtCy0LjRhyIsImVtcGxveWVlSWQiOiJlNTEwNjc0NS0zNjgxLTRiMWUtOTczYS1mNDhkZDFiODA2YTciLCJpYXQiOjE3Nzg0MjMwODUsImV4cCI6MTc3OTAyNzg4NSwiaXNzIjoiRUZLTy1BTyJ9.GGGzE_53-91BmhcXnTkKrgQNS9YRAAymmARhQSgg1oY",
  "refreshToken": "NOw4NwxQ36oTDVysxg6EghmAHHFHARCaMPVbeaD6_QQ"
}
```

**Key fields:**
- `accessToken` (string): JWT token for Bearer auth
- `refreshToken` (string): Token for session refresh

---

## Personnel API

### GET /personnel/locations

**Path:** `/personnel/locations`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page (default: 100)
- `offset` (number, optional): Pagination offset
- `code` (string, optional): Filter by location code
- `type` (string, optional): Filter by type (office, factory)
- `city` (string, optional): Filter by city

**Response (200):**
```json
{
  "locations": [
    {
      "id": "c9b5f796-b67f-4790-966c-b7d6225c4d30",
      "name": "Жировой комбинат (ЕЖК) - Майонезы",
      "code": "EKB_PLANT",
      "type": "factory",
      "streetAddress": "ул. Титова, 27",
      "postalAreaId": "549cb1e5-77f6-4318-a874-64afaa66f313",
      "sourceSystemId": null
    }
  ],
  "total": 13
}
```

**Key fields:**
- `locations` (array): List of location objects
  - `id` (string, UUID): Location identifier
  - `name` (string): Location name
  - `code` (string): Unique location code
  - `type` (string): "office" or "factory"
  - `streetAddress` (string): Physical address
  - `postalAreaId` (string, UUID): Postal area reference
  - `sourceSystemId` (string, nullable): External system reference
- `total` (number): Total count of locations

---

### GET /personnel/departments

**Path:** `/personnel/departments`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `code` (string, optional): Filter by department code
- `type` (string, optional): Filter by type (DIVISION, DEPARTMENT, SECTION, UNIT)
- `parentId` (string, optional): Filter by parent department

**Response (200):**
```json
{
  "departments": [
    {
      "id": "ff4d3613-be20-4931-8871-3529f77746a2",
      "name": "IT-отдел",
      "code": "DEP-UPR-ITD",
      "type": "department",
      "parentId": "f22958aa-3cb7-4ed2-a122-60f1569c473e",
      "headEmployeeId": "58156fda-4575-4271-b165-797b2549714c",
      "sourceSystemId": null
    }
  ],
  "total": 49
}
```

**Key fields:**
- `departments` (array): List of department objects
  - `id` (string, UUID): Department identifier
  - `name` (string): Department name
  - `code` (string): Unique department code
  - `type` (string): Department type enum
  - `parentId` (string, UUID, nullable): Parent department reference
  - `headEmployeeId` (string, UUID, nullable): Head of department
  - `sourceSystemId` (string, nullable): External system reference
- `total` (number): Total count of departments

---

### GET /personnel/positions

**Path:** `/personnel/positions`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `departmentId` (string, optional): Filter by department

**Response (200):**
```json
{
  "positions": [
    {
      "id": "27cde08e-dafe-40b0-a6b9-1f0ad9401400",
      "title": "HR-менеджер",
      "code": "POS-0250"
    }
  ],
  "total": 302
}
```

**Key fields:**
- `positions` (array): List of position objects
  - `id` (string, UUID): Position identifier
  - `title` (string): Position title
  - `code` (string): Unique position code
- `total` (number): Total count of positions

---

### GET /personnel/employees

**Path:** `/personnel/employees`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `departmentId` (string, optional): Filter by department
- `positionId` (string, optional): Filter by position
- `status` (string, optional): Filter by status (ACTIVE, TERMINATED, ON_LEAVE)
- `employmentType` (string, optional): Filter by type (FULL_TIME, PART_TIME, CONTRACT)

**Response (200):**
```json
{
  "employees": [
    {
      "id": "623e2a46-0c46-4062-8709-b0e07d8a9060",
      "personnelNumber": "EMP-00244",
      "fullName": "Абрамова Анастасия Романовна",
      "dateOfBirth": "1975-11-24T00:00:00.000Z",
      "positionId": "23f581ec-b18b-468d-9710-81fceb35fe8a",
      "departmentId": "ab751713-a58e-4f2e-b73e-02e9986f5aa8",
      "workstationId": "14c6beeb-9efa-47ea-986b-99ed9909d966",
      "hireDate": "2024-01-18T00:00:00.000Z",
      "terminationDate": null,
      "employmentType": "main",
      "status": "active",
      "sourceSystemId": null
    }
  ],
  "total": 2000
}
```

**Key fields:**
- `employees` (array): List of employee objects
  - `id` (string, UUID): Employee identifier
  - `personnelNumber` (string): Employee number
  - `fullName` (string): Full name
  - `dateOfBirth` (string, ISO datetime): Birth date
  - `positionId` (string, UUID): Position reference
  - `departmentId` (string, UUID): Department reference
  - `workstationId` (string, UUID, nullable): Workstation reference
  - `hireDate` (string, ISO datetime): Hire date
  - `terminationDate` (string, ISO datetime, nullable): Termination date if applicable
  - `employmentType` (string): "main", "part_time", "contract"
  - `status` (string): "active", "terminated", "on_leave"
  - `sourceSystemId` (string, nullable): External system reference
- `total` (number): Total count of employees

---

### GET /personnel/workstations

**Path:** `/personnel/workstations`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `code` (string, optional): Filter by workstation code
- `locationId` (string, optional): Filter by location
- `productionLineId` (string, optional): Filter by production line
- `workstationType` (string, optional): Filter by type

**Response (200):**
```json
{
  "workstations": [
    {
      "id": "dd6dbbcd-3bd2-4bfa-9dd9-a54550a8a820",
      "name": "Контрольный пост - Завод ТЗПМ",
      "code": "TAM_CTRL1",
      "locationId": "0cc70402-a232-4209-924c-98f46ec5a6d1",
      "productionLineId": "4d1b5527-2315-0129-4000-409c8f901120",
      "workstationType": "control_point",
      "sourceSystemId": null
    }
  ],
  "total": 16
}
```

**Key fields:**
- `workstations` (array): List of workstation objects
  - `id` (string, UUID): Workstation identifier
  - `name` (string): Workstation name
  - `code` (string): Unique workstation code
  - `locationId` (string, UUID): Location reference
  - `productionLineId` (string, UUID, nullable): Production line reference
  - `workstationType` (string): Type of workstation
  - `sourceSystemId` (string, nullable): External system reference
- `total` (number): Total count of workstations

---

## Production API

### GET /production/production-lines

**Path:** `/production/production-lines`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `code` (string, optional): Filter by line code
- `name` (string, optional): Filter by line name
- `isActive` (boolean, optional): Filter by active status

**Response (200):**
```json
{
  "productionLines": [
    {
      "id": "3d57ea5f-fcd5-3a77-24cb-7996f830f190",
      "name": "Линия А - Основное производство (Алматы)",
      "code": "ALM_LINE_A",
      "description": "Линия А - Основное производство (Алматы)",
      "isActive": true,
      "createdAt": "2026-05-08T15:05:59.117Z",
      "updatedAt": "2026-05-08T15:05:59.117Z"
    }
  ],
  "total": 8
}
```

**Key fields:**
- `productionLines` (array): List of production line objects
  - `id` (string, UUID): Production line identifier
  - `name` (string): Line name
  - `code` (string): Unique line code
  - `description` (string): Line description
  - `isActive` (boolean): Active status
  - `createdAt` (string, ISO datetime): Creation timestamp
  - `updatedAt` (string, ISO datetime): Last update timestamp
- `total` (number): Total count of production lines

---

### GET /production/products

**Path:** `/production/products`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `category` (string, optional): Filter by category (raw_material, semi_finished, finished_product, packaging)
- `brand` (string, optional): Filter by brand

**Response (200):**
```json
{
  "products": [
    {
      "id": "d9ef7951-3e45-4c96-a01d-7c92286c0213",
      "code": "PKG-BOTTLE-500ML",
      "name": "Бутылка ПЭТ 500мл",
      "category": "packaging",
      "brand": null,
      "unitOfMeasure": {
        "id": "5cbeb66e-4a7b-4e46-bc43-83308c6ae766",
        "code": "шт",
        "name": "шт"
      },
      "shelfLifeDays": null,
      "requiresQualityCheck": false
    }
  ],
  "total": 16
}
```

**Key fields:**
- `products` (array): List of product objects
  - `id` (string, UUID): Product identifier
  - `code` (string): Unique product code
  - `name` (string): Product name
  - `category` (string): Product category
  - `brand` (string, nullable): Brand name
  - `unitOfMeasure` (object, nullable): Unit of measure with id, code, name
  - `shelfLifeDays` (number, nullable): Shelf life in days
  - `requiresQualityCheck` (boolean): Quality check requirement
- `total` (number): Total count of products

---

### GET /production/orders

**Path:** `/production/orders`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `status` (string, optional): Filter by status (PLANNED, IN_PROGRESS, COMPLETED, CANCELLED)
- `productId` (string, optional): Filter by product
- `productionLineId` (string, optional): Filter by production line
- `from` (string, optional): ISO date start
- `to` (string, optional): ISO date end

**Response (200):**
```json
{
  "orders": [
    {
      "id": "0d341281-2caf-4d43-ae64-0387c2cdfe85",
      "externalOrderId": "ORD-004802",
      "productId": "d8128e57-29d0-48e8-9d51-5a35b387262f",
      "targetQuantity": 6543.971,
      "actualQuantity": 6521.551,
      "status": "completed",
      "productionLineId": "a0a65c5f-bb95-e4a8-e1be-3b6dff660b2d",
      "plannedStart": "2026-05-04T20:48:11.091Z",
      "plannedEnd": "2026-05-06T20:48:11.091Z",
      "actualStart": "2026-05-05T20:48:11.091Z",
      "actualEnd": "2026-05-05T20:48:11.091Z"
    }
  ],
  "total": 5000
}
```

**Key fields:**
- `orders` (array): List of order objects
  - `id` (string, UUID): Order identifier
  - `externalOrderId` (string): External order ID
  - `productId` (string, UUID): Product reference
  - `targetQuantity` (number): Target production quantity
  - `actualQuantity` (number): Actual production quantity
  - `status` (string): Order status enum
  - `productionLineId` (string, UUID): Production line reference
  - `plannedStart` (string, ISO datetime): Planned start
  - `plannedEnd` (string, ISO datetime): Planned end
  - `actualStart` (string, ISO datetime, nullable): Actual start
  - `actualEnd` (string, ISO datetime, nullable): Actual end
- `total` (number): Total count of orders

---

### GET /production/orders/{id}

**Path:** `/production/orders/{id}`  
**Method:** `GET`  
**Path Parameters:**
- `id` (string, UUID): Order identifier

**Response (200):** Same structure as GET /production/orders with additional `outputs` array:
```json
{
  "id": "0d341281-2caf-4d43-ae64-0387c2cdfe85",
  "externalOrderId": "ORD-004802",
  "productId": "d8128e57-29d0-48e8-9d51-5a35b387262f",
  "targetQuantity": 6543.971,
  "actualQuantity": 6521.551,
  "status": "completed",
  "productionLineId": "a0a65c5f-bb95-e4a8-e1be-3b6dff660b2d",
  "plannedStart": "2026-05-04T20:48:11.091Z",
  "plannedEnd": "2026-05-06T20:48:11.091Z",
  "actualStart": "2026-05-05T20:48:11.091Z",
  "actualEnd": "2026-05-05T20:48:11.091Z",
  "outputs": [
    {
      "id": "a4e2b4f1-b90d-45f6-87bd-411e7d2a6483",
      "orderId": "0d341281-2caf-4d43-ae64-0387c2cdfe85",
      "productId": "d8128e57-29d0-48e8-9d51-5a35b387262f",
      "lotNumber": "LOT-20260508-905",
      "quantity": 854.363,
      "qualityStatus": "approved",
      "productionDate": "2026-05-08T20:48:11.091Z",
      "shift": "Утренняя"
    }
  ]
}
```

---

### GET /production/output

**Path:** `/production/output`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `orderId` (string, optional): Filter by order
- `productId` (string, optional): Filter by product
- `lotNumber` (string, optional): Filter by lot number
- `from` (string, optional): ISO date start
- `to` (string, optional): ISO date end

**Response (200):**
```json
{
  "outputs": [
    {
      "id": "a4e2b4f1-b90d-45f6-87bd-411e7d2a6483",
      "orderId": "0d341281-2caf-4d43-ae64-0387c2cdfe85",
      "productId": "d8128e57-29d0-48e8-9d51-5a35b387262f",
      "lotNumber": "LOT-20260508-905",
      "quantity": 854.363,
      "qualityStatus": "approved",
      "productionDate": "2026-05-08T20:48:11.091Z",
      "shift": "Утренняя"
    }
  ],
  "total": 18612
}
```

**Key fields:**
- `outputs` (array): List of output objects
  - `id` (string, UUID): Output record identifier
  - `orderId` (string, UUID): Associated order
  - `productId` (string, UUID): Product reference
  - `lotNumber` (string): Batch/lot number
  - `quantity` (number): Output quantity
  - `qualityStatus` (string): "approved", "rejected", "quarantine"
  - `productionDate` (string, ISO datetime): Production date
  - `shift` (string): Shift name
- `total` (number): Total count

---

### GET /production/sales

**Path:** `/production/sales`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `productId` (string, optional): Filter by product
- `region` (string, optional): Filter by region
- `channel` (string, optional): Filter by channel (RETAIL, WHOLESALE, ONLINE, EXPORT)
- `from` (string, optional): ISO date start
- `to` (string, optional): ISO date end

**Response (200):**
```json
{
  "sales": [
    {
      "id": "b9647330-2d05-422b-a77d-2791994f11c3",
      "externalId": "SALE-0049852",
      "productId": "a31b5c69-4095-4e12-869c-b8b459d58f8f",
      "customerId": "7fbf1f89-f3b7-463c-9c8f-fdf628c23195",
      "quantity": 1501.444,
      "amount": 1728026.56,
      "saleDate": "2026-05-04T00:00:00.000Z",
      "region": "ПФО",
      "channel": "retail"
    }
  ],
  "total": 50000
}
```

**Key fields:**
- `sales` (array): List of sale objects
  - `id` (string, UUID): Sale record identifier
  - `externalId` (string): External sale ID
  - `productId` (string, UUID): Product reference
  - `customerId` (string, UUID): Customer reference
  - `quantity` (number): Sale quantity
  - `amount` (number): Sale amount (currency)
  - `saleDate` (string, ISO datetime): Sale date
  - `region` (string): Region/territory
  - `channel` (string): Sales channel
- `total` (number): Total count

---

### GET /production/sales/summary

**Path:** `/production/sales/summary`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `groupBy` (string, optional): Group by dimension (region, channel, product)
- `from` (string, optional): ISO date start
- `to` (string, optional): ISO date end

**Response (200):**
```json
{
  "summary": [
    {
      "groupKey": "СФО",
      "totalQuantity": 20993378.776,
      "totalAmount": 7834257524.91,
      "salesCount": 5157
    },
    {
      "groupKey": "ЮФО",
      "totalQuantity": 34992921.487,
      "totalAmount": 12894227632.37,
      "salesCount": 8462
    }
  ],
  "totalAmount": 81056943531.24,
  "totalQuantity": 238099955.603,
  "total": 5
}
```

**Key fields:**
- `summary` (array): List of summary groups
  - `groupKey` (string): Group identifier (region/channel/product name)
  - `totalQuantity` (number): Total quantity in group
  - `totalAmount` (number): Total amount in group
  - `salesCount` (number): Number of sales in group
- `totalAmount` (number): Grand total amount
- `totalQuantity` (number): Grand total quantity
- `total` (number): Number of groups

---

### GET /production/kpi

**Path:** `/production/kpi`  
**Method:** `GET`  
**Query Parameters:**
- `from` (string, optional): ISO date start
- `to` (string, optional): ISO date end
- `productionLineId` (string, optional): Filter by production line

**Response (200):**
```json
{
  "totalOutput": 79190291.608,
  "defectRate": 0.03487299201612002,
  "completedOrders": 3910,
  "totalOrders": 5000,
  "oeeEstimate": 0.7547293202433941
}
```

**Key fields:**
- `totalOutput` (number): Total output quantity
- `defectRate` (number): Defect rate (0-1 decimal)
- `completedOrders` (number): Count of completed orders
- `totalOrders` (number): Count of total orders
- `oeeEstimate` (number): Overall Equipment Effectiveness estimate (0-1 decimal)

---

### GET /production/quality

**Path:** `/production/quality`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `productId` (string, optional): Filter by product
- `lotNumber` (string, optional): Filter by lot number
- `decision` (string, optional): Filter by decision (APPROVED, REJECTED, QUARANTINE)
- `inSpec` (boolean, optional): Filter by in-spec status

**Response (200):**
```json
{
  "results": [
    {
      "id": "2c685d39-8402-421d-b731-7c7155d981b3",
      "lotNumber": "LOT-20260508-905",
      "qualitySpecId": "abd133b5-426d-4c40-bc31-a249f8dbb09c",
      "productId": "",
      "parameterName": "",
      "resultValue": 0.650719,
      "qualityStatus": "approved",
      "testDate": "2026-05-09T20:48:11.091Z"
    }
  ],
  "total": 5181
}
```

**Key fields:**
- `results` (array): List of quality results
  - `id` (string, UUID): Quality result identifier
  - `lotNumber` (string): Lot number
  - `qualitySpecId` (string, UUID): Quality spec reference
  - `productId` (string, UUID): Product reference (may be empty)
  - `parameterName` (string): Quality parameter name (may be empty)
  - `resultValue` (number): Measured value
  - `qualityStatus` (string): "approved", "rejected", "quarantine"
  - `testDate` (string, ISO datetime): Test date
- `total` (number): Total count

---

### GET /production/sensors

**Path:** `/production/sensors`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `productionLineId` (string, optional): Filter by production line
- `parameterName` (string, optional): Filter by parameter name
- `quality` (string, optional): Filter by signal quality (GOOD, UNCERTAIN, BAD)
- `from` (string, optional): ISO datetime start
- `to` (string, optional): ISO datetime end

**Response (200):**
```json
{
  "readings": [
    {
      "id": "6f62c3b3-9102-43a9-befa-c017328ce66c",
      "sensorId": "46e965ef-efa5-4839-8dec-1974596faf46",
      "deviceId": "SENSOR-NOG_LINE_A-T03-РАСХ",
      "productionLineId": "a0a65c5f-bb95-e4a8-e1be-3b6dff660b2d",
      "sensorParameterId": "6b0ea8f9-168b-406e-8015-879fd71016fc",
      "value": 4360.7101,
      "quality": "bad",
      "recordedAt": "2026-05-05T12:59:00.000Z"
    }
  ],
  "total": 22272
}
```

**Key fields:**
- `readings` (array): List of sensor readings
  - `id` (string, UUID): Reading identifier
  - `sensorId` (string, UUID): Sensor reference
  - `deviceId` (string): Physical device identifier
  - `productionLineId` (string, UUID): Production line reference
  - `sensorParameterId` (string, UUID): Parameter type reference
  - `value` (number): Measured value
  - `quality` (string): Signal quality enum
  - `recordedAt` (string, ISO datetime): Recording timestamp
- `total` (number): Total count

---

### GET /production/inventory

**Path:** `/production/inventory`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset
- `productId` (string, optional): Filter by product
- `warehouseId` (string, optional): Filter by warehouse

**Response (200):**
```json
{
  "inventory": [
    {
      "id": "c3d7a566-5bb8-4ac1-9774-e6542c12c1a5",
      "productId": "cef90bf6-801f-48b4-9bbe-2edb9668c824",
      "warehouseId": "0f0ece7c-b002-444c-b9c8-61bf8be0f64e",
      "lotNumber": "LOT-20260314-004",
      "quantity": 2352.971,
      "lastUpdated": "2026-03-14T03:41:10.369Z"
    }
  ],
  "total": 34
}
```

**Key fields:**
- `inventory` (array): List of inventory items
  - `id` (string, UUID): Inventory record identifier
  - `productId` (string, UUID): Product reference
  - `warehouseId` (string, UUID): Warehouse reference
  - `lotNumber` (string): Lot/batch number
  - `quantity` (number): Available quantity
  - `lastUpdated` (string, ISO datetime): Last update timestamp
- `total` (number): Total count

---

### GET /production/units-of-measure

**Path:** `/production/units-of-measure`  
**Method:** `GET`  
**Query Parameters:** None (returns all units)

**Response (200):**
```json
{
  "unitsOfMeasure": [
    {
      "id": "bfff1635-3800-4fb8-8e66-e7ed300691e0",
      "code": "кг",
      "name": "кг",
      "createdAt": "2026-05-08T15:05:57.765Z"
    },
    {
      "id": "82e54ec5-8a51-472d-91ce-2ccad76a7269",
      "code": "л",
      "name": "л",
      "createdAt": "2026-05-08T15:05:57.874Z"
    }
  ],
  "total": 3
}
```

**Key fields:**
- `unitsOfMeasure` (array): List of unit objects
  - `id` (string, UUID): Unit identifier
  - `code` (string): Unit code (kg, l, шт, etc.)
  - `name` (string): Unit name
  - `createdAt` (string, ISO datetime): Creation timestamp
- `total` (number): Total count

---

### GET /production/customers

**Path:** `/production/customers`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset

**Response (200):**
```json
{
  "customers": [
    {
      "id": "ec3464dc-777b-485a-adba-5d99408d23c1",
      "name": "ООО Монетка",
      "createdAt": "2026-05-08T15:06:00.413Z"
    },
    {
      "id": "d907572d-70c8-4ce2-8fa0-7bc583c43a6c",
      "name": "ООО Бристол",
      "createdAt": "2026-05-08T15:06:00.359Z"
    }
  ],
  "total": 10
}
```

**Key fields:**
- `customers` (array): List of customer objects
  - `id` (string, UUID): Customer identifier
  - `name` (string): Customer name
  - `createdAt` (string, ISO datetime): Creation timestamp
- `total` (number): Total count

---

### GET /production/warehouses

**Path:** `/production/warehouses`  
**Method:** `GET`  
**Query Parameters:**
- `limit` (number, optional): Records per page
- `offset` (number, optional): Pagination offset

**Response (200):**
```json
{
  "warehouses": [
    {
      "id": "36688e3d-5f73-4327-bdd5-c0148bf901f6",
      "name": "Архивный склад",
      "code": "WH-ARCH-01",
      "createdAt": "2026-05-08T15:05:59.874Z"
    },
    {
      "id": "0f0ece7c-b002-444c-b9c8-61bf8be0f64e",
      "name": "Экспортный склад",
      "code": "WH-EXP-01",
      "createdAt": "2026-05-08T15:05:59.821Z"
    }
  ],
  "total": 8
}
```

**Key fields:**
- `warehouses` (array): List of warehouse objects
  - `id` (string, UUID): Warehouse identifier
  - `name` (string): Warehouse name
  - `code` (string): Unique warehouse code
  - `createdAt` (string, ISO datetime): Creation timestamp
- `total` (number): Total count

---

## Common Patterns

### Pagination
Most endpoints support:
- `offset` (number): Starting record position
- `limit` (number): Maximum records per page (typically max 100)

Responses include `total` field with total count of matching records.

### UUID Fields
Fields ending in `Id` are typically UUIDs (e.g., `productId`, `employeeId`, `locationId`).

### ISO Datetime Fields
Date/time fields are ISO 8601 format with timezone (e.g., `2026-05-08T15:05:59.117Z`).

### Nullable Fields
Fields can be `null` for optional or unset values (e.g., `terminationDate`, `sourceSystemId`).

### Authentication
All endpoints require Bearer token in Authorization header:
```
Authorization: Bearer {accessToken}
```

Token obtained from `POST /auth/login` response.

---

## Notes on Response Variations

1. **Array vs Object Wrapping**: Some endpoints return wrapped arrays (e.g., `{"sales": [...]}`) while others return root arrays.
2. **Missing Fields**: Some returned objects have empty strings for certain fields (e.g., `quality.productId`, `quality.parameterName`).
3. **Nullable Nested Objects**: Some nested objects (e.g., `unitOfMeasure`) can be null.
4. **Pagination**: Not all endpoints support pagination (e.g., `/production/kpi` does not).
