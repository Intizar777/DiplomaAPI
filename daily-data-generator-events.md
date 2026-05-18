# Daily Data Generator — Events Reference

Документ описывает все events, которые генерируются при работе модуля `DailyDataGeneratorService`.
Каждый event публикуется через RabbitMQ exchange `production.events` после записи в transactional outbox.

## Envelope (обёртка)

Каждое сообщение в RabbitMQ имеет единую структуру-обёртку:

```json
{
  "event_id": "uuid-v4",
  "event_type": "production.order.changed.event",
  "timestamp": "2026-05-17T01:00:00.000Z",
  "source_service": "production",
  "correlation_id": "uuid-v4",
  "version": "1.0",
  "payload": { ... }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `event_id` | UUID v4 | Уникальный идентификатор события |
| `event_type` | string | Routing key / topic (см. ниже) |
| `timestamp` | ISO 8601 | Время публикации |
| `source_service` | string | Всегда `"production"` |
| `correlation_id` | UUID v4 | ID для трассировки цепочки |
| `version` | string | Версия схемы (`"1.0"`) |
| `payload` | object | Тело события (см. ниже) |

---

## Events по фазам генерации

### Фаза 2 — Закрытие вчерашних заказов

#### `production.order.changed.event`

Генерируется при: start (PLANNED → IN_PROGRESS), complete (IN_PROGRESS → COMPLETED).

```json
{
  "orderId": "uuid",
  "externalOrderId": "ORD-20260516-001",
  "productId": "uuid",
  "targetQuantity": 1500.0,
  "actualQuantity": 1425.5,
  "status": "COMPLETED",
  "productionLineId": "uuid",
  "plannedStart": "2026-05-16T06:00:00.000Z",
  "plannedEnd": "2026-05-16T22:00:00.000Z",
  "actualStart": "2026-05-16T06:05:00.000Z",
  "actualEnd": "2026-05-17T01:00:00.000Z",
  "changedAt": "2026-05-17T01:00:00.000Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `orderId` | UUID | ID заказа |
| `externalOrderId` | string \| null | Внешний номер заказа |
| `productId` | UUID | ID продукта |
| `targetQuantity` | number | Плановый объём |
| `actualQuantity` | number \| null | Фактический объём (null если не завершён) |
| `status` | enum | `PLANNED` \| `IN_PROGRESS` \| `COMPLETED` \| `CANCELLED` |
| `productionLineId` | UUID | ID производственной линии |
| `plannedStart` | ISO 8601 | Плановое начало |
| `plannedEnd` | ISO 8601 | Плановое окончание |
| `actualStart` | ISO 8601 \| null | Фактическое начало |
| `actualEnd` | ISO 8601 \| null | Фактическое окончание |
| `changedAt` | ISO 8601 | Время изменения |

---

#### `production.batch-input.recorded.event`

Генерируется при: записи приёмки сырья (2–4 на каждый завершённый заказ).

```json
{
  "id": "uuid",
  "orderId": "uuid",
  "productId": "uuid",
  "quantity": 450.123,
  "inputDate": "2026-05-16T00:00:00.000Z",
  "createdAt": "2026-05-17T01:00:05.000Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | ID записи batch input |
| `orderId` | UUID | ID производственного заказа |
| `productId` | UUID | ID сырья (RAW_MATERIAL) |
| `quantity` | number | Количество (кг/л) |
| `inputDate` | ISO 8601 | Дата приёмки |
| `createdAt` | ISO 8601 | Время создания записи |

---

#### `production.output.recorded.event`

Генерируется при: записи выпуска продукции (2–4 лота на каждый завершённый заказ).

```json
{
  "id": "uuid",
  "orderId": "uuid",
  "lotNumber": "LOT-20260516-001",
  "quantity": 375.5,
  "productionDate": "2026-05-16T00:00:00.000Z",
  "shift": "morning",
  "qualityStatus": "PENDING"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | ID записи выпуска |
| `orderId` | UUID | ID производственного заказа |
| `lotNumber` | string | Номер партии (LOT-YYYYMMDD-NNN) |
| `quantity` | number | Количество |
| `productionDate` | ISO 8601 | Дата производства |
| `shift` | string | Смена: `morning` \| `evening` \| `night` |
| `qualityStatus` | string | `PENDING` \| `APPROVED` \| `REJECTED` |

---

#### `production.quality-result.recorded.event`

Генерируется при: записи результата контроля качества (для каждого лота × каждый QualitySpec продукта).

```json
{
  "id": "uuid",
  "lotNumber": "LOT-20260516-001",
  "productId": "uuid",
  "qualityStatus": "APPROVED",
  "resultValue": 12.345678,
  "qualitySpecId": "uuid",
  "testDate": "2026-05-16T00:00:00.000Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | ID результата |
| `lotNumber` | string | Номер партии |
| `productId` | UUID | ID продукта |
| `qualityStatus` | enum | `APPROVED` \| `PENDING` \| `REJECTED` |
| `resultValue` | number | Измеренное значение параметра |
| `qualitySpecId` | UUID | ID спецификации качества |
| `testDate` | ISO 8601 | Дата проверки |

---

#### `production.inventory.updated.event`

Генерируется при: обновлении остатков на складе (готовая продукция + сырьё).

```json
{
  "id": "uuid",
  "productId": "uuid",
  "warehouseId": "uuid",
  "quantity": 1425,
  "lotNumber": null,
  "lastUpdated": "2026-05-17T01:00:10.000Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | ID записи инвентаря |
| `productId` | UUID | ID продукта |
| `warehouseId` | UUID | ID склада |
| `quantity` | number | Текущее количество |
| `lotNumber` | string \| null | Номер партии (если привязан) |
| `lastUpdated` | ISO 8601 | Время последнего обновления |

---

### Фаза 3 — Новые заказы на сегодня

#### `production.order.changed.event`

Тот же формат что и в Фазе 2, но со `status: "PLANNED"`, `actualQuantity: null`, `actualStart: null`, `actualEnd: null`.

---

### Фаза 4 — Продажи

#### `production.sale.recorded.event`

Генерируется при: записи продажи (30 в день по умолчанию).

```json
{
  "id": "uuid",
  "externalId": "SALE-20260516-0001",
  "productId": "uuid",
  "customerId": "uuid",
  "quantity": 250.5,
  "amount": 87500.00,
  "cost": 61250.00,
  "saleDate": "2026-05-16T00:00:00.000Z",
  "region": "Краснодарский край",
  "channel": "WHOLESALE"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | ID продажи |
| `externalId` | string | Внешний номер (SALE-YYYYMMDD-NNNN) |
| `productId` | UUID | ID продукта (FINISHED_PRODUCT) |
| `customerId` | UUID | ID клиента |
| `quantity` | number | Количество |
| `amount` | number | Сумма продажи |
| `cost` | number \| null | Себестоимость |
| `saleDate` | ISO 8601 | Дата продажи |
| `region` | string | Регион |
| `channel` | enum | `RETAIL` \| `WHOLESALE` \| `HORECA` \| `EXPORT` |

---

### Фаза 5 — Простои

#### `production.downtime-event.recorded.event`

Генерируется при: записи события простоя (2–4 в день).

```json
{
  "id": "uuid",
  "productionLineId": "uuid",
  "reason": "Аварийная остановка насоса подачи сырья",
  "category": "UNPLANNED_BREAKDOWN",
  "startedAt": "2026-05-16T14:30:00.000Z",
  "endedAt": "2026-05-16T16:45:00.000Z",
  "durationMinutes": 135,
  "createdAt": "2026-05-17T01:00:15.000Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | ID события простоя |
| `productionLineId` | UUID | ID производственной линии |
| `reason` | string | Причина простоя |
| `category` | enum | `PLANNED_MAINTENANCE` \| `UNPLANNED_BREAKDOWN` \| `QUALITY_ISSUE` \| `MATERIAL_SHORTAGE` \| `OTHER` |
| `startedAt` | ISO 8601 | Начало простоя |
| `endedAt` | ISO 8601 \| null | Окончание простоя |
| `durationMinutes` | number \| null | Длительность в минутах |
| `createdAt` | ISO 8601 | Время создания записи |

---

### Фаза 6 — Показания датчиков

#### `production.sensor-reading.recorded.event`

Генерируется при: записи показания датчика (8 × линии × параметры в день).

```json
{
  "id": "uuid",
  "sensorId": "uuid",
  "deviceId": "SENSOR-LINE01-ТЕМП",
  "productionLineId": "uuid",
  "parameterName": "Температура",
  "value": 78.4521,
  "unit": "°C",
  "quality": "GOOD",
  "recordedAt": "2026-05-16T10:30:00.000Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | ID показания |
| `sensorId` | UUID | ID сенсора |
| `deviceId` | string | Идентификатор устройства |
| `productionLineId` | UUID | ID производственной линии |
| `parameterName` | string | Название параметра (Температура, Давление, Расход жидкости, Влажность) |
| `value` | number | Измеренное значение |
| `unit` | string | Единица измерения (°C, бар, л/ч, %) |
| `quality` | enum | `GOOD` \| `DEGRADED` \| `BAD` |
| `recordedAt` | ISO 8601 | Время измерения |

---

#### `production.sensor.anomaly.event`

Генерируется при: обнаружении аномалии в показании (BAD quality или выход за пределы).

```json
{
  "readingId": "uuid",
  "deviceId": "SENSOR-LINE01-ТЕМП",
  "productionLineId": "uuid",
  "parameterName": "Температура",
  "value": 99.5,
  "unit": "°C",
  "quality": "BAD",
  "anomalyType": "VALUE_OUT_OF_RANGE",
  "severity": "HIGH",
  "reason": "Value 99.5 exceeds upper limit 95",
  "lowerLimit": 60,
  "upperLimit": 95,
  "detectedAt": "2026-05-17T01:00:20.000Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `readingId` | UUID | ID показания-источника |
| `deviceId` | string | Идентификатор устройства |
| `productionLineId` | UUID | ID линии |
| `parameterName` | string | Параметр |
| `value` | number | Аномальное значение |
| `unit` | string | Единица измерения |
| `quality` | enum | `GOOD` \| `DEGRADED` \| `BAD` |
| `anomalyType` | enum | `VALUE_OUT_OF_RANGE` \| `BAD_QUALITY` \| `MISSING_DATA` \| `DEVIATION_SPIKE` |
| `severity` | enum | `LOW` \| `MEDIUM` \| `HIGH` \| `CRITICAL` |
| `reason` | string | Описание причины |
| `lowerLimit` | number? | Нижний порог |
| `upperLimit` | number? | Верхний порог |
| `detectedAt` | ISO 8601 | Время обнаружения |

---

## Сводная таблица

| # | Topic | Фаза | Кол-во за цикл |
|---|-------|------|-----------------|
| 1 | `production.order.changed.event` | 2, 3 | ~22 (12 close + 10 new) |
| 2 | `production.batch-input.recorded.event` | 2 | ~36 (12 orders × 3 avg) |
| 3 | `production.output.recorded.event` | 2 | ~36 (12 orders × 3 avg) |
| 4 | `production.quality-result.recorded.event` | 2 | ~108+ (lots × specs) |
| 5 | `production.inventory.updated.event` | 2 | ~24 (12 finished + 12 raw) |
| 6 | `production.sale.recorded.event` | 4 | 30 |
| 7 | `production.downtime-event.recorded.event` | 5 | 2–4 |
| 8 | `production.sensor-reading.recorded.event` | 6 | ~192 (6 lines × 4 params × 8) |
| 9 | `production.sensor.anomaly.event` | 6 | ~6 (~3% от readings) |

**Итого:** ~450–500 events за один цикл генерации (при настройках по умолчанию).

---

## Enums Reference

```
OrderStatus:     PLANNED | IN_PROGRESS | COMPLETED | CANCELLED
QualityStatus:   APPROVED | PENDING | REJECTED
SaleChannel:     RETAIL | WHOLESALE | HORECA | EXPORT
SensorQuality:   GOOD | DEGRADED | BAD
DowntimeCategory: PLANNED_MAINTENANCE | UNPLANNED_BREAKDOWN | QUALITY_ISSUE | MATERIAL_SHORTAGE | OTHER
SensorAnomalyType: VALUE_OUT_OF_RANGE | BAD_QUALITY | MISSING_DATA | DEVIATION_SPIKE
SensorAnomalySeverity: LOW | MEDIUM | HIGH | CRITICAL
```
