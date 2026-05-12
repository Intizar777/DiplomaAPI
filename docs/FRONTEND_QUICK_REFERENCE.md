# Frontend Quick Reference

**API Base URL:** `http://localhost:3000/api/production`  
**Auth:** `Authorization: Bearer <token>`  
**Content-Type:** `application/json`

---

## 🎯 Top 5 Endpoints

| Endpoint | Метод | Параметры | Возвращает |
|----------|-------|-----------|-----------|
| `/kpi` | GET | `from_date`, `to_date`, `granularity=day` | OEE, дефекты, OTIF, тренд |
| `/sales/margin` | GET | `from_date`, `to_date`, `limit=20` | Маржа по продуктам |
| `/downtime-events/summary` | GET | `from_date?`, `to_date?` | Простои по категориям |
| `/promo-campaigns/{id}/effectiveness` | GET | `campaign_id` | ROI, uplift, cost_per_uplift |
| `/kpi/line-productivity` | GET | `from_date`, `to_date` | Производительность линий (т/ч) |

---

## 📊 KPI Cards

```javascript
GET /kpi?from_date=2026-05-01&to_date=2026-05-31&granularity=day
```

Ответ содержит:
- `oee_estimate` — OEE (0-1)
- `defect_rate` — Брак (0-1)
- `targets` — с `status: ok|warning|critical`
- `trend` — массив {period, value...}
- `change_percent` — сравнение с предпериодом

**Цвета:**
- 🟢 `ok` — в норме
- 🟡 `warning` — ниже target
- 🔴 `critical` — ниже min

---

## 📈 Графики

Все KPI содержат `trend` для Recharts:
```json
{
  "trend": [
    { "period": "2026-05-01", "total_output": 180.2, "oee_estimate": 0.83 },
    { "period": "2026-05-02", "total_output": 175.8, "oee_estimate": 0.82 }
  ]
}
```

```typescript
<LineChart data={kpi.trend}>
  <Line dataKey="oee_estimate" stroke="#8884d8" />
</LineChart>
```

---

## 💰 Маржа

```javascript
GET /sales/margin?from_date=2026-05-01&to_date=2026-05-31
```

Ответ:
```json
{
  "margins": [
    {
      "product_name": "Творог 5%",
      "total_revenue": 62500,
      "margin_percent": 50.0
    }
  ],
  "aggregated": {
    "avg_margin_percent": 50.0
  }
}
```

---

## 🎯 Эффективность промо

```javascript
GET /promo-campaigns/{campaign_id}/effectiveness
```

Ответ:
```json
{
  "campaign_name": "Скидка 10%",
  "budget": 50000,
  "uplift": 50000,
  "roi_percent": 150,          // > 100% зелёный
  "cost_per_uplift_unit": 50
}
```

---

## ⏸️ Простои

```javascript
GET /downtime-events/summary?from_date=2026-05-01&to_date=2026-05-31
```

Ответ:
```json
{
  "items": [
    {
      "category": "UNPLANNED_BREAKDOWN",
      "total_minutes": 520,
      "count": 5
    }
  ],
  "total_downtime_minutes": 940
}
```

Категории: `PLANNED_MAINTENANCE`, `UNPLANNED_BREAKDOWN`, `QUALITY_ISSUE`, `MATERIAL_SHORTAGE`, `OTHER`

---

## 📋 Производственные линии

```javascript
GET /production-lines?division=...&limit=20
```

Используй для select/dropdown фильтров.

---

## 🔍 Параметры фильтрации

```javascript
// Дата
?from_date=2026-05-01&to_date=2026-05-31

// Гранулярность (для trend)
?granularity=day|week|month

// Пагинация
?offset=0&limit=20

// Группировка
?group_by=productionLine|product|division

// Метрика (для breakdown)
?metric=oeeEstimate|defectRate|lineThroughput|otifRate

// Фильтры
?production_line_id=uuid
?product_id=uuid
?channel=DIRECT|DISTRIBUTOR|RETAIL|ONLINE
?category=PLANNED_MAINTENANCE
```

---

## ✅ Регистрация данных (POST)

**Приёмка сырья:**
```javascript
POST /batch-inputs
{
  "order_id": "uuid",
  "product_id": "uuid",
  "quantity": 1000.5,
  "input_date": "2026-05-10T08:00:00Z"
}
```

**Простой:**
```javascript
POST /downtime-events
{
  "production_line_id": "uuid",
  "reason": "Поломка вала",
  "category": "UNPLANNED_BREAKDOWN",
  "started_at": "2026-05-10T08:30:00Z",
  "ended_at": "2026-05-10T10:15:00Z"
}
```

**Промо-акция:**
```javascript
POST /promo-campaigns
{
  "name": "Скидка творог 10%",
  "channel": "DIRECT",
  "discount_percent": 10,
  "start_date": "2026-05-01",
  "end_date": "2026-05-31",
  "budget": 50000
}
```

---

## 🚀 Fetch Helper

```typescript
const API_BASE = 'http://localhost:3000/api/production';

async function apiCall(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  
  const response = await fetch(API_BASE + endpoint, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Использование:
const kpi = await apiCall('/kpi?from_date=2026-05-01&to_date=2026-05-31');
```

---

## 📱 React Hooks

```typescript
function useKPI(fromDate, toDate, token) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiCall(`/kpi?from_date=${fromDate}&to_date=${toDate}`)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [fromDate, toDate, token]);

  return { data, loading, error };
}

// Использование:
const { data: kpi } = useKPI('2026-05-01', '2026-05-31', token);
```

---

## 🔴 Обработка ошибок

```javascript
try {
  const data = await fetch(url, options).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  });
} catch (error) {
  if (error.message.includes('401')) {
    // Истёк token, перейти на логин
  } else if (error.message.includes('400')) {
    // Ошибка валидации параметров
  } else {
    // Сервер недоступен
  }
}
```

---

## 📚 Подробная документация

👉 [docs/frontend-api-guide.md](frontend-api-guide.md) — полный гайд с примерами

---

**Версия:** 2.0 | **Дата:** 2026-05-12 | **Статус:** Phase 2-3
