# Frontend API Integration Guide

**Версия:** 2.0 (Phase 2-3) | **Дата:** 2026-05-12

## Быстрый старт

### Base URL
```
http://localhost:3000/api/production
```

### Аутентификация
Все запросы требуют JWT token:
```javascript
headers: {
  'Authorization': 'Bearer <token>',
  'Content-Type': 'application/json'
}
```

---

## 📊 KPI Метрики

### 1. Основные KPI (OEE, Дефекты, OTIF)

**Эндпоинт:** `GET /kpi`

**Параметры:**
```
from_date: YYYY-MM-DD (обязательно)
to_date: YYYY-MM-DD (обязательно)
production_line_id: UUID (опционально)
granularity: day|week|month (опционально, по умолчанию day)
compare_with_previous: true|false (опционально)
```

**Пример запроса:**
```javascript
const response = await fetch(
  '/api/production/kpi?from_date=2026-05-01&to_date=2026-05-31&granularity=day',
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);
const kpi = await response.json();
```

**Структура ответа:**
```json
{
  "total_output": 1250.5,           // Общий выпуск (тонны)
  "defect_rate": 0.012,              // Доля брака (0-1)
  "completed_orders": 8,             // Выполненные заказы
  "total_orders": 10,                // Всего заказов
  "availability": 0.95,              // Доступность (0-1)
  "performance": 0.92,               // Производительность (0-1)
  "oee_estimate": 0.825,             // OEE (0-1)
  "line_throughput": 156.3,          // Пропускная способность
  "targets": {
    "oee_estimate": {
      "target": 0.85,
      "min": 0.75,
      "max": 1.0,
      "status": "warning"            // ok|warning|critical
    },
    "defect_rate": {
      "target": 0.015,
      "min": 0.0,
      "max": 0.015,
      "status": "ok"
    },
    "otif_rate": {
      "target": 0.95,
      "min": 0.9,
      "max": 1.0,
      "status": "ok"
    }
  },
  "trend": [
    {
      "period": "2026-05-01",
      "total_output": 180.2,
      "defect_rate": 0.011,
      "oee_estimate": 0.83
    },
    {
      "period": "2026-05-02",
      "total_output": 175.8,
      "defect_rate": 0.013,
      "oee_estimate": 0.82
    }
  ],
  "change_percent": {
    "totalOutput": 5.2,              // Изменение от предпред. периода (%)
    "oeeEstimate": -2.1
  }
}
```

