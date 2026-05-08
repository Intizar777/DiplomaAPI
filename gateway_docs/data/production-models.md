# Модели данных: Production Service

Производственный домен: продукты, заказы, выпуск, качество, датчики, склады, продажи.

## Product

**Таблица:** `products`  
**Назначение:** Каталог продуктов и компонентов

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `code` | String @unique | Код продукта (например, "PRODUCT-001") |
| `name` | String | Название продукта |
| `category` | ProductCategory | raw_material, semi_finished, finished_product, packaging |
| `brand` | String? | Бренд (optional) |
| `unitOfMeasureId` | UUID | Единица измерения (FK UnitOfMeasure) |
| `unitOfMeasure` | UnitOfMeasure? | Связанная единица измерения (id, code, name) |
| `shelfLifeDays` | Int? | Срок хранения в днях (nullable) |
| `requiresQualityCheck` | Boolean | Требуется ли контроль качества |
| `sourceSystemId` | String? | ID в ERP |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Связи:** orders, sales, inventory, qualitySpecs

## UnitOfMeasure

**Таблица:** `units_of_measure`  
**Назначение:** Справочник единиц измерения (3NF нормализация)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `code` | String @unique | Код (кг, л, шт) |
| `name` | String | Название (Килограмм, Литр, Штука) |
| `createdAt` | DateTime | Дата создания |

**Связи:** products (обратная)

**Примеры:**
- kg, Килограмм
- л, Литр
- шт, Штука

## ProductionLine

**Таблица:** `production_lines`  
**Назначение:** Производственные линии (включены в v1.2.0)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `name` | String @unique | Название линии |
| `code` | String @unique | Код линии |
| `description` | String? | Описание (опционально) |
| `isActive` | Boolean | Активна ли (default: true) |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Связи:** orders (ProductionOrder), sensors (Sensor)  
**Cross-service:** Workstation в Personnel Service ссылается на `productionLineId` (без DB constraint).

**Events (Outbox):**
- `production.production-line.changed.event` — публикуется при создании/обновлении линии через `OutboxMessage`. Payload: `{ productionLineId, name, code, description, isActive, changedAt }`. Потребляется Personnel Service для инкрементальной синхронизации `ProductionLineView`.

## ProductionOrder

**Таблица:** `production_orders`  
**Назначение:** Производственные заказы (что и когда производить)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `externalOrderId` | String? | ID заказа из внешней системы |
| `productId` | UUID | Какой продукт производить (FK Product) |
| `targetQuantity` | Decimal | Запланированное количество |
| `actualQuantity` | Decimal? | Фактическое количество |
| `unitOfMeasure` | String | Единица измерения |
| `status` | OrderStatus | planned, in_progress, completed, cancelled |
| `productionLineId` | UUID | Производственная линия (FK ProductionLine) |
| `plannedStart`, `plannedEnd` | DateTime | Плановые даты |
| `actualStart`, `actualEnd` | DateTime? | Фактические даты |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Связи:** product (FK), productionLine (FK), outputs (ProductionOutput)

**Примеры:**
- Заказ: 500 кг продукта "Сыр" на линии "LINE-01", 2026-05-15 10:00–12:00

## ProductionOutput

**Таблица:** `production_output`  
**Назначение:** Выпуск продукции по заказам (партии)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `orderId` | UUID | Производственный заказ (FK ProductionOrder) |
| `lotNumber` | String | Номер партии |
| `quantity` | Decimal | Количество |
| `qualityStatus` | QualityStatus | pending, approved, rejected |
| `productionDate` | DateTime | Дата производства |
| `shift` | String | Смена |
| `createdAt` | DateTime | Дата создания |

**Связи:** order (FK ProductionOrder)

## QualitySpec

**Таблица:** `quality_specs`  
**Назначение:** Спецификации качества для продуктов (3NF нормализация)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `productId` | UUID | На какой продукт (FK Product) |
| `parameterName` | String | Название параметра (Влажность, pH, и т.д.) |
| `lowerLimit` | Decimal | Нижний предел (допустимое минимум) |
| `upperLimit` | Decimal | Верхний предел (допустимое максимум) |
| `isActive` | Boolean | Активна ли (default: true) |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Связи:** product (FK), qualityResults (обратная)

