# Dashboard Reports Structure

Предложения по структуре отчётов для всех 5 дашбордов.  
Основано на реальных таблицах БД: `aggregated_kpi`, `order_snapshots`, `quality_results`, `quality_specs`, `production_output`, `aggregated_sales`, `inventory_snapshots`.

---

## Wave 1 — Line Master Dashboard (`/api/v1/dashboards/line-master`)

**Роль:** Мастер производственной линии. Нужен оперативный контроль смены.

---

### Отчёт 1: Прогресс смены (`/shift-progress`)

**Назначение:** Сколько лотов выпущено в каждую смену за выбранную дату.

**Параметры запроса:**
- `production_date` (date, default: today)

**Структура ответа:**

```json
{
  "production_date": "2026-05-09",
  "shifts": [
    {
      "shift": "Shift 1",
      "lot_count": 12,
      "total_quantity": "1450.000",
      "approved_count": 11,
      "defect_count": 1,
      "defect_rate": "8.33"
    },
    {
      "shift": "Shift 2",
      "lot_count": 9,
      "total_quantity": "1080.000",
      "approved_count": 9,
      "defect_count": 0,
      "defect_rate": "0.00"
    },
    {
      "shift": "Shift 3",
      "lot_count": 7,
      "total_quantity": "840.000",
      "approved_count": 6,
      "defect_count": 1,
      "defect_rate": "14.29"
    }
  ]
}
```

**Источник данных:** `production_output` JOIN `quality_results` (по `lot_number`)

---

### Отчёт 2: Сравнение смен (`/shift-comparison`)

**Назначение:** Динамика по сменам за период — для выявления просадок и аномалий.

**Параметры запроса:**
- `date_from` (date, default: today-7)
- `date_to` (date, default: today)

**Структура ответа:**

```json
{
  "period_from": "2026-05-02",
  "period_to": "2026-05-09",
  "data": [
    {
      "production_date": "2026-05-02",
      "shift": "Shift 1",
      "lot_count": 10,
      "total_quantity": "1200.000",
      "defect_rate": "10.00"
    }
  ]
}
```

**Визуализация (рекомендация):** Линейный график по датам, три линии (по сменам), ось Y = defect_rate или lot_count.

---

### Отчёт 3: Сводка дефектов (`/defect-summary`)

**Назначение:** Разбивка дефектов по параметрам — для поиска узких мест в контроле качества.

**Параметры запроса:**
- `date_from`, `date_to`

**Структура ответа:**

```json
{
  "period_from": "2026-05-02",
  "period_to": "2026-05-09",
  "parameters": [
    {
      "parameter_name": "pH",
      "total_tests": 48,
      "fail_count": 6,
      "fail_rate": "12.50"
    },
    {
      "parameter_name": "viscosity",
      "total_tests": 48,
      "fail_count": 2,
      "fail_rate": "4.17"
    }
  ]
}
```

**Визуализация (рекомендация):** Горизонтальный bar chart с сортировкой по `fail_rate` DESC.

---

## Wave 2 — Group Manager Dashboard (`/api/v1/dashboards/gm`)

**Роль:** Групповой менеджер. Нужна стратегическая картина по всем линиям.

---

### Отчёт 4: OEE по линиям (`/oee-summary`)

**Назначение:** Эффективность каждой линии (OEE) с трендом и сравнением с целевым значением.

**Параметры запроса:**
- `period_days` (int: 7 | 30 | 90, default: 30)

**Структура ответа:**

```json
{
  "period_days": 30,
  "target_oee": 75.0,
  "lines": [
    {
      "production_line": "Line-1",
      "avg_oee": "81.50",
      "vs_target": "+6.50",
      "rank": 1,
      "trend": [
        {"period_from": "2026-04-09", "period_to": "2026-04-15", "oee_estimate": "79.00"},
        {"period_from": "2026-04-16", "period_to": "2026-04-22", "oee_estimate": "83.00"}
      ]
    },
    {
      "production_line": "Line-2",
      "avg_oee": "68.30",
      "vs_target": "-6.70",
      "rank": 2,
      "trend": []
    }
  ]
}
```

