# Запуск задач синхронизации вручную

## Быстрый старт

### Список всех задач
```bash
python run_sync_job.py list
```

### Запустить одну задачу
```bash
python run_sync_job.py kpi
python run_sync_job.py sales
python run_sync_job.py orders
```

### Запустить все задачи
```bash
python run_sync_job.py all
```

## Доступные задачи

| Команда | Описание | Зависимости |
|---------|---------|-------------|
| `references` | Справочные таблицы (локации, отделы, должности, сотрудники) | - |
| `products` | Продукты | references |
| `quality_specs` | Спецификации качества | products |
| `kpi` | KPI производства (агрегированные) | - |
| `kpi_per_line` | KPI по производственным линиям | - |
| `sales` | Продажи | - |
| `orders` | Производственные заказы | - |
| `quality` | Результаты контроля качества | - |
| `output` | Выпуск продукции | - |
| `sensors` | Показания датчиков | - |
| `inventory` | Остатки на складах | - |
| `batch_inputs` | Входные партии сырья | - |
| `downtime_events` | События простоя линий | - |
| `promo_campaigns` | Промо-кампании | - |
| `aggregate_sales_trends` | Агрегация трендов продаж | sales |
| `cleanup` | Очистка старых данных | - |

## Примеры

### Синхронизировать только KPI
```bash
python run_sync_job.py kpi
```

Output:
```
▶️  Запуск: KPI производства (kpi)
✅ Завершено: kpi
```

### Синхронизировать продажи и тренды
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
✅ Спецификации качества
...

Всего: 16/16 успешно
```

## Порядок выполнения при `all`

Задачи выполняются в определенном порядке для соблюдения зависимостей:

1. **Уровень 0 (справочные данные)**
   - references → products → quality_specs

2. **Уровень 1 (транзакционные данные)**
   - kpi, kpi_per_line, sales, orders, quality, output, sensors, inventory, batch_inputs, downtime_events, promo_campaigns

3. **Уровень 2 (локальные агрегации)**
   - aggregate_sales_trends

## Логирование

Все операции логируются в структурированном формате JSON:

```bash
# Просмотр логов
tail -f logs/dashboard_api.log | grep sync_task

# Фильтр по задаче
tail -f logs/dashboard_api.log | grep "task=kpi"
```

## Обработка ошибок

Если задача упадет:

```bash
python run_sync_job.py sales
# ❌ Ошибка в sales: Connection timeout
```

Проверьте:
1. Gateway API доступен: `curl http://localhost:3000/api/health`
2. Переменные окружения: `GATEWAY_URL`, `GATEWAY_AUTH_EMAIL`, `GATEWAY_AUTH_PASSWORD`
3. Логи: `tail -f logs/dashboard_api.log`

## Интеграция с cron

Текущее расписание (в `app/cron/scheduler.py`):

```
00:00 - references
00:05 - products
00:10 - quality_specs
00:15 - kpi
00:20 - kpi_per_line
00:25 - sales
00:30 - orders
00:35 - quality
00:40 - output
00:45 - sensors
00:48 - inventory
00:50 - batch_inputs
00:52 - downtime_events
00:54 - promo_campaigns
00:57 - aggregate_sales_trends
```

Для ручного запуска используйте `run_sync_job.py`.

## Мониторинг

Проверить статус последней синхронизации:

```bash
# Через API
curl http://localhost:8000/api/v1/sync/status

# Через БД
psql -d dashboard_api -c "SELECT * FROM sync_log ORDER BY created_at DESC LIMIT 10;"
```

## Отладка

Запустить задачу с подробным логированием:

```bash
LOG_LEVEL=DEBUG python run_sync_job.py kpi
```

Это выведет все запросы к Gateway API и детали обработки данных.
