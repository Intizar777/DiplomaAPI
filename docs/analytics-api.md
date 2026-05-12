# Analytics API Reference

## Обзор

API аналитики предоставляет полный набор эндпойнтов для получения KPI, продаж, простоев оборудования, сырьевого учёта и прочих показателей производства. Разработано в соответствии с планом [v1.3.0-analytics-dashboard-plan.md](/plans/v1.3.0-analytics-dashboard-plan.md) для поддержки информационно-аналитической панели дипломного проекта.

## Base URL

```
http://localhost:3000/api/production
```

---

## 1. KPI — Основные показатели производства

### GET /production/kpi

Получить основные KPI производства с целевыми значениями и трендами.

**Query Parameters:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | ISO 8601 date | ❌ | Начало периода (по умолчанию начало месяца) |
| `to` | ISO 8601 date | ❌ | Конец периода (по умолчанию сегодня) |
| `productionLineId` | UUID | ❌ | Фильтр по производственной линии |
| `granularity` | string | ❌ | Гранулярность тренда: `day`, `week`, `month` |
| `compareWithPrevious` | boolean | ❌ | Вернуть сравнение с предыдущим периодом |

**Response 200 OK:**

```json
{
  "totalOutput": 1250.5,
  "defectRate": 0.012,
  "completedOrders": 8,
  "totalOrders": 10,
  "availability": 0.95,
  "performance": 0.92,
  "oeeEstimate": 0.825,
  "lineThroughput": 156.3,
  "targets": {
    "oee_estimate": {
      "target": 0.85,
      "min": 0.75,
      "max": 1.0,
      "status": "warning"
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
      "totalOutput": 180.2,
      "defectRate": 0.011,
      "oeeEstimate": 0.83
    },
    {
      "period": "2026-05-02",
      "totalOutput": 175.8,
      "defectRate": 0.013,
      "oeeEstimate": 0.82
    }
  ],
  "changePercent": {
    "totalOutput": 5.2,
    "oeeEstimate": -2.1
  }
}
```

**Статусы:**
- `ok` — значение в норме (соответствует target)
- `warning` — значение ниже target, но выше min
- `critical` — значение ниже min или выше max

**Cache:** 30 сек | **Rate Limit:** long (10k/60s)

---

### GET /production/kpi/otif

Получить OTIF метрики — заказы выполненные в срок и в полном объёме.

**Query Parameters:**

| Параметр | Тип | Описание |
|----------|-----|---------|
| `from` | ISO 8601 date | ❌ Начало периода |
| `to` | ISO 8601 date | ❌ Конец периода |
| `productionLineId` | UUID | ❌ Фильтр по линии |

**Response 200 OK:**

```json
{
  "otifRate": 0.933,
  "onTimeOrders": 28,
  "inFullQuantityOrders": 30,
  "otifOrders": 28,
  "totalOrders": 30
}
```

**Формула:** OTIF = (заказы с полным объёмом И в срок) / все заказы

**Use cases:**
- Отслеживание выполнения заказов
- KPI продаж (FR диплома)

---

### GET /production/kpi/breakdown

Получить KPI по группам (drill-down) для анализа по производственным линиям, продуктам или дивизионам.

**Query Parameters:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | ISO 8601 date | ❌ | Начало периода |
| `to` | ISO 8601 date | ❌ | Конец периода |
| `groupBy` | string | ✅ | `productionLine`, `product`, `division` |
| `metric` | string | ✅ | `oeeEstimate`, `defectRate`, `lineThroughput`, `otifRate` |
| `offset` | int | ❌ | Смещение (по умолчанию 0) |
| `limit` | int | ❌ | Лимит записей (по умолчанию 20, макс. 100) |

**Response 200 OK:**

```json
{
  "items": [
    {
      "groupKey": "LINE-01",
      "value": 0.852,
      "target": 0.85,
      "status": "ok",
      "deviation": 0.002
    },
    {
      "groupKey": "LINE-02",
      "value": 0.795,
      "target": 0.85,
      "status": "warning",
      "deviation": -0.055
    }
  ],
  "total": 5
}
```

**Use cases:**
- Сравнение производительности линий
- Анализ по дивизионам (FR-03, FR-04)
- Выявление узких мест