**Источник данных:** `aggregated_kpi.oee_estimate`  
**Визуализация (рекомендация):** Taблица с цветовой индикацией (зелёный > 75%, красный < 75%) + мини-спарклайны тренда.

---

### Отчёт 5: Исполнение плана (`/plan-execution`)

**Назначение:** Сравнение план/факт по количеству продукции на каждой линии.

**Параметры запроса:**
- `date_from`, `date_to`

**Структура ответа:**

```json
{
  "period_from": "2026-04-09",
  "period_to": "2026-05-09",
  "lines": [
    {
      "production_line": "Line-1",
      "target_quantity": "50000.000",
      "actual_quantity": "47500.000",
      "fulfillment_pct": "95.00",
      "completed_orders": 18,
      "total_orders": 20,
      "in_progress_orders": 2,
      "overdue_orders": 0
    }
  ]
}
```

**Источник данных:** `order_snapshots` (GROUP BY `production_line`)  
**Визуализация (рекомендация):** Grouped bar chart (план vs факт) + таблица со статусом заказов.

---

### Отчёт 6: Рейтинг простоев (`/downtime-ranking`)

**Назначение:** Линии, отранжированные по суммарному опозданию (Парето-анализ).

**Параметры запроса:**
- `date_from`, `date_to`

**Структура ответа:**

```json
{
  "period_from": "2026-04-09",
  "period_to": "2026-05-09",
  "lines": [
    {
      "production_line": "Line-3",
      "total_delay_hours": "48.50",
      "order_count": 12,
      "avg_delay_per_order": "4.04",
      "rank": 1,
      "cumulative_pct": "42.00"
    },
    {
      "production_line": "Line-1",
      "total_delay_hours": "32.00",
      "order_count": 18,
      "avg_delay_per_order": "1.78",
      "rank": 2,
      "cumulative_pct": "70.00"
    }
  ],
  "total_delay_hours": "115.50"
}
```

**Источник данных:** `order_snapshots` (только завершённые; `actual_end - planned_end`)  
**Визуализация (рекомендация):** Pareto chart — столбцы (delay_hours) + линия (cumulative_pct).

---

## Wave 3 — Quality Engineer Dashboard (`/api/v1/dashboards/qe`)

**Роль:** Инженер качества. Нужен глубокий анализ параметров и отклонений.

---

### Отчёт 7: Тренды параметров (`/parameter-trends`)

**Назначение:** Динамика каждого контрольного параметра по дням с полосами допусков.

**Параметры запроса:**
- `date_from` (default: today-30), `date_to` (default: today)

**Структура ответа:**

```json
{
  "period_from": "2026-04-09",
  "period_to": "2026-05-09",
  "parameters": [
    {
      "parameter_name": "pH",
      "total_tests": 120,
      "total_out_of_spec": 8,
      "overall_out_of_spec_pct": "6.67",
      "trend": [
        {
          "test_date": "2026-04-09",
          "avg_value": "6.95",
          "test_count": 4,
          "out_of_spec_count": 0,
          "out_of_spec_pct": "0.00",
          "lower_limit": "6.50",
          "upper_limit": "7.50"
        }
      ]
    }
  ]
}
```

**Источник данных:** `quality_results` LEFT JOIN `quality_specs`  
**Визуализация (рекомендация):** Линейный график `avg_value` с серой полосой [lower_limit, upper_limit] + красные точки в дни с out_of_spec_pct > 0.

---

### Отчёт 8: Анализ партий (`/batch-analysis`)

**Назначение:** Список партий с отклонениями — drill-down по каждому несоответствию.

**Параметры запроса:**
- `date_from`, `date_to`

**Структура ответа:**

