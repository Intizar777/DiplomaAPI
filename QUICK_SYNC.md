# Быстрая шпаргалка: Запуск задач синхронизации

## Основные команды

```bash
# Список всех задач
python run_sync_job.py list

# Одна задача
python run_sync_job.py kpi
python run_sync_job.py sales
python run_sync_job.py orders

# Все задачи
python run_sync_job.py all
```

## Популярные сценарии

### Синхронизировать KPI
```bash
python run_sync_job.py kpi
python run_sync_job.py kpi_per_line
```

### Синхронизировать продажи
```bash
python run_sync_job.py sales
python run_sync_job.py aggregate_sales_trends
```

### Синхронизировать заказы и выпуск
```bash
python run_sync_job.py orders
python run_sync_job.py output
```

### Синхронизировать качество
```bash
python run_sync_job.py quality
python run_sync_job.py quality_specs
```

### Полная синхронизация (все данные)
```bash
python run_sync_job.py all
```

## Проверка статуса

```bash
# Последние синхронизации
curl http://localhost:8000/api/v1/sync/status

# Логи
tail -f logs/dashboard_api.log | grep sync_task
```

## Если что-то не работает

1. **Проверить Gateway**
   ```bash
   curl http://localhost:3000/api/health
   ```

2. **Проверить переменные окружения**
   ```bash
   echo $GATEWAY_URL
   echo $GATEWAY_AUTH_EMAIL
   ```

3. **Посмотреть логи**
   ```bash
   tail -100 logs/dashboard_api.log
   ```

4. **Запустить с отладкой**
   ```bash
   LOG_LEVEL=DEBUG python run_sync_job.py kpi
   ```

## Все доступные задачи

- `references` - Справочные таблицы
- `products` - Продукты
- `quality_specs` - Спецификации качества
- `kpi` - KPI производства
- `kpi_per_line` - KPI по линиям
- `sales` - Продажи
- `orders` - Заказы
- `quality` - Качество
- `output` - Выпуск продукции
- `sensors` - Датчики
- `inventory` - Инвентарь
- `batch_inputs` - Входные партии
- `downtime_events` - События простоя
- `promo_campaigns` - Промо-кампании
- `aggregate_sales_trends` - Агрегация трендов
- `cleanup` - Очистка старых данных
