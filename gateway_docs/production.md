# Production Service

## Назначение

`production` обслуживает производственный домен: справочник продукции, производственные заказы, выпуск, качество, складские остатки, продажи, показания датчиков и агрегированные KPI. Сервис реализован как NestJS-приложение с RabbitMQ RPC-интерфейсом, PostgreSQL через Prisma и событийной интеграцией через RabbitMQ events/outbox.

## Как сервис встроен в систему

- Команды принимает через exchange `efko.production.commands`.
- Запросы принимает через exchange `efko.production.queries`.
- Доменные события публикует в exchange `efko.production.events`.
- Очереди команд и запросов разделены: `production-service.commands.queue` и `production-service.queries.queue`.
- Внешний HTTP есть только у bootstrap c префиксом `api`; бизнес-операции в коде экспонируются как RabbitRPC, а не как REST-контроллеры.

## Основные модули

- `ProductsModule`: создание и выборка продуктов.
- `OrdersModule`: создание производственных заказов, смена статуса, чтение одного заказа и списка.
- `OutputModule`: фиксация выпуска по партиям и выборка выпуска.
- `QualityModule`: запись лабораторных результатов и выборка качества.
- `InventoryModule`: upsert складских остатков и выборка остатков.
- `SalesModule`: запись продаж и агрегированная/детальная аналитика по продажам.
- `SensorsModule`: запись телеметрии и выборка показаний.
- `KpiModule`: расчёт агрегированных производственных KPI.
- `ProductionInfrastructureModule`: wiring Prisma-репозиториев, use case-ов и `RmqEventEmitterService`.
- `OutboxModule`: интеграция общего outbox поверх Prisma с публикацией в `efko.production.events`.

## RabbitMQ Commands и Queries

Все команды отправляются в exchange `efko.production.commands`, очередь `production-service.commands.queue`.
Все запросы отправляются в exchange `efko.production.queries`, очередь `production-service.queries.queue`.

Все RPC handlers используют `ValidationPipe` с `transform`, `whitelist`, `forbidNonWhitelisted`, читают correlation/user metadata из Rabbit headers и обёрнуты в `productionRpcErrorInterceptor`.

### Commands

#### ProductionCreateProductCommand

Создать продукт. При наличии `sourceSystemId` use case сначала пытается сделать upsert по внешнему идентификатору.

**Exchange:** `efko.production.commands`  
**Request Body:**

```typescript
{
  code: string;                    // Уникальный код продукта
  name: string;                    // Название продукта
  category: ProductCategory;       // RAW_MATERIAL | SEMI_FINISHED | FINISHED_PRODUCT | PACKAGING
  brand?: string;                  // Бренд (опционально)
  unitOfMeasure: string;           // Единица измерения (kg, l, piece и т.д.)
  shelfLifeDays?: number;          // Срок годности в днях (опционально)
  requiresQualityCheck?: boolean;  // Требуется ли контроль качества
  sourceSystemId?: string;         // ID из внешней системы (для ETL)
}
```

**Response:**

```typescript
{
  id: string;
  code: string;
  name: string;
  category: ProductCategory;
  brand: string | null;
  unitOfMeasure: string;
  shelfLifeDays: number | null;
  requiresQualityCheck: boolean;
  sourceSystemId: string | null;
}
```

**Ошибки:** `PRODUCT_CODE_ALREADY_EXISTS` -> `409`

---

#### ProductionCreateOrderCommand

Создать производственный заказ.

**Exchange:** `efko.production.commands`  
**Request Body:**

```typescript
{
  externalOrderId?: string;  // Номер заказа во внешней системе (опционально)
  productId: string;         // UUID продукта
  targetQuantity: number;    // Плановое количество
  unitOfMeasure: string;     // Единица измерения
  productionLine: string;    // Название производственной линии
  plannedStart: string;      // Плановое начало (ISO datetime)
  plannedEnd: string;        // Плановое окончание (ISO datetime)
}
```

**Response:**

