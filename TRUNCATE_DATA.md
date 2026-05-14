# Полная очистка данных (TRUNCATE)

## ⚠️ ВНИМАНИЕ

Эта операция **удалит ВСЕ данные** из всех таблиц БД. Используйте только для:
- Разработки и тестирования
- Очистки перед полной переинициализацией
- Сброса состояния БД

## Использование

### Запустить truncate
```bash
python run_sync_job.py truncate
```

Система попросит подтверждение:
```
============================================================
⚠️  ВНИМАНИЕ: Это удалит ВСЕ данные из всех таблиц!
============================================================
Введите 'yes' для подтверждения: yes

▶️  Запуск: ⚠️  TRUNCATE ВСЕ ДАННЫЕ (опасно!) (truncate)
✅ Завершено: truncate
```

## Что будет удалено

Все таблицы:
- AggregatedKPI
- AggregatedSales
- SalesTrends
- SaleRecord
- OrderSnapshot
- QualityResult
- ProductionOutput
- SensorReading
- InventorySnapshot
- BatchInput
- DowntimeEvent
- PromoCampaign
- SyncLog
- SyncError
- QualitySpec
- Sensor
- Product
- SensorParameter
- Customer
- Warehouse
- UnitOfMeasure
- LineCapacityPlan
- KPIConfig
- ProductionLine

## Порядок удаления

1. **Сначала** удаляются транзакционные данные (заказы, продажи, выпуск и т.д.)
2. **Потом** удаляются справочные данные (продукты, параметры и т.д.)
3. Используется `CASCADE` для соблюдения FK ограничений

## После truncate

После очистки:
- БД полностью пуста
- Можно запустить полную синхронизацию: `python run_sync_job.py all`
- Все данные будут заново загружены из Gateway

## Пример: Полный сброс

```bash
# 1. Очистить все данные
python run_sync_job.py truncate

# 2. Загрузить все данные заново
python run_sync_job.py all

# 3. Проверить результат
curl http://localhost:8000/api/v1/sync/status
```

## Логирование

Операция логируется с уровнем WARNING:

```bash
tail -f logs/dashboard_api.log | grep truncate_all_data
```

Output:
```json
{
  "event": "truncate_all_data_started",
  "phase": "entry",
  "warning": "This will delete ALL data from all tables"
}
{
  "event": "truncate_table_done",
  "table": "aggregated_kpi"
}
...
{
  "event": "truncate_all_data_completed",
  "phase": "exit",
  "status": "success",
  "tables_truncated": 24
}
```

## Безопасность

- ✅ Требует явного подтверждения (`yes`)
- ✅ Логируется с WARNING уровнем
- ✅ Не может быть запущена случайно
- ✅ Использует транзакции для целостности

## Альтернативы

### Очистить только старые данные
```bash
python run_sync_job.py cleanup
```
Удалит данные старше 90 дней (настраивается в `RETENTION_DAYS`)

### Очистить конкретную таблицу
```bash
psql -d dashboard_api -c "TRUNCATE TABLE aggregated_kpi CASCADE;"
```

## Восстановление

Если случайно запустили truncate:
1. Восстановите из backup: `pg_restore -d dashboard_api backup.sql`
2. Или запустите полную синхронизацию: `python run_sync_job.py all`
