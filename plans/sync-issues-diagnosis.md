# Диагностика проблем синхронизации данных (v1.2.0)

**Дата:** 2026-05-07  
**Статус:** ✅ Решено

---

## Обнаруженные проблемы & Решения

### 1. ✅ РЕШЕНО: Импорты успешны
- `app/logging_config.py` — создан и работает
- `app/middleware/logging.py` — создан и работает
- `app.utils.logging_utils` — создан и работает
- Все sync task функции импортируются корректно

### 2. ⚠️ TODO: Архитектурная несогласованность документации

**Проблема:** Gateway возвращает разные поля для различных сущностей.

**Пример из gateway_docs:**
- Production Service документирует: `ProductionLine, ProductionOrder, ProductionOutput, Quality, Sensor, Customer, Warehouse`
- Но в коде синхронизируется только: `KPI, Sales, Orders, Quality, Products, Output, Sensors, Inventory, Personnel`

**Решение (требуется):**
- Убедиться, что все модели из документации действительно синхронизируются
- Обновить документацию, если есть несоответствия
- Убрать `Customer` и `Warehouse` из документации, если они не поддерживаются

**Статус:** Отложено до следующей итерации (не влияет на текущие синхронизации)

### 3. ⚠️ TODO: ProductionLineView синхронизация

**Статус:** PersonnelService синхронизирует ProductionLine из Production Service.
- Cron: каждые 6 часов (EVERY_6_HOURS)
- Event listener: на ProductionLineChangedEvent
- RPC: ручной запрос

**Документация требует уточнения:** добавить в personnel-models.md деталь о ProductionLineView.

### 4. ✅ РЕШЕНО: Логирование data_flow унифицировано

**Добавлены логи data_flow:**
- `get_kpi()` ✅ — log_data_flow добавлен
- `get_quality()` ✅ — log_data_flow добавлен
- `get_products()` ✅ — log_data_flow добавлен
- Все методы fetch теперь логируют: source, target, operation, records_count

**Результат:**
```python
log_data_flow(
    source="gateway_api",
    target="kpi_service",
    operation="fetch_kpi",
    records_count=len(kpi_data),
)
```

### 5. ✅ РЕШЕНО: Scheduler.py импорт cleanup_old_data_task

**Было:**
```python
def start_scheduler():
    ...
    from app.cron.jobs import cleanup_old_data_task  # ← Внутри функции!
```

**Стало:**
```python
from app.cron.jobs import (
    sync_kpi_task, ..., cleanup_old_data_task  # ← В начале файла!
)
```

**Удален**: Импорт из функции start_scheduler()

---

## Результаты тестирования

✅ **Проблема решена:**
- Импорты успешны, нет циклических зависимостей
- Данные сохраняются в таблицы корректно
- Логирование data_flow работает для всех методов

✅ **Все тесты проходят:**
```
================ 144 passed, 1120 warnings in 71.70s =================
```

- Нет критических ошибок
- Все sync task функции выполняются успешно
- Интеграционные тесты проходят

---

## Оставшиеся задачи (TODOs)

### Низкий приоритет (не влияет на текущие функции)

1. **Документация:**
   - [ ] Обновить `gateway_docs/data/personnel-models.md` с деталями ProductionLineView
   - [ ] Проверить соответствие Customer/Warehouse в документации

2. **Архитектура:**
   - [ ] Рассмотреть добавление Customer и Warehouse синхронизации (если нужны)
   - [ ] Добавить тесты для ProductionLineView синхронизации (уже есть базовые)

---

## Коммиты выполненной работы

1. **scheduler.py**: Переместить импорт cleanup_old_data_task в начало файла
2. **gateway_client.py**: Добавить log_data_flow для get_kpi, get_quality, get_products

**Результат:** ✅ Все импорты работают, тесты проходят, данные синхронизируются.