```typescript
{
  id: string;
  externalOrderId: string | null;
  productId: string;
  status: OrderStatus;  // PLANNED | IN_PROGRESS | COMPLETED | CANCELLED
}
```

**Ошибки:** `PRODUCT_NOT_FOUND` -> `404`

---

#### ProductionUpdateOrderStatusCommand

Обновить статус производственного заказа.

**Exchange:** `efko.production.commands`  
**Request Body:**

```typescript
{
  id: string;
  action: 'start' | 'complete' | 'cancel';
  actualQuantity?: number;  // Фактическое количество (опционально)
}
```

**Response:**

```typescript
{
  id: string;
  status: OrderStatus;
  actualQuantity: number | null;
  actualStart: string | null;  // ISO datetime
  actualEnd: string | null;    // ISO datetime
}
```

**Ошибки:** `INVALID_ORDER_STATUS_TRANSITION` -> `409`

---

#### ProductionRecordOutputCommand

Зарегистрировать выпуск продукции.

**Exchange:** `efko.production.commands`  
**Request Body:**

```typescript
{
  orderId: string;     // UUID заказа
  productId: string;   // UUID продукта
  lotNumber: string;   // Номер партии (уникальный для этого выпуска)
  quantity: number;    // Количество выпущено
  shift: string;       // Смена (например: "morning", "night")
}
```

**Response:**

```typescript
{
  id: string;
  orderId: string;
  lotNumber: string;
  quantity: number;
}
```

---

#### ProductionRecordQualityResultCommand

Записать результат контроля качества.

**Exchange:** `efko.production.commands`  
**Request Body:**

```typescript
{
  lotNumber: string;       // Номер партии
  productId: string;       // UUID продукта
  parameterName: string;   // Название параметра (moisture, pH, temperature и т.д.)
  resultValue: number;     // Значение результата
  lowerLimit: number;      // Нижний допустимый предел
  upperLimit: number;      // Верхний допустимый предел
  testDate: string;        // Дата теста (ISO date)
}
```

**Response:**

```typescript
{
  id: string;
  lotNumber: string;
  productId: string;
  inSpec: boolean;        // Соответствует норме
  qualityStatus: QualityStatus;  // APPROVED | REJECTED | PENDING
}
```

---

#### ProductionUpsertInventoryCommand

Создать или обновить остаток на складе.

**Exchange:** `efko.production.commands`  
**Request Body:**

```typescript
{
  productId: string;         // UUID продукта
  warehouseCode: string;     // Код склада
  lotNumber?: string;        // Номер партии (опционально)
  quantity: number;          // Количество
  unitOfMeasure: string;     // Единица измерения
}
```

**Response:**

```typescript
{
  id: string;
  productId: string;
  warehouseCode: string;
  quantity: number;
}
```

---

#### ProductionRecordSaleCommand

Зарегистрировать продажу.

**Exchange:** `efko.production.commands`  
**Request Body:**

```typescript
{
  externalId: string;    // Уникальный ID продажи во внешней системе
  productId: string;     // UUID продукта
  customerName: string;  // Название клиента
  quantity: number;      // Количество
  amount: number;        // Сумма продажи
  saleDate: string;      // Дата продажи (ISO date)
  region: string;        // Регион
  channel: SaleChannel;  // RETAIL | WHOLESALE | HORECA | EXPORT
}
```

**Response:**

```typescript
{
  id: string;
  externalId: string;
  productId: string;
  amount: number;
}
```

---

#### ProductionRecordSensorReadingCommand

Записать показание датчика.

**Exchange:** `efko.production.commands`  
**Request Body:**

```typescript
{
  deviceId: string;            // ID датчика
  productionLine: string;      // Производственная линия
  parameterName: string;       // Название параметра (temperature, pressure и т.д.)
  value: number;               // Значение показания
  unit: string;                // Единица измерения
  quality: SensorQuality;      // GOOD | DEGRADED | BAD
}
```

**Response:**

```typescript
{
  id: string;
  deviceId: string;
  productionLine: string;
  parameterName: string;
  quality: SensorQuality;
}
```

---

