# Анализ задач синхронизации и таблиц

## Обзор

В `app/cron/jobs.py` определено **14 основных задач синхронизации**, которые заполняют **20+ таблиц** в PostgreSQL.

---

## Задачи синхронизации и их таблицы

### 1. **sync_kpi_task()** → `AggregatedKPI`
- **Период**: 30 дней назад от воскресенья текущей недели
- **Таблица**: `aggregated_kpi`
- **Назначение**: Агрегированные KPI метрики по периодам и линиям производства
- **Поля**: total_output, defect_rate, completed_orders, oee_estimate, avg_order_completion_time
- **Уникальность**: (period_from, period_to, production_line)

### 2. **sync_kpi_per_line_task()** → `AggregatedKPI`
- **Период**: 30 дней назад от воскресенья текущей недели
- **Таблица**: `aggregated_kpi` (та же, что и выше)
- **Метод**: `sync_kpi_per_line` (отдельный метод в KPIService)
- **Назначение**: KPI по каждой линии отдельно (детализация)

### 3. **sync_sales_task()** → `AggregatedSales` + `SaleRecord`
- **Период**: 30 дней назад до сегодня
- **Таблицы**:
  - `aggregated_sales` — агрегированные продажи (по регионам, каналам, продуктам)
  - `sale_records` — сырые записи продаж (нормализованы с FK на customers)
- **Поля**: total_quantity, total_amount, sales_count, avg_order_value
- **Уникальность**: (period_from, period_to, group_by_type, group_key)

### 4. **sync_orders_task()** → `OrderSnapshot`
- **Период**: 1 день назад до сегодня
- **Таблица**: `order_snapshots`
- **Назначение**: Исторические снимки производственных заказов
- **Поля**: order_id, product_id, target_quantity, actual_quantity, status, production_line, planned/actual dates
- **Уникальность**: (order_id, snapshot_date)

### 5. **sync_quality_task()** → `QualityResult`
- **Период**: 7 дней назад до сегодня
- **Таблица**: `quality_results`
- **Назначение**: Результаты контроля качества
- **Поля**: lot_number, product_id, parameter_name, result_value, decision (PASS/FAIL/REWORK)
- **Уникальность**: event_id (для идемпотентности)
- **FK**: quality_spec_id → quality_specs

### 6. **sync_products_task()** → `Product`
- **Период**: Полная синхронизация (full_sync=True)
- **Таблица**: `products`
- **Назначение**: Справочник продуктов
- **Поля**: code, name, category, brand, unit_of_measure_id, shelf_life_days, requires_quality_check
- **Уникальность**: code (unique)
- **FK**: unit_of_measure_id → units_of_measure

### 7. **sync_output_task()** → `ProductionOutput`
- **Период**: 1 день назад до сегодня
- **Таблица**: `production_output`
- **Назначение**: Записи производственного выпуска (партии/лоты)
- **Поля**: order_id, product_id, lot_number, quantity, quality_status, production_date, shift
- **Уникальность**: event_id (для идемпотентности)

### 8. **sync_sensors_task()** → `SensorReading`
- **Период**: 30 дней назад до сегодня
- **Таблица**: `sensor_readings`
- **Назначение**: История показаний IoT датчиков
- **Поля**: sensor_id, value, quality, recorded_at
- **FK**: sensor_id → sensors (каскадное удаление)

### 9. **sync_inventory_task()** → `InventorySnapshot`
- **Период**: Полная синхронизация (full_sync=True)
- **Таблица**: `inventory_snapshots`
- **Назначение**: Снимки уровней запасов на складах
- **Поля**: product_id, warehouse_id, lot_number, quantity, last_updated
- **FK**: warehouse_id → warehouses
- **Уникальность**: event_id (для идемпотентности)

### 10. **sync_references_task()** → Справочные таблицы
- **Период**: Полная синхронизация (full_sync=True)
- **Таблицы** (3 отдельных блока try/except):
  
  **a) UnitOfMeasure** (`units_of_measure`)
  - Единицы измерения (кг, литры, штуки и т.д.)
  - Уникальность: code (unique)
  
  **b) Customer** (`customers`)
  - Справочник клиентов
  - Поля: name, code, region, is_active
  - Уникальность: code (unique)
  - FK: используется в sale_records
  
  **c) Warehouse** (`warehouses`)
  - Справочник складов
  - Поля: name, code, capacity, is_active
  - Уникальность: code (unique)
  - FK: используется в inventory_snapshots

### 11. **sync_batch_inputs_task()** → `BatchInput`
- **Период**: 7 дней назад до сегодня
- **Таблица**: `batch_inputs`
- **Назначение**: Входные материалы для производственных партий
- **Сервис**: BatchInputService

### 12. **sync_downtime_events_task()** → `DowntimeEvent`
- **Период**: 7 дней назад до сегодня
- **Таблица**: `downtime_events`
- **Назначение**: События простоев производства
- **Сервис**: DowntimeEventService

### 13. **sync_promo_campaigns_task()** → `PromoCampaign`
- **Период**: 30 дней назад до 30 дней вперед
- **Таблица**: `promo_campaigns`
- **Назначение**: Промо-кампании
- **Сервис**: PromoCampaignService

### 14. **aggregate_sales_trends_task()** → `SalesTrends`
- **Период**: 35 дней назад до сегодня
- **Таблица**: `sales_trends`
- **Назначение**: Агрегированные тренды продаж по дням/неделям/месяцам
- **Источник**: Агрегирует данные из `sale_records`
- **Интервалы**: day, week, month
- **Уникальность**: (trend_date, interval_type, region, channel)