**Примеры:**
- Product: "Сыр", Parameter: "Влажность", Lower: 35, Upper: 45
- Product: "Сыр", Parameter: "pH", Lower: 6.0, Upper: 6.8

## QualityResult

**Таблица:** `quality_results`  
**Назначение:** Результаты контроля качества (тестирование партий)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `lotNumber` | String | Номер партии |
| `resultValue` | Decimal | Измеренное значение |
| `qualitySpecId` | UUID | Спецификация для сравнения (FK QualitySpec) |
| `qualityStatus` | QualityStatus | pending, approved, rejected |
| `testDate` | DateTime | Когда проводился тест |
| `createdAt` | DateTime | Дата создания записи |

**Связи:** qualitySpec

## SensorParameter

**Таблица:** `sensor_parameters`  
**Назначение:** Справочник параметров датчиков (3NF нормализация)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `name` | String @unique | Название параметра на русском (Температура, Давление) |
| `unit` | String | Единица измерения (°C, кПа, л/ч) |
| `createdAt` | DateTime | Дата создания |

**Примеры параметров:**
- Температура (TEMP, °C)
- Давление (PRESSURE, кПа)
- Расход жидкости (FLOW_RATE, л/ч)
- Влажность (HUMIDITY, %)

## Sensor

**Таблица:** `sensors`  
**Назначение:** Физические датчики на производственных линиях

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `deviceId` | String @unique | Серийный номер устройства |
| `productionLineId` | UUID | На какой линии установлен (FK ProductionLine) |
| `sensorParameterId` | UUID | Какой параметр измеряет (FK SensorParameter) |
| `isActive` | Boolean | Активен ли (default: true) |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Связи:** productionLine, sensorParameter, sensorReadings (обратная)

## SensorReading

**Таблица:** `sensor_readings`  
**Назначение:** Показания датчиков (временные ряды)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `sensorId` | UUID | Какой датчик (FK Sensor) |
| `value` | Decimal | Значение |
| `quality` | SensorQuality | good, degraded, bad |
| `recordedAt` | DateTime | Когда записано |
| `createdAt` | DateTime | Дата создания |

**Связи:** sensor (FK)

**Примеры:**
- Sensor: "TEMP-001", Value: 45.3, Quality: GOOD, 2026-05-07 15:30:00

## Customer

**Таблица:** `customers`  
**Назначение:** Справочник клиентов (3NF нормализация)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `name` | String @unique | Название клиента |
| `createdAt` | DateTime | Дата создания |

**Связи:** sales

## Sale

**Таблица:** `sales`  
**Назначение:** Продажи готовой продукции

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `externalId` | String | ID продажи из внешней системы |
| `productId` | UUID | Какой продукт (FK Product) |
| `customerId` | UUID | Кому продали (FK Customer) |
| `quantity` | Decimal | Количество |
| `amount` | Decimal | Сумма в деньгах |
| `saleDate` | Date | Дата продажи |
| `region` | String | Регион доставки |
| `channel` | SaleChannel | retail, wholesale, horeca, export |
| `createdAt` | DateTime | Дата создания |

**Связи:** product, customer

## Warehouse

**Таблица:** `warehouses`  
**Назначение:** Справочник складов (3NF нормализация)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `code` | String @unique | Код склада |
| `name` | String | Название склада |
| `createdAt` | DateTime | Дата создания |

**Связи:** inventory

## Inventory

**Таблица:** `inventory`  
**Назначение:** Складские остатки

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `productId` | UUID | Какой продукт (FK Product) |
| `warehouseId` | UUID | В каком складе (FK Warehouse) |
| `lotNumber` | String? | Номер партии (optional) |
| `quantity` | Decimal | Количество |
| `lastUpdated` | DateTime | Когда последний раз обновлено |

**Связи:** product, warehouse

## Enums

| Enum | Значения |
|------|----------|
| **ProductCategory** | raw_material, semi_finished, finished_product, packaging |
| **OrderStatus** | planned, in_progress, completed, cancelled |
| **QualityStatus** | pending, approved, rejected |
| **SaleChannel** | retail, wholesale, horeca, export |
| **SensorQuality** | good, degraded, bad |

---

**Related:** [../architecture/3nf-normalization.md](../architecture/3nf-normalization.md), [../data/personnel-models.md](../data/personnel-models.md)