### Queries

#### ProductionGetProductsQuery

Получить список продуктов.

**Exchange:** `efko.production.queries`  
**Request Body:**

```typescript
{
  category?: ProductCategory;  // Фильтр по категории (опционально)
  brand?: string;             // Фильтр по бренду (опционально)
}
```

**Response:**

```typescript
{
  products: Array<{
    id: string;
    code: string;
    name: string;
    category: ProductCategory;
    brand: string | null;
    unitOfMeasure: string;
    shelfLifeDays: number | null;
    requiresQualityCheck: boolean;
  }>;
}
```

---

#### ProductionGetOrdersQuery

Получить список производственных заказов.

**Exchange:** `efko.production.queries`  
**Request Body:**

```typescript
{
  status?: OrderStatus;         // Фильтр по статусу (опционально)
  productId?: string;           // Фильтр по продукту (опционально)
  productionLine?: string;      // Фильтр по линии (опционально)
  from?: string;               // Начало периода (ISO date)
  to?: string;                 // Конец периода (ISO date)
}
```

**Response:**

```typescript
{
  orders: Array<{
    id: string;
    externalOrderId: string | null;
    productId: string;
    targetQuantity: number;
    actualQuantity: number | null;
    unitOfMeasure: string;
    status: OrderStatus;
    productionLine: string;
    plannedStart: string;
    plannedEnd: string;
    actualStart: string | null;
    actualEnd: string | null;
  }>;
}
```

---

#### ProductionGetOrderQuery

Получить заказ по ID с полной информацией о выпусках.

**Exchange:** `efko.production.queries`  
**Request Body:**

```typescript
{
  id: string;  // UUID заказа
}
```

**Response:**

```typescript
{
  id: string;
  externalOrderId: string | null;
  productId: string;
  targetQuantity: number;
  actualQuantity: number | null;
  unitOfMeasure: string;
  status: OrderStatus;
  productionLine: string;
  plannedStart: string;
  plannedEnd: string;
  actualStart: string | null;
  actualEnd: string | null;
  outputs: Array<{
    id: string;
    orderId: string;
    productId: string;
    lotNumber: string;
    quantity: number;
    qualityStatus: QualityStatus;
    productionDate: string;
    shift: string;
  }>;
}
```

---

#### ProductionGetOutputQuery

Получить список выпусков продукции.

**Exchange:** `efko.production.queries`  
**Request Body:**

```typescript
{
  orderId?: string;     // Фильтр по заказу (опционально)
  productId?: string;   // Фильтр по продукту (опционально)
  lotNumber?: string;   // Фильтр по номеру партии (опционально)
  from?: string;       // Начало периода (ISO date)
  to?: string;         // Конец периода (ISO date)
}
```

**Response:**

```typescript
{
  outputs: Array<{
    id: string;
    orderId: string;
    productId: string;
    lotNumber: string;
    quantity: number;
    qualityStatus: QualityStatus;
    productionDate: string;
    shift: string;
  }>;
}
```

---

#### ProductionGetQualityQuery

Получить результаты контроля качества.

**Exchange:** `efko.production.queries`  
**Request Body:**

```typescript
{
  productId?: string;     // Фильтр по продукту (опционально)
  lotNumber?: string;     // Фильтр по номеру партии (опционально)
  qualityStatus?: QualityStatus;  // Фильтр по статусу качества (опционально)
  inSpec?: boolean;       // Только соответствующие норме (опционально)
}
```

**Response:**

```typescript
{
  results: Array<{
    id: string;
    lotNumber: string;
    productId: string;
    parameterName: string;
    resultValue: number;
    qualitySpecId?: string;
    lowerLimit?: number;
    upperLimit?: number;
    inSpec?: boolean;
    qualityStatus: QualityStatus;
    testDate: string;
  }>;
}
```

---

#### ProductionGetInventoryQuery

Получить остатки на складах.

**Exchange:** `efko.production.queries`  
**Request Body:**

```typescript
{
  productId?: string;       // Фильтр по продукту (опционально)
  warehouseCode?: string;   // Фильтр по складу (опционально)
}
```