```json
{
  "period_from": "2026-04-09",
  "period_to": "2026-05-09",
  "lot_count": 3,
  "lots": [
    {
      "lot_number": "LOT-2026-001",
      "product_name": "Product Alpha",
      "production_date": "2026-04-15",
      "shift": "Shift 2",
      "fail_count": 2,
      "deviations": [
        {
          "parameter_name": "pH",
          "result_value": "8.50",
          "lower_limit": "6.50",
          "upper_limit": "7.50",
          "deviation_magnitude": "1.0000"
        },
        {
          "parameter_name": "viscosity",
          "result_value": "85.00",
          "lower_limit": "100.00",
          "upper_limit": "200.00",
          "deviation_magnitude": "15.0000"
        }
      ]
    }
  ]
}
```

**Источник данных:** `quality_results` (только `in_spec=FALSE`) + `production_output` (метаданные)  
**Визуализация (рекомендация):** Таблица партий с раскрывающимися строками (accordion) для деталей по параметрам.

---

### Отчёт 9: Pareto дефектов (`/defect-pareto`)

**Назначение:** Какие параметры дают наибольший вклад в общий объём дефектов.

**Параметры запроса:**
- `date_from`, `date_to`
- `product_id` (UUID, optional) — фильтр по продукту

**Структура ответа:**

```json
{
  "period_from": "2026-04-09",
  "period_to": "2026-05-09",
  "product_id": null,
  "total_defects": 24,
  "parameters": [
    {
      "parameter_name": "pH",
      "defect_count": 14,
      "total_tests": 120,
      "defect_pct": "11.67",
      "cumulative_pct": "58.33"
    },
    {
      "parameter_name": "viscosity",
      "defect_count": 7,
      "total_tests": 115,
      "defect_pct": "6.09",
      "cumulative_pct": "87.50"
    },
    {
      "parameter_name": "acidity",
      "defect_count": 3,
      "total_tests": 90,
      "defect_pct": "3.33",
      "cumulative_pct": "100.00"
    }
  ]
}
```

**Источник данных:** `quality_results` GROUP BY `parameter_name`  
**Визуализация (рекомендация):** Pareto chart — столбцы (defect_count) + линия (cumulative_pct), горизонтальная линия на 80%.

---

## Wave 4 — Finance Manager Dashboard (`/api/v1/dashboards/finance`)

**Роль:** Финансовый менеджер. Нужен анализ выручки, структуры продаж и отклонений.

> **Ограничение:** Данные по затратам (энергия, материалы, труд) в Gateway отсутствуют.  
> Отчёты строятся на `aggregated_sales` и `sale_records`.

---

### Отчёт 10: Структура продаж (`/sales-breakdown`)

**Назначение:** Разбивка выручки по каналам, регионам и продуктам за период.

**Параметры запроса:**
- `date_from`, `date_to`
- `group_by` (enum: `channel` | `region` | `product`, default: `channel`)

**Структура ответа:**

```json
{
  "period_from": "2026-04-01",
  "period_to": "2026-04-30",
  "group_by": "channel",
  "total_amount": "5200000.00",
  "total_quantity": "48500.000",
  "groups": [
    {
      "group_key": "wholesale",
      "total_amount": "3100000.00",
      "total_quantity": "29000.000",
      "sales_count": 140,
      "avg_order_value": "22142.86",
      "amount_share_pct": "59.62"
    },
    {
      "group_key": "retail",
      "total_amount": "2100000.00",
      "total_quantity": "19500.000",
      "sales_count": 320,
      "avg_order_value": "6562.50",
      "amount_share_pct": "40.38"
    }
  ]
}
```

**Источник данных:** `aggregated_sales` (фильтр по `group_by_type`)  
**Визуализация (рекомендация):** Pie chart (доли) + таблица с суммами.

---

### Отчёт 11: Тренд выручки (`/revenue-trend`)

**Назначение:** Динамика продаж по дням/неделям/месяцам — для выявления сезонности и аномалий.

**Параметры запроса:**
- `date_from`, `date_to`
- `interval` (enum: `day` | `week` | `month`, default: `week`)
- `region` (optional), `channel` (optional)

**Структура ответа:**

