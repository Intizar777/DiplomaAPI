# API Endpoint Curl Test Report
**Date:** 2026-05-19  
**Server:** `uvicorn app.main:app --reload --port 8000`

---

## Сводка ошибок (500 Internal Server Error)

| Endpoint | Без параметров | С параметрами | Тип ошибки |
|----------|:---:|:---:|------------|
| `GET /api/v1/sales/top-products` | ❌ 500 | ✅ 200 | Pydantic: `total_quantity=None` не конвертируется в Decimal |
| `GET /api/v1/orders/plan-execution` | ❌ 500 | ❌ 500 | Pydantic: missing fields в схеме / пустой ответ без total_target |
| `GET /api/v1/orders/downtime` | ❌ 500 | ❌ 500 | Missing fields / `int.quantize()` AttributeError |
| `GET /api/v1/output/summary` | ❌ 500 | ❌ 500 | Pydantic: missing обязательное поле `meta` |
| `GET /api/v1/output/by-shift` | ❌ 500 | ❌ 500 | Pydantic: missing обязательное поле `meta` |
| `GET /api/v1/inventory/current` | ❌ 500 | ❌ 500 | Pydantic: missing обязательное поле `meta` |
| `GET /api/production/kpi/line-productivity` | ❌ 422 | ❌ 500 | Pydantic: сервис возвращает `product_line_id`, схема ждёт `production_line` |

---

## Ручки с обязательными параметрами (422 без них)

| Endpoint | Обязательные параметры |
|----------|----------------------|
| `GET /api/v1/inventory/trends` | `product_id` |
| `GET /api/v1/oee/summary` | `period_from`, `period_to` |
| `GET /api/production/kpi` | `from_date`, `to_date` |
| `GET /api/production/kpi/otif` | `from_date`, `to_date` |
| `GET /api/production/kpi/breakdown` | `from_date`, `to_date` |
| `GET /api/production/sales/margin` | `from_date`, `to_date` |
| `GET /api/production/kpi/line-productivity` | `from_date`, `to_date` |
| `GET /api/production/kpi/scrap-percentage` | `from_date`, `to_date` |
| `GET /api/production/batch-inputs/yield` | `order_id` |

---

## Детали по ошибкам с логами сервера

### 1. `GET /api/v1/sales/top-products` — 500 (только без параметров)

**Запрос:** `curl http://localhost:8000/api/v1/sales/top-products`  
**Ответ:** `{"detail":"Internal server error","trace_id":"6d186c56-0161-4a"}`  

**Лог сервера:**
```
error_message='2 validation errors for TopProductsResponse
products.8.total_quantity
  Decimal input should be an integer, float, string or Decimal object 
  [type=decimal_type, input_value=None, input_type=NoneType]
products.9.total_quantity
  Decimal input should be an integer, float, string or Decimal object 
  [type=decimal_type, input_value=None, input_type=NoneType]'
error_type=ValidationError  path=/api/v1/sales/top-products  query=
```

**Причина:** SQL-запрос без фильтра по датам возвращает строки с `total_quantity = NULL` для некоторых продуктов. Pydantic-схема объявляет `total_quantity: Decimal` без `Optional`.  
**С параметрами:** `?start_date=2024-01-01&end_date=2024-12-31` — возвращает 200 OK.

**Фикс:** В схеме `TopProductItem` сделать `total_quantity: Optional[Decimal] = None`, или в SQL добавить `COALESCE(sum(quantity), 0)`.

---

### 2. `GET /api/v1/orders/plan-execution` — 500 (оба варианта)

**Запрос (без параметров):** `curl http://localhost:8000/api/v1/orders/plan-execution`  
**Лог сервера:**
```
error_message="5 validation errors for PlanExecutionLineItem
orders_planned   Field required [type=missing]
orders_in_progress   Field required [type=missing]
orders_completed   Field required [type=missing]
orders_cancelled   Field required [type=missing]
..."
input_value={'production_line': '1aeb...', 'overdue_orders': 3401}
```

**Причина:** Сервис возвращает dict с полем `overdue_orders`, но без `orders_planned`, `orders_in_progress`, `orders_completed`, `orders_cancelled`, которые обязательны в `PlanExecutionLineItem`.

**Запрос (с датами без данных):** `curl "http://localhost:8000/api/v1/orders/plan-execution?start_date=2024-01-01&end_date=2024-12-31"`  
**Лог сервера:**
```
error_message="3 validation errors for PlanExecutionResponse
total_target   Field required [type=missing]
total_actual   Field required [type=missing]
..."
input_value={'period_from': ..., 'lines': []}
```

**Причина:** Когда `lines` пустой, сервис не вычисляет `total_target`/`total_actual`.  
**Фикс:** Добавить все поля orders_* в возвращаемый dict, вычислять `total_target`/`total_actual` из `lines` даже если пустой (по умолчанию 0).

