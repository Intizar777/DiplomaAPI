# Sync Audit: Найденные проблемы и план исправлений

> Дата аудита: 2026-05-09  
> Состояние БД на момент аудита: order_snapshots=5000, quality_results=71, sensor_readings=100, inventory_snapshots=34, aggregated_kpi=58 — все остальные таблицы пустые (0 строк).

---

## Сводка проблем по сервисам

### 1. `output_service.py` — КРИТИЧНО (сломан каждый cron-запуск)

**Проблема:** `NameError: name 'UUID' is not defined` — `UUID` используется в методе `upsert_from_event` (строка 141), но не импортирован в начале файла.

**Симптом в логах:** `output: failed` с ошибкой `NameError: name 'UUID' is not defined` при каждом запуске.

**Фикс:**
```python
# Добавить в начало файла:
from uuid import UUID
```

---

### 2. `product_service.py` — КРИТИЧНО (products таблица всегда пустая)

**Проблема:** Gateway возвращает `unitOfMeasure` как **строку** (`"kg"`, `"liters"`), а `sync_from_gateway` передаёт эту строку в `_sync_unit_of_measure(unit_data: dict)`, который вызывает `unit_data.get("id")` → `AttributeError: 'str' object has no attribute 'get'`. Исключение не поймано в цикле sync → весь sync продуктов падает без записи в sync_log.

**Симптом:** `products: running` в sync_logs (статус никогда не меняется на completed/failed), `products` таблица = 0 строк.

**Последствие:** Все сервисы, которые обогащают `product_name` из таблицы `products`, всегда получают `None`.

**Gateway docs (`GET /production/products`):**
```typescript
products: Array<{
  unitOfMeasure: string;  // строка, не объект
  ...
}>
```

**Фикс в `_sync_unit_of_measure`:** добавить обработку строкового аргумента — если `unit_data` это строка, создать/найти `UnitOfMeasure` по коду без ID (генерировать `uuid4()`).

```python
async def _sync_unit_of_measure(self, unit_data) -> Optional[UUID]:
    if not unit_data:
        return None
    # Gateway возвращает строку вместо объекта
    if isinstance(unit_data, str):
        code = unit_data.strip()
        if not code:
            return None
        existing = await self.db.execute(select(UnitOfMeasure).where(UnitOfMeasure.code == code))
        unit = existing.scalar_one_or_none()
        if not unit:
            unit = UnitOfMeasure(id=uuid4(), code=code, name=code)
            self.db.add(unit)
        return unit.id
    # Далее старая логика для объекта (dict)
    ...
```

---

### 3. `quality_service.py` — КРИТИЧНО (неправильное поле decision)

**Проблема 1:** Gateway возвращает поле `qualityStatus`, а код читает `result.get("decision", "pending")` → поле `decision` в response не существует → все 71 записей в БД имеют `decision = "pending"`.

**Gateway docs (`GET /production/quality`):**
```typescript
results: Array<{
  qualityStatus: QualityStatus;  // "approved" | "rejected" | "quarantine"
  // поля "decision" нет!
}>
```

**Фикс:** `result.get("qualityStatus", "pending").lower()`

---

**Проблема 2:** `spec_data = result.get("qualitySpec")` → Gateway **не** возвращает вложенный объект `qualitySpec`. Он возвращает поля `lowerLimit`, `upperLimit` **напрямую** в ответе. `spec_data` всегда `None` → `quality_spec_id` всегда `NULL`.

**Gateway docs:**
```typescript
results: Array<{
  lowerLimit: number;   // напрямую, не в объекте
  upperLimit: number;   // напрямую, не в объекте
  ...
}>
```

**Фикс:** Строить `spec_data` из inline-полей ответа:
```python
spec_data = {
    "id": result.get("id"),  # нет отдельного spec ID — используем result ID или пропускаем
    "lowerLimit": result.get("lowerLimit"),
    "upperLimit": result.get("upperLimit"),
    "isActive": True,
}
```

Примечание: у gateway нет отдельного ID для QualitySpec — нужно использовать `(product_id, parameter_name)` как натуральный ключ (уже реализовано в `_sync_quality_spec`), `spec_id` генерировать через `uuid4()`.

---

**Проблема 3:** `product_name=None` захардкожен — нет обогащения из таблицы `products`.

**Фикс:** Загружать `product_names` map перед циклом (как в output_service).

---

### 4. `order_service.py` — Данные неполные

**Проблема 1:** `raw_snapshot_id = order.get("snapshotId")` — Gateway никогда не возвращает поле `snapshotId`, он возвращает `id`. В результате `snapshot_id = None`, но SQLAlchemy генерирует UUID через default — то есть строки вставляются, но корреляция между snapshot и gateway-order потеряна. `order_id = order.get("id")` при этом всё равно заполняется корректно.

**Фикс:** Использовать `uuid4()` явно для snapshot `id` (смысл snapshot = новый снимок каждый день, gateway ID → `order_id`). Текущее поведение де-факто уже такое благодаря SQLAlchemy default, но код следует сделать явным:
```python
snapshot_id = uuid4()  # собственный ID snapshot
```