```json
{
  "period_from": "2026-01-01",
  "period_to": "2026-04-30",
  "interval": "month",
  "filters": {"region": null, "channel": "wholesale"},
  "data": [
    {
      "trend_date": "2026-01-01",
      "total_amount": "1200000.00",
      "total_quantity": "11000.000",
      "order_count": 45,
      "mom_growth_pct": null
    },
    {
      "trend_date": "2026-02-01",
      "total_amount": "1350000.00",
      "total_quantity": "12400.000",
      "order_count": 52,
      "mom_growth_pct": "12.50"
    }
  ]
}
```

**Источник данных:** `sales_trends`  
**Визуализация (рекомендация):** Линейный/bar chart с `total_amount` по оси Y, `trend_date` по оси X.

---

### Отчёт 12: Топ продуктов (`/top-products`)

**Назначение:** Рейтинг продуктов по выручке/объёму для приоритизации производства.

**Параметры запроса:**
- `date_from`, `date_to`
- `limit` (int, default: 10, max: 50)
- `sort_by` (enum: `amount` | `quantity`, default: `amount`)

**Структура ответа:**

```json
{
  "period_from": "2026-04-01",
  "period_to": "2026-04-30",
  "sort_by": "amount",
  "total_amount": "5200000.00",
  "products": [
    {
      "product_name": "Product Alpha",
      "total_amount": "1800000.00",
      "total_quantity": "16000.000",
      "sales_count": 95,
      "amount_share_pct": "34.62",
      "rank": 1
    }
  ]
}
```

**Источник данных:** `sale_records` GROUP BY `product_id`  
**Визуализация (рекомендация):** Горизонтальный bar chart с `amount_share_pct` + таблица.

---

## Wave 5 — Warehouse Manager Dashboard (`/api/v1/dashboards/warehouse`)

**Роль:** Менеджер склада. Нужен контроль остатков, предупреждения о дефиците и прогноз отгрузок.

---

### Отчёт 13: Уровни запасов (`/inventory-levels`)

**Назначение:** Текущие остатки по продуктам и складам — для контроля доступности.

**Параметры запроса:**
- `snapshot_date` (date, default: today)
- `warehouse_id` (UUID, optional)
- `product_id` (UUID, optional)

**Структура ответа:**

```json
{
  "snapshot_date": "2026-05-09",
  "warehouse_filter": null,
  "total_products": 18,
  "items": [
    {
      "product_name": "Product Alpha",
      "product_id": "uuid-...",
      "warehouse_id": "uuid-...",
      "total_quantity": "4200.000",
      "unit_of_measure": "kg",
      "lot_count": 3,
      "last_updated": "2026-05-09T08:30:00Z"
    }
  ]
}
```

**Источник данных:** `inventory_snapshots` JOIN `warehouses`  
**Визуализация (рекомендация):** Таблица с фильтрами по складу/продукту, сортировка по `total_quantity`.

---

### Отчёт 14: Динамика запасов (`/inventory-trend`)

**Назначение:** Изменение остатков по продукту за период — для выявления тенденций к дефициту.

**Параметры запроса:**
- `product_id` (UUID, required)
- `date_from`, `date_to`
- `warehouse_id` (UUID, optional)

**Структура ответа:**

```json
{
  "product_id": "uuid-...",
  "product_name": "Product Alpha",
  "period_from": "2026-04-09",
  "period_to": "2026-05-09",
  "data": [
    {
      "snapshot_date": "2026-04-09",
      "total_quantity": "5000.000",
      "lot_count": 4
    },
    {
      "snapshot_date": "2026-04-16",
      "total_quantity": "3800.000",
      "lot_count": 3
    },
    {
      "snapshot_date": "2026-05-09",
      "total_quantity": "4200.000",
      "lot_count": 3
    }
  ],
  "trend_direction": "stable"
}
```

**Источник данных:** `inventory_snapshots` GROUP BY `snapshot_date`  
**Визуализация (рекомендация):** Линейный график `total_quantity` по датам.

---