**Response:**

```typescript
{
  inventory: Array<{
    id: string;
    productId: string;
    warehouseCode: string;
    lotNumber: string | null;
    quantity: number;
    unitOfMeasure: string;
    lastUpdated: string;  // ISO datetime
  }>;
}
```

---

#### ProductionGetSalesQuery

Получить список продаж.

**Exchange:** `efko.production.queries`  
**Request Body:**

```typescript
{
  productId?: string;   // Фильтр по продукту (опционально)
  region?: string;      // Фильтр по региону (опционально)
  channel?: SaleChannel;  // Фильтр по каналу (опционально)
  from?: string;       // Начало периода (ISO date)
  to?: string;         // Конец периода (ISO date)
}
```

**Response:**

```typescript
{
  sales: Array<{
    id: string;
    externalId: string;
    productId: string;
    customerName: string;
    quantity: number;
    amount: number;
    saleDate: string;
    region: string;
    channel: SaleChannel;
  }>;
}
```

---

#### ProductionGetSalesSummaryQuery

Получить сводку по продажам (агрегированные данные).

**Exchange:** `efko.production.queries`  
**Request Body:**

```typescript
{
  from?: string;           // Начало периода (ISO date)
  to?: string;             // Конец периода (ISO date)
  groupBy?: 'region' | 'channel' | 'product';  // Оси группировки (опционально)
}
```

**Response:**

```typescript
{
  summary: Array<{
    groupKey: string;       // Ключ группировки (регион, канал или код продукта)
    totalQuantity: number;  // Общее количество продано
    totalAmount: number;    // Общая сумма
    salesCount: number;     // Количество продаж
  }>;
  totalAmount: number;      // Итоговая сумма
  totalQuantity: number;    // Итоговое количество
}
```

---

#### ProductionGetSensorsQuery

Получить показания датчиков.

**Exchange:** `efko.production.queries`  
**Request Body:**

```typescript
{
  productionLine?: string;   // Фильтр по линии (опционально)
  parameterName?: string;    // Фильтр по параметру (опционально)
  quality?: SensorQuality;   // Фильтр по качеству (опционально)
  from?: string;            // Начало диапазона (ISO datetime)
  to?: string;              // Конец диапазона (ISO datetime)
}
```

**Response:**

```typescript
{
  readings: Array<{
    id: string;
    deviceId: string;
    productionLine: string;
    parameterName: string;
    value: number;
    unit: string;
    quality: SensorQuality;
    recordedAt: string;  // ISO datetime
  }>;
}
```

---

#### ProductionGetKpiQuery

Получить KPI производства (агрегированные показатели).

**Exchange:** `efko.production.queries`  
**Request Body:**

```typescript
{
  from?: string;              // Начало периода (ISO date)
  to?: string;                // Конец периода (ISO date)
  productionLine?: string;    // Фильтр по линии (опционально)
}
```

**Response:**

```typescript
{
  totalOutput: number;       // Общий выпуск
  defectRate: number;        // Процент брака
  completedOrders: number;   // Завершено заказов
  totalOrders: number;       // Всего заказов
  oeeEstimate: number;       // Оценка OEE (Overall Equipment Effectiveness)
}
```

---

## Основная бизнес-логика

- Продукты создаются через доменную модель `ProductEntity`; при ETL-импортах возможен update существующей записи по `sourceSystemId`, а не только insert.
- Заказы ссылаются на продукт; создание и смена статуса идут через `ProductionOrderEntity`, которая валидирует допустимые переходы статусов.
- Выпуск хранится по заказу, продукту и номеру партии; номер партии валидируется через `LotNumber`.
- Качество хранится как набор результатов по параметрам с расчётом `inSpec` и доменным `decision`.
- Показания датчиков после записи прогоняются через `SensorAnomalyDetector`; при выходе за пределы публикуется отдельное событие аномалии.
- KPI считаются на чтении: `totalOutput`, `defectRate`, `completedOrders`, `totalOrders`, `oeeEstimate`. 
  
  **Формула OEE Estimate:**
  - **Availability (Доступность)** = completedOrders / totalOrders  
    Доля завершённых заказов от общего количества заказов за период.
  - **Quality (Качество)** = (totalOutput − rejectedOutput) / totalOutput  
    Доля продукции, прошедшей контроль качества, от общего выпуска.
  - **OEE Estimate** = Availability × Quality  
  
  **Важно:** Это упрощённая оценка OEE, рассчитываемая на основе двух компонентов. Полноценный OEE также включает компонент **Performance (Производительность)**, который не рассчитывается в текущей реализации. Используется как индикатор эффективности, но не как точная метрика OEE в классическом понимании.