**React компонент (пример):**
```typescript
import { useState, useEffect } from 'react';

export function KPIDashboard({ fromDate, toDate, token }) {
  const [kpi, setKpi] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchKpi = async () => {
      const res = await fetch(
        `/api/production/kpi?from_date=${fromDate}&to_date=${toDate}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      setKpi(await res.json());
      setLoading(false);
    };
    fetchKpi();
  }, [fromDate, toDate, token]);

  if (loading) return <div>Загрузка...</div>;
  if (!kpi) return <div>Ошибка загрузки</div>;

  return (
    <div className="kpi-grid">
      <KPICard 
        label="OEE" 
        value={(kpi.oee_estimate * 100).toFixed(1) + '%'}
        status={kpi.targets.oee_estimate.status}
      />
      <KPICard 
        label="Брак" 
        value={(kpi.defect_rate * 100).toFixed(2) + '%'}
        status={kpi.targets.defect_rate.status}
      />
      <TrendChart data={kpi.trend} />
    </div>
  );
}
```

**Статусы:**
- `ok` — зелёный, значение соответствует target
- `warning` — жёлтый, ниже target, но выше min
- `critical` — красный, ниже min или выше max

---

### 2. OTIF (On-Time In-Full)

**Эндпоинт:** `GET /kpi/otif`

**Параметры:**
```
from_date: YYYY-MM-DD (обязательно)
to_date: YYYY-MM-DD (обязательно)
production_line_id: UUID (опционально)
```

**Ответ:**
```json
{
  "otif_rate": 0.933,
  "on_time_orders": 28,              // Заказы в срок
  "in_full_quantity_orders": 30,     // Заказы в полном объёме
  "otif_orders": 28,                 // И то, и другое
  "total_orders": 30
}
```

**OTIF Формула:** (заказы в срок И в полном объёме) / всего заказов

---

### 3. KPI по группам (Drill-down)

**Эндпоинт:** `GET /kpi/breakdown`

**Параметры:**
```
from_date: YYYY-MM-DD (обязательно)
to_date: YYYY-MM-DD (обязательно)
group_by: productionLine|product|division (обязательно)
metric: oeeEstimate|defectRate|lineThroughput|otifRate (обязательно)
offset: int (по умолчанию 0)
limit: int (по умолчанию 20, макс. 100)
```

**Пример: KPI по производственным линиям**
```javascript
const response = await fetch(
  '/api/production/kpi/breakdown?from_date=2026-05-01&to_date=2026-05-31' +
  '&group_by=productionLine&metric=oeeEstimate&limit=10',
  { headers: { 'Authorization': `Bearer ${token}` } }
);
const breakdown = await response.json();
// breakdown.items = [
//   { group_key: "LINE-01", value: 0.852, target: 0.85, status: "ok", deviation: 0.002 },
//   { group_key: "LINE-02", value: 0.795, target: 0.85, status: "warning", deviation: -0.055 }
// ]
```

**Использование:** Сравнение производительности по линиям, поиск узких мест, анализ по дивизионам

---

### 4. Производительность линии (Phase 2)

**Эндпоинт:** `GET /kpi/line-productivity`

**Параметры:**
```
from_date: YYYY-MM-DD (обязательно)
to_date: YYYY-MM-DD (обязательно)
production_line_id: UUID (опционально)
```

**Ответ:**
```json
{
  "items": [
    {
      "production_line": "LINE-01",
      "productivity": 12.5,             // Тонн/час
      "total_output": 250,              // Общий выпуск за период
      "days": 20,                       // Рабочих дней
      "target": 15.0,
      "status": "warning",
      "deviation": -2.5
    }
  ],
  "period": {
    "from": "2026-05-01",
    "to": "2026-05-31"
  },
  "unit": "tonnes/hour"
}
```

---

### 5. Процент брака (Phase 2)

**Эндпоинт:** `GET /kpi/scrap-percentage`

**Параметры:**
```
from_date: YYYY-MM-DD (обязательно)
to_date: YYYY-MM-DD (обязательно)
product_id: UUID (опционально)
```

**Ответ:**
```json
{
  "scrap_percentage": 0.8,
  "rejected_tests": 8,
  "total_tests": 1000,
  "target": 1.5,
  "status": "ok",
  "period": {
    "from": "2026-05-01",
    "to": "2026-05-31"
  }
}
```

---

## 💰 Продажи и Маржа

### 1. Маржинальность по продуктам

**Эндпоинт:** `GET /sales/margin`

**Параметры:**
```
from_date: YYYY-MM-DD (обязательно)
to_date: YYYY-MM-DD (обязательно)
product_id: UUID (опционально)
offset: int (по умолчанию 0)
limit: int (по умолчанию 20, макс. 100)
```

**Пример запроса:**
```javascript
const response = await fetch(
  '/api/production/sales/margin?from_date=2026-05-01&to_date=2026-05-31&limit=50',
  { headers: { 'Authorization': `Bearer ${token}` } }
);
const salesData = await response.json();
```

**Ответ:**
```json
{
  "margins": [
    {
      "product_id": "uuid-1",
      "product_code": "PROD-001",
      "product_name": "Творог 5%",
      "total_quantity": 500,
      "total_revenue": 62500,
      "total_cost": 31250,
      "total_margin": 31250,
      "margin_percent": 50.0,
      "margin_per_unit": 62.5
    },
    {
      "product_id": "uuid-2",
      "product_code": "PROD-002",
      "product_name": "Масло сливочное",
      "total_quantity": 1000,
      "total_revenue": 250000,
      "total_cost": 125000,
      "total_margin": 125000,
      "margin_percent": 50.0,
      "margin_per_unit": 125.0
    }
  ],
  "total": 8,
  "aggregated": {
    "total_revenue": 210000,
    "total_cost": 105000,
    "total_margin": 105000,
    "avg_margin_percent": 50.0
  }
}
```

**Таблица в React:**
```typescript
export function MarginTable({ margins }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Продукт</th>
          <th>Выручка</th>
          <th>Маржа</th>
          <th>Маржа %</th>
        </tr>
      </thead>
      <tbody>
        {margins.margins.map(item => (
          <tr key={item.product_id}>
            <td>{item.product_name}</td>
            <td>₽ {item.total_revenue.toLocaleString()}</td>
            <td>₽ {item.total_margin.toLocaleString()}</td>
            <td>{item.margin_percent.toFixed(1)}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

## 📦 Сырьевой учёт (Batch Input)

### 1. Регистрация приёмки сырья

**Эндпоинт:** `POST /batch-inputs`

**Body:**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "product_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "quantity": 1000.5,
  "input_date": "2026-05-10T08:00:00Z"
}
```

**Ответ (201 Created):**
```json
{
  "id": "uuid",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "product_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "quantity": 1000.5,
  "input_date": "2026-05-10T08:00:00Z",
  "created_at": "2026-05-10T08:05:00Z",
  "updated_at": "2026-05-10T08:05:00Z"
}
```

**JavaScript:**
```javascript
async function recordBatchInput(batchData, token) {
  const response = await fetch('/api/production/batch-inputs', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(batchData)
  });
  return response.json();
}

// Использование:
const batch = {
  order_id: orderId,
  product_id: rawMaterialId,
  quantity: 1000.5,
  input_date: new Date().toISOString()
};
const result = await recordBatchInput(batch, token);
console.log(`Приёмка #${result.id} создана`);
```

---

### 2. Выход готовой продукции (Yield)

**Эндпоинт:** `GET /batch-inputs/yield?order_id=<uuid>`

**Параметры:**
```
order_id: UUID (обязательно)
```

**Ответ:**
```json
{
  "order_id": "uuid",
  "total_input": 1000.5,
  "total_output": 850.2,
  "yield_percent": 85.0,
  "target": 86.0
}
```

**Интерпретация:** Из 1000.5 тонн сырья получили 850.2 тонны готовой продукции (85% выхода). Целевой показатель 86%.

**React компонент:**
```typescript
export function YieldCard({ orderId, token }) {
  const [yieldData, setYieldData] = useState(null);

  useEffect(() => {
    fetch(`/api/production/batch-inputs/yield?order_id=${orderId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setYieldData);
  }, [orderId, token]);

  if (!yieldData) return <div>Загрузка...</div>;

  const status = yieldData.yield_percent >= yieldData.target ? 'ok' : 'warning';

  return (
    <div className={`yield-card ${status}`}>
      <h3>Выход масла с тонны семян</h3>
      <div className="metric">
        <span className="label">Выход:</span>
        <span className="value">{yieldData.yield_percent.toFixed(1)}%</span>
      </div>
      <div className="target">
        <span>Target: {yieldData.target.toFixed(1)}%</span>
      </div>
    </div>
  );
}
```

---

### 3. Список приёмок сырья

**Эндпоинт:** `GET /batch-inputs`

**Параметры:**
```
order_id: UUID (опционально)
product_id: UUID (опционально)
offset: int (по умолчанию 0)
limit: int (по умолчанию 20, макс. 100)
```

**Ответ:**
```json
{
  "items": [
    {
      "id": "uuid-1",
      "order_id": "order-uuid",
      "product_id": "product-uuid",
      "quantity": 1000.5,
      "input_date": "2026-05-10T08:00:00Z",
      "created_at": "2026-05-10T08:05:00Z",
      "updated_at": "2026-05-10T08:05:00Z"
    }
  ],
  "total": 5
}
```

---

## ⏸️ Простои оборудования (Downtime)

### 1. Регистрация простоя

**Эндпоинт:** `POST /downtime-events`

**Body:**
```json
{
  "production_line_id": "uuid",
  "reason": "Поломка вала редуктора",
  "category": "UNPLANNED_BREAKDOWN",
  "started_at": "2026-05-10T08:30:00Z",
  "ended_at": "2026-05-10T10:15:00Z",
  "duration_minutes": 105
}
```

**Категории:**
- `PLANNED_MAINTENANCE` — плановое обслуживание
- `UNPLANNED_BREAKDOWN` — аварийный отказ
- `QUALITY_ISSUE` — проблема с качеством
- `MATERIAL_SHORTAGE` — нехватка материала
- `OTHER` — прочее

**Ответ (201 Created):**
```json
{
  "id": "uuid",
  "production_line_id": "uuid",
  "reason": "Поломка вала редуктора",
  "category": "UNPLANNED_BREAKDOWN",
  "started_at": "2026-05-10T08:30:00Z",
  "ended_at": "2026-05-10T10:15:00Z",
  "duration_minutes": 105,
  "created_at": "2026-05-10T10:20:00Z",
  "updated_at": "2026-05-10T10:20:00Z"
}
```

---

### 2. Сводка простоев по категориям

**Эндпоинт:** `GET /downtime-events/summary`

**Параметры:**
```
from_date: YYYY-MM-DD (опционально)
to_date: YYYY-MM-DD (опционально)
```

**Ответ:**
```json
{
  "items": [
    {
      "category": "UNPLANNED_BREAKDOWN",
      "total_minutes": 520,
      "count": 5
    },
    {
      "category": "PLANNED_MAINTENANCE",
      "total_minutes": 240,
      "count": 2
    },
    {
      "category": "QUALITY_ISSUE",
      "total_minutes": 180,
      "count": 3
    }
  ],
  "total_events": 10,
  "total_downtime_minutes": 940
}
```

**Диаграмма в React (Pie Chart):**
```typescript
import { PieChart } from 'recharts';

export function DowntimePie({ downtime }) {
  const chartData = downtime.items.map(item => ({
    name: translateCategory(item.category),
    value: item.total_minutes,
    count: item.count
  }));

  return (
    <div>
      <h3>Распределение простоев</h3>
      <PieChart width={400} height={300} data={chartData}>
        {/* Recharts config */}
      </PieChart>
      <p>Всего: {downtime.total_downtime_minutes} мин ({
        (downtime.total_downtime_minutes / 60).toFixed(1)} ч)</p>
    </div>
  );
}

function translateCategory(cat) {
  const map = {
    'UNPLANNED_BREAKDOWN': 'Аварийный отказ',
    'PLANNED_MAINTENANCE': 'Плановое ТО',
    'QUALITY_ISSUE': 'Проблемы качества',
    'MATERIAL_SHORTAGE': 'Нехватка материала',
    'OTHER': 'Прочее'
  };
  return map[cat] || cat;
}
```

---

### 3. Список простоев

**Эндпоинт:** `GET /downtime-events`

**Параметры:**
```
from_date: YYYY-MM-DD (опционально)
to_date: YYYY-MM-DD (опционально)
production_line_id: UUID (опционально)
category: string (опционально)
offset: int (по умолчанию 0)
limit: int (по умолчанию 20, макс. 100)
```

---

## 🎯 Промо-акции (Promo Campaigns)

### 1. Создание промо-акции

**Эндпоинт:** `POST /promo-campaigns`

**Body:**
```json
{
  "name": "Скидка на творог 10%",
  "description": "Весенняя акция на молочные продукты",
  "channel": "DIRECT",
  "product_id": "uuid",
  "discount_percent": 10,
  "start_date": "2026-05-01",
  "end_date": "2026-05-31",
  "budget": 50000
}
```

**Каналы:**
- `DIRECT` — прямые продажи
- `DISTRIBUTOR` — дистрибьюторы
- `RETAIL` — розница
- `ONLINE` — онлайн

**Ответ (201 Created):**
```json
{
  "id": "uuid",
  "name": "Скидка на творог 10%",
  "description": "Весенняя акция на молочные продукты",
  "channel": "DIRECT",
  "product_id": "uuid",
  "discount_percent": 10,
  "start_date": "2026-05-01",
  "end_date": "2026-05-31",
  "budget": 50000,
  "created_at": "2026-05-10T12:00:00Z",
  "updated_at": "2026-05-10T12:00:00Z"
}
```

---

### 2. Список промо-акций

**Эндпоинт:** `GET /promo-campaigns`

**Параметры:**
```
from_date: YYYY-MM-DD (опционально)
to_date: YYYY-MM-DD (опционально)
channel: string (опционально)
offset: int (по умолчанию 0)
limit: int (по умолчанию 20, макс. 100)
```

---

### 3. Эффективность промо-акции (ROI)

**Эндпоинт:** `GET /promo-campaigns/{campaign_id}/effectiveness`

**Параметры:**
```
campaign_id: UUID (обязательно, в пути)
```

**Ответ:**
```json
{
  "campaign_id": "uuid",
  "campaign_name": "Скидка на творог 10%",
  "budget": 50000,
  "sales_during_campaign": 125000,
  "baseline_sales": 75000,
  "uplift": 50000,
  "cost_per_uplift_unit": 50,
  "roi": 1.5,
  "roi_percent": 150
}
```

**Интерпретация:**
- **Uplift** — дополнительные продажи благодаря акции (125k - 75k = 50k)
- **ROI** — возврат инвестиций (50k / 50k = 1.0 = 100%)
- **Cost per uplift** — сколько потратили на 1 единицу дополнительных продаж

**React компонент:**
```typescript
export function CampaignEffectiveness({ campaignId, token }) {
  const [effectiveness, setEffectiveness] = useState(null);

  useEffect(() => {
    fetch(`/api/production/promo-campaigns/${campaignId}/effectiveness`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setEffectiveness);
  }, [campaignId, token]);

  if (!effectiveness) return <div>Загрузка...</div>;

  const roiStatus = effectiveness.roi_percent >= 100 ? 'success' : 'warning';

  return (
    <div className={`effectiveness ${roiStatus}`}>
      <h3>ROI: {effectiveness.roi_percent.toFixed(0)}%</h3>
      <div className="metrics">
        <div>
          <label>Бюджет:</label>
          <span>₽ {effectiveness.budget.toLocaleString()}</span>
        </div>
        <div>
          <label>Uplift:</label>
          <span>₽ {effectiveness.uplift.toLocaleString()}</span>
        </div>
        <div>
          <label>Базовые продажи:</label>
          <span>₽ {effectiveness.baseline_sales.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
```

---

## 📋 Справочники

### 1. Производственные линии

**Эндпоинт:** `GET /production-lines`

**Параметры:**
```
division: string (опционально) — фильтр по дивизиону
offset: int (по умолчанию 0)
limit: int (по умолчанию 20, макс. 100)
```

**Ответ:**
```json
{
  "production_lines": [
    {
      "id": "uuid-1",
      "code": "LINE-01",
      "name": "Линия молока",
      "description": "Основная линия обработки молока",
      "division": "Управление производством и технологиями",
      "is_active": true
    },
    {
      "id": "uuid-2",
      "code": "LINE-02",
      "name": "Линия масла",
      "description": "Линия производства сливочного масла",
      "division": "Управление производством и технологиями",
      "is_active": true
    }
  ],
  "total": 5
}
```

**Select для фильтрации:**
```typescript
export function LineSelector({ division, token, onSelect }) {
  const [lines, setLines] = useState([]);

  useEffect(() => {
    const url = '/api/production/production-lines' + 
      (division ? `?division=${encodeURIComponent(division)}` : '');
    
    fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => setLines(data.production_lines));
  }, [division, token]);

  return (
    <select onChange={(e) => onSelect(e.target.value)}>
      <option value="">Все линии</option>
      {lines.map(line => (
        <option key={line.id} value={line.id}>
          {line.code} — {line.name}
        </option>
      ))}
    </select>
  );
}
```

---

## 🎨 Работа со статусами (Traffic Light)

Все метрики с целевыми значениями возвращают `status`:

```json
{
  "value": 0.82,
  "target": 0.85,
  "min": 0.75,
  "max": 1.0,
  "status": "warning"
}
```

**Логика:**
- **`ok`** (🟢 зелёный) — значение соответствует target
- **`warning`** (🟡 жёлтый) — значение < target, но >= min
- **`critical`** (🔴 красный) — значение < min или > max

**CSS класс в React:**
```typescript
function StatusIndicator({ status, value, target }) {
  const colorMap = {
    'ok': '#4caf50',        // зелёный
    'warning': '#ff9800',   // оранжевый
    'critical': '#f44336'   // красный
  };

  return (
    <div 
      className={`status-indicator ${status}`}
      style={{ backgroundColor: colorMap[status] }}
    >
      <span>{status === 'ok' ? '✓' : '⚠'}</span>
      <span>{(value * 100).toFixed(1)}% vs {(target * 100).toFixed(1)}%</span>
    </div>
  );
}
```

---

## 📈 Графики и тренды

### Данные для графиков

Все KPI возвращают `trend` — массив точек для построения графиков:

```json
{
  "trend": [
    {
      "period": "2026-05-01",
      "total_output": 180.2,
      "defect_rate": 0.011,
      "oee_estimate": 0.83
    },
    {
      "period": "2026-05-02",
      "total_output": 175.8,
      "defect_rate": 0.013,
      "oee_estimate": 0.82
    }
  ]
}
```

**Recharts пример:**
```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

export function TrendChart({ trend }) {
  return (
    <LineChart width={600} height={300} data={trend}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="period" />
      <YAxis yAxisId="left" />
      <YAxis yAxisId="right" orientation="right" />
      <Tooltip />
      <Line 
        yAxisId="left"
        type="monotone" 
        dataKey="total_output" 
        stroke="#8884d8" 
        name="Выпуск (т)"
      />
      <Line 
        yAxisId="right"
        type="monotone" 
        dataKey="oee_estimate" 
        stroke="#82ca9d" 
        name="OEE"
      />
    </LineChart>
  );
}
```

---

## 🔄 Пример: Полный dashboard

```typescript
import { useState, useEffect } from 'react';

export function AnalyticsDashboard({ token }) {
  const [period, setPeriod] = useState({
    fromDate: '2026-05-01',
    toDate: '2026-05-31'
  });
  
  const [kpi, setKpi] = useState(null);
  const [downtime, setDowntime] = useState(null);
  const [margin, setMargin] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);

      // Параллельные запросы
      const [kpiRes, downtimeRes, marginRes] = await Promise.all([
        fetch(
          `/api/production/kpi?from_date=${period.fromDate}&to_date=${period.toDate}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        ),
        fetch(
          `/api/production/downtime-events/summary?from_date=${period.fromDate}&to_date=${period.toDate}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        ),
        fetch(
          `/api/production/sales/margin?from_date=${period.fromDate}&to_date=${period.toDate}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        )
      ]);

      const [kpiData, downtimeData, marginData] = await Promise.all([
        kpiRes.json(),
        downtimeRes.json(),
        marginRes.json()
      ]);

      setKpi(kpiData);
      setDowntime(downtimeData);
      setMargin(marginData);
      setLoading(false);
    };

    fetchData();
  }, [period, token]);

  if (loading) return <div>Загрузка...</div>;

  return (
    <div className="dashboard">
      <h1>Аналитика производства</h1>
      
      {/* Период */}
      <div className="period-selector">
        <input 
          type="date" 
          value={period.fromDate}
          onChange={(e) => setPeriod({ ...period, fromDate: e.target.value })}
        />
        <input 
          type="date"
          value={period.toDate}
          onChange={(e) => setPeriod({ ...period, toDate: e.target.value })}
        />
      </div>

      {/* KPI Cards */}
      <div className="kpi-section">
        <h2>Основные показатели</h2>
        <div className="kpi-grid">
          <KPICard 
            title="OEE" 
            value={(kpi.oee_estimate * 100).toFixed(1) + '%'}
            target={kpi.targets.oee_estimate.target}
            status={kpi.targets.oee_estimate.status}
          />
          <KPICard 
            title="Выход" 
            value={(kpi.defect_rate * 100).toFixed(2) + '%'}
            target={kpi.targets.defect_rate.target}
            status={kpi.targets.defect_rate.status}
          />
          <KPICard 
            title="OTIF" 
            value={(kpi.targets.otif_rate.target * 100).toFixed(1) + '%'}
            status={kpi.targets.otif_rate.status}
          />
        </div>
      </div>

      {/* Trend Chart */}
      <div className="chart-section">
        <h2>Тренд</h2>
        <TrendChart trend={kpi.trend} />
      </div>

      {/* Downtime */}
      <div className="downtime-section">
        <h2>Простои</h2>
        <DowntimePie downtime={downtime} />
      </div>

      {/* Margin */}
      <div className="margin-section">
        <h2>Маржинальность</h2>
        <MarginTable margins={margin} />
      </div>
    </div>
  );
}
```

---

## ❌ Обработка ошибок

**Коды ответов:**
- `200` — успех
- `201` — создано
- `400` — ошибка валидации параметров
- `401` — не авторизован (невалидный token)
- `403` — доступ запрещён
- `404` — ресурс не найден
- `429` — превышен rate limit
- `503` — сервис недоступен

**Пример обработки:**
```typescript
async function fetchKPI(params, token) {
  try {
    const response = await fetch(
      `/api/production/kpi?from_date=${params.fromDate}&to_date=${params.toDate}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Session expired');
      }
      if (response.status === 400) {
        const error = await response.json();
        throw new Error(`Validation: ${error.detail}`);
      }
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('KPI fetch failed:', error);
    throw error;
  }
}
```

---

## 📚 Чит-лист фронтенд разработчика

### Старт работы:
- [ ] Сохранить `http://localhost:3000/api/production` как базовый URL
- [ ] Получить JWT token от backend
- [ ] Проверить доступ на `/production-lines` (простой GET)

### KPI Dashboard:
- [ ] Добавить date picker для фильтра по периоду
- [ ] Загрузить KPI с `GET /kpi`
- [ ] Вывести KPI cards с цветовой индикацией (status)
- [ ] Нарисовать линейный график с `trend` данными

### Drill-down:
- [ ] Добавить select "Group by" (productionLine, product, division)
- [ ] Загрузить `GET /kpi/breakdown`
- [ ] Вывести таблицу с сортировкой по deviation

### Простои:
- [ ] Добавить pie chart для `/downtime-events/summary`
- [ ] Показать общее время простоев в часах

### Маржа:
- [ ] Таблица с `/sales/margin` (revenue, margin %, margin per unit)
- [ ] Footerline с aggregated (total revenue, avg margin %)

### Промо-акции:
- [ ] Список кампаний с `/promo-campaigns`
- [ ] Клик на кампанию → подгрузить `/effectiveness`
- [ ] Показать ROI % с цветовой индикацией (>100% зелёный)

---

## 🚀 Развёртывание

**Backend запущен локально:**
```bash
cd /home/ivan/projects/DiplomaAPI
./init.sh                           # Инициализация БД
uvicorn app.main:app --reload       # Запуск API на :3000
```

**Swagger документация:**
```
http://localhost:3000/docs
```

---

## 🐛 Отладка

**Включить логи запросов:**
```javascript
// Перед каждым fetch()
console.log('>> REQUEST', method, url, body);
fetch(...)
  .then(r => {
    console.log('<< RESPONSE', r.status, r.statusText);
    return r.json();
  })
```

**Проверить response в браузере:**
```javascript
// В DevTools Console
fetch('/api/production/kpi?from_date=2026-05-01&to_date=2026-05-31', {
  headers: { 'Authorization': 'Bearer <token>' }
})
  .then(r => r.json())
  .then(d => console.table(d))
```

---

## 📞 Support

Если эндпоинт возвращает `500 Service Unavailable`:
1. Проверить, запущен ли backend: `curl http://localhost:3000/health`
2. Проверить логи: `docker logs diploma-api`
3. Проверить JWT token: `curl -H "Authorization: Bearer <token>" http://localhost:3000/api/production/production-lines`

---

**Последнее обновление:** 2026-05-12  
**Статус:** Phase 2-3 (Production)  
**Автор:** AI Assistant
