# Задачи синхронизации, обращающиеся к Gateway API

## Все 16 задач обращаются к Gateway

Каждая задача синхронизации использует `GatewayClient` через соответствующий сервис.

---

## Детальная матрица

| Задача | Сервис | Gateway метод | Таблица | Период |
|--------|--------|---------------|--------|--------|
| **sync_kpi_task** | KPIService | `get_kpi()` | aggregated_kpi | 30 дн |
| **sync_kpi_per_line_task** | KPIService | `get_kpi(production_line_id=...)` | aggregated_kpi | 30 дн |
| **sync_sales_task** | SalesService | `get_sales()` | aggregated_sales, sale_records | 30 дн |
| **sync_orders_task** | OrderService | `get_orders()` | order_snapshots | 1 дн |
| **sync_quality_task** | QualityService | `get_quality()` | quality_results | 7 дн |
| **sync_products_task** | ProductService | `get_products()` | products | Full |
| **sync_output_task** | OutputService | `get_output()` | production_output | 1 дн |
| **sync_sensors_task** | SensorService | `get_sensor_readings()` | sensor_readings | 30 дн |
| **sync_inventory_task** | InventoryService | `get_inventory()` | inventory_snapshots | Full |
| **sync_references_task** | GatewayClient (напрямую) | `get_units_of_measure()`, `get_customers()`, `get_warehouses()` | units_of_measure, customers, warehouses | Full |
| **sync_batch_inputs_task** | BatchInputService | `get_batch_inputs()` | batch_inputs | 7 дн |
| **sync_downtime_events_task** | DowntimeEventService | `get_downtime_events()` | downtime_events | 7 дн |
| **sync_promo_campaigns_task** | PromoCampaignService | `get_promo_campaigns()` | promo_campaigns | 30 дн ± |
| **sync_quality_specs_task** | GatewayClient (напрямую) | `get_quality_specs()` | quality_specs | Full |
| **aggregate_sales_trends_task** | - | ❌ Не обращается | sales_trends | Агрегирует из sale_records |
| **cleanup_old_data_task** | - | ❌ Не обращается | Удаляет старые | Retention |

---

## Сервисы, использующие GatewayClient

### 1. **KPIService** (2 вызова)
```python
def __init__(self, db: AsyncSession, gateway: GatewayClient):
    self.gateway = gateway

# Методы:
await self.gateway.get_kpi(from_date, to_date)
await self.gateway.get_kpi(from_date, to_date, production_line_id=line_id)
```

### 2. **SalesService** (1 вызов)
```python
def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
    self.gateway = gateway

# Метод:
await self.gateway.get_sales(from_date, to_date)
```

### 3. **OrderService** (1 вызов)
```python
def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
    self.gateway = gateway

# Метод:
await self.gateway.get_orders(from_date, to_date)
```

### 4. **QualityService** (1 вызов)
```python
def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
    self.gateway = gateway

# Метод:
await self.gateway.get_quality()
```

### 5. **ProductService** (1 вызов)
```python
def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
    self.gateway = gateway

# Метод:
await self.gateway.get_products()
```

### 6. **OutputService** (1 вызов)
```python
def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
    self.gateway = gateway

# Метод:
await self.gateway.get_output(from_date, to_date)
```

### 7. **SensorService** (1 вызов)
```python
def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
    self.gateway = gateway

# Метод:
await self.gateway.get_sensor_readings(from_date=from_date, to_date=to_date)
```

### 8. **InventoryService** (1 вызов)
```python
def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
    self.gateway = gateway

# Метод:
await self.gateway.get_inventory()
```

### 9. **BatchInputService** (1 вызов)
```python
def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
    self.gateway = gateway

# Метод:
await self.gateway.get_batch_inputs(from_date, to_date)
```

### 10. **DowntimeEventService** (1 вызов)
```python
def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
    self.gateway = gateway

# Метод:
await self.gateway.get_downtime_events(from_date, to_date)
```

### 11. **PromoCampaignService** (1 вызов)
```python
def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
    self.gateway = gateway

# Метод:
await self.gateway.get_promo_campaigns(from_date, to_date)
```

### 12. **GatewayClient (напрямую в sync_references_task)**
```python
gateway = GatewayClient()

# Методы:
await gateway.get_units_of_measure()
await gateway.get_customers()
await gateway.get_warehouses()
```

### 13. **GatewayClient (напрямую в sync_quality_specs_task)**
```python
gateway = GatewayClient()

# Метод:
await gateway.get_quality_specs()
```

---

## Задачи БЕЗ обращения к Gateway

### 1. **aggregate_sales_trends_task**
- Агрегирует данные из `sale_records` (уже синхронизированные)
- Группирует по дням/неделям/месяцам
- Заполняет `sales_trends`

### 2. **cleanup_old_data_task**
- Удаляет старые записи из БД
- Не обращается к Gateway

---

## Итого

- **14 задач** обращаются к Gateway API
- **2 задачи** работают только с локальной БД
- **11 сервисов** используют GatewayClient
- **2 задачи** используют GatewayClient напрямую (references, quality_specs)