### Отчёт 15: Прогноз отгрузок (`/shipment-forecast`)

**Назначение:** Ожидаемые объёмы к отгрузке на основе запланированных заказов.

**Параметры запроса:**
- `date_from` (default: today)
- `date_to` (default: today+30)
- `production_line` (optional)

**Структура ответа:**

```json
{
  "period_from": "2026-05-09",
  "period_to": "2026-06-09",
  "total_planned_quantity": "85000.000",
  "forecast": [
    {
      "planned_end_date": "2026-05-15",
      "production_line": "Line-1",
      "product_name": "Product Alpha",
      "target_quantity": "5000.000",
      "unit_of_measure": "kg",
      "order_count": 2,
      "status": "IN_PROGRESS"
    }
  ]
}
```

**Источник данных:** `order_snapshots` (фильтр `status IN ('PLANNED', 'IN_PROGRESS')`, `planned_end BETWEEN ...`)  
**Визуализация (рекомендация):** Timeline/Gantt-подобная таблица по дням, с группировкой по линии.

---

## Сводная таблица отчётов

| # | Wave | Дашборд | Эндпоинт | Источник данных | Статус |
|---|------|---------|----------|-----------------|--------|
| 1 | 1 | Line Master | `/shift-progress` | `production_output` + `quality_results` | ✅ Готово |
| 2 | 1 | Line Master | `/shift-comparison` | `production_output` | ✅ Готово |
| 3 | 1 | Line Master | `/defect-summary` | `quality_results` | ✅ Готово |
| 4 | 2 | Group Manager | `/gm/oee-summary` | `aggregated_kpi` | ✅ Готово |
| 5 | 2 | Group Manager | `/gm/plan-execution` | `order_snapshots` | ✅ Готово |
| 6 | 2 | Group Manager | `/gm/downtime-ranking` | `order_snapshots` | ✅ Готово |
| 7 | 3 | Quality Engineer | `/qe/parameter-trends` | `quality_results` + `quality_specs` | Запланировано |
| 8 | 3 | Quality Engineer | `/qe/batch-analysis` | `quality_results` + `production_output` | Запланировано |
| 9 | 3 | Quality Engineer | `/qe/defect-pareto` | `quality_results` | Запланировано |
| 10 | 4 | Finance Manager | `/finance/sales-breakdown` | `aggregated_sales` | Запланировано |
| 11 | 4 | Finance Manager | `/finance/revenue-trend` | `sales_trends` | Запланировано |
| 12 | 4 | Finance Manager | `/finance/top-products` | `sale_records` | Запланировано |
| 13 | 5 | Warehouse Manager | `/warehouse/inventory-levels` | `inventory_snapshots` | Запланировано |
| 14 | 5 | Warehouse Manager | `/warehouse/inventory-trend` | `inventory_snapshots` | Запланировано |
| 15 | 5 | Warehouse Manager | `/warehouse/shipment-forecast` | `order_snapshots` | Запланировано |

---

## Замечания по реализации

### Finance Manager (Wave 4) — изменения относительно оригинального плана
Оригинальный план предполагал `/cost-structure`, `/variance`, `/budget-comparison`, но данных по затратам в Gateway нет.  
Предлагаемые эндпоинты (`/sales-breakdown`, `/revenue-trend`, `/top-products`) строятся на уже синхронизированных таблицах `aggregated_sales` и `sale_records` — реализация возможна без изменений схемы БД.

### Warehouse Manager (Wave 5) — изменения относительно оригинального плана
`/expiry-alerts` требует поля `expiry_date` в `inventory_snapshots` — его нет.  
Вместо него предлагается `/inventory-trend` (динамика остатков), который реализуем с текущими данными.  
`/shipment-forecast` переиспользует `order_snapshots` (уже синхронизирована).

### Общий совет по Decimal
Все денежные и количественные поля — `Decimal`, не `float`. В JSON сериализуются как строки (Pydantic v2 default). Фронтенд должен ожидать строки для числовых полей с высокой точностью.
