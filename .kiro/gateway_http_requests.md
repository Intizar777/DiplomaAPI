# Где делаются HTTP запросы к Gateway

## Основной файл: `app/services/gateway_client.py`

Все HTTP запросы к Gateway API делаются в классе `GatewayClient`.

---

## Ключевые методы для синхронизации

### 1. **Аутентификация**
```python
async def login() -> str:
    # POST /auth/login
    # Получает accessToken
```

### 2. **Production API** (основные данные)

| Метод | HTTP | Endpoint | Используется в |
|-------|------|----------|---|
| `get_kpi()` | GET | `/production/kpi` | sync_kpi_task, sync_kpi_per_line_task |
| `get_sales()` | GET | `/production/sales` | sync_sales_task |
| `get_orders()` | GET | `/production/orders` | sync_orders_task |
| `get_quality()` | GET | `/production/quality` | sync_quality_task |
| `get_output()` | GET | `/production/output` | sync_output_task |
| `get_products()` | GET | `/production/products` | sync_products_task |
| `get_sensor_readings()` | GET | `/production/sensors` | sync_sensors_task |
| `get_inventory()` | GET | `/production/inventory` | sync_inventory_task |
| `get_batch_inputs()` | GET | `/production/batch-inputs` | sync_batch_inputs_task |
| `get_downtime_events()` | GET | `/production/downtime-events` | sync_downtime_events_task |
| `get_promo_campaigns()` | GET | `/production/promo-campaigns` | sync_promo_campaigns_task |

### 3. **Reference Data API** (справочники)

| Метод | HTTP | Endpoint | Используется в |
|-------|------|----------|---|
| `get_units_of_measure()` | GET | `/production/units-of-measure` | sync_references_task |
| `get_customers()` | GET | `/production/customers` | sync_references_task |
| `get_warehouses()` | GET | `/production/warehouses` | sync_references_task |
| `get_quality_specs()` | GET | `/production/quality-specs` | sync_quality_specs_task |

---

## Внутренние методы (используются всеми запросами)

### `_request()` — основной метод для HTTP запросов
```python
async def _request(
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    max_retries: Optional[int] = None,
    _is_retry: bool = False
) -> Dict[str, Any]:
    """
    - Добавляет Authorization header с Bearer token
    - Retry logic с exponential backoff (2^attempt, max 30 сек)
    - Обработка 401 (переаутентификация)
    - Логирование всех попыток и ошибок
    """
```

### `_fetch_all_pages()` — пагинация
```python
async def _fetch_all_pages(
    endpoint: str,
    data_key: str,
    base_params: Optional[Dict[str, Any]] = None,
    page_size: int = 1000
) -> List[Dict[str, Any]]:
    """
    - Автоматическая пагинация (offset/limit)
    - Fallback если Gateway не поддерживает пагинацию
    - Rate limiting: 0.15 сек между страницами
    """
```

---

## Параметры запросов

### Фильтры по датам
```python
params = {
    "from": from_date.isoformat(),  # YYYY-MM-DD
    "to": to_date.isoformat()       # YYYY-MM-DD
}
```

### Пагинация
```python
params = {
    "offset": 0,      # Начало
    "limit": 1000     # Размер страницы (max 100 для некоторых endpoints)
}
```

### Специфичные фильтры
```python
# KPI
params["productionLineId"] = line_id

# Orders
params["status"] = status
params["productionLine"] = production_line

# Quality
params["productId"] = product_id
params["lotNumber"] = lot_number
params["decision"] = decision

# Sensors
params["productionLineId"] = production_line
params["parameterName"] = parameter_name
params["quality"] = quality
params["include"] = "sensorParameter"

# Inventory
params["productId"] = product_id
params["warehouseCode"] = warehouse_code
```

---

## Обработка ошибок

### Retry logic
- **5xx ошибки**: Retry с exponential backoff
- **4xx ошибки**: Нет retry (кроме 401)
- **401 (Unauthorized)**: Переаутентификация + 1 retry
- **Timeout**: Retry с exponential backoff
- **Connection error**: Retry с exponential backoff

### Специальные случаи
- **400 "limit must not be greater than 100"**: Автоматический retry с limit=100
- **400 на пагинированном запросе**: Fallback на non-paginated запрос

---

## Логирование

Все запросы логируются в structlog:
- `gateway_request_attempt` — начало попытки
- `gateway_request_success` — успешный ответ (status, elapsed_ms, response_size)
- `gateway_request_failed_all_retries` — все попытки исчерпаны
- `gateway_timeout_retry` — timeout
- `gateway_connect_retry` — connection error
- `gateway_token_expired_relogin` — 401 и переаутентификация
- `gateway_pagination_*` — логи пагинации

---

## Конфигурация (из settings)

```python
gateway_url              # Base URL Gateway API
gateway_auth_email       # Email для login
gateway_auth_password    # Password для login
gateway_timeout_connect  # Timeout на подключение (сек)
gateway_timeout_read     # Timeout на чтение (сек)
gateway_max_retries      # Макс попыток (default 3)
```

---

## Пример: Как работает sync_sales_task

```
1. sync_sales_task() вызывает SalesService.sync_from_gateway(from_date, to_date)

2. SalesService.__init__ получает GatewayClient

3. SalesService.sync_from_gateway() вызывает:
   await self.gateway.get_sales(from_date, to_date)

4. GatewayClient.get_sales() вызывает:
   await self._fetch_all_pages("/production/sales", "sales", params)

5. _fetch_all_pages() в цикле вызывает:
   await self._request("GET", "/production/sales", params={...})

6. _request() выполняет:
   - Проверяет token (login если нужно)
   - Создает httpx.AsyncClient
   - Отправляет GET запрос с Authorization header
   - Retry logic если ошибка
   - Логирует результат

7. Ответ парсится в SalesResponse (Pydantic)

8. SalesService сохраняет данные в БД
```