## Хранение данных

PostgreSQL/Prisma, основные таблицы:

- `products`: код, категория, бренд, единица измерения, срок годности, признак обязательного контроля качества, `source_system_id`.
- `production_orders`: внешний номер заказа, продукт, целевое/фактическое количество, линия, плановые и фактические даты, статус.
- `production_output`: заказ, продукт, номер партии, количество, статус качества, дата выпуска, смена.
- `sales`: внешний идентификатор продажи, продукт, клиент, количество, сумма, дата, регион, канал.
- `inventory`: продукт, склад, партия, количество, единица измерения, время последнего обновления.
- `quality_results`: партия, продукт, параметр, значение, пределы, `in_spec`, решение, дата теста.
- `sensor_readings`: устройство, линия, параметр, значение, единица, качество, время измерения.
- `outbox_messages`: event type, payload, correlation id, статус отправки, retry counters, error message.

## Интеграции

- RabbitMQ RPC для всех команд и запросов production-домена.
- RabbitMQ events для доменных событий:
  - через `EventEmitterService` публикуются события заказов, выпуска, качества, продаж, датчиков и аномалий;
  - через `OutboxMessageRepository` записываются события по продуктам в `outbox_messages`, а затем доставляются общим outbox-механизмом.
- ETL ожидаемо является важным upstream: его mapper-ы бьют в `ProductionCreateProductCommand`, `ProductionCreateOrderCommand`, `ProductionRecordOutputCommand`, `ProductionRecordQualityResultCommand`, `ProductionUpsertInventoryCommand`, `ProductionRecordSaleCommand`, `ProductionRecordSensorReadingCommand`.

## Обработка ошибок

- Доменные ошибки наследуются от `ProductionError` и мапятся в transport-safe ответ через `productionRpcErrorInterceptor`.
- Явные маппинги:
  - `INVALID_*` -> `400`
  - `*_NOT_FOUND` -> `404`
  - конфликтные состояния (`PRODUCT_CODE_ALREADY_EXISTS`, `INVALID_ORDER_STATUS_TRANSITION`) -> `409`
- Валидационные ошибки Nest `ValidationPipe` тоже упаковываются в RPC error response с HTTP-like `statusCode`.

## Observability и logging

- Логирование через `nestjs-pino`.
- В dev-режиме лог дублируется в `logs/production.log` и очищается на старте процесса.
- Контроллеры пишут topic, `correlationId`, `userId`, `userRole`.
- Use case-ы логируют ключевые бизнес-операции через `buildLogContext(...)`.
- Сигнал об аномалиях датчиков логируется отдельным `warn`.

## Зависимости

- NestJS
- Prisma + PostgreSQL
- `@golevelup/nestjs-rabbitmq`
- `nestjs-pino`
- `@efko-kernel/contracts`
- `@efko-kernel/interfaces`
- `@efko-kernel/nest-utils`

## Наблюдения и пробелы по коду

- В коде сервиса нет полноценного HTTP API для бизнес-операций, несмотря на запуск HTTP-сервера.
- Для событий используется смешанная модель: часть use case-ов публикует события сразу через emitter, а часть пишет в outbox.
- В `GetKpiUseCase` выход для `rejected` определяется по строке `qualityStatus === 'rejected'`; это стоит учитывать как зависимость от формата маппинга enum/репозитория.