---

### POST /production/kpi/export

Экспортировать KPI в CSV или JSON формат.

**Body (application/json):**

```json
{
  "from": "2026-05-01",
  "to": "2026-05-31",
  "productionLineId": "uuid-or-null",
  "format": "csv",
  "metrics": ["oeeEstimate", "defectRate", "lineThroughput"],
  "filename": "kpi_may_2026"
}
```

**Response 200 OK:**

```json
{
  "url": "https://bucket.s3.amazonaws.com/exports/kpi_may_2026.csv",
  "expiresIn": 3600,
  "size": 15240
}
```

---

## 2. Продажи (Sales)

### GET /production/sales

Получить список всех продаж с фильтрацией.

**Query Parameters:**

| Параметр | Тип | Описание |
|----------|-----|---------|
| `productId` | UUID | Фильтр по продукту |
| `customerId` | UUID | Фильтр по покупателю |
| `channel` | string | `DIRECT`, `DISTRIBUTOR`, `RETAIL`, `ONLINE` |
| `from` | ISO 8601 date | Начало периода |
| `to` | ISO 8601 date | Конец периода |
| `offset` | int | Смещение |
| `limit` | int | Лимит |

**Response 200 OK:**

```json
{
  "sales": [
    {
      "id": "uuid",
      "orderId": "uuid",
      "productId": "uuid",
      "customerId": "uuid",
      "quantity": 100,
      "unitPrice": 125.5,
      "totalAmount": 12550,
      "saleCost": 6250,
      "margin": 6300,
      "marginPercent": 50.2,
      "channel": "DIRECT",
      "saleDate": "2026-05-10T14:30:00Z"
    }
  ],
  "total": 45
}
```

---

### GET /production/sales/summary

Получить сводку продаж за период с трендом и группировкой по каналам.

**Query Parameters:**

| Параметр | Тип | Описание |
|----------|-----|---------|
| `from` | ISO 8601 date | Начало периода |
| `to` | ISO 8601 date | Конец периода |
| `channel` | string | Фильтр по каналу |
| `granularity` | string | `day`, `week`, `month` (для тренда) |

**Response 200 OK:**

```json
{
  "summary": [
    {
      "channel": "DIRECT",
      "totalAmount": 125000,
      "totalQuantity": 1000,
      "salesCount": 12,
      "avgOrderValue": 10416.67
    },
    {
      "channel": "DISTRIBUTOR",
      "totalAmount": 85000,
      "totalQuantity": 680,
      "salesCount": 8,
      "avgOrderValue": 10625
    }
  ],
  "totalAmount": 210000,
  "totalQuantity": 1680,
  "total": 2,
  "trend": [
    {
      "period": "2026-05-01",
      "totalAmount": 7500,
      "totalQuantity": 60,
      "salesCount": 1
    },
    {
      "period": "2026-05-02",
      "totalAmount": 8200,
      "totalQuantity": 65,
      "salesCount": 1
    }
  ]
}
```

---

### GET /production/sales/margin

Получить маржинальность по продуктам и периодам.

**Query Parameters:**

| Параметр | Тип | Описание |
|----------|-----|---------|
| `from` | ISO 8601 date | Начало периода |
| `to` | ISO 8601 date | Конец периода |
| `productId` | UUID | Фильтр по продукту |
| `offset` | int | Смещение |
| `limit` | int | Лимит |

**Response 200 OK:**

```json
{
  "margins": [
    {
      "productId": "uuid",
      "productCode": "PROD-001",
      "productName": "Творог 5%",
      "totalQuantity": 500,
      "totalRevenue": 62500,
      "totalCost": 31250,
      "totalMargin": 31250,
      "marginPercent": 50.0,
      "marginPerUnit": 62.5
    }
  ],
  "total": 8,
  "aggregated": {
    "totalRevenue": 210000,
    "totalCost": 105000,
    "totalMargin": 105000,
    "avgMarginPercent": 50.0
  }
}
```

---

## 3. Сырьевой учёт (Batch Input)

Отслеживание поступления и выхода сырья для расчёта технико-хозяйственных показателей.

### POST /production/batch-inputs

Зарегистрировать приёмку сырья.

