# Как работает синхронизация KPI

## Два режима синхронизации

### 1️⃣ Initial Sync (первая синхронизация)

**Когда:** Когда таблица `aggregated_kpi` пуста

**Как вызывается:**
```python
await kpi_service.sync_from_gateway(from_date=None, to_date=None)
```

**Что происходит:**

1. **Период:** 2024-01-01 до сегодня
2. **Гранулярность:** По месяцам
3. **Для каждого месяца:**
   - Запрашивает KPI у Gateway: `GET /production/kpi?from=2024-01-01&to=2024-01-31`
   - Если `totalOrders > 0` → сохраняет в БД
   - Иначе пропускает месяц

**Пример:**
```
2024-01-01 to 2024-01-31 → GET /production/kpi → сохранено
2024-02-01 to 2024-02-29 → GET /production/kpi → сохранено
2024-03-01 to 2024-03-31 → GET /production/kpi → сохранено
...
2026-05-01 to 2026-05-14 → GET /production/kpi → сохранено
```

**Результат:** БД содержит KPI за каждый месяц с 2024-01 по сегодня

### 2️⃣ Incremental Sync (регулярная синхронизация)

**Когда:** Каждый час по расписанию (в `sync_kpi_task`)

**Как вызывается:**
```python
today = date.today()
monday = today - timedelta(days=today.weekday())  # Понедельник текущей недели
sunday = monday + timedelta(days=6)               # Воскресенье текущей недели
from_date = sunday - timedelta(days=30)           # 30 дней назад от воскресенья
to_date = sunday                                  # Воскресенье текущей недели

await kpi_service.sync_from_gateway(from_date=from_date, to_date=to_date)
```

**Что происходит:**

1. **Период:** Последние 30 дней + текущая неделя до воскресенья
2. **Гранулярность:** Один запрос на весь период
3. **Запрос:** `GET /production/kpi?from=2026-04-14&to=2026-05-12`
4. **Сохранение:** Одна запись за весь период (upsert)

**Пример (сегодня 2026-05-14, среда):**
```
Понедельник текущей недели: 2026-05-12
Воскресенье текущей недели: 2026-05-18
30 дней назад от воскресенья: 2026-04-18

Запрос: GET /production/kpi?from=2026-04-18&to=2026-05-18
Сохранено: 1 запись (period_from=2026-04-18, period_to=2026-05-18)
```

## Сравнение

| Параметр | Initial Sync | Incremental Sync |
|----------|--------------|------------------|
| **Когда** | Первый раз | Каждый час |
| **Период** | 2024-01 до сегодня | Последние 30 дней + текущая неделя |
| **Гранулярность** | По месяцам | Один период |
| **Запросов к Gateway** | ~30 (по месяцам) | 1 |
| **Записей в БД** | ~30 | 1 (upsert) |
| **Время выполнения** | Долгое | Быстрое |

## Логика в коде

### Initial Sync (from_date=None, to_date=None)

```python
if from_date and to_date:
    # Incremental sync
    ...
else:
    # Initial sync: fetch KPI for each month from 2024-01 to now
    start = date(2024, 1, 1)
    end = date.today()
    
    current = start
    while current <= end:
        # Для каждого месяца
        month_start = date(year, month, 1)
        month_end = date(year, month, last_day)
        
        kpi_response = await self.gateway.get_kpi(
            from_date=month_start, 
            to_date=month_end
        )
        
        if kpi_response.totalOrders > 0:
            # Сохранить месячные данные
            aggregated = AggregatedKPI(
                period_from=month_start,
                period_to=month_end,
                ...
            )
            self.db.add(aggregated)
```

### Incremental Sync (from_date и to_date заданы)

```python
if from_date and to_date:
    # Incremental sync: single period (upsert)
    kpi_response = await self.gateway.get_kpi(from_date, to_date)
    
    # Upsert: если запись существует, обновить; иначе создать
    stmt = insert(AggregatedKPI).values(
        period_from=from_date,
        period_to=to_date,
        ...
    ).on_conflict_do_update(
        index_elements=['period_from', 'period_to', 'production_line'],
        set_={...}
    )
```

## Как это вызывается

### В cron/jobs.py

```python
async def sync_kpi_task():
    """Sync KPI data from Gateway (aggregated across all lines)."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    from_date = sunday - timedelta(days=30)
    to_date = sunday

    from app.models import AggregatedKPI
    await _run_sync_task(
        task_name="kpi",
        model_class=AggregatedKPI,
        service_class=KPIService,
        from_date=from_date,
        to_date=to_date,
    )
```

### В _run_sync_task

```python
async def _run_sync_task(...):
    ...
    service = service_class(db, gateway)
    
    # Проверяет: есть ли уже данные в таблице?
    if full_sync or not await _has_any_records(model_class):
        # Initial sync (первый раз)
        records = await service.sync_from_gateway(None, None)
    else:
        # Incremental sync (регулярно)
        records = await service.sync_from_gateway(from_date, to_date)
```

## Пример: Полный цикл

### День 1: Первая синхронизация

```bash
$ python run_sync_job.py kpi

# Таблица пуста → Initial sync
# Запрашивает KPI за каждый месяц с 2024-01 по 2026-05
# Сохраняет ~30 записей (по месяцам)

✅ Завершено: kpi
```

### День 2: Регулярная синхронизация (каждый час)

```bash
# Автоматически в 00:15 каждый день

# Таблица не пуста → Incremental sync
# Запрашивает KPI за последние 30 дней + текущая неделя
# Обновляет 1 запись (upsert)

✅ Завершено: kpi
```

## Почему так?

1. **Initial sync по месяцам:** Нужна история за 2+ года
2. **Incremental sync за период:** Быстрее, чем по месяцам
3. **Upsert:** Если данные изменились, обновляет; если нет, оставляет
4. **30 дней + текущая неделя:** Покрывает возможные задержки в обновлении данных

## Итого

- **Initial:** 2024-01 → сегодня, по месяцам, ~30 запросов
- **Incremental:** Последние 30 дней + текущая неделя, 1 запрос, upsert