---

### 3. `GET /api/v1/orders/downtime` — 500 (оба варианта)

**Запрос (без параметров):** `curl http://localhost:8000/api/v1/orders/downtime`  
**Лог сервера:**
```
error_message="4 validation errors for DowntimeLineItem
delayed_orders   Field required [type=missing]
avg_delay_hours   Field required [type=missing]
..."
input_value={'rank': 1, 'production_line': ..., 'delay_pct': Decimal('13.51')}
```

**Причина:** Сервис не включает `delayed_orders` и `avg_delay_hours` в возвращаемый dict.

**Запрос (с датами):** `curl "http://localhost:8000/api/v1/orders/downtime?start_date=2024-01-01&end_date=2024-12-31"`  
**Лог сервера:**
```
error_message="'int' object has no attribute 'quantize'"
error_type=AttributeError
path=/api/v1/orders/downtime
```

**Причина:** `.quantize()` вызывается на `int` вместо `Decimal`.  
**Фикс:** Добавить `delayed_orders` и `avg_delay_hours` в dict сервиса. Обернуть значение в `Decimal(...)` перед вызовом `.quantize()`.

---

### 4. `GET /api/v1/output/summary` и `GET /api/v1/output/by-shift` — 500

**Запрос:** `curl http://localhost:8000/api/v1/output/summary`  
**Лог сервера:**
```
error_message="1 validation error:
  {'type': 'missing', 'loc': ('response', 'meta'), 'msg': 'Field required',
   'input': {'items': [{'date': ..., 'shift': None, 'total_quantity': ..., 
             'lot_count': 49, 'approved_count': 42}, ...]}}"
```

**Причина:** Response-схема объявляет `meta` как обязательное поле (пагинация), но сервис возвращает только `items`. Одна и та же проблема для `/output/summary` и `/output/by-shift`.

**Фикс:** Сделать `meta` в схеме ответа `Optional` — `meta: Optional[PaginationMeta] = None`.

---

### 5. `GET /api/v1/inventory/current` — 500

**Запрос:** `curl http://localhost:8000/api/v1/inventory/current`  
**Лог сервера:**
```
error_message="1 validation error:
  {'type': 'missing', 'loc': ('response', 'meta'), 'msg': 'Field required',
   'input': {'items': [{'product_id': ..., 'product_name': 'Горчица острая', 
             'warehouse_code': 'WH-EXP-01', 'lot_number': ..., 'quantity': 3093.488, ...}]}}"
```

**Причина:** Та же проблема — `meta` обязательно в схеме, но сервис его не возвращает.  
**Фикс:** `meta: Optional[PaginationMeta] = None` в схеме ответа.

---

### 6. `GET /api/production/kpi/line-productivity` — 500 (с `from_date`/`to_date`)

**Запрос:** `curl "http://localhost:8000/api/production/kpi/line-productivity?from_date=2024-01-01&to_date=2024-12-31"`  
**Лог сервера:**
```
error_message="8 validation errors:
  {'type': 'missing', 'loc': ('response', 'items', 0, 'production_line'), 'msg': 'Field required',
   'input': {'product_line_id': '3d57ea5f-...', 'productivity': Decimal('7457.28...'),
             'total_output': Decimal('43669872.020'), 'days': 366, 'target': ..., 
             'status': 'ok', 'deviation': ...}}"
```

**Причина:** Сервис возвращает ключ `product_line_id`, а схема `LineProductivityItem` ожидает поле `production_line`.  
**Фикс:** В сервисе переименовать ключ `product_line_id` → `production_line` в возвращаемом dict (или добавить маппинг).

---

## Полный список результатов

### ✅ Работающие (200 OK)