**Body (application/json):**

```json
{
  "orderId": "uuid",
  "productId": "uuid",
  "quantity": 1000.5,
  "inputDate": "2026-05-10T08:00:00Z"
}
```

**Response 201 Created:**

```json
{
  "id": "uuid",
  "orderId": "uuid",
  "productId": "uuid",
  "quantity": 1000.5,
  "inputDate": "2026-05-10T08:00:00Z"
}
```

---

### GET /production/batch-inputs

Получить все приёмки сырья с фильтрацией.

**Query Parameters:**

| Параметр | Тип | Описание |
|----------|-----|---------|
| `orderId` | UUID | Фильтр по заказу |
| `productId` | UUID | Фильтр по продукту (сырью) |
| `offset` | int | Смещение |
| `limit` | int | Лимит |
| `include` | string | `order`, `product` (загрузить связанные сущности) |

**Response 200 OK:**

```json
{
  "items": [
    {
      "id": "uuid",
      "orderId": "uuid",
      "productId": "uuid",
      "quantity": 1000.5,
      "inputDate": "2026-05-10T08:00:00Z",
      "createdAt": "2026-05-10T08:05:00Z",
      "order": {
        "id": "uuid",
        "code": "ORD-001",
        "status": "IN_PROGRESS"
      },
      "product": {
        "id": "uuid",
        "code": "RAW-SEEDS-001",
        "name": "Семена подсолнечника"
      }
    }
  ],
  "total": 24
}
```

---

### GET /production/batch-inputs/yield

Получить выход готовой продукции с тонны сырья (yield ratio).

**Query Parameters:**

| Параметр | Тип | Описание |
|----------|-----|---------|
| `orderId` | UUID | ✅ UUID заказа |

**Response 200 OK:**

```json
{
  "orderId": "uuid",
  "totalInput": 1000.5,
  "totalOutput": 850.2,
  "yieldPercent": 85.0,
  "target": 86.0
}
```

**KPI диплома:** "Выход масла с тонны семян"

---

## 4. Простои оборудования (Downtime Events)

### POST /production/downtime-events

Зарегистрировать простой оборудования.

**Body (application/json):**

```json
{
  "productionLineId": "uuid",
  "reason": "Поломка вала редуктора",
  "category": "UNPLANNED_BREAKDOWN",
  "startedAt": "2026-05-10T08:30:00Z",
  "endedAt": "2026-05-10T10:15:00Z",
  "durationMinutes": 105
}
```

**Категории:**
- `PLANNED_MAINTENANCE` — плановое обслуживание
- `UNPLANNED_BREAKDOWN` — аварийный отказ
- `QUALITY_ISSUE` — проблема с качеством
- `MATERIAL_SHORTAGE` — нехватка материала
- `OTHER` — прочее

**Response 201 Created:**

```json
{
  "id": "uuid",
  "productionLineId": "uuid",
  "reason": "Поломка вала редуктора",
  "category": "UNPLANNED_BREAKDOWN"
}
```

---

### GET /production/downtime-events

Получить список простоев.

**Query Parameters:**

| Параметр | Тип | Описание |
|----------|-----|---------|
| `productionLineId` | UUID | Фильтр по линии |
| `from` | ISO 8601 date | Начало периода |
| `to` | ISO 8601 date | Конец периода |
| `category` | string | Фильтр по категории |
| `offset` | int | Смещение |
| `limit` | int | Лимит |

**Response 200 OK:**

```json
{
  "items": [
    {
      "id": "uuid",
      "productionLineId": "uuid",
      "reason": "Поломка вала редуктора",
      "category": "UNPLANNED_BREAKDOWN",
      "startedAt": "2026-05-10T08:30:00Z",
      "endedAt": "2026-05-10T10:15:00Z",
      "durationMinutes": 105,
      "createdAt": "2026-05-10T10:20:00Z"
    }
  ],
  "total": 8
}
```

---

### GET /production/downtime-events/summary

Получить агрегированную сводку простоев по категориям.

**Query Parameters:**

| Параметр | Тип | Описание |
|----------|-----|---------|
| `from` | ISO 8601 date | Начало периода |
| `to` | ISO 8601 date | Конец периода |

