# API Documentation for Frontend

**Версия:** 3.0 | **Дата:** 2026-05-12 | **Статус:** Полная документация

---

## Содержание

1. [Обзор API](#обзор-api)
2. [Аутентификация](#аутентификация)
3. [Общие паттерны](#общие-паттерны)
4. [Справочник по доменам](#справочник-по-доменам)
   - [Health](#health)
   - [Sales](#sales)
   - [Orders](#orders)
   - [Quality](#quality)
   - [Products](#products)
   - [Output](#output)
   - [Sensors](#sensors)
   - [Inventory](#inventory)
   - [Production Analytics (KPI)](#production-analytics-kpi)
   - [OEE](#oee)
   - [Sync](#sync)
   - [Dashboards](#dashboards)
5. [Обработка ошибок](#обработка-ошибок)
6. [TypeScript типы](#typescript-типы)
7. [React примеры](#react-примеры)

---

## Обзор API

**Base URL:** `http://localhost:3000/api/production` (Production Analytics)
**Alternative Base URL:** `http://localhost:3000/api/v1` (Sales, Orders, Quality, OEE, Sync, Dashboards)

**Все эндпоинты:**
- Методы: GET (чтение), POST (создание)
- Аутентификация: JWT Bearer Token (планируется в v2)
- Формат ответа: JSON
- Пагинация: offset/limit или page/limit
- Фильтры: query parameters

**CORS:** Разрешены все origins (`*`)

---

## Аутентификация

**Статус v1:** Аутентификация не требуется — все эндпоинты публичные.

**v2 (планируется):**
```typescript
headers: {
  'Authorization': 'Bearer <token>',
  'Content-Type': 'application/json'
}
```

---

## Общие паттерны

### Формат дат
Все даты передаются в формате `YYYY-MM-DD` (ISO 8601). Примеры:
- `2026-05-01` — 1 мая 2026
- `2026-12-31` — 31 декабря 2026

### Пагинация

**Offset/Limit ( основной):**
```
?offset=0&limit=20
```
- `offset` — смещение от начала (≥0)
- `limit` — количество записей (1-100, по умолчанию 100)

**Page/Limit:**
```
?page=1&limit=100
```
- `page` — номер страницы (≥1)
- `limit` — записей на страницу (1-500, по умолчанию 100)

**Ответ пагинации:**
```typescript
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}
```

### Фильтры
- `from_date` / `to_date` — диапазон дат (для analytics/production)
- `from` / `to` — диапазон дат (для sales, orders, quality)
- `start_date` / `end_date` — диапазон дат (для orders/plan-execution, downtime)
- `production_line_id` — UUID производственной линии
- `product_id` — UUID продукта
- `group_by` — тип группировки (varies by endpoint)
- `interval` — интервал агрегации (day/week/month)

### Статусы KPI
- `ok` — значение ≥ target (зелёный)
- `warning` — значение от target-10% до target (жёлтый)
- `critical` — значение < target-10% (красный)

---

## Справочник по доменам

---

### Health

**Описание:** Health check и базовая информация о сервисе.

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/health` | Проверка здоровья (БД) |
| `GET` | `/` | Корневая информация |

#### GET `/health`
```typescript
interface HealthResponse {
  status: string;        // "ok" | "error"
  version: string;       // "1.0.0"
  timestamp: string;     // ISO datetime
}

const response = await fetch('/health');
const data = await response.json();
```

#### GET `/`
```typescript
// Ответ:
{
  name: "Dashboard Analytics API",
  version: "1.0.0",
  docs: "/docs",
  health: "/health"
}
```

---

### Sales

**Описание:** Данные продаж, тренды, топ продуктов, регионы.

**Base:** `/api/v1/sales`

#### GET `/api/v1/sales/summary`
Агрегированная сводка продаж.

```typescript
interface SalesSummaryParams {
  from?: string;        // YYYY-MM-DD
  to?: string;          // YYYY-MM-DD
  group_by?: 'region' | 'channel' | 'product';  // default: 'region'
}

interface SalesSummaryItem {
  group_key: string;
  total_quantity: string;    // Decimal
  total_amount: string;      // Decimal
  sales_count: number;
  avg_order_value: string | null;
}

interface SalesSummaryResponse {
  summary: SalesSummaryItem[];
  total_amount: string;
  total_quantity: string;
  period_from: string;       // YYYY-MM-DD
  period_to: string;
  group_by: string;
}

// Пример:
const response = await fetch(
  '/api/v1/sales/summary?from=2026-05-01&to=2026-05-31&group_by=channel'
);
const data: SalesSummaryResponse = await response.json();
```

#### GET `/api/v1/sales/trends`
Тренды продаж по времени.

```typescript
interface SalesTrendsParams {
  from?: string;
  to?: string;
  interval?: 'day' | 'week' | 'month';
  region?: string;
  channel?: string;
}

interface SalesTrendPoint {
  trend_date: string;    // YYYY-MM-DD
  total_amount: string;
  total_quantity: string;
  order_count: number;
}

interface SalesTrendsResponse {
  trends: SalesTrendPoint[];
  interval: string;
  period_from: string;
  period_to: string;
  region: string | null;
  channel: string | null;
}

// Пример:
const trends = await fetch(
  '/api/v1/sales/trends?from=2026-05-01&to=2026-05-31&interval=day'
).then(r => r.json()) as SalesTrendsResponse;
```

#### GET `/api/v1/sales/top-products`
Топ продуктов по выручке.

```typescript
interface TopProductsParams {
  from?: string;
  to?: string;
  limit?: number;       // 1-1000, default: 10
}

interface TopProductItem {
  product_id: string;
  product_name: string;
  total_quantity: string;
  total_amount: string;
  sales_count: number;
}

interface TopProductsResponse {
  products: TopProductItem[];
  period_from: string;
  period_to: string;
  limit: number;
}

// Пример:
const topProducts = await fetch(
  '/api/v1/sales/top-products?from=2026-05-01&to=2026-05-31&limit=5'
).then(r => r.json()) as TopProductsResponse;
```

#### GET `/api/v1/sales/regions`
Продажи по регионам с процентами.

```typescript
interface SalesRegionItem {
  region: string;
  total_quantity: string;
  total_amount: string;
  sales_count: number;
  percentage: string;    // Decimal, % от общего
}

interface SalesRegionsResponse {
  regions: SalesRegionItem[];
  period_from: string;
  period_to: string;
}

// Пример:
const regions = await fetch(
  '/api/v1/sales/regions?from=2026-05-01&to=2026-05-31'
).then(r => r.json()) as SalesRegionsResponse;
```

---

### Orders

**Описание:** Отслеживание заказов, статусы, план vs факт, простои.

**Base:** `/api/v1/orders`

#### GET `/api/v1/orders/status-summary`
Сводка заказов по статусам и линиям.

```typescript
interface OrderStatusSummaryParams {
  from?: string;
  to?: string;
  production_line?: string;
}

interface OrderStatusCount {
  planned: number;
  in_progress: number;
  completed: number;
  cancelled: number;
}

interface OrderStatusSummaryResponse {
  by_status: OrderStatusCount;
  by_production_line: Record<string, OrderStatusCount>;
  period_from: string;
  period_to: string;
}

// Пример:
const summary = await fetch(
  '/api/v1/orders/status-summary?from=2026-05-01&to=2026-05-31'
).then(r => r.json()) as OrderStatusSummaryResponse;
```

#### GET `/api/v1/orders/list`
Пагинированный список заказов.

```typescript
interface OrderListParams {
  from?: string;
  to?: string;
  status?: string;
  production_line?: string;
  page?: number;        // default: 1
  limit?: number;       // default: 100
}

interface OrderListItem {
  order_id: string;
  external_order_id: string | null;
  product_id: string;
  product_name: string | null;
  target_quantity: string | null;
  actual_quantity: string | null;
  unit_of_measure: string | null;
  status: string;
  production_line: string | null;
  planned_start: string | null;  // ISO datetime
  planned_end: string | null;
  actual_start: string | null;
  actual_end: string | null;
  snapshot_date: string;          // YYYY-MM-DD
}

interface OrderListResponse {
  orders: OrderListItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// Пример:
const orders = await fetch(
  '/api/v1/orders/list?from=2026-05-01&to=2026-05-31&page=1&limit=20'
).then(r => r.json()) as OrderListResponse;
```

#### GET `/api/v1/orders/plan-execution`
План vs факт по производственным линиям.

```typescript
interface PlanExecutionParams {
  start_date?: string;
  end_date?: string;
}

interface PlanExecutionLineItem {
  production_line: string | null;
  target_quantity: string;
  actual_quantity: string;
  fulfillment_pct: string;
  total_orders: number;
  completed_orders: number;
  in_progress_orders: number;
  overdue_orders: number;
}

interface PlanExecutionResponse {
  period_from: string;
  period_to: string;
  lines: PlanExecutionLineItem[];
}

// Пример:
const planExec = await fetch(
  '/api/v1/orders/plan-execution?start_date=2026-05-01&end_date=2026-05-31'
).then(r => r.json()) as PlanExecutionResponse;
```

#### GET `/api/v1/orders/downtime`
Парето-рейтинг по часам задержки.

```typescript
interface DowntimeParams {
  start_date?: string;
  end_date?: string;
}

interface DowntimeLineItem {
  rank: number;
  production_line: string | null;
  total_delay_hours: string;
  order_count: number;
  avg_delay_per_order: string;
  cumulative_pct: string;
}

interface DowntimeResponse {
  total_delay_hours: string;
  period_from: string;
  period_to: string;
  lines: DowntimeLineItem[];
}

// Пример:
const downtime = await fetch(
  '/api/v1/orders/downtime?start_date=2026-05-01&end_date=2026-05-31'
).then(r => r.json()) as DowntimeResponse;
```

#### GET `/api/v1/orders/{order_id}`
Детали одного заказа с выходами.

```typescript
interface OrderOutputItem {
  output_id: string;
  lot_number: string;
  quantity: string;
  quality_status: string;
  production_date: string;
  shift: string;
}

interface OrderDetailResponse {
  order_id: string;
  external_order_id: string | null;
  product_id: string;
  product_name: string | null;
  target_quantity: string | null;
  actual_quantity: string | null;
  unit_of_measure: string | null;
  status: string;
  production_line: string | null;
  planned_start: string | null;
  planned_end: string | null;
  actual_start: string | null;
  actual_end: string | null;
  outputs: OrderOutputItem[];
}

// Пример:
const order = await fetch(
  '/api/v1/orders/550e8400-e29b-41d4-a716-446655440000'
).then(r => r.json()) as OrderDetailResponse;
```

---

### Quality

**Описание:** Контроль качества, дефекты, партии, отклонения.

**Base:** `/api/v1/quality`

#### GET `/api/v1/quality/summary`
Сводка качества.

```typescript
interface QualitySummaryParams {
  from?: string;
  to?: string;
  product_id?: string;
}

interface QualityParameterStats {
  in_spec_percent: string;
  tests_count: number;
}

interface QualitySummaryResponse {
  average_quality: string;         // Decimal, %
  approved_count: number;
  rejected_count: number;
  pending_count: number;
  defect_rate: string;             // Decimal, %
  by_parameter: Record<string, QualityParameterStats>;
  period_from: string;
  period_to: string;
}

// Пример:
const qualitySummary = await fetch(
  '/api/v1/quality/summary?from=2026-05-01&to=2026-05-31'
).then(r => r.json()) as QualitySummaryResponse;
```

#### GET `/api/v1/quality/defect-trends`
Тренды дефектов по времени.

```typescript
interface DefectTrendsParams {
  from?: string;
  to?: string;
}

interface DefectTrendPoint {
  trend_date: string;
  defect_rate: string;
  rejected_count: number;
  total_tests: number;
}

interface DefectTrendsResponse {
  trends: DefectTrendPoint[];
  period_from: string;
  period_to: string;
}

// Пример:
const defectTrends = await fetch(
  '/api/v1/quality/defect-trends?from=2026-05-01&to=2026-05-31'
).then(r => r.json()) as DefectTrendsResponse;
```

#### GET `/api/v1/quality/lots`
Качественные партии с решениями.

```typescript
interface QualityLotsParams {
  from?: string;
  to?: string;
  decision?: string;    // approved | rejected | pending
}

interface QualityLotItem {
  lot_number: string;
  product_id: string;
  product_name: string | null;
  decision: string;
  test_date: string;
  parameters_tested: number;
  parameters_passed: number;
}

interface QualityLotsResponse {
  lots: QualityLotItem[];
  total: number;
  approved_count: number;
  rejected_count: number;
  pending_count: number;
  period_from: string;
  period_to: string;
}

// Пример:
const lots = await fetch(
  '/api/v1/quality/lots?from=2026-05-01&to=2026-05-31&decision=rejected'
).then(r => r.json()) as QualityLotsResponse;
```

#### GET `/api/v1/quality/parameter-trends`
Дневные тренды параметров с допусками.

```typescript
interface ParameterTrendsParams {
  start_date?: string;
  end_date?: string;
  production_line?: string;
}

interface ParameterTrendsResponse {
  period_from: string;
  period_to: string;
  parameters: Array<{
    parameter_name: string;
    total_tests: number;
    total_out_of_spec: number;
    overall_out_of_spec_pct: string;
    trend: Array<{
      test_date: string;
      avg_value: string;
      test_count: number;
      out_of_spec_count: number;
      out_of_spec_pct: string;
      lower_limit: string | null;
      upper_limit: string | null;
    }>;
  }>;
}

// Пример:
const paramTrends = await fetch(
  '/api/v1/quality/parameter-trends?start_date=2026-05-01&end_date=2026-05-31'
).then(r => r.json()) as ParameterTrendsResponse;
```

#### GET `/api/v1/quality/lots/{lot_number}/deviations`
Отклонения для конкретной партии.

```typescript
interface LotDeviationItem {
  parameter_name: string;
  result_value: string;
  lower_limit: string | null;
  upper_limit: string | null;
  deviation_magnitude: string;
}

interface LotDeviationsResponse {
  lot_number: string;
  product_name: string | null;
  shift: string | null;
  fail_count: number;
  deviations: LotDeviationItem[];
}

// Пример:
const deviations = await fetch(
  '/api/v1/quality/lots/LOT-2026-001/deviations'
).then(r => r.json()) as LotDeviationsResponse;
```

#### GET `/api/v1/quality/defect-pareto`
Парето-диаграмма дефектов.

```typescript
interface DefectParetoParams {
  start_date?: string;
  end_date?: string;
  production_line?: string;
}

interface DefectParetoResponse {
  period_from: string;
  period_to: string;
  total_defects: number;
  parameters: Array<{
    parameter_name: string;
    defect_count: number;
    total_tests: number;
    defect_pct: string;
    cumulative_pct: string;
  }>;
}

// Пример:
const pareto = await fetch(
  '/api/v1/quality/defect-pareto?start_date=2026-05-01&end_date=2026-05-31'
).then(r => r.json()) as DefectParetoResponse;
```

---

### Products

**Описание:** Список продуктов и детали.

**Base:** `/api/v1/products`

#### GET `/api/v1/products`
Список продуктов.

```typescript
interface ProductsParams {
  category?: string;
  brand?: string;
}

// Ответ (untyped):
{
  items: Array<{
    id: string;
    code: string;
    name: string;
    category: string;
    brand: string;
    // ...другие поля
  }>;
  count: number;
}

// Пример:
const products = await fetch(
  '/api/v1/products?category=молочные'
).then(r => r.json());
```

#### GET `/api/v1/products/{product_id}`
Один продукт по ID.

```typescript
// Ответ (untyped):
{
  id: string;
  code: string;
  name: string;
  category: string;
  brand: string;
  // ...другие поля
}

// Пример:
const product = await fetch(
  '/api/v1/products/550e8400-e29b-41d4-a716-446655440000'
).then(r => r.json());
```

---

### Output

**Описание:** Выпуск продукции по сменам и дням.

**Base:** `/api/v1/output`

#### GET `/api/v1/output/summary`
Сводка выпуска по дням/сменам.

```typescript
interface OutputSummaryParams {
  from?: string;
  to?: string;
  group_by?: 'day' | 'shift';
}

// Ответ (untyped):
// Данные агрегированы по дням или сменам
```

#### GET `/api/v1/output/by-shift`
Выпуск по сменам.

```typescript
interface OutputByShiftParams {
  from?: string;
  to?: string;
}

// Ответ (untyped):
// Данные сгруппированы по сменам
```

---

### Sensors

**Описание:** Данные с датчиков, alerts, статистика.

**Base:** `/api/v1/sensors`

#### GET `/api/v1/sensors/history`
История показаний датчиков.

```typescript
interface SensorsHistoryParams {
  production_line?: string;
  parameter_name?: string;
  from?: string;
  to?: string;
  limit?: number;       // 1-5000, default: 500
}

// Ответ (untyped):
// Массив показаний датчиков
```

#### GET `/api/v1/sensors/alerts`
Данные датчиков с проблемами качества.

```typescript
interface SensorsAlertsParams {
  from?: string;
  to?: string;
  limit?: number;       // 1-1000, default: 100
}

// Ответ (untyped):
// Массив alerts
```

#### GET `/api/v1/sensors/stats`
Агрегированная статистика по параметрам/линиям.

```typescript
interface SensorsStatsParams {
  production_line?: string;
}

// Ответ (untyped):
// Статистика по параметрам
```

---

### Inventory

**Описание:** Уровни запасов.

**Base:** `/api/v1/inventory`

#### GET `/api/v1/inventory/current`
Текущий inventory (последний снапшот).

```typescript
interface InventoryCurrentParams {
  warehouse_code?: string;
  product_id?: string;
}

// Ответ (untyped):
// Текущие остатки
```

#### GET `/api/v1/inventory/trends`
Тренды inventory для продукта.

```typescript
interface InventoryTrendsParams {
  product_id: string;   // обязательно
  from?: string;
  to?: string;
}

// Ответ (untyped):
// Тренды запасов по дням
```

---

### Production Analytics (KPI)

**Описание:** Основной домен — KPI, OTIF, breakdown, downtime, batch inputs, promo campaigns.

**Base:** `/api/production`

#### GET `/api/production/kpi`
Обогащённые KPI с targets, trends, comparison.

```typescript
interface KPIParams {
  from_date: string;          // обязательно, YYYY-MM-DD
  to_date: string;            // обязательно, YYYY-MM-DD
  production_line_id?: string;
  granularity?: 'day' | 'week' | 'month';
  compare_with_previous?: boolean;
}

interface KPITarget {
  target: string;
  min: string;
  max: string;
  status: 'ok' | 'warning' | 'critical';
}

interface KPITargets {
  oee_estimate: KPITarget | null;
  defect_rate: KPITarget | null;
  otif_rate: KPITarget | null;
}

interface KPITrendPoint {
  period: string;
  total_output: string;
  defect_rate: string;
  oee_estimate: string | null;
}

interface KPIResponse {
  total_output: string;
  defect_rate: string;
  completed_orders: number;
  total_orders: number;
  availability: string;
  performance: string;
  oee_estimate: string;
  line_throughput: string;
  targets: KPITargets;
  trend: KPITrendPoint[];
  change_percent: Record<string, string> | null;
}

// Пример:
const kpi = await fetch(
  '/api/production/kpi?from_date=2026-05-01&to_date=2026-05-31&granularity=day'
).then(r => r.json()) as KPIResponse;

// Карточка KPI с цветом:
const getStatusColor = (status: string) => {
  switch(status) {
    case 'ok': return 'green';
    case 'warning': return 'yellow';
    case 'critical': return 'red';
    default: return 'gray';
  }
};
```

#### GET `/api/production/kpi/otif`
Метрики OTIF (On-Time In-Full).

```typescript
interface OTIFParams {
  from_date: string;          // обязательно
  to_date: string;            // обязательно
  production_line_id?: string;
}

interface OTIFResponse {
  otif_rate: string;           // Decimal, 0-1
  on_time_orders: number;
  in_full_quantity_orders: number;
  otif_orders: number;
  total_orders: number;
}

// Пример:
const otif = await fetch(
  '/api/production/kpi/otif?from_date=2026-05-01&to_date=2026-05-31'
).then(r => r.json()) as OTIFResponse;
```

#### GET `/api/production/kpi/breakdown`
KPI breakdown по линиям/продуктам/дивизиям.

```typescript
interface KPIBreakdownParams {
  from_date: string;          // обязательно
  to_date: string;            // обязательно
  group_by?: 'productionLine' | 'product' | 'division';
  metric?: 'oeeEstimate' | 'defectRate' | 'lineThroughput' | 'otifRate';
  offset?: number;
  limit?: number;
}

interface KPIBreakdownItem {
  group_key: string;
  value: string;
  target: string | null;
  status: 'ok' | 'warning' | 'critical';
  deviation: string | null;
}

interface KPIBreakdownResponse {
  items: KPIBreakdownItem[];
  total: number;
}

// Пример:
const breakdown = await fetch(
  '/api/production/kpi/breakdown?from_date=2026-05-01&to_date=2026-05-31&group_by=productionLine&metric=oeeEstimate'
).then(r => r.json()) as KPIBreakdownResponse;
```

#### GET `/api/production/sales/margin`
Маржа по продуктам.

```typescript
interface SalesMarginParams {
  from_date: string;          // обязательно
  to_date: string;            // обязательно
  product_id?: string;
  offset?: number;
  limit?: number;
}

interface SalesMarginItem {
  product_id: string;
  product_code: string;
  product_name: string;
  total_quantity: string;
  total_revenue: string;
  total_cost: string;
  total_margin: string;
  margin_percent: string;
  margin_per_unit: string;
}

interface SalesMarginResponse {
  margins: SalesMarginItem[];
  total: number;
  aggregated: {
    total_revenue: string;
    total_cost: string;
    total_margin: string;
    avg_margin_percent: string;
  };
}

// Пример:
const margin = await fetch(
  '/api/production/sales/margin?from_date=2026-05-01&to_date=2026-05-31&limit=20'
).then(r => r.json()) as SalesMarginResponse;
```

#### POST `/api/production/batch-inputs`
Создание записи приёмки сырья.

```typescript
interface BatchInputCreate {
  order_id?: string;
  product_id?: string;
  quantity: string;          // Decimal, 3 знака
  input_date: string;        // ISO datetime
}

interface BatchInputResponse {
  id: string;
  order_id: string | null;
  product_id: string | null;
  quantity: string;
  input_date: string;
  created_at: string;
  updated_at: string;
}

// Пример:
const newInput = await fetch('/api/production/batch-inputs', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    order_id: '550e8400-e29b-41d4-a716-446655440000',
    product_id: '550e8400-e29b-41d4-a716-446655440001',
    quantity: '1000.500',
    input_date: '2026-05-10T08:00:00Z'
  })
}).then(r => r.json()) as BatchInputResponse;
```

#### GET `/api/production/batch-inputs`
Список записей приёмки.

```typescript
interface BatchInputListParams {
  order_id?: string;
  product_id?: string;
  offset?: number;
  limit?: number;
}

interface BatchInputListResponse {
  items: BatchInputResponse[];
  total: number;
}

// Пример:
const batchInputs = await fetch(
  '/api/production/batch-inputs?order_id=550e8400-e29b-41d4-a716-446655440000'
).then(r => r.json()) as BatchInputListResponse;
```

#### GET `/api/production/batch-inputs/yield`
Yield ratio для заказа.

```typescript
interface YieldParams {
  order_id: string;          // обязательно
}

interface YieldResponse {
  order_id: string;
  total_input: string;
  total_output: string;
  yield_percent: string;
  target: string;
}

// Пример:
const yieldData = await fetch(
  '/api/production/batch-inputs/yield?order_id=550e8400-e29b-41d4-a716-446655440000'
).then(r => r.json()) as YieldResponse;
```

#### POST `/api/production/downtime-events`
Создание записи простоя.

```typescript
interface DowntimeEventCreate {
  production_line_id?: string;
  reason: string;
  category: 'PLANNED_MAINTENANCE' | 'UNPLANNED_BREAKDOWN' | 'QUALITY_ISSUE' | 'MATERIAL_SHORTAGE' | 'OTHER';
  started_at: string;        // ISO datetime
  ended_at?: string;
  duration_minutes?: number;
}

interface DowntimeEventResponse {
  id: string;
  production_line_id: string | null;
  reason: string;
  category: string;
  started_at: string;
  ended_at: string | null;
  duration_minutes: number | null;
  created_at: string;
  updated_at: string;
}

// Пример:
const newDowntime = await fetch('/api/production/downtime-events', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    production_line_id: '550e8400-e29b-41d4-a716-446655440000',
    reason: 'Поломка вала',
    category: 'UNPLANNED_BREAKDOWN',
    started_at: '2026-05-10T08:30:00Z',
    ended_at: '2026-05-10T10:15:00Z',
    duration_minutes: 105
  })
}).then(r => r.json()) as DowntimeEventResponse;
```

#### GET `/api/production/downtime-events`
Список событий простоя.

```typescript
interface DowntimeEventListParams {
  from_date?: string;
  to_date?: string;
  production_line_id?: string;
  category?: string;
  offset?: number;
  limit?: number;
}

interface DowntimeEventListResponse {
  items: DowntimeEventResponse[];
  total: number;
}

// Пример:
const downtimeEvents = await fetch(
  '/api/production/downtime-events?from_date=2026-05-01&to_date=2026-05-31'
).then(r => r.json()) as DowntimeEventListResponse;
```

#### GET `/api/production/downtime-events/summary`
Агрегированный простой по категориям.

```typescript
interface DowntimeSummaryParams {
  from_date?: string;
  to_date?: string;
}

interface DowntimeSummaryItem {
  category: string;
  total_minutes: number;
  count: number;
}

interface DowntimeSummaryResponse {
  items: DowntimeSummaryItem[];
  total_events: number;
  total_downtime_minutes: number;
}

// Пример:
const summary = await fetch(
  '/api/production/downtime-events/summary?from_date=2026-05-01&to_date=2026-05-31'
).then(r => r.json()) as DowntimeSummaryResponse;
```

#### POST `/api/production/promo-campaigns`
Создание промо-акции.

```typescript
interface PromoCampaignCreate {
  name: string;
  description?: string;
  channel: 'DIRECT' | 'DISTRIBUTOR' | 'RETAIL' | 'ONLINE';
  product_id?: string;
  discount_percent?: string;
  start_date: string;        // YYYY-MM-DD
  end_date?: string;
  budget?: string;
}

interface PromoCampaignResponse {
  id: string;
  name: string;
  description: string | null;
  channel: string;
  product_id: string | null;
  discount_percent: string | null;
  start_date: string;
  end_date: string | null;
  budget: string | null;
  created_at: string;
  updated_at: string;
}

// Пример:
const newCampaign = await fetch('/api/production/promo-campaigns', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Скидка творог 10%',
    channel: 'DIRECT',
    discount_percent: '10',
    start_date: '2026-05-01',
    end_date: '2026-05-31',
    budget: '50000'
  })
}).then(r => r.json()) as PromoCampaignResponse;
```

#### GET `/api/production/promo-campaigns`
Список промо-акций.

```typescript
interface PromoCampaignListParams {
  from_date?: string;
  to_date?: string;
  channel?: string;
  offset?: number;
  limit?: number;
}

interface PromoCampaignListResponse {
  items: PromoCampaignResponse[];
  total: number;
}

// Пример:
const campaigns = await fetch(
  '/api/production/promo-campaigns?from_date=2026-05-01&to_date=2026-05-31'
).then(r => r.json()) as PromoCampaignListResponse;
```

#### GET `/api/production/promo-campaigns/{campaign_id}/effectiveness`
Эффективность кампании (ROI, uplift).

```typescript
interface PromoCampaignEffectivenessResponse {
  campaign_id: string;
  campaign_name: string;
  budget: string | null;
  sales_during_campaign: string;
  baseline_sales: string;
  uplift: string;
  cost_per_uplift_unit: string | null;
  roi: string;
  roi_percent: string;
}

// Пример:
const effectiveness = await fetch(
  '/api/production/promo-campaigns/550e8400-e29b-41d4-a716-446655440000/effectiveness'
).then(r => r.json()) as PromoCampaignEffectivenessResponse;
```

#### GET `/api/production/kpi/line-productivity`
Производительность линий (тонн/час).

```typescript
interface LineProductivityParams {
  from_date: string;          // обязательно
  to_date: string;            // обязательно
  production_line_id?: string;
}

interface LineProductivityItem {
  production_line: string;
  productivity: string;
  total_output: string;
  days: number;
  target: string;
  status: 'ok' | 'warning' | 'critical';
  deviation: string;
}

interface LineProductivityResponse {
  items: LineProductivityItem[];
  period: { from_date: string; to_date: string };
  unit: string;
}

// Пример:
const productivity = await fetch(
  '/api/production/kpi/line-productivity?from_date=2026-05-01&to_date=2026-05-31'
).then(r => r.json()) as LineProductivityResponse;
```

#### GET `/api/production/kpi/scrap-percentage`
Процент брака (качественные дефекты).

```typescript
interface ScrapPercentageParams {
  from_date: string;          // обязательно
  to_date: string;            // обязательно
  product_id?: string;
}

interface ScrapPercentageResponse {
  scrap_percentage: string;
  rejected_tests: number;
  total_tests: number;
  target: string;
  status: 'ok' | 'warning' | 'critical';
  period: { from_date: string; to_date: string };
}

// Пример:
const scrap = await fetch(
  '/api/production/kpi/scrap-percentage?from_date=2026-05-01&to_date=2026-05-31'
).then(r => r.json()) as ScrapPercentageResponse;
```

#### GET `/api/production/production-lines`
Справочник производственных линий.

```typescript
interface ProductionLinesParams {
  division?: string;
  offset?: number;
  limit?: number;
}

interface ProductionLineResponse {
  id: string;
  code: string;
  name: string;
  description: string | null;
  division: string | null;
  is_active: boolean;
}

interface ProductionLinesListResponse {
  production_lines: ProductionLineResponse[];
  total: number;
}

// Пример:
const lines = await fetch(
  '/api/production/production-lines?division=молочный&limit=20'
).then(r => r.json()) as ProductionLinesListResponse;
```

---

### OEE

**Описание:** Overall Equipment Effectiveness — доступность, производительность, качество.

**Base:** `/api/v1/oee`

#### GET `/api/v1/oee/summary`
OEE summary за период.

```typescript
interface OEESummaryParams {
  period_from: string;        // обязательно
  period_to: string;          // обязательно
  production_line_id?: string;
}

interface OEEComponentResponse {
  component: string;
  value: string;
  target: string;
  status: string;
}

interface OEELineResponse {
  production_line_id: string;
  production_line_name: string;
  availability: OEEComponentResponse;
  performance: OEEComponentResponse;
  quality: OEEComponentResponse;
  oee: string;
  target_oee: string;
  period_from: string;
  period_to: string;
}

interface OEESummaryResponse {
  summary_date: string;
  lines: OEELineResponse[];
  total_oee: string;
  lines_above_target: number;
  lines_below_target: number;
  period_from: string;
  period_to: string;
}

// Пример:
const oee = await fetch(
  '/api/v1/oee/summary?period_from=2026-05-01&period_to=2026-05-31'
).then(r => r.json()) as OEESummaryResponse;
```

#### GET `/api/v1/oee/line/{production_line_id}`
OEE для конкретной линии.

```typescript
// Аналог OEESummaryResponse, но для одной линии

// Пример:
const oeeLine = await fetch(
  '/api/v1/oee/line/550e8400-e29b-41d4-a716-446655440000?period_from=2026-05-01&period_to=2026-05-31'
).then(r => r.json()) as OEELineResponse;
```

#### GET `/api/v1/oee/today`
OEE за сегодня.

```typescript
// Параметры не требуются
const oeeToday = await fetch('/api/v1/oee/today').then(r => r.json()) as OEESummaryResponse;
```

#### GET `/api/v1/oee/this-week`
OEE за текущую неделю.

```typescript
const oeeWeek = await fetch('/api/v1/oee/this-week').then(r => r.json()) as OEESummaryResponse;
```

#### GET `/api/v1/oee/this-month`
OEE за текущий месяц.

```typescript
const oeeMonth = await fetch('/api/v1/oee/this-month').then(r => r.json()) as OEESummaryResponse;
```

#### POST `/api/v1/oee/capacity-plan`
Установка/обновление плана мощности линии.

```typescript
interface LineCapacityPlanRequest {
  production_line_id: string;
  planned_hours_per_day: number;   // 1-24
  target_oee_percent: string;      // 0-100
  period_from: string;
  period_to?: string;
}

interface LineCapacityPlanResponse {
  id: string;
  production_line_id: string;
  planned_hours_per_day: number;
  target_oee_percent: string;
  period_from: string;
  period_to: string | null;
  created_at: string;
  updated_at: string;
}

// Пример:
const plan = await fetch('/api/v1/oee/capacity-plan', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    production_line_id: '550e8400-e29b-41d4-a716-446655440000',
    planned_hours_per_day: 16,
    target_oee_percent: '85',
    period_from: '2026-05-01',
    period_to: '2026-05-31'
  })
}).then(r => r.json()) as LineCapacityPlanResponse;
```

---

### Sync

**Описание:** Управление синхронизацией данных.

**Base:** `/api/v1/sync`

#### GET `/api/v1/sync/status`
Статус всех задач синхронизации.

```typescript
interface SyncTaskStatus {
  task_name: string;
  status: string;          // pending | running | completed | failed
  last_run: string | null;
  last_success: string | null;
  records_processed: number;
  records_inserted: number;
  records_updated: number;
  error_message: string | null;
}

interface SyncStatusResponse {
  tasks: SyncTaskStatus[];
  overall_status: string;
  last_sync: string | null;
}

// Пример:
const syncStatus = await fetch('/api/v1/sync/status').then(r => r.json()) as SyncStatusResponse;
```

#### POST `/api/v1/sync/trigger`
Запуск всех задач синхронизации.

```typescript
interface SyncTriggerResponse {
  message: string;
  triggered_tasks: string[];
}

// Пример:
const triggerAll = await fetch('/api/v1/sync/trigger', { method: 'POST' }).then(r => r.json()) as SyncTriggerResponse;
```

#### POST `/api/v1/sync/trigger/{task_name}`
Запуск конкретной задачи.

```typescript
// task_name: kpi | kpi_per_line | sales | orders | quality | products | output | sensors | inventory | references

// Пример:
const triggerSales = await fetch('/api/v1/sync/trigger/sales', { method: 'POST' }).then(r => r.json()) as SyncTriggerResponse;
```

#### POST `/api/v1/sync/cleanup`
Запуск очистки данных.

```typescript
// Пример:
const cleanup = await fetch('/api/v1/sync/cleanup', { method: 'POST' }).then(r => r.json());
```

#### POST `/api/v1/sync/stop`
Остановка всех задач.

```typescript
// Пример:
const stopAll = await fetch('/api/v1/sync/stop', { method: 'POST' }).then(r => r.json());
```

#### POST `/api/v1/sync/stop/{task_name}`
Остановка конкретной задачи.

```typescript
// Пример:
const stopSales = await fetch('/api/v1/sync/stop/sales', { method: 'POST' }).then(r => r.json());
```

#### GET `/api/v1/sync/running`
Список запущенных задач.

```typescript
// Пример:
const running = await fetch('/api/v1/sync/running').then(r => r.json());
```

#### POST `/api/v1/sync/initial_sync`
Начальная синхронизация (все таблицы).

```typescript
// Пример:
const initialSync = await fetch('/api/v1/sync/initial_sync', { method: 'POST' }).then(r => r.json());
```

---

### Dashboards

**Описание:** Ролевые дашборды — Line Master, GM, QE, Finance.

---

#### Line Master Dashboard

**Base:** `/api/v1/dashboards/line-master`

##### GET `/shift-progress`
Прогресс смен за дату.

```typescript
interface ShiftProgressParams {
  production_date?: string;   // default: today
}

interface ShiftItem {
  shift: string;
  lot_count: number;
  total_quantity: string;
  approved_count: number;
  defect_count: number;
  defect_rate: string;
}

interface ShiftProgressResponse {
  date: string;
  shifts: ShiftItem[];
  total_quantity: string;
  total_lots: number;
}

// Пример:
const shiftProgress = await fetch(
  '/api/v1/dashboards/line-master/shift-progress?production_date=2026-05-10'
).then(r => r.json()) as ShiftProgressResponse;
```

##### GET `/shift-comparison`
Сравнение смен за период.

```typescript
interface ShiftComparisonParams {
  date_from?: string;        // default: 7 days ago
  date_to?: string;          // default: today
}

interface ShiftComparisonPeriod {
  date: string;
  shift: string | null;
  total_quantity: string;
  lot_count: number;
  defect_count: number;
}

interface ShiftComparisonResponse {
  period_from: string;
  period_to: string;
  shifts: ShiftComparisonPeriod[];
}

// Пример:
const comparison = await fetch(
  '/api/v1/dashboards/line-master/shift-comparison?date_from=2026-05-05&date_to=2026-05-10'
).then(r => r.json()) as ShiftComparisonResponse;
```

##### GET `/defect-summary`
Дефекты по параметрам за период.

```typescript
interface DefectSummaryParams {
  date_from?: string;        // default: 7 days ago
  date_to?: string;          // default: today
}

interface DefectItem {
  parameter_name: string;
  total_tests: number;
  failed_tests: number;
  fail_rate: string;
}

interface DefectSummaryResponse {
  period_from: string;
  period_to: string;
  total_defects: number;
  items: DefectItem[];
}

// Пример:
const defects = await fetch(
  '/api/v1/dashboards/line-master/defect-summary?date_from=2026-05-05&date_to=2026-05-10'
).then(r => r.json()) as DefectSummaryResponse;
```

---

#### Group Manager Dashboard

**Base:** `/api/v1/dashboards/gm`

##### GET `/oee-summary`
OEE по производственным линиям vs 75% target.

```typescript
interface GM_OEESummaryParams {
  period_days?: number;      // 1-365, default: 30
}

interface OEEDataPoint {
  period_from: string;
  period_to: string;
  oee_value: string;
}

interface OEELineItem {
  production_line: string | null;
  avg_oee: string;
  vs_target_pct: string;
  completed_orders: number;
  total_orders: number;
  avg_defect_rate: string;
  data_points: number;
  trend: OEEDataPoint[];
}

interface GM_OEESummaryResponse {
  period_days: number;
  period_from: string;
  period_to: string;
  lines: OEELineItem[];
  oee_target: string;
}

// Пример:
const gmOee = await fetch(
  '/api/v1/dashboards/gm/oee-summary?period_days=30'
).then(r => r.json()) as GM_OEESummaryResponse;
```

##### GET `/plan-execution`
План vs факт по линиям.

```typescript
interface GM_PlanExecutionParams {
  date_from?: string;        // default: 30 days ago
  date_to?: string;          // default: today
}

interface PlanExecutionLineItem {
  production_line: string | null;
  target_quantity: string;
  actual_quantity: string;
  fulfillment_pct: string;
  orders_planned: number;
  orders_in_progress: number;
  orders_completed: number;
  orders_cancelled: number;
  total_snapshots: number;
}

interface GM_PlanExecutionResponse {
  period_from: string;
  period_to: string;
  lines: PlanExecutionLineItem[];
  total_target: string;
  total_actual: string;
  overall_fulfillment_pct: string;
}

// Пример:
const planExecution = await fetch(
  '/api/v1/dashboards/gm/plan-execution?date_from=2026-04-10&date_to=2026-05-10'
).then(r => r.json()) as GM_PlanExecutionResponse;
```

##### GET `/downtime-ranking`
Парето-рейтинг линий по простоям.

```typescript
interface GM_DowntimeRankingParams {
  date_from?: string;        // default: 30 days ago
  date_to?: string;          // default: today
}

interface DowntimeLineItem {
  production_line: string | null;
  total_delay_hours: string;
  delayed_orders: number;
  avg_delay_hours: string;
  total_completed: number;
  delay_pct: string;
}

interface GM_DowntimeRankingResponse {
  period_from: string;
  period_to: string;
  lines: DowntimeLineItem[];
  total_delay_hours: string;
  total_delayed_orders: number;
}

// Пример:
const downtimeRanking = await fetch(
  '/api/v1/dashboards/gm/downtime-ranking?date_from=2026-04-10&date_to=2026-05-10'
).then(r => r.json()) as GM_DowntimeRankingResponse;
```

---

#### Quality Engineer Dashboard

**Base:** `/api/v1/dashboards/qe`

##### GET `/parameter-trends`
Дневные тренды качества с допусками.

```typescript
interface QE_ParameterTrendsParams {
  date_from?: string;        // default: 30 days ago
  date_to?: string;          // default: today
}

interface TrendDataPoint {
  test_date: string;
  avg_value: string;
  test_count: number;
  out_of_spec_count: number;
  out_of_spec_pct: string;
  lower_limit: string | null;
  upper_limit: string | null;
}

interface ParameterTrendItem {
  parameter_name: string;
  total_tests: number;
  total_out_of_spec: number;
  overall_out_of_spec_pct: string;
  trend: TrendDataPoint[];
}

interface QE_ParameterTrendsResponse {
  period_from: string;
  period_to: string;
  parameters: ParameterTrendItem[];
}

// Пример:
const paramTrends = await fetch(
  '/api/v1/dashboards/qe/parameter-trends?date_from=2026-04-10&date_to=2026-05-10'
).then(r => r.json()) as QE_ParameterTrendsResponse;
```

##### GET `/batch-analysis`
Анализ партий с отклонениями.

```typescript
interface QE_BatchAnalysisParams {
  date_from?: string;        // default: 30 days ago
  date_to?: string;          // default: today
}

interface DeviationItem {
  parameter_name: string;
  result_value: string;
  lower_limit: string | null;
  upper_limit: string | null;
  deviation_magnitude: string;
}

interface BatchAnalysisItem {
  lot_number: string;
  product_name: string | null;
  production_date: string | null;
  shift: string | null;
  fail_count: number;
  deviations: DeviationItem[];
}

interface QE_BatchAnalysisResponse {
  period_from: string;
  period_to: string;
  lot_count: number;
  lots: BatchAnalysisItem[];
}

// Пример:
const batchAnalysis = await fetch(
  '/api/v1/dashboards/qe/batch-analysis?date_from=2026-04-10&date_to=2026-05-10'
).then(r => r.json()) as QE_BatchAnalysisResponse;
```

##### GET `/defect-pareto`
Парето-диаграмма дефектов.

```typescript
interface QE_DefectParetoParams {
  date_from?: string;        // default: 30 days ago
  date_to?: string;          // default: today
  product_id?: string;
}

interface ParetoItem {
  parameter_name: string;
  defect_count: number;
  total_tests: number;
  defect_pct: string;
  cumulative_pct: string;
}

interface QE_DefectParetoResponse {
  period_from: string;
  period_to: string;
  product_id: string | null;
  total_defects: number;
  parameters: ParetoItem[];
}

// Пример:
const pareto = await fetch(
  '/api/v1/dashboards/qe/defect-pareto?date_from=2026-04-10&date_to=2026-05-10'
).then(r => r.json()) as QE_DefectParetoResponse;
```

---

#### Finance Manager Dashboard

**Base:** `/api/v1/dashboards/finance`

##### GET `/sales-breakdown`
Разбивка выручки по каналам/регионам/продуктам.

```typescript
interface Finance_SalesBreakdownParams {
  date_from?: string;        // default: 30 days ago
  date_to?: string;          // default: today
  group_by?: 'channel' | 'region' | 'product';  // default: 'channel'
}

interface SalesGroupItem {
  group_key: string;
  total_amount: string;
  total_quantity: string;
  sales_count: number;
  avg_order_value: string;
  amount_share_pct: string;
}

interface Finance_SalesBreakdownResponse {
  period_from: string;
  period_to: string;
  group_by: string;
  total_amount: string;
  total_quantity: string;
  groups: SalesGroupItem[];
}

// Пример:
const breakdown = await fetch(
  '/api/v1/dashboards/finance/sales-breakdown?date_from=2026-04-10&date_to=2026-05-10&group_by=channel'
).then(r => r.json()) as Finance_SalesBreakdownResponse;
```

##### GET `/revenue-trend`
Тренд выручки с MoM growth.

```typescript
interface Finance_RevenueTrendParams {
  date_from?: string;        // default: 90 days ago
  date_to?: string;          // default: today
  interval?: 'day' | 'week' | 'month';  // default: 'week'
  region?: string;
  channel?: string;
}

interface RevenueTrendPoint {
  trend_date: string;
  total_amount: string;
  total_quantity: string;
  order_count: number;
  mom_growth_pct: string | null;
}

interface Finance_RevenueTrendResponse {
  period_from: string;
  period_to: string;
  interval: string;
  region: string | null;
  channel: string | null;
  data: RevenueTrendPoint[];
}

// Пример:
const revenueTrend = await fetch(
  '/api/v1/dashboards/finance/revenue-trend?date_from=2026-01-01&date_to=2026-05-10&interval=week'
).then(r => r.json()) as Finance_RevenueTrendResponse;
```

##### GET `/top-products`
Топ продуктов по выручке/объёму.

```typescript
interface Finance_TopProductsParams {
  date_from?: string;        // default: 30 days ago
  date_to?: string;          // default: today
  limit?: number;            // 1-50, default: 10
  sort_by?: 'amount' | 'quantity';  // default: 'amount'
}

interface TopProductItem {
  rank: number;
  product_name: string;
  total_amount: string;
  total_quantity: string;
  sales_count: number;
  amount_share_pct: string;
}

interface Finance_TopProductsResponse {
  period_from: string;
  period_to: string;
  sort_by: string;
  total_amount: string;
  products: TopProductItem[];
}

// Пример:
const topProducts = await fetch(
  '/api/v1/dashboards/finance/top-products?date_from=2026-04-10&date_to=2026-05-10&limit=5'
).then(r => r.json()) as Finance_TopProductsResponse;
```

---

## Обработка ошибок

### Коды ответов

| Код | Описание | Пример |
|-----|----------|--------|
| `200` | OK | Успешный запрос |
| `201` | Created | Ресурс создан (POST) |
| `400` | Bad Request | Неверные параметры |
| `404` | Not Found | Ресурс не найден |
| `422` | Validation Error | Невалидная модель |
| `500` | Internal Server Error | Внутренняя ошибка |

### Формат ошибок

```typescript
// 400 / 404
{
  detail: "error message",
  trace_id: "abc123def456"
}

// 422 Validation Error
{
  detail: [
    {
      loc: ["query", "from_date"],
      msg: "field required",
      type: "value_error.missing"
    }
  ],
  trace_id: "abc123def456"
}

// 500
{
  detail: "Internal server error",
  trace_id: "abc123def456"
}
```

### Обработка ошибок в TypeScript

```typescript
async function apiCall<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(endpoint, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    
    switch (response.status) {
      case 400:
        throw new Error(`Bad request: ${error.detail}`);
      case 404:
        throw new Error(`Not found: ${error.detail}`);
      case 422:
        const validationErrors = error.detail?.map((e: any) => 
          `${e.loc?.join('.')} — ${e.msg}`
        ).join(', ');
        throw new Error(`Validation error: ${validationErrors}`);
      case 500:
        throw new Error(`Server error (trace_id: ${error.trace_id})`);
      default:
        throw new Error(`HTTP ${response.status}: ${error.detail}`);
    }
  }

  return response.json();
}
```

---

## TypeScript типы

```typescript
// ========== Общие типы ==========

type Decimal = string;  // Все Decimal значения приходят как строки

interface DateRange {
  from?: string;        // YYYY-MM-DD
  to?: string;          // YYYY-MM-DD
}

interface Pagination {
  offset?: number;      // ≥0
  limit?: number;       // 1-100
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

type Status = 'ok' | 'warning' | 'critical';

// ========== KPI ==========

interface KPITarget {
  target: Decimal;
  min: Decimal;
  max: Decimal;
  status: Status;
}

interface KPITargets {
  oee_estimate: KPITarget | null;
  defect_rate: KPITarget | null;
  otif_rate: KPITarget | null;
}

interface KPITrendPoint {
  period: string;
  total_output: Decimal;
  defect_rate: Decimal;
  oee_estimate: Decimal | null;
}

interface KPIResponse {
  total_output: Decimal;
  defect_rate: Decimal;
  completed_orders: number;
  total_orders: number;
  availability: Decimal;
  performance: Decimal;
  oee_estimate: Decimal;
  line_throughput: Decimal;
  targets: KPITargets;
  trend: KPITrendPoint[];
  change_percent: Record<string, Decimal> | null;
}

// ========== Sales ==========

interface SalesSummaryItem {
  group_key: string;
  total_quantity: Decimal;
  total_amount: Decimal;
  sales_count: number;
  avg_order_value: Decimal | null;
}

interface SalesSummaryResponse {
  summary: SalesSummaryItem[];
  total_amount: Decimal;
  total_quantity: Decimal;
  period_from: string;
  period_to: string;
  group_by: string;
}

// ========== Orders ==========

interface OrderStatusCount {
  planned: number;
  in_progress: number;
  completed: number;
  cancelled: number;
}

interface OrderListItem {
  order_id: string;
  external_order_id: string | null;
  product_id: string;
  product_name: string | null;
  target_quantity: Decimal | null;
  actual_quantity: Decimal | null;
  unit_of_measure: string | null;
  status: string;
  production_line: string | null;
  planned_start: string | null;
  planned_end: string | null;
  actual_start: string | null;
  actual_end: string | null;
  snapshot_date: string;
}

// ========== Quality ==========

interface QualitySummaryResponse {
  average_quality: Decimal;
  approved_count: number;
  rejected_count: number;
  pending_count: number;
  defect_rate: Decimal;
  by_parameter: Record<string, { in_spec_percent: Decimal; tests_count: number }>;
  period_from: string;
  period_to: string;
}

// ========== OEE ==========

interface OEEComponentResponse {
  component: string;
  value: Decimal;
  target: Decimal;
  status: string;
}

interface OEESummaryResponse {
  summary_date: string;
  lines: OEELineResponse[];
  total_oee: Decimal;
  lines_above_target: number;
  lines_below_target: number;
  period_from: string;
  period_to: string;
}

// ========== Sync ==========

interface SyncTaskStatus {
  task_name: string;
  status: string;
  last_run: string | null;
  last_success: string | null;
  records_processed: number;
  records_inserted: number;
  records_updated: number;
  error_message: string | null;
}
```

---

## React примеры

### 1. Хук для KPI

```typescript
import { useState, useEffect } from 'react';

function useKPI(fromDate: string, toDate: string) {
  const [data, setData] = useState<KPIResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!fromDate || !toDate) return;
    
    setLoading(true);
    setError(null);
    
    fetch(`/api/production/kpi?from_date=${fromDate}&to_date=${toDate}&granularity=day`)
      .then(r => r.json())
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [fromDate, toDate]);

  return { data, loading, error };
}

// Использование:
function KPICard() {
  const { data, loading, error } = useKPI('2026-05-01', '2026-05-31');
  
  if (loading) return <div>Загрузка...</div>;
  if (error) return <div>Ошибка: {error}</div>;
  if (!data) return null;

  return (
    <div>
      <h2>OEE: {(parseFloat(data.oee_estimate) * 100).toFixed(1)}%</h2>
      <p>Брак: {(parseFloat(data.defect_rate) * 100).toFixed(1)}%</p>
      
      {data.targets.oee_estimate && (
        <span style={{ color: getStatusColor(data.targets.oee_estimate.status) }}>
          Target: {(parseFloat(data.targets.oee_estimate.target) * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}
```

### 2. Хук для списка заказов с пагинацией

```typescript
import { useState, useEffect, useCallback } from 'react';

function useOrders(fromDate: string, toDate: string, page: number = 1, limit: number = 20) {
  const [data, setData] = useState<OrderListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/v1/orders/list?from=${fromDate}&to=${toDate}&page=${page}&limit=${limit}`)
      .then(r => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, [fromDate, toDate, page, limit]);

  const nextPage = useCallback(() => {
    if (data && data.page < data.pages) {
      // set page state
    }
  }, [data]);

  return { data, loading, nextPage };
}

// Использование:
function OrdersTable() {
  const [page, setPage] = useState(1);
  const { data, loading } = useOrders('2026-05-01', '2026-05-31', page);
  
  if (loading) return <div>Загрузка...</div>;
  if (!data) return null;

  return (
    <div>
      <table>
        <thead>
          <tr>
            <th>Заказ</th>
            <th>Продукт</th>
            <th>Статус</th>
            <th>Количество</th>
          </tr>
        </thead>
        <tbody>
          {data.orders.map(order => (
            <tr key={order.order_id}>
              <td>{order.external_order_id || order.order_id}</td>
              <td>{order.product_name}</td>
              <td>{order.status}</td>
              <td>{order.actual_quantity || order.target_quantity}</td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <div>
        Страница {data.page} из {data.pages}
        <button onClick={() => setPage(p => Math.max(1, p - 1))}>←</button>
        <button onClick={() => setPage(p => Math.min(data.pages, p + 1))}>→</button>
      </div>
    </div>
  );
}
```

### 3. Компонент с фильтрами

```typescript
import { useState } from 'react';

function SalesDashboard() {
  const [fromDate, setFromDate] = useState('2026-05-01');
  const [toDate, setToDate] = useState('2026-05-31');
  const [groupBy, setGroupBy] = useState<'region' | 'channel' | 'product'>('channel');

  const url = `/api/v1/sales/summary?from=${fromDate}&to=${toDate}&group_by=${groupBy}`;

  return (
    <div>
      <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        <label>
          С:
          <input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} />
        </label>
        <label>
          По:
          <input type="date" value={toDate} onChange={e => setToDate(e.target.value)} />
        </label>
        <select value={groupBy} onChange={e => setGroupBy(e.target.value as any)}>
          <option value="region">По региону</option>
          <option value="channel">По каналу</option>
          <option value="product">По продукту</option>
        </select>
      </div>
      
      {/* Sales chart component */}
    </div>
  );
}
```

### 4. Мутации (POST)

```typescript
async function createDowntimeEvent(data: DowntimeEventCreate) {
  const response = await fetch('/api/production/downtime-events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json() as Promise<DowntimeEventResponse>;
}

// Использование:
async function handleSubmit() {
  try {
    const event = await createDowntimeEvent({
      production_line_id: '550e8400-e29b-41d4-a716-446655440000',
      reason: 'Поломка вала',
      category: 'UNPLANNED_BREAKDOWN',
      started_at: '2026-05-10T08:30:00Z',
      ended_at: '2026-05-10T10:15:00Z',
      duration_minutes: 105,
    });
    console.log('Создано:', event.id);
  } catch (error) {
    console.error('Ошибка:', error);
  }
}
```

### 5. Chart с Recharts

```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function OEEChart({ trend }: { trend: KPITrendPoint[] }) {
  const data = trend.map(point => ({
    date: point.period,
    oee: parseFloat(point.oee_estimate || '0') * 100,
    defect: parseFloat(point.defect_rate) * 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="oee" stroke="#8884d8" name="OEE %" />
        <Line type="monotone" dataKey="defect" stroke="#82ca9d" name="Брак %" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

---

## Быстрая справка по эндпоинтам

| Домен | Префикс | Методы | Кол-во |
|-------|---------|--------|--------|
| Health | `/` | GET | 2 |
| Sales | `/api/v1/sales` | GET | 4 |
| Orders | `/api/v1/orders` | GET | 5 |
| Quality | `/api/v1/quality` | GET | 6 |
| Products | `/api/v1/products` | GET | 2 |
| Output | `/api/v1/output` | GET | 2 |
| Sensors | `/api/v1/sensors` | GET | 3 |
| Inventory | `/api/v1/inventory` | GET | 2 |
| Production Analytics | `/api/production` | GET, POST | 17 |
| OEE | `/api/v1/oee` | GET, POST | 6 |
| Sync | `/api/v1/sync` | GET, POST | 8 |
| Line Master | `/api/v1/dashboards/line-master` | GET | 3 |
| GM Dashboard | `/api/v1/dashboards/gm` | GET | 3 |
| QE Dashboard | `/api/v1/dashboards/qe` | GET | 3 |
| Finance | `/api/v1/dashboards/finance` | GET | 3 |
| **Итого** | | | **~72** |

---

**Документация API:** http://localhost:3000/docs (Swagger UI)  
**ReDoc:** http://localhost:3000/redoc  
**OpenAPI JSON:** http://localhost:3000/openapi.json
