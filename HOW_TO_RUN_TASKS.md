# Как запускать задачи синхронизации

## 3 способа запуска

### 1️⃣ Автоматически (по расписанию)
Задачи запускаются автоматически каждый час согласно расписанию в `app/cron/scheduler.py`:
- 00:00 - references
- 00:05 - products
- 00:10 - quality_specs
- 00:15 - kpi
- ... и т.д.

**Ничего делать не нужно** — работает в фоне при запуске приложения.

### 2️⃣ Через API
```bash
# Проверить статус
curl http://localhost:8000/api/v1/sync/status

# Запустить синхронизацию вручную
curl -X POST http://localhost:8000/api/v1/sync/trigger
```

### 3️⃣ Через CLI (рекомендуется для отладки)
```bash
# Список всех задач
python run_sync_job.py list

# Одна задача
python run_sync_job.py kpi

# Все задачи
python run_sync_job.py all
```

## Примеры использования

### Синхронизировать только KPI
```bash
python run_sync_job.py kpi
```

### Синхронизировать продажи
```bash
python run_sync_job.py sales
python run_sync_job.py aggregate_sales_trends
```

### Полная синхронизация
```bash
python run_sync_job.py all
```

Output:
```
============================================================
Запуск всех задач синхронизации
============================================================

▶️  Запуск: Справочные таблицы (references)
✅ Завершено: references

▶️  Запуск: Продукты (products)
✅ Завершено: products

...

============================================================
ИТОГИ
============================================================
✅ Справочные таблицы
✅ Продукты
...

Всего: 16/16 успешно
```

## Доступные задачи

```
references          - Справочные таблицы (локации, отделы, должности, сотрудники)
products            - Продукты
quality_specs       - Спецификации качества
kpi                 - KPI производства (агрегированные)
kpi_per_line        - KPI по производственным линиям
sales               - Продажи
orders              - Производственные заказы
quality             - Результаты контроля качества
output              - Выпуск продукции
sensors             - Показания датчиков
inventory           - Остатки на складах
batch_inputs        - Входные партии сырья
downtime_events     - События простоя линий
promo_campaigns     - Промо-кампании
aggregate_sales_trends - Агрегация трендов продаж
cleanup             - Очистка старых данных
```

## Проверка результатов

### Через API
```bash
curl http://localhost:8000/api/v1/sync/status
```

Response:
```json
{
  "lastSync": "2026-05-14T19:57:30.000Z",
  "status": "completed",
  "recordsProcessed": 15234,
  "nextSync": "2026-05-14T20:00:00.000Z"
}
```

### Через БД
```bash
psql -d dashboard_api -c "
  SELECT task_name, status, records_processed, completed_at 
  FROM sync_log 
  ORDER BY created_at DESC 
  LIMIT 10;
"
```

### Через логи
```bash
tail -f logs/dashboard_api.log | grep sync_task
```

## Отладка

### Запустить с подробным логированием
```bash
LOG_LEVEL=DEBUG python run_sync_job.py kpi
```

### Проверить доступность Gateway
```bash
curl http://localhost:3000/api/health
```

### Проверить конфигурацию
```bash
python -c "from app.config import settings; print(f'Gateway: {settings.gateway_url}')"
```

## Файлы

- `run_sync_job.py` - CLI для запуска задач вручную
- `app/cron/scheduler.py` - Автоматическое расписание
- `app/cron/jobs.py` - Определения задач
- `MANUAL_SYNC.md` - Подробная документация
- `QUICK_SYNC.md` - Быстрая шпаргалка

## Рекомендации

1. **Для разработки:** Используйте `python run_sync_job.py <task>` для тестирования отдельных задач
2. **Для отладки:** Запускайте с `LOG_LEVEL=DEBUG` для подробных логов
3. **Для production:** Полагайтесь на автоматическое расписание в `scheduler.py`
4. **Для мониторинга:** Проверяйте `sync_log` таблицу в БД

---

**Готово!** Теперь ты можешь запускать задачи как вручную, так и автоматически.