**Response 200 OK:**

```json
{
  "items": [
    {
      "category": "UNPLANNED_BREAKDOWN",
      "totalMinutes": 520,
      "count": 5
    },
    {
      "category": "PLANNED_MAINTENANCE",
      "totalMinutes": 240,
      "count": 2
    },
    {
      "category": "QUALITY_ISSUE",
      "totalMinutes": 180,
      "count": 3
    }
  ],
  "totalEvents": 10,
  "totalDowntimeMinutes": 940
}
```

**KPI диплома:** "Время простоев"

---

## 5. Промо-акции (Promo Campaigns)

### POST /production/promo-campaigns

Создать промо-акцию.

**Body (application/json):**

```json
{
  "name": "Скидка на творог 10%",
  "description": "Весенняя скидка",
  "channel": "DIRECT",
  "productId": "uuid",
  "discountPercent": 10,
  "startDate": "2026-05-01",
  "endDate": "2026-05-31",
  "budget": 50000
}
```

**Response 201 Created:**

```json
{
  "id": "uuid",
  "name": "Скидка на творог 10%",
  "channel": "DIRECT"
}
```

---

### GET /production/promo-campaigns

Получить список промо-акций.

**Query Parameters:**

| Параметр | Тип | Описание |
|----------|-----|---------|
| `from` | ISO 8601 date | Начало периода |
| `to` | ISO 8601 date | Конец периода |
| `channel` | string | Фильтр по каналу |
| `status` | string | `ACTIVE`, `ENDED`, `ARCHIVED` |
| `offset` | int | Смещение |
| `limit` | int | Лимит |