**Проблема 2:** `product_name=None` — нет обогащения.

**Фикс:** Загрузить product_names map и использовать `product_names.get(UUID(product_id))`.

**Проблема 3:** `production_line=order.get("productionLine")` — код корректный. По данным БД (5000 строк, production_line=NULL во всех), gateway **не** возвращает это поле в реальных данных (несмотря на документацию). **Обогащение невозможно без данных от gateway** — код правильный, проблема на стороне gateway или в качестве данных.

---

### 5. `sensor_service.py` + `gateway_client.py` — Неправильный endpoint

**Проблема:** `gateway_client.get_sensors()` запрашивает `/production/sensors` (список устройств-датчиков), но с ключом пагинации `"readings"`. Список датчиков возвращает ключ `"sensors"`, а не `"readings"` → результат всегда пустой список.

Реальные показания датчиков находятся по адресу `/production/sensor-readings` (возвращает `"readings": Array<{id, sensorId, deviceId, parameterName, value, unit, quality, recordedAt}>`).

**Симптом:** `sensors: completed` с 0 records, хотя в БД уже есть 100 строк sensor_readings (попали туда другим путём — через события).

**Фиксы:**
1. В `gateway_client.py`:
   - Переименовать `get_sensors()` → `get_sensor_list()`, исправить ключ `"readings"` → `"sensors"` (для синхронизации устройств)
   - Добавить новый метод `get_sensor_readings()` для `/production/sensor-readings` с ключом `"readings"`

2. В `sensor_service.sync_from_gateway()`:
   - Вызывать `gateway.get_sensor_readings()` вместо `gateway.get_sensors()`
   - Убрать синхронизацию вложенного объекта `sensor` (его нет в readings response)
   - Использовать `reading_data.get("sensorId")` для `sensor_id` (FK) — с предварительным поиском в таблице `sensors`

---

### 6. `inventory_service.py` — warehouse_id всегда NULL

**Проблема:** `warehouse_data = item_data.get("warehouse")` — вложенный объект `warehouse?` является **необязательным** в gateway response. Если его нет, `warehouse_id = None`. Gateway **всегда** возвращает `warehouseId: string` (UUID), но код его не использует для связи с существующей записью в `warehouses`.

**Gateway docs:**
```typescript
inventory: Array<{
  warehouseId: string;   // всегда есть
  warehouse?: { id, code, name, location };  // опционально
}>
```

**Фикс:** Если `warehouse` объект отсутствует, попробовать найти Warehouse по `item_data.get("warehouseId")`:
```python
warehouse_id = None
warehouse_data = item_data.get("warehouse")
if warehouse_data:
    warehouse_id = await self._sync_warehouse(warehouse_data)
elif item_data.get("warehouseId"):
    raw_wh_id = item_data.get("warehouseId")
    try:
        warehouse_id = UUID(raw_wh_id)
    except (ValueError, TypeError):
        pass
```

---

## Итоговый список изменений

| Файл | Тип | Описание |
|------|-----|----------|
| `app/services/output_service.py` | Fix | Добавить `from uuid import UUID` |
| `app/services/product_service.py` | Fix | `_sync_unit_of_measure` — обработка строки вместо dict |
| `app/services/quality_service.py` | Fix | `decision` → `qualityStatus`; qualitySpec из inline-полей; product_name обогащение |
| `app/services/order_service.py` | Fix | `snapshotId` → явный `uuid4()`; product_name обогащение |
| `app/services/gateway_client.py` | Fix | Rename `get_sensors` → `get_sensor_list` (ключ `"sensors"`); добавить `get_sensor_readings` (endpoint `/production/sensor-readings`, ключ `"readings"`) |
| `app/services/sensor_service.py` | Fix | Использовать `get_sensor_readings()`; убрать sync вложенного sensor; использовать `sensorId` для FK |
| `app/services/inventory_service.py` | Fix | Fallback на `warehouseId` поле если нет вложенного `warehouse` объекта |

---

## Порядок применения фиксов

1. `output_service.py` — независимый, применить первым (самый простой)
2. `product_service.py` — критично для всего downstream (product_name в остальных сервисах)
3. `quality_service.py`
4. `order_service.py`
5. `gateway_client.py` + `sensor_service.py` (взаимосвязаны, применять вместе)
6. `inventory_service.py`

---

## Что НЕ входит в этот план

- **`production_line` в orders_snapshot** — код корректный (`order.get("productionLine")`), проблема в данных gateway (поле возвращается пустым). Требует отдельного расследования на стороне gateway.
- **Пустые reference-таблицы** (`customers`, `warehouses`, `locations` и др.) — sync-логика в `_run_initial_sync` должна их заполнять, но требует отдельной диагностики. Возможно, gateway возвращает пустые коллекции.
- **`sales` и `kpi` синки в статусе "running"** — вероятно зависают из-за проблем с gateway или с логикой агрегации. Требует отдельного расследования.
- **Миграции** — изменений в схеме БД нет, только логика сервисов.
