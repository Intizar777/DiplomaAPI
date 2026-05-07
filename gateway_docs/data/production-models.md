# Модели данных: Production Service

Производственный домен: продукты, заказы, качество, датчики, склады, продажи.

## Product

**Таблица:** `products`  
**Назначение:** Каталог продуктов и компонентов

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `code` | String @unique | Код продукта (например, "PRODUCT-001") |
| `name` | String | Название продукта |
| `category` | ProductCategory | RAW_MATERIAL, SEMI_FINISHED, FINISHED_PRODUCT, PACKAGING |
| `brand` | String? | Бренд (optional) |
| `unitOfMeasure` | String | Единица измерения (kg, л, шт, и т.д.) |
| `shelfLifeDays` | Int? | Срок хранения в днях (nullable) |
| `requiresQualityCheck` | Boolean | Требуется ли контроль качества |
| `sourceSystemId` | String? | ID в ERP |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Связи:** orders, sales, inventory, qualitySpecs

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
| `status` | OrderStatus | PLANNED, IN_PROGRESS, COMPLETED, CANCELLED |
| `productionLine` | String | Код производственной линии |
| `plannedStart`, `plannedEnd` | DateTime | Плановые даты |
| `actualStart`, `actualEnd` | DateTime? | Фактические даты |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Связи:** product (FK), qualityResults (обратная)

**Примеры:**
- Заказ: 500 кг продукта "Сыр" на линии "LINE-01", 2026-05-15 10:00–12:00

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
| `productId` | UUID | Какой продукт (FK Product) |
| `parameterName` | String | Название параметра |
| `resultValue` | Decimal | Измеренное значение |
| `qualitySpecId` | UUID? | Спецификация для сравнения (FK QualitySpec) |
| `qualityStatus` | QualityStatus | PENDING, APPROVED, REJECTED |
| `testDate` | DateTime | Когда проводился тест |
| `createdAt` | DateTime | Дата создания записи |

**Связи:** product, qualitySpec

## SensorParameter

**Таблица:** `sensor_parameters`  
**Назначение:** Справочник параметров датчиков (3NF нормализация)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `name` | String | Название параметра на русском (Температура, Давление) |
| `code` | String @unique | Код параметра (TEMP, PRESSURE) |
| `unit` | String | Единица измерения (°C, кПа, л/ч) |
| `description` | String? | Описание (optional) |
| `isActive` | Boolean | Активен ли (default: true) |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

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
| `quality` | SensorQuality | GOOD, DEGRADED, BAD |
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
| `name` | String | Название клиента |
| `code` | String @unique | Код клиента |
| `region` | String | Регион доставки |
| `isActive` | Boolean | Активен ли (default: true) |
| `sourceSystemId` | String? | ID в ERP |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

## Sale

**Таблица:** `sales`  
**Назначение:** Продажи готовой продукции

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `externalId` | String | ID продажи из внешней системы |
| `productId` | UUID | Какой продукт (FK Product) |
| `customerId` | UUID? | Кому продали (FK Customer, nullable) |
| `quantity` | Decimal | Количество |
| `amount` | Decimal | Сумма в деньгах |
| `saleDate` | Date | Дата продажи |
| `channel` | SaleChannel | RETAIL, WHOLESALE, HORECA, EXPORT |
| `createdAt` | DateTime | Дата создания |

**Связи:** product, customer

## Warehouse

**Таблица:** `warehouses`  
**Назначение:** Справочник складов (3NF нормализация)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `name` | String | Название склада |
| `code` | String @unique | Код склада |
| `location` | String | Физическое местоположение |
| `capacity` | Decimal? | Вместимость (м³ или единиц) |
| `isActive` | Boolean | Активен ли (default: true) |
| `sourceSystemId` | String? | ID в системе управления складом |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

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
| `unitOfMeasure` | String | Единица измерения |
| `lastUpdated` | DateTime | Когда последний раз обновлено |

**Связи:** product, warehouse

## Enums

| Enum | Значения |
|------|----------|
| **ProductCategory** | RAW_MATERIAL, SEMI_FINISHED, FINISHED_PRODUCT, PACKAGING |
| **OrderStatus** | PLANNED, IN_PROGRESS, COMPLETED, CANCELLED |
| **QualityStatus** | PENDING, APPROVED, REJECTED |
| **SaleChannel** | RETAIL, WHOLESALE, HORECA, EXPORT |
| **SensorQuality** | GOOD, DEGRADED, BAD |

---

**Related:** [../architecture/3nf-normalization.md](../architecture/3nf-normalization.md), [all-models.md](all-models.md)