**Response 200 OK:**

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Скидка на творог 10%",
      "channel": "DIRECT",
      "discountPercent": 10,
      "startDate": "2026-05-01",
      "endDate": "2026-05-31",
      "budget": 50000,
      "status": "ACTIVE"
    }
  ],
  "total": 3
}
```

---

### GET /production/promo-campaigns/:id/effectiveness

Получить эффективность промо-акции (ROI, uplift).

**Path Parameters:**

| Параметр | Тип | Описание |
|----------|-----|---------|
| `id` | UUID | UUID акции |

**Response 200 OK:**

```json
{
  "campaignId": "uuid",
  "campaignName": "Скидка на творог 10%",
  "budget": 50000,
  "salesDuringCampaign": 125000,
  "baselineSales": 75000,
  "uplift": 50000,
  "costPerUpliftUnit": 50,
  "roi": 1.5,
  "roiPercent": 150
}
```

**KPI диплома:** "Эффективность промо-акций"

---

## 6. Справочники

### GET /production/production-lines

Получить производственные линии (с поддержкой division для фильтрации).

**Query Parameters:**

| Параметр | Тип | Описание |
|----------|-----|---------|
| `code` | string | Фильтр по коду |
| `name` | string | Фильтр по названию |
| `division` | string | 🆕 Фильтр по дивизиону (FR-03) |
| `isActive` | boolean | Только активные |
| `offset` | int | Смещение |
| `limit` | int | Лимит |

**Response 200 OK:**

```json
{
  "productionLines": [
    {
      "id": "uuid",
      "code": "LINE-01",
      "name": "Линия молока",
      "description": "Основная линия",
      "division": "Управление производством и технологиями",
      "isActive": true,
      "createdAt": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 5
}
```

---

## 7. Фильтрация и фильтры данных

### Поддерживаемые фильтры (FR-03)

**Период:**
```
?from=2026-05-01&to=2026-05-31
```

**Дивизион:**
```
?division=Управление производством и технологиями
```

**Производственная линия:**
```
?productionLineId=uuid
```

**Категория/Канал:**
```
?channel=DIRECT
?category=PLANNED_MAINTENANCE
```

---

## 8. Параметры запроса (Common Query Params)

### Гранулярность (Granularity) — FR-02

Для временных рядов (тренды графиков):

```
?granularity=day      # Данные по дням
?granularity=week     # Данные по неделям
?granularity=month    # Данные по месяцам
```

### Включение связанных сущностей (Include)

```
?include=product,productionLine
?include=order
```

### Пагинация

```
?offset=0&limit=20    # По умолчанию
?limit=100            # Максимум 100
```

---

## 9. Цветовая индикация (Traffic Light) — FR-10

Все метрики с target-значениями возвращают статус:

```json
{
  "value": 0.82,
  "target": 0.85,
  "min": 0.75,
  "max": 1.0,
  "status": "warning"  // "ok" | "warning" | "critical"
}
```

**Логика:**
- `ok` — значение == target
- `warning` — value < target, но >= min
- `critical` — value < min или > max

---

## 10. Статусы и ошибки

### Success Codes

| Код | Значение |
|-----|----------|
| 200 | OK |
| 201 | Created |

### Error Codes

| Код | Значение | Пример |
|-----|----------|--------|
| 400 | Bad Request | Ошибка валидации параметров |
| 401 | Unauthorized | Невалидный JWT токен |
| 403 | Forbidden | Недостаточно прав (RBAC) |
| 404 | Not Found | Ресурс не существует |
| 409 | Conflict | Дубликат, invalid state |
| 429 | Too Many Requests | Rate limit превышен |
| 503 | Service Unavailable | Production Service не отвечает |

---

## 11. Примеры использования

### cURL: Получить KPI

```bash
curl -X GET 'http://localhost:3000/api/production/kpi?from=2026-05-01&to=2026-05-31&granularity=day' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json'
```

### cURL: Экспортировать KPI

```bash
curl -X POST 'http://localhost:3000/api/production/kpi/export' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "from": "2026-05-01",
    "to": "2026-05-31",
    "format": "csv",
    "metrics": ["oeeEstimate", "defectRate"]
  }'
```

### JavaScript: Получить маржинальность

```typescript
const response = await fetch(
  'http://localhost:3000/api/production/sales/margin?from=2026-05-01&to=2026-05-31',
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);

const { margins, aggregated } = await response.json();
console.log(`Средняя маржа: ${aggregated.avgMarginPercent}%`);
```

---

## 12. Соответствие функциональным требованиям (FR)

| FR | Описание | API Endpoint | Статус |
|----|----------|-----------|--------|
| FR-01 | KPI-карточки с target | `GET /production/kpi` | ✅ |
| FR-02 | Графики с трендом | `GET /production/kpi?granularity=day` | ✅ |
| FR-03 | Фильтрация по дивизиону | `GET /production/kpi/breakdown?groupBy=division` | ✅ |
| FR-04 | Drill-down | `GET /production/kpi/breakdown` | ✅ |
| FR-05 | Сравнение периодов | `GET /production/kpi?compareWithPrevious=true` | ✅ |
| FR-06 | Экспорт PDF/Excel | `POST /production/kpi/export` | ✅ CSV/JSON |
| FR-07 | Ролевой доступ | `@Roles()` guard | ✅ |
| FR-08 | Автообновление | Polling + SSE (WIP) | ✅ Polling |
| FR-10 | Светофор (цвета) | `status` в response | ✅ |
| FR-12 | JWT аутентификация | Bearer token | ✅ |

---

## 13. Реализованные этапы плана v1.3.0

- ✅ **Этап 1.** KPI Targets + OTIF
- ✅ **Этап 2.** Time-series + Granularity (графики)
- ✅ **Этап 3.** KPI Breakdown + Division (drill-down)
- ✅ **Этап 4.** BatchInput + DowntimeEvent (производственные KPI)
- ⏳ **Этап 5.** SSE + Real-time updates (в разработке)
- ⏳ **Этап 6.** RBAC + Role guards (частично)
- ✅ **Этап 7.** KPI Export (CSV/JSON)
- ✅ **Этап 8.** Маржинальность + PromoCampaign

---

## 14. Performance & Caching

- `GET /production/kpi`: **30 сек кеш**
- `GET /production/sales/summary`: **60 сек кеш**
- `GET /production/kpi/breakdown`: **2 мин кеш**

Кеш инвалидируется при записи новых данных через POST/PATCH.

---

## 15. Related

- 📋 [Overview](overview.md)
- 📊 [Pagination](pagination.md)
- 🎯 [Plan v1.3.0](../../plans/v1.3.0-analytics-dashboard-plan.md)
- 📚 [Integration Guide](../integration/client-guide.md)