### 15. **cleanup_old_data_task()** → Удаление старых данных
- **Период**: Удаляет записи старше `settings.retention_days` (по умолчанию 90 дней)
- **Таблицы для очистки**:
  - `order_snapshots`
  - `quality_results`
  - `production_output`
  - `sensor_readings`
  - `inventory_snapshots`
  - `sale_records`
  - `sync_logs`

### 16. **sync_quality_specs_task()** → `QualitySpec`
- **Период**: Полная синхронизация (full_sync=True)
- **Таблица**: `quality_specs`
- **Назначение**: Спецификации качества для продуктов (нормализованы отдельно от результатов)
- **Поля**: product_id, parameter_name, lower_limit, upper_limit, is_active
- **Сервис**: reference_sync.upsert_quality_spec

---

## Матрица таблиц и их заполнение

| Таблица | Задача | Период | Тип | Уникальность |
|---------|--------|--------|-----|--------------|
| aggregated_kpi | sync_kpi_task, sync_kpi_per_line_task | 30 дн | Агрегат | (period_from, period_to, production_line) |
| aggregated_sales | sync_sales_task | 30 дн | Агрегат | (period_from, period_to, group_by_type, group_key) |
| sale_records | sync_sales_task | 30 дн | Сырые | event_id |
| sales_trends | aggregate_sales_trends_task | 35 дн | Агрегат | (trend_date, interval_type, region, channel) |
| order_snapshots | sync_orders_task | 1 дн | Снимок | event_id |
| quality_results | sync_quality_task | 7 дн | Результат | event_id |
| quality_specs | sync_quality_specs_task | Full | Справочник | product_id + parameter_name |
| products | sync_products_task | Full | Справочник | code |
| production_output | sync_output_task | 1 дн | Сырые | event_id |
| sensor_readings | sync_sensors_task | 30 дн | Сырые | - |
| inventory_snapshots | sync_inventory_task | Full | Снимок | event_id |
| units_of_measure | sync_references_task | Full | Справочник | code |
| customers | sync_references_task | Full | Справочник | code |
| warehouses | sync_references_task | Full | Справочник | code |
| batch_inputs | sync_batch_inputs_task | 7 дн | Сырые | - |
| downtime_events | sync_downtime_events_task | 7 дн | Сырые | - |
| promo_campaigns | sync_promo_campaigns_task | 30 дн ± | Справочник | - |
| sync_logs | cleanup_old_data_task | Full | Логи | - |

---

## Иерархия зависимостей

```
Справочники (Full sync):
├── units_of_measure
├── customers
├── warehouses
├── products (зависит от units_of_measure)
├── quality_specs (зависит от products)
└── sensors (зависит от production_lines, sensor_parameters)

Сырые данные (Incremental):
├── sale_records (зависит от customers, products)
├── order_snapshots (зависит от products)
├── quality_results (зависит от quality_specs, products)
├── production_output (зависит от products)
├── sensor_readings (зависит от sensors)
├── inventory_snapshots (зависит от warehouses, products)
├── batch_inputs
├── downtime_events
└── promo_campaigns

Агрегированные данные (Derived):
├── aggregated_kpi (из production_output, quality_results)
├── aggregated_sales (из sale_records)
├── sales_trends (из sale_records)
└── cleanup_old_data (удаляет старые сырые данные)
```

---

## Ключевые паттерны

### Идемпотентность
- Используется `event_id` (UUID) для отслеживания уже обработанных событий
- Таблицы: sale_records, order_snapshots, quality_results, production_output, inventory_snapshots

### Нормализация
- Справочные таблицы (customers, warehouses, units_of_measure) связаны через FK
- Денормализация имен для удобства отчетов (warehouse_name, product_name в inventory_snapshots)

### Периоды синхронизации
- **Full sync**: products, quality_specs, customers, warehouses, units_of_measure, inventory_snapshots
- **30 дней**: KPI, sales, sensors, promo_campaigns
- **7 дней**: quality, batch_inputs, downtime_events
- **1 день**: orders, production_output
- **35 дней**: sales_trends (для охвата границ недель/месяцев)

### Очистка данных
- Retention: 90 дней (настраивается в settings.retention_days)
- Удаляются: order_snapshots, quality_results, production_output, sensor_readings, inventory_snapshots, sale_records, sync_logs

---

## Обработка ошибок

### Общий паттерн (_run_sync_task)
- Создает SyncLog запись
- Логирует entry/checkpoint/exit
- При ошибке: полный traceback, тип ошибки, сообщение
- Статусы: RUNNING → COMPLETED или FAILED

### Специальный паттерн (sync_references_task)
- Каждый справочник в отдельном try/except
- Ошибка в одном не убивает остальные
- Финальный статус: COMPLETED (если хотя бы один успешен) или FAILED

---

## Сервисы, используемые в синхронизации

| Сервис | Таблицы | Методы |
|--------|---------|--------|
| KPIService | aggregated_kpi | sync_from_gateway, sync_kpi_per_line |
| SalesService | aggregated_sales, sale_records | sync_from_gateway |
| OrderService | order_snapshots | sync_from_gateway |
| QualityService | quality_results | sync_from_gateway |
| ProductService | products | sync_from_gateway |
| OutputService | production_output | sync_from_gateway |
| SensorService | sensor_readings | sync_from_gateway |
| InventoryService | inventory_snapshots | sync_from_gateway |
| BatchInputService | batch_inputs | sync_from_gateway |
| DowntimeEventService | downtime_events | sync_from_gateway |
| PromoCampaignService | promo_campaigns | sync_from_gateway |
| reference_sync | units_of_measure, customers, warehouses, quality_specs | upsert_* |