| Endpoint | Без параметров | С параметрами | Примечания |
|----------|:---:|:---:|-----------|
| `GET /health` | ✅ 200 | — | |
| `GET /` | ✅ 200 | — | |
| `GET /api/v1/sales/summary` | ✅ 200 | ✅ 200 | Фильтр дат не применяется |
| `GET /api/v1/sales/trends` | ✅ 200 | ✅ 200 | Фильтр дат не применяется |
| `GET /api/v1/sales/top-products` | ❌ 500 | ✅ 200 | |
| `GET /api/v1/sales/regions` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/orders/status-summary` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/orders/list` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/orders/plan-execution` | ❌ 500 | ❌ 500 | |
| `GET /api/v1/orders/downtime` | ❌ 500 | ❌ 500 | |
| `GET /api/v1/quality/summary` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/quality/defect-trends` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/quality/lots` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/quality/parameter-trends` | ✅ 200 | ✅ 200 | Фильтр дат работает |
| `GET /api/v1/quality/defect-pareto` | ✅ 200 | ✅ 200 | Фильтр дат работает |
| `GET /api/v1/products` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/output/summary` | ❌ 500 | ❌ 500 | |
| `GET /api/v1/output/by-shift` | ❌ 500 | ❌ 500 | |
| `GET /api/v1/sensors/history` | ✅ 200 | ✅ 200 | Данные пустые (items=[]) |
| `GET /api/v1/sensors/alerts` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/sensors/stats` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/inventory/current` | ❌ 500 | ❌ 500 | |
| `GET /api/v1/inventory/trends` | ❌ 422 | ✅ 200 (c product_id) | product_id обязателен |
| `GET /api/v1/dashboards/line-master/shift-progress` | ✅ 200 | — | |
| `GET /api/v1/dashboards/line-master/shift-comparison` | ✅ 200 | — | |
| `GET /api/v1/dashboards/line-master/defect-summary` | ✅ 200 | — | |
| `GET /api/v1/dashboards/gm/oee-summary` | ✅ 200 | ✅ 200 | Фильтр дат не применяется |
| `GET /api/v1/dashboards/gm/plan-execution` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/dashboards/gm/downtime-ranking` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/dashboards/qe/parameter-trends` | ✅ 200 | — | |
| `GET /api/v1/dashboards/qe/batch-analysis` | ✅ 200 | — | |
| `GET /api/v1/dashboards/qe/defect-pareto` | ✅ 200 | — | |
| `GET /api/v1/dashboards/finance/sales-breakdown` | ✅ 200 | ✅ 200 | Фильтр дат не применяется |
| `GET /api/v1/dashboards/finance/revenue-trend` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/dashboards/finance/top-products` | ✅ 200 | ✅ 200 | |
| `GET /api/v1/oee/today` | ✅ 200 | — | |
| `GET /api/v1/oee/this-week` | ✅ 200 | — | |
| `GET /api/v1/oee/this-month` | ✅ 200 | — | |
| `GET /api/v1/oee/summary` | ❌ 422 | ✅ 200 (period_from/period_to) | |
| `GET /api/production/kpi` | ❌ 422 | ✅ 200 (from_date/to_date) | |
| `GET /api/production/kpi/otif` | ❌ 422 | ✅ 200 (from_date/to_date) | |
| `GET /api/production/kpi/breakdown` | ❌ 422 | ✅ 200 (from_date/to_date) | |
| `GET /api/production/sales/margin` | ❌ 422 | ✅ 200 | Данные пустые |
| `GET /api/production/kpi/line-productivity` | ❌ 422 | ❌ 500 | |
| `GET /api/production/kpi/scrap-percentage` | ❌ 422 | ✅ 200 | |
| `GET /api/production/production-lines` | ✅ 200 | — | |
| `GET /api/production/batch-inputs` | ✅ 200 | ✅ 200 | |
| `GET /api/production/batch-inputs/yield` | ❌ 422 | ❌ 422 | order_id обязателен |
| `GET /api/production/downtime-events` | ✅ 200 | ✅ 200 | Фильтр дат работает |
| `GET /api/production/downtime-events/summary` | ✅ 200 | ✅ 200 | Фильтр дат работает |
| `GET /api/production/promo-campaigns` | ✅ 200 | — | |
| `GET /api/production/kpi/debug/date-range` | ✅ 200 | — | |
| `GET /api/v1/export/gm` | ✅ 200 | — | Возвращает XLSX |
| `GET /api/v1/export/finance` | ✅ 200 | — | Возвращает XLSX |
| `GET /api/v1/export/qe` | ✅ 200 | — | Возвращает XLSX |
| `GET /api/v1/export/production-overview` | ✅ 200 | — | Возвращает XLSX |
| `GET /api/v1/export/line-master` | ✅ 200 | — | Возвращает XLSX |

---

## Сводка фиксов

| # | Проблема | Затронутые ручки | Фикс |
|---|----------|-----------------|------|
| 1 | `total_quantity=None` crash в Pydantic | `/sales/top-products` | `Optional[Decimal] = None` в схеме или `COALESCE` в SQL |
| 2 | Missing `orders_*` fields в dict сервиса | `/orders/plan-execution` | Добавить `orders_planned/in_progress/completed/cancelled` в dict |
| 3 | `total_target`/`total_actual` отсутствуют при пустом `lines` | `/orders/plan-execution` | Вычислять из `lines` sum, по умолчанию 0 |
| 4 | Missing `delayed_orders`, `avg_delay_hours` в dict | `/orders/downtime` | Добавить поля в dict сервиса |
| 5 | `int.quantize()` AttributeError | `/orders/downtime` (с датами) | `Decimal(value).quantize(...)` вместо `value.quantize(...)` |
| 6 | `meta` обязательно но не возвращается сервисом | `/output/summary`, `/output/by-shift`, `/inventory/current` | `meta: Optional[...] = None` в схеме ответа |
| 7 | Ключ `product_line_id` vs `production_line` в схеме | `/kpi/line-productivity` | Переименовать ключ в сервисе |
