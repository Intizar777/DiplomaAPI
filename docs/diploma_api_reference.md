# Справочник по API системы «Dashboard Analytics»

## Приложение к дипломной работе

**Проект:** DiplomaAPI — аналитический сервис агрегации данных из микросервисов EFKO  
**Версия API:** 1.0.0  
**Базовый URL:** `http://localhost:8000`  
**Документация:** Swagger UI — `/docs` | ReDoc — `/redoc` | OpenAPI JSON — `/openapi.json`

---

## Содержание

1. [Введение](#1-введение)
2. [Архитектура системы](#2-архитектура-системы)
3. [Модели данных](#3-модели-данных)
4. [Справочник по API](#4-справочник-по-api)
   - [4.1 Health / Системные](#41-health--системные)
   - [4.2 KPI](#42-kpi)
   - [4.3 Продажи (Sales)](#43-продажи-sales)
   - [4.4 Заказы (Orders)](#44-заказы-orders)
   - [4.5 Качество (Quality)](#45-качество-quality)
   - [4.6 Синхронизация (Sync)](#46-синхронизация-sync)
   - [4.7 Продукты (Products)](#47-продукты-products)
   - [4.8 Запасы (Inventory)](#48-запасы-inventory)
   - [4.9 Датчики (Sensors)](#49-датчики-sensors)
   - [4.10 Выпуск (Output)](#410-выпуск-output)
   - [4.11 Персонал (Personnel)](#411-персонал-personnel)
   - [4.12 Дашборд Master Line](#412-дашборд-master-line)
   - [4.13 Дашборд Group Manager](#413-дашборд-group-manager)
   - [4.14 Дашборд Quality Engineer](#414-дашборд-quality-engineer)
   - [4.15 Дашборд Finance Manager](#415-дашборд-finance-manager)
   - [4.16 Отчёты (Reports)](#416-отчёты-reports)
5. [Диаграммы взаимодействия](#5-диаграммы-взаимодействия)
6. [Приложения](#6-приложения)

---

## 1. Введение

### 1.1. Назначение документа

Настоящий документ представляет собой справочник по REST API системы Dashboard Analytics, разработанной в рамках дипломной работы. Система предназначена для агрегации и аналитики производственных данных из микросервисов EFKO (производственная компания группы «ЭФКО»).

### 1.2. Назначение системы

Dashboard Analytics — это FastAPI-сервис, который:

- Агрегирует данные KPI, продаж, заказов, качества, запасов, датчиков и персонала из внешних микросервисов EFKO через Gateway API
- Синхронизирует данные ежечасно через APScheduler
- Хранит данные в PostgreSQL (единственный источник правды)
- Поддерживает обновления в реальном времени через RabbitMQ
- Предоставляет RESTful-эндпоинты для аналитических запросов
- Генерирует отчёты в форматах CSV и XLSX

### 1.3. Методы взаимодействия с API

Все запросы выполняются через HTTP. API использует следующие HTTP-методы:

| Метод | Назначение |
|-------|-----------|
| `GET` | Получение данных |
| `POST` | Запуск операций (синхронизация, отчёты) |

### 1.4. Формат данных

- Входящие данные: JSON (для POST-запросов)
- Исходящие данные: JSON (Content-Type: `application/json`)
- Даты: ISO 8601 (`YYYY-MM-DD` или `YYYY-MM-DDTHH:MM:SS`)
- UUID: формат UUID v4

### 1.5. Обработка ошибок

| Код ответа | Описание |
|-----------|---------|
| `200` | Успешный запрос |
| `202` | Запрос принят (асинхронные операции) |
| `400` | Неверный запрос (неверные параметры) |
| `404` | Ресурс не найден |
| `422` | Ошибка валидации (Pydantic) |
| `500` | Внутренняя ошибка сервера |

Структура ошибки:

```json
{
  "detail": "Описание ошибки",
  "trace_id": "trace-id"
}
```

---

## 2. Архитектура системы

### 2.1. Общая архитектура

Система построена по трёхслойной архитектуре: маршрутизация → бизнес-логика → база данных.

```mermaid
graph TB
    subgraph "Клиенты"
        Client[Дашборды / Веб-приложения]
    end

    subgraph "API Gateway (FastAPI)"
        Health[Health Check]
        KPI[KPI API]
        Sales[Sales API]
        Orders[Orders API]
        Quality[Quality API]
        Sync[Sync API]
        Products[Products API]
        Inventory[Inventory API]
        Sensors[Sensors API]
        Output[Output API]
        Personnel[Personnel API]
        Dashboards[Dashboard API]
        Reports[Reports API]
    end

    subgraph "Service Layer"
        KPIService[KPI Service]
        SalesService[Sales Service]
        OrderService[Order Service]
        QualityService[Quality Service]
        ProductService[Product Service]
        OutputService[Output Service]
        SensorService[Sensor Service]
        InventoryService[Inventory Service]
        PersonnelService[Personnel Service]
        LMDashboard[Line Master Dashboard]
        GMDashboard[Group Manager Dashboard]
        QEDashboard[Quality Engineer Dashboard]
        FinanceDashboard[Finance Manager Dashboard]
        ReportService[Report Service]
        GatewayClient[Gateway Client]
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL 14+)]
        Alembic[Alembic Migrations]
    end

    subgraph "Синхронизация"
        Scheduler[APScheduler / Cron]
        RabbitMQ[RabbitMQ Consumer]
    end

    subgraph "Внешний API"
        GatewayAPI[EFKO Gateway API]
    end

    Client --> Health
    Client --> KPI
    Client --> Sales
    Client --> Orders
    Client --> Quality
    Client --> Sync
    Client --> Products
    Client --> Inventory
    Client --> Sensors
    Client --> Output
    Client --> Personnel
    Client --> Dashboards
    Client --> Reports

    KPI --> KPIService
    Sales --> SalesService
    Orders --> OrderService
    Quality --> QualityService
    Products --> ProductService
    Output --> OutputService
    Sensors --> SensorService
    Inventory --> InventoryService
    Personnel --> PersonnelService
    Dashboards --> LMDashboard
    Dashboards --> GMDashboard
    Dashboards --> QEDashboard
    Dashboards --> FinanceDashboard
    Reports --> ReportService

    KPIService --> PostgreSQL
    SalesService --> PostgreSQL
    OrderService --> PostgreSQL
    QualityService --> PostgreSQL
    ProductService --> PostgreSQL
    OutputService --> PostgreSQL
    SensorService --> PostgreSQL
    InventoryService --> PostgreSQL
    PersonnelService --> PostgreSQL
    LMDashboard --> PostgreSQL
    GMDashboard --> PostgreSQL
    QEDashboard --> PostgreSQL
    FinanceDashboard --> PostgreSQL

    KPIService --> GatewayClient
    SalesService --> GatewayClient
    OrderService --> GatewayClient
    QualityService --> GatewayClient
    ProductService --> GatewayClient
    OutputService --> GatewayClient
    SensorService --> GatewayClient
    InventoryService --> GatewayClient
    PersonnelService --> GatewayClient

    GatewayClient --> GatewayAPI

    Scheduler --> KPIService
    Scheduler --> SalesService
    Scheduler --> OrderService
    Scheduler --> QualityService
    Scheduler --> ProductService
    Scheduler --> OutputService
    Scheduler --> SensorService
    Scheduler --> InventoryService
    Scheduler --> PersonnelService

    RabbitMQ --> KPIService
    RabbitMQ --> SalesService
    RabbitMQ --> OrderService
    RabbitMQ --> QualityService
    RabbitMQ --> ProductService
    RabbitMQ --> OutputService
    RabbitMQ --> SensorService
    RabbitMQ --> InventoryService
```

### 2.2. Трёхслойная архитектура

| Слой | Назначение | Технология |
|------|-----------|-----------|
| **Route Layer** | Тонкая валидация, делегирование в сервисы | FastAPI (3–5 строк на эндпоинт) |
| **Service Layer** | Вся бизнес-логика, запросы к БД, вызовы Gateway API | Python + SQLAlchemy ORM + httpx |
| **Data Layer** | Персистентность данных | PostgreSQL 14+ + Alembic |

### 2.3. Потоки данных

#### 2.3.1. Синхронизация (по расписанию)

```mermaid
sequenceDiagram
    participant Scheduler as Cron Scheduler
    participant Service as Service Layer
    participant Gateway as Gateway API
    participant DB as PostgreSQL

    loop Каждый час
        Scheduler->>Service: Вызов sync_from_gateway()
        Service->>Gateway: HTTP GET (httpx async)
        Gateway-->>Service: JSON ответ
        Service->>DB: Upsert (INSERT ... ON CONFLICT)
        Service-->>Scheduler: Результат
    end
```

#### 2.3.2. Обработка запросов (HTTP)

```mermaid
sequenceDiagram
    participant Client as Клиент
    participant Router as FastAPI Router
    participant Service as Service Layer
    participant DB as PostgreSQL

    Client->>Router: GET /api/v1/kpi/current
    Router->>Router: Pydantic валидация параметров
    Router->>Service: service.get_current_kpi()
    Service->>DB: SELECT запрос (async)
    DB-->>Service: Результат
    Service-->>Router: Pydantic объект
    Router-->>Client: JSON ответ (200)
```

#### 2.3.3. Обработка событий (RabbitMQ)

```mermaid
sequenceDiagram
    participant RabbitMQ as RabbitMQ
    participant Consumer as Event Consumer
    participant Dispatcher as Event Dispatcher
    participant Handler as Event Handler
    participant Service as Service Layer
    participant DB as PostgreSQL

    RabbitMQ->>Consumer: Message (efko.production.events)
    Consumer->>Dispatcher: route_event(event)
    Dispatcher->>Handler: handler(event.payload)
    Handler->>Service: upsert_from_event(event)
    Service->>DB: INSERT ... ON CONFLICT (event_id)
    DB-->>Service: Result
    Service-->>Handler: OK
    Handler-->>Dispatcher: OK
    Dispatcher-->>Consumer: OK
    Consumer->>RabbitMQ: ACK
```

### 2.4. Технологический стек

| Компонент | Технология | Версия |
|-----------|-----------|--------|
| Фреймворк | FastAPI | 0.104+ |
| ORM | SQLAlchemy | 2.x (async) |
| База данных | PostgreSQL | 14+ |
| Валидация | Pydantic | v2 |
| HTTP-клиент | httpx | async |
| Планировщик | APScheduler | 3.x |
| Очередь сообщений | RabbitMQ (aio-pika) | — |
| Логирование | structlog (JSON) | — |
| Миграции | Alembic | 1.12+ |
| Тестирование | pytest + testcontainers | — |
| Контейнеризация | Docker + Docker Compose | — |
| Сервер | uvicorn | — |

---

## 3. Модели данных

### 3.1. ER-диаграмма

```mermaid
erDiagram
    AggregatedKPI {
        UUID id PK
        DATE period_from
        DATE period_to
        VARCHAR production_line
        DECIMAL total_output
        DECIMAL defect_rate
        INTEGER completed_orders
        INTEGER total_orders
        DECIMAL oee_estimate
    }

    AggregatedSales {
        UUID id PK
        DATE period_from
        DATE period_to
        VARCHAR group_by_type
        VARCHAR group_key
        DECIMAL total_quantity
        DECIMAL total_amount
        INTEGER sales_count
        DECIMAL avg_order_value
    }

    SalesTrends {
        UUID id PK
        DATE trend_date
        VARCHAR interval_type
        VARCHAR region
        VARCHAR channel
        DECIMAL total_amount
        DECIMAL total_quantity
        INTEGER order_count
    }

    SaleRecord {
        UUID id PK
        VARCHAR external_id
        UUID product_id
        VARCHAR product_name
        UUID customer_id FK
        VARCHAR customer_name
        DECIMAL quantity
        DECIMAL amount
        DATE sale_date
        VARCHAR region
        VARCHAR channel
        DATE snapshot_date
        UUID event_id
    }

    OrderSnapshot {
        UUID id PK
        UUID order_id
        VARCHAR external_order_id
        UUID product_id
        VARCHAR product_name
        DECIMAL target_quantity
        DECIMAL actual_quantity
        VARCHAR unit_of_measure
        VARCHAR status
        VARCHAR production_line
        TIMESTAMP planned_start
        TIMESTAMP planned_end
        TIMESTAMP actual_start
        TIMESTAMP actual_end
        DATE snapshot_date
        UUID event_id
    }

    QualityResult {
        UUID id PK
        VARCHAR lot_number
        UUID product_id
        VARCHAR product_name
        VARCHAR parameter_name
        DECIMAL result_value
        UUID quality_spec_id FK
        BOOLEAN in_spec
        VARCHAR decision
        DATE test_date
        UUID event_id
    }

    Product {
        UUID id PK
        VARCHAR code
        VARCHAR name
        VARCHAR category
        VARCHAR brand
        UUID unit_of_measure_id FK
        INTEGER shelf_life_days
        BOOLEAN requires_quality_check
        VARCHAR source_system_id
        UUID event_id
    }

    ProductionOutput {
        UUID id PK
        UUID order_id
        UUID product_id
        VARCHAR product_name
        VARCHAR lot_number
        DECIMAL quantity
        VARCHAR quality_status
        DATE production_date
        VARCHAR shift
        DATE snapshot_date
        UUID event_id
    }

    SensorReading {
        UUID id PK
        UUID sensor_id FK
        DECIMAL value
        VARCHAR quality
        TIMESTAMP recorded_at
        TIMESTAMP snapshot_date
    }

    InventorySnapshot {
        UUID id PK
        UUID product_id
        VARCHAR product_name
        UUID warehouse_id FK
        VARCHAR lot_number
        DECIMAL quantity
        VARCHAR unit_of_measure
        TIMESTAMP last_updated
        DATE snapshot_date
        UUID event_id
    }

    UnitOfMeasure {
        UUID id PK
        VARCHAR code
        VARCHAR name
        VARCHAR source_system_id
    }

    Warehouse {
        UUID id PK
        VARCHAR name
        VARCHAR code
        VARCHAR location
        DECIMAL capacity
        BOOLEAN is_active
        VARCHAR source_system_id
    }

    Customer {
        UUID id PK
        VARCHAR name
        VARCHAR code
        VARCHAR region
        BOOLEAN is_active
        VARCHAR source_system_id
    }

    QualitySpec {
        UUID id PK
        UUID product_id FK
        VARCHAR parameter_name
        DECIMAL lower_limit
        DECIMAL upper_limit
        BOOLEAN is_active
    }

    SensorParameter {
        UUID id PK
        VARCHAR name
        VARCHAR code
        VARCHAR unit
        VARCHAR description
        BOOLEAN is_active
    }

    Sensor {
        UUID id PK
        VARCHAR device_id
        UUID production_line_id FK
        UUID sensor_parameter_id FK
        BOOLEAN is_active
    }

    Location {
        UUID id PK
        VARCHAR name
        VARCHAR code
        VARCHAR type
        VARCHAR address
        BOOLEAN is_active
    }

    ProductionLine {
        UUID id PK
        VARCHAR name
        VARCHAR code
        UUID location_id FK
        VARCHAR description
        BOOLEAN is_active
    }

    Department {
        UUID id PK
        VARCHAR name
        VARCHAR code
        UUID location_id FK
        UUID parent_id FK
        VARCHAR type
        BOOLEAN is_active
    }

    Position {
        UUID id PK
        VARCHAR name
        VARCHAR code
        UUID department_id FK
        VARCHAR level
        BOOLEAN is_active
    }

    Workstation {
        UUID id PK
        VARCHAR name
        VARCHAR code
        UUID location_id FK
        UUID production_line_id FK
        VARCHAR type
        BOOLEAN is_active
    }

    Employee {
        UUID id PK
        VARCHAR first_name
        VARCHAR last_name
        VARCHAR middle_name
        VARCHAR employee_number
        UUID position_id FK
        UUID workstation_id FK
        VARCHAR status
        VARCHAR email
        VARCHAR phone
        DATE hire_date
    }

    SyncLog {
        UUID id PK
        VARCHAR task_name
        VARCHAR status
        TIMESTAMP started_at
        TIMESTAMP completed_at
        INTEGER records_processed
        INTEGER records_inserted
        INTEGER records_updated
        VARCHAR error_message
    }

    SyncError {
        UUID id PK
        UUID sync_log_id FK
        VARCHAR error_type
        VARCHAR error_code
        VARCHAR error_message
        VARCHAR entity_type
        VARCHAR entity_id
    }

    AggregatedKPI ||--o{ OrderSnapshot : "order_id"
    SaleRecord }o--|| Customer : "customer_id"
    SaleRecord }o--|| Product : "product_id"
    QualityResult }o--|| QualitySpec : "quality_spec_id"
    QualityResult }o--|| Product : "product_id"
    Product }o--|| UnitOfMeasure : "unit_of_measure_id"
    ProductionOutput }o--|| Product : "product_id"
    SensorReading }o--|| Sensor : "sensor_id"
    Sensor }o--|| SensorParameter : "sensor_parameter_id"
    InventorySnapshot }o--|| Warehouse : "warehouse_id"
    InventorySnapshot }o--|| Product : "product_id"
    ProductionLine }o--|| Location : "location_id"
    Department }o--|| Location : "location_id"
    Department }o--o| Department : "parent_id"
    Position }o--|| Department : "department_id"
    Workstation }o--|| Location : "location_id"
    Workstation }o--|| ProductionLine : "production_line_id"
    Employee }o--|| Position : "position_id"
    Employee }o--|| Workstation : "workstation_id"
    SyncError }o--|| SyncLog : "sync_log_id"
```

### 3.2. Описание моделей

#### 3.2.1. AggregatedKPI (`aggregated_kpi`)

Агрегированные ключевые показатели эффективности производства.

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID (PK) | Уникальный идентификатор |
| `period_from` | DATE | Начало периода |
| `period_to` | DATE | Конец периода |
| `production_line` | VARCHAR(50) | Линия производства (nullable) |
| `total_output` | DECIMAL(15,3) | Общий объём выпуска |
| `defect_rate` | DECIMAL(5,2) | Процент брака |
| `completed_orders` | INTEGER | Количество завершённых заказов |
| `total_orders` | INTEGER | Общее количество заказов |
| `oee_estimate` | DECIMAL(5,2) | Оценка OEE (nullable) |
| `avg_order_completion_time` | VARCHAR(50) | Среднее время выполнения заказа (nullable) |
| `created_at` | TIMESTAMP | Дата создания записи |
| `updated_at` | TIMESTAMP | Дата обновления записи |

**Уникальное ограничение:** `(period_from, period_to, production_line)`

#### 3.2.2. AggregatedSales (`aggregated_sales`)

Агрегированные данные продаж по группировкам.

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID (PK) | Уникальный идентификатор |
| `period_from` | DATE | Начало периода |
| `period_to` | DATE | Конец периода |
| `group_by_type` | VARCHAR(20) | Тип группировки: `region`, `channel`, `product` |
| `group_key` | VARCHAR(100) | Значение группы |
| `total_quantity` | DECIMAL(15,3) | Общее количество |
| `total_amount` | DECIMAL(15,2) | Общая сумма |
| `sales_count` | INTEGER | Количество продаж |
| `avg_order_value` | DECIMAL(15,2) | Средний чек (nullable) |

**Уникальное ограничение:** `(period_from, period_to, group_by_type, group_key)`

#### 3.2.3. SalesTrends (`sales_trends`)

Тренды продаж по временным интервалам.

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID (PK) | Уникальный идентификатор |
| `trend_date` | DATE | Дата точки тренда |
| `interval_type` | VARCHAR(10) | Тип интервала: `day`, `week`, `month` |
| `region` | VARCHAR(100) | Регион (nullable) |
| `channel` | VARCHAR(50) | Канал продаж (nullable) |
| `total_amount` | DECIMAL(15,2) | Общая сумма |
| `total_quantity` | DECIMAL(15,3) | Общее количество |
| `order_count` | INTEGER | Количество заказов |

**Уникальное ограничение:** `(trend_date, interval_type, region, channel)`

#### 3.2.4. SaleRecord (`sale_records`)

Записи о продажах.

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID (PK) | Уникальный идентификатор |
| `external_id` | VARCHAR(100) | Внешний идентификатор (nullable) |
| `product_id` | UUID | ID продукта |
| `product_name` | VARCHAR(255) | Название продукта (nullable) |
| `customer_id` | UUID (FK) | ID клиента |
| `customer_name` | VARCHAR(255) | Имя клиента (nullable) |
| `quantity` | DECIMAL(15,3) | Количество (nullable) |
| `amount` | DECIMAL(15,2) | Сумма (nullable) |
| `sale_date` | DATE | Дата продажи |
| `region` | VARCHAR(100) | Регион |
| `channel` | VARCHAR(50) | Канал продаж |
| `snapshot_date` | DATE | Дата снимка |
| `event_id` | UUID | ID события (UNIQUE) |

#### 3.2.5. OrderSnapshot (`order_snapshots`)

Снимки состояния заказов.

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID (PK) | Уникальный идентификатор |
| `order_id` | UUID | ID заказа |
| `external_order_id` | VARCHAR(100) | Внешний ID заказа (nullable) |
| `product_id` | UUID | ID продукта |
| `product_name` | VARCHAR(255) | Название продукта (nullable) |
| `target_quantity` | DECIMAL(15,3) | Целевое количество (nullable) |
| `actual_quantity` | DECIMAL(15,3) | Фактическое количество (nullable) |
| `unit_of_measure` | VARCHAR(20) | Единица измерения (nullable) |
| `status` | VARCHAR(20) | Статус: `planned`, `in_progress`, `completed`, `cancelled` |
| `production_line` | VARCHAR(50) | Линия производства (nullable) |
| `planned_start` | TIMESTAMP | Плановая дата начала (nullable) |
| `planned_end` | TIMESTAMP | Плановая дата окончания (nullable) |
| `actual_start` | TIMESTAMP | Фактическая дата начала (nullable) |
| `actual_end` | TIMESTAMP | Фактическая дата окончания (nullable) |
| `snapshot_date` | DATE | Дата снимка |
| `event_id` | UUID | ID события (UNIQUE) |

#### 3.2.6. QualityResult (`quality_results`)

Результаты контроля качества.

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID (PK) | Уникальный идентификатор |
| `lot_number` | VARCHAR(100) | Номер партии |
| `product_id` | UUID | ID продукта |
| `product_name` | VARCHAR(255) | Название продукта (nullable) |
| `parameter_name` | VARCHAR(50) | Параметр качества |
| `result_value` | DECIMAL(10,4) | Результат измерения (nullable) |
| `quality_spec_id` | UUID (FK) | ID спецификации качества (nullable) |
| `in_spec` | BOOLEAN | В рамках спецификации |
| `decision` | VARCHAR(20) | Решение: `approved`, `rejected`, `pending` |
| `test_date` | DATE | Дата тестирования |
| `event_id` | UUID | ID события (UNIQUE) |

#### 3.2.7. Product (`products`)

Продукция.

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID (PK) | Уникальный идентификатор |
| `code` | VARCHAR(100) | Код продукта (UNIQUE) |
| `name` | VARCHAR(255) | Название |
| `category` | VARCHAR(50) | Категория (nullable) |
| `brand` | VARCHAR(255) | Бренд (nullable) |
| `unit_of_measure_id` | UUID (FK) | ID единицы измерения (nullable) |
| `shelf_life_days` | INTEGER | Срок годности в днях (nullable) |
| `requires_quality_check` | BOOLEAN | Требуется ли проверка качества (nullable, default False) |
| `source_system_id` | VARCHAR(100) | ID в исходной системе (nullable) |
| `event_id` | UUID | ID события (UNIQUE) |

#### 3.2.8. ProductionOutput (`production_output`)

Данные выпуска продукции.

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID (PK) | Уникальный идентификатор |
| `order_id` | UUID | ID заказа (nullable) |
| `product_id` | UUID | ID продукта |
| `product_name` | VARCHAR(255) | Название продукта (nullable) |
| `lot_number` | VARCHAR(100) | Номер партии |
| `quantity` | DECIMAL(15,3) | Количество (nullable) |
| `quality_status` | VARCHAR(20) | Статус качества (nullable) |
| `production_date` | DATE | Дата производства |
| `shift` | VARCHAR(20) | Смена (nullable) |
| `snapshot_date` | DATE | Дата снимка |
| `event_id` | UUID | ID события (UNIQUE) |

#### 3.2.9. SensorReading (`sensor_readings`)

Показания датчиков.

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID (PK) | Уникальный идентификатор |
| `sensor_id` | UUID (FK) | ID датчика |
| `value` | DECIMAL(12,4) | Значение (nullable) |
| `quality` | VARCHAR(20) | Качество (nullable) |
| `recorded_at` | TIMESTAMP | Время записи |
| `snapshot_date` | TIMESTAMP | Дата снимка |

#### 3.2.10. InventorySnapshot (`inventory_snapshots`)

Снимки запасов.

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID (PK) | Уникальный идентификатор |
| `product_id` | UUID | ID продукта |
| `product_name` | VARCHAR(255) | Название продукта (nullable) |
| `warehouse_id` | UUID (FK) | ID склада (nullable) |
| `lot_number` | VARCHAR(100) | Номер партии (nullable) |
| `quantity` | DECIMAL(15,3) | Количество (nullable) |
| `unit_of_measure` | VARCHAR(20) | Единица измерения (nullable) |
| `last_updated` | TIMESTAMP | Последнее обновление (nullable) |
| `snapshot_date` | DATE | Дата снимка |
| `event_id` | UUID | ID события (UNIQUE) |

#### 3.2.11. Reference Models (Справочники)

| Модель | Таблица | Описание |
|--------|---------|---------|
| `UnitOfMeasure` | `units_of_measure` | Единицы измерения (code, name) |
| `Warehouse` | `warehouses` | Склады (name, code, location, capacity, is_active) |
| `Customer` | `customers` | Клиенты (name, code, region, is_active) |
| `QualitySpec` | `quality_specs` | Спецификации качества (product_id, parameter_name, lower/upper_limit) |
| `SensorParameter` | `sensor_parameters` | Параметры датчиков (name, code, unit) |
| `Sensor` | `sensors` | Датчики (device_id, production_line_id, sensor_parameter_id) |

#### 3.2.12. Personnel Models (Персонал)

| Модель | Таблица | Описание |
|--------|---------|---------|
| `Location` | `locations` | Локации (name, code, type, address) |
| `ProductionLine` | `production_lines` | Линии производства (name, code, location_id) |
| `Department` | `departments` | Подразделения (name, code, location_id, parent_id, type) |
| `Position` | `positions` | Должности (name, code, department_id, level) |
| `Workstation` | `workstations` | Рабочие места (name, code, location_id, production_line_id, type) |
| `Employee` | `employees` | Сотрудники (first_name, last_name, middle_name, employee_number, position_id, workstation_id, status, email, phone, hire_date) |

#### 3.2.13. Sync Log Models (Логи синхронизации)

| Модель | Таблица | Описание |
|--------|---------|---------|
| `SyncLog` | `sync_logs` | Логи синхронизации (task_name, status, started_at, completed_at, records_processed/inserted/updated, error_message) |
| `SyncError` | `sync_errors` | Ошибки синхронизации (sync_log_id, error_type, error_code, error_message, entity_type, entity_id) |

### 3.3. Перечисления (Enums)

| Перечисление | Значения | Описание |
|-------------|----------|---------|
| `SyncStatus` | `pending`, `running`, `completed`, `failed` | Статус задачи синхронизации |
| `OrderStatus` | `planned`, `in_progress`, `completed`, `cancelled` | Статус заказа |
| `QualityDecision` | `approved`, `rejected`, `pending` | Решение по качеству |

---

## 4. Справочник по API

### 4.1. Health / Системные

#### `GET /health`

Health check с проверкой подключения к БД.

| Параметр | Тип | Описание |
|----------|-----|---------|
| — | — | Нет параметров |

**Ответ (200):**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-05-11T12:00:00"
}
```

| Поле | Тип | Описание |
|------|-----|---------|
| `status` | string | Статус сервиса |
| `version` | string | Версия API |
| `timestamp` | datetime | Текущее время |

---

#### `GET /`

Корневой эндпоинт с базовой информацией.

---

### 4.2. KPI

**Префикс:** `/api/v1/kpi`  
**Тег:** `KPI`

#### `GET /api/v1/kpi/current`

Текущие (последние) KPI-показатели.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `production_line` | string | Нет | Фильтр по линии производства |

**Ответ (200) — `KPICurrentResponse`:**

```json
{
  "data": {
    "total_output": "12500.500",
    "defect_rate": "2.35",
    "completed_orders": 45,
    "total_orders": 50,
    "oee_estimate": "82.50",
    "production_line": "Line-1"
  },
  "period_from": "2026-05-01",
  "period_to": "2026-05-31"
}
```

---

#### `GET /api/v1/kpi/history`

История KPI за период.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |
| `production_line` | string | Нет | Фильтр по линии производства |

> По умолчанию: последние 30 дней.

**Ответ (200) — `KPIHistoryResponse`:**

```json
{
  "items": [
    {
      "period_from": "2026-05-01",
      "period_to": "2026-05-31",
      "production_line": "Line-1",
      "total_output": "12500.500",
      "defect_rate": "2.35",
      "completed_orders": 45,
      "total_orders": 50,
      "oee_estimate": "82.50"
    }
  ],
  "period_from": "2026-04-11",
  "period_to": "2026-05-11"
}
```

---

#### `GET /api/v1/kpi/all`

Все KPI-записи (без фильтра по дате).

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `production_line` | string | Нет | Фильтр по линии производства |

**Ответ:** `KPIHistoryResponse`

---

#### `GET /api/v1/kpi/compare`

Сравнение KPI между двумя периодами.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `period1_from` | date | Да | Начало первого периода |
| `period1_to` | date | Да | Конец первого периода |
| `period2_from` | date | Да | Начало второго периода |
| `period2_to` | date | Да | Конец второго периода |

**Ответ (200) — `KPICompareResponse`:**

```json
{
  "period1": {
    "period_from": "2026-04-01",
    "period_to": "2026-04-30",
    "total_output": "10000.000",
    "defect_rate": "3.00",
    "completed_orders": 40,
    "total_orders": 45,
    "oee_estimate": "78.00"
  },
  "period2": {
    "period_from": "2026-05-01",
    "period_to": "2026-05-31",
    "total_output": "12500.500",
    "defect_rate": "2.35",
    "completed_orders": 45,
    "total_orders": 50,
    "oee_estimate": "82.50"
  },
  "output_change_percent": "25.01",
  "defect_rate_change": "-0.65",
  "order_completion_change": "5.00"
}
```

---

#### `GET /api/v1/kpi/per-line/current`

Текущие KPI для всех линий производства.

**Ответ:** `KPIHistoryResponse`

---

#### `GET /api/v1/kpi/per-line/history`

История KPI по линиям производства за период.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |
| `production_line` | string | Нет | Фильтр по линии производства |

**Ответ:** `KPIHistoryResponse`

---

### 4.3. Продажи (Sales)

**Префикс:** `/api/v1/sales`  
**Тег:** `Sales`

#### `GET /api/v1/sales/summary`

Агрегированная сводка продаж по региону, каналу или продукту.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |
| `group_by` | string | Нет | Группировка: `region`, `channel`, `product` (по умолчанию: `region`) |

**Ответ (200) — `SalesSummaryResponse`:**

```json
{
  "summary": [
    {
      "group_key": "North",
      "total_quantity": "5000.000",
      "total_amount": "250000.00",
      "sales_count": 120,
      "avg_order_value": "2083.33"
    }
  ],
  "total_amount": "500000.00",
  "total_quantity": "10000.000",
  "period_from": "2026-04-11",
  "period_to": "2026-05-11",
  "group_by": "region"
}
```

---

#### `GET /api/v1/sales/trends`

Тренды продаж по временным интервалам.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |
| `interval` | string | Нет | Интервал: `day`, `week`, `month` (по умолчанию: `day`) |
| `region` | string | Нет | Фильтр по региону |
| `channel` | string | Нет | Фильтр по каналу продаж |

**Ответ (200) — `SalesTrendsResponse`:**

```json
{
  "trends": [
    {
      "trend_date": "2026-05-01",
      "total_amount": "15000.00",
      "total_quantity": "300.000",
      "order_count": 10
    }
  ],
  "interval": "day",
  "period_from": "2026-04-11",
  "period_to": "2026-05-11",
  "region": null,
  "channel": null
}
```

---

#### `GET /api/v1/sales/top-products`

Топ продуктов по выручке.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |
| `limit` | int | Нет | Количество продуктов (1–1000, по умолчанию: 10) |

**Ответ (200) — `TopProductsResponse`:**

```json
{
  "products": [
    {
      "product_id": "uuid-1",
      "product_name": "Масло подсолнечное",
      "total_quantity": "2000.000",
      "total_amount": "100000.00",
      "sales_count": 50
    }
  ],
  "period_from": "2026-04-11",
  "period_to": "2026-05-11",
  "limit": 10
}
```

---

#### `GET /api/v1/sales/regions`

Продажи по регионам с процентами.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |

**Ответ (200) — `SalesRegionsResponse`:**

```json
{
  "regions": [
    {
      "region": "North",
      "total_quantity": "5000.000",
      "total_amount": "250000.00",
      "sales_count": 120,
      "percentage": "50.00"
    }
  ],
  "period_from": "2026-04-11",
  "period_to": "2026-05-11"
}
```

---

### 4.4. Заказы (Orders)

**Префикс:** `/api/v1/orders`  
**Тег:** `Orders`

#### `GET /api/v1/orders/status-summary`

Сводка заказов по статусам и линиям производства.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |
| `production_line` | string | Нет | Фильтр по линии производства |

**Ответ (200) — `OrderStatusSummaryResponse`:**

```json
{
  "by_status": {
    "planned": 10,
    "in_progress": 5,
    "completed": 30,
    "cancelled": 3
  },
  "by_production_line": {
    "Line-1": {
      "planned": 5,
      "in_progress": 3,
      "completed": 15,
      "cancelled": 1
    }
  },
  "period_from": "2026-04-11",
  "period_to": "2026-05-11"
}
```

---

#### `GET /api/v1/orders/list`

Пагинированный список заказов.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |
| `status` | string | Нет | Фильтр по статусу: `planned`, `in_progress`, `completed`, `cancelled` |
| `production_line` | string | Нет | Фильтр по линии производства |
| `page` | int | Нет | Номер страницы (по умолчанию: 1) |
| `limit` | int | Нет | Количество на странице (1–500, по умолчанию: 100) |

**Ответ (200) — `OrderListResponse`:**

```json
{
  "orders": [
    {
      "order_id": "uuid-1",
      "external_order_id": "EXT-001",
      "product_id": "uuid-product-1",
      "product_name": "Масло подсолнечное",
      "target_quantity": "1000.000",
      "actual_quantity": "950.000",
      "unit_of_measure": "кг",
      "status": "completed",
      "production_line": "Line-1",
      "planned_start": "2026-05-01T08:00:00",
      "planned_end": "2026-05-01T16:00:00",
      "actual_start": "2026-05-01T08:15:00",
      "actual_end": "2026-05-01T15:30:00",
      "snapshot_date": "2026-05-01"
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 100,
  "pages": 1
}
```

---

#### `GET /api/v1/orders/plan-execution`

План vs факт выполнения по линиям производства.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `start_date` | date | Нет | Дата начала (по умолчанию: 30 дней назад) |
| `end_date` | date | Нет | Дата окончания (по умолчанию: сегодня) |

**Ответ (200) — `PlanExecutionResponse`:**

```json
{
  "period_from": "2026-04-11",
  "period_to": "2026-05-11",
  "lines": [
    {
      "production_line": "Line-1",
      "target_quantity": "5000.000",
      "actual_quantity": "4800.000",
      "fulfillment_pct": "96.00",
      "total_orders": 20,
      "completed_orders": 18,
      "in_progress_orders": 2,
      "overdue_orders": 0
    }
  ]
}
```

---

#### `GET /api/v1/orders/downtime`

Рейтинг линий производства по времени простоя (Pareto).

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `start_date` | date | Нет | Дата начала (по умолчанию: 30 дней назад) |
| `end_date` | date | Нет | Дата окончания (по умолчанию: сегодня) |

**Ответ (200) — `DowntimeResponse`:**

```json
{
  "total_delay_hours": "45.50",
  "period_from": "2026-04-11",
  "period_to": "2026-05-11",
  "lines": [
    {
      "rank": 1,
      "production_line": "Line-2",
      "total_delay_hours": "25.00",
      "order_count": 5,
      "avg_delay_per_order": "5.00",
      "cumulative_pct": "54.95"
    }
  ]
}
```

---

#### `GET /api/v1/orders/{order_id}`

Детальная информация о конкретном заказе.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `order_id` | string | Да | ID заказа |

**Ответ (200) — `OrderDetailResponse`:**

```json
{
  "order_id": "uuid-1",
  "external_order_id": "EXT-001",
  "product_id": "uuid-product-1",
  "product_name": "Масло подсолнечное",
  "target_quantity": "1000.000",
  "actual_quantity": "950.000",
  "unit_of_measure": "кг",
  "status": "completed",
  "production_line": "Line-1",
  "planned_start": "2026-05-01T08:00:00",
  "planned_end": "2026-05-01T16:00:00",
  "actual_start": "2026-05-01T08:15:00",
  "actual_end": "2026-05-01T15:30:00",
  "outputs": [
    {
      "output_id": "uuid-output-1",
      "lot_number": "LOT-001",
      "quantity": "950.000",
      "quality_status": "approved",
      "production_date": "2026-05-01",
      "shift": "Shift 1"
    }
  ]
}
```

**Ошибка (404):** Заказ не найден.

---

### 4.5. Качество (Quality)

**Префикс:** `/api/v1/quality`  
**Тег:** `Quality`

#### `GET /api/v1/quality/summary`

Сводка по контролю качества.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |
| `product_id` | string | Нет | Фильтр по ID продукта |

**Ответ (200) — `QualitySummaryResponse`:**

```json
{
  "average_quality": "97.50",
  "approved_count": 150,
  "rejected_count": 5,
  "pending_count": 10,
  "defect_rate": "3.23",
  "by_parameter": {
    "acidity": {
      "in_spec_percent": "98.50",
      "tests_count": 50
    },
    "moisture": {
      "in_spec_percent": "95.00",
      "tests_count": 45
    }
  },
  "period_from": "2026-04-11",
  "period_to": "2026-05-11"
}
```

---

#### `GET /api/v1/quality/defect-trends`

Тренды процента брака по дням.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |

**Ответ (200) — `DefectTrendsResponse`:**

```json
{
  "trends": [
    {
      "trend_date": "2026-05-01",
      "defect_rate": "2.50",
      "rejected_count": 3,
      "total_tests": 120
    }
  ],
  "period_from": "2026-04-11",
  "period_to": "2026-05-11"
}
```

---

#### `GET /api/v1/quality/lots`

Качество партий с решениями.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |
| `decision` | string | Нет | Фильтр по решению: `approved`, `rejected`, `pending` |

**Ответ (200) — `QualityLotsResponse`:**

```json
{
  "lots": [
    {
      "lot_number": "LOT-001",
      "product_id": "uuid-product-1",
      "product_name": "Масло подсолнечное",
      "decision": "approved",
      "test_date": "2026-05-01",
      "parameters_tested": 5,
      "parameters_passed": 5
    }
  ],
  "total": 50,
  "approved_count": 45,
  "rejected_count": 3,
  "pending_count": 2,
  "period_from": "2026-04-11",
  "period_to": "2026-05-11"
}
```

---

#### `GET /api/v1/quality/parameter-trends`

Ежедневные тренды параметров качества с границами спецификаций.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `start_date` | date | Нет | Дата начала (по умолчанию: 7 дней назад) |
| `end_date` | date | Нет | Дата окончания (по умолчанию: сегодня) |
| `production_line` | string | Нет | Фильтр по линии производства |

**Ответ (200) — `ParameterTrendsResponse`:**

```json
{
  "period_from": "2026-05-04",
  "period_to": "2026-05-11",
  "parameters": [
    {
      "parameter_name": "acidity",
      "total_tests": 50,
      "total_out_of_spec": 2,
      "overall_out_of_spec_pct": "4.00",
      "trend": [
        {
          "test_date": "2026-05-04",
          "avg_value": "0.15",
          "test_count": 10,
          "out_of_spec_count": 0,
          "out_of_spec_pct": "0.00",
          "lower_limit": "0.10",
          "upper_limit": "0.20"
        }
      ]
    }
  ]
}
```

---

#### `GET /api/v1/quality/lots/{lot_number}/deviations`

Отклонения параметров от спецификаций для конкретной партии.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `lot_number` | string | Да | Номер партии |

**Ответ (200) — `LotDeviationsResponse`:**

```json
{
  "lot_number": "LOT-001",
  "product_name": "Масло подсолнечное",
  "shift": "Shift 1",
  "fail_count": 2,
  "deviations": [
    {
      "parameter_name": "acidity",
      "result_value": "0.25",
      "lower_limit": "0.10",
      "upper_limit": "0.20",
      "deviation_magnitude": "0.05"
    }
  ]
}
```

**Ошибка (404):** Партия не найдена.

---

#### `GET /api/v1/quality/defect-pareto`

Pareto-диаграмма брака.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `start_date` | date | Нет | Дата начала (по умолчанию: 7 дней назад) |
| `end_date` | date | Нет | Дата окончания (по умолчанию: сегодня) |
| `production_line` | string | Нет | Фильтр по линии производства |

**Ответ (200) — `DefectParetoResponse`:**

```json
{
  "period_from": "2026-05-04",
  "period_to": "2026-05-11",
  "product_id": null,
  "total_defects": 15,
  "parameters": [
    {
      "parameter_name": "acidity",
      "defect_count": 8,
      "total_tests": 50,
      "defect_pct": "16.00",
      "cumulative_pct": "53.33"
    }
  ]
}
```

---

### 4.6. Синхронизация (Sync)

**Префикс:** `/api/v1/sync`  
**Тег:** `Sync`

#### `GET /api/v1/sync/status`

Статус всех задач синхронизации.

**Ответ (200) — `SyncStatusResponse`:**

```json
{
  "tasks": [
    {
      "task_name": "kpi",
      "status": "completed",
      "last_run": "2026-05-11T12:00:00",
      "last_success": "2026-05-11T12:00:00",
      "records_processed": 150,
      "records_inserted": 145,
      "records_updated": 5,
      "error_message": null
    }
  ],
  "overall_status": "healthy",
  "last_sync": "2026-05-11T12:00:00"
}
```

---

#### `POST /api/v1/sync/trigger`

Запуск ВСЕХ задач синхронизации в фоне.

**Ответ (200) — `SyncTriggerResponse`:**

```json
{
  "message": "Sync tasks triggered: ['kpi', 'sales', 'orders', ...]",
  "triggered_tasks": ["kpi", "sales", "orders", "quality", "products", "output", "sensors", "inventory", "personnel", "references"]
}
```

---

#### `POST /api/v1/sync/trigger/{task_name}`

Запуск конкретной задачи синхронизации.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `task_name` | string | Да | Имя задачи: `kpi`, `kpi_per_line`, `sales`, `orders`, `quality`, `products`, `output`, `sensors`, `inventory`, `personnel`, `references` |

**Ответ (200) — `SyncTriggerResponse`**

**Ошибка (400):** Неверное имя задачи.

---

#### `POST /api/v1/sync/cleanup`

Запуск очистки старых данных (удаление записей старше `retention_days`).

**Ответ (200):**

```json
{
  "message": "Cleanup task triggered in background",
  "status": "triggered"
}
```

---

#### `POST /api/v1/sync/stop`

Остановка ВСЕХ запущенных задач.

**Ответ (200):**

```json
{
  "message": "Stopped 3 task(s)",
  "stopped": ["kpi", "sales", "orders"],
  "status": "ok"
}
```

---

#### `POST /api/v1/sync/stop/{task_name}`

Остановка конкретной задачи.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `task_name` | string | Да | Имя задачи |

**Ответ (200):**

```json
{
  "message": "Task 'kpi' stopped",
  "stopped": ["kpi"],
  "status": "ok"
}
```

---

#### `GET /api/v1/sync/running`

Список запущенных задач.

**Ответ (200):**

```json
{
  "running_tasks": [
    {
      "name": "kpi",
      "done": false,
      "cancelled": false
    }
  ],
  "count": 1
}
```

---

#### `POST /api/v1/sync/initial_sync`

Начальная массовая синхронизация (асинхронная, в фоне).

**Ответ (200):**

```json
{
  "status": "initiated",
  "message": "Initial sync started in background. Check /sync/status for progress.",
  "task_id": "initial_sync"
}
```

---

### 4.7. Продукты (Products)

**Префикс:** `/api/v1/products`  
**Тег:** `Products`

#### `GET /api/v1/products`

Список продуктов с фильтрами.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `category` | string | Нет | Фильтр по категории |
| `brand` | string | Нет | Фильтр по бренду |

**Ответ (200):**

```json
{
  "items": [
    {
      "id": "uuid-1",
      "code": "PRD-001",
      "name": "Масло подсолнечное",
      "category": "Масла",
      "brand": "EFKO",
      "unit_of_measure_id": "uuid-unit-1",
      "shelf_life_days": 365,
      "requires_quality_check": true
    }
  ],
  "count": 10
}
```

---

#### `GET /api/v1/products/{product_id}`

Конкретный продукт по ID.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `product_id` | string | Да | ID продукта |

**Ответ (200):**

```json
{
  "id": "uuid-1",
  "code": "PRD-001",
  "name": "Масло подсолнечное",
  "category": "Масла",
  "brand": "EFKO",
  "unit_of_measure": "кг",
  "shelf_life_days": 365,
  "requires_quality_check": true
}
```

**Ошибка (404):** Продукт не найден.

---

### 4.8. Запасы (Inventory)

**Префикс:** `/api/v1/inventory`  
**Тег:** `Inventory`

#### `GET /api/v1/inventory/current`

Текущие запасы (последний снимок).

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `warehouse_code` | string | Нет | Фильтр по коду склада |
| `product_id` | string | Нет | Фильтр по ID продукта |

**Ответ (200):** Массив записей запасов.

---

#### `GET /api/v1/inventory/trends`

Тренды запасов для конкретного продукта.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `product_id` | string | Да | ID продукта |
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |

**Ответ (200):** Массив точек тренда запасов.

---

### 4.9. Датчики (Sensors)

**Префикс:** `/api/v1/sensors`  
**Тег:** `Sensors`

#### `GET /api/v1/sensors/history`

История показаний датчиков.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `production_line` | string | Нет | Фильтр по линии производства |
| `parameter_name` | string | Нет | Фильтр по параметру |
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |
| `limit` | int | Нет | Максимум показаний (1–5000, по умолчанию: 500) |

> По умолчанию: последние 1 день.

**Ответ (200):** Массив показаний датчиков.

---

#### `GET /api/v1/sensors/alerts`

Показания датчиков с проблемами качества (аномалии).

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |
| `limit` | int | Нет | Максимум алертов (1–1000, по умолчанию: 100) |

> По умолчанию: последние 7 дней.

**Ответ (200):** Массив алертов.

---

#### `GET /api/v1/sensors/stats`

Агрегированная статистика по параметрам и линиям.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `production_line` | string | Нет | Фильтр по линии производства |

**Ответ (200):** Статистика по параметрам.

---

### 4.10. Выпуск (Output)

**Префикс:** `/api/v1/output`  
**Тег:** `Output`

#### `GET /api/v1/output/summary`

Сводка выпуска по дням/сменам.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |
| `group_by` | string | Нет | Группировка: `day`, `shift` (по умолчанию: `day`) |

**Ответ (200):** Агрегированные данные выпуска.

---

#### `GET /api/v1/output/by-shift`

Выпуск по сменам для графика.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `from` | date | Нет | Дата начала (alias: `date_from`) |
| `to` | date | Нет | Дата окончания (alias: `date_to`) |

**Ответ (200):** Данные по сменам.

---

### 4.11. Персонал (Personnel)

**Префикс:** `/api/v1/personnel`  
**Тег:** `Personnel`

#### `GET /api/v1/personnel/locations`

Локации с опциональным фильтром по типу.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `type` | string | Нет | Фильтр по типу локации |

**Ответ (200) — `List[LocationResponse]`:**

```json
[
  {
    "id": "uuid-1",
    "name": "Завод Липецк",
    "code": "LIP",
    "type": "factory",
    "address": "г. Липецк, ул. Промышленная, 1",
    "is_active": true
  }
]
```

---

#### `GET /api/v1/personnel/departments`

Подразделения с опциональным фильтром по типу.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `type` | string | Нет | Фильтр по типу подразделения |

**Ответ (200) — `List[DepartmentResponse]`:**

```json
[
  {
    "id": "uuid-1",
    "name": "Производственный цех",
    "code": "PRD-01",
    "location_id": "uuid-loc-1",
    "parent_id": null,
    "type": "production",
    "is_active": true
  }
]
```

---

#### `GET /api/v1/personnel/positions`

Должности с опциональным фильтром по подразделению.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `department_id` | string | Нет | Фильтр по ID подразделения |

**Ответ (200) — `List[PositionResponse]`:**

```json
[
  {
    "id": "uuid-1",
    "name": "Оператор линии",
    "code": "OPR-01",
    "department_id": "uuid-dept-1",
    "level": "specialist",
    "is_active": true
  }
]
```

---

#### `GET /api/v1/personnel/employees`

Сотрудники с фильтрами.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `department_id` | string | Нет | Фильтр по ID подразделения |
| `status` | string | Нет | Фильтр по статусу сотрудника |

**Ответ (200) — `List[EmployeeResponse]`:**

```json
[
  {
    "id": "uuid-1",
    "first_name": "Иван",
    "last_name": "Иванов",
    "middle_name": "Иванович",
    "employee_number": "EMP-001",
    "position_id": "uuid-pos-1",
    "workstation_id": "uuid-ws-1",
    "status": "active",
    "email": "ivanov@efko.local",
    "phone": "+7-999-123-4567",
    "hire_date": "2024-01-15"
  }
]
```

---

#### `GET /api/v1/personnel/summary`

Сводные подсчёты всех сущностей персонала.

**Ответ (200) — `PersonnelSummaryResponse`:**

```json
{
  "locations": 5,
  "production_lines": 12,
  "departments": 25,
  "positions": 80,
  "workstations": 150,
  "employees": 500
}
```

---

### 4.12. Дашборд Master Line

**Префикс:** `/api/v1/dashboards/line-master`  
**Тег:** `Line Master Dashboard`

#### `GET /api/v1/dashboards/line-master/shift-progress`

Прогресс производства по сменам за конкретную дату.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `production_date` | date | Нет | Дата производства (по умолчанию: сегодня) |

**Ответ (200) — `ShiftProgressResponse`:**

```json
{
  "date": "2026-05-11",
  "shifts": [
    {
      "shift": "Shift 1",
      "lot_count": 15,
      "total_quantity": "3000.000",
      "approved_count": 14,
      "defect_count": 1,
      "defect_rate": "6.67"
    }
  ],
  "total_quantity": "6000.000",
  "total_lots": 30
}
```

---

#### `GET /api/v1/dashboards/line-master/shift-comparison`

Сравнение смен за период.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `date_from` | date | Нет | Дата начала (по умолчанию: 7 дней назад) |
| `date_to` | date | Нет | Дата окончания (по умолчанию: сегодня) |

**Ответ (200) — `ShiftComparisonResponse`:**

```json
{
  "period_from": "2026-05-04",
  "period_to": "2026-05-11",
  "shifts": [
    {
      "date": "2026-05-04",
      "shift": "Shift 1",
      "total_quantity": "3000.000",
      "lot_count": 15,
      "defect_count": 1
    }
  ]
}
```

---

#### `GET /api/v1/dashboards/line-master/defect-summary`

Сводка по дефектам по параметрам качества.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `date_from` | date | Нет | Дата начала (по умолчанию: 7 дней назад) |
| `date_to` | date | Нет | Дата окончания (по умолчанию: сегодня) |

**Ответ (200) — `DefectSummaryResponse`:**

```json
{
  "period_from": "2026-05-04",
  "period_to": "2026-05-11",
  "total_defects": 15,
  "items": [
    {
      "parameter_name": "acidity",
      "total_tests": 50,
      "failed_tests": 8,
      "fail_rate": "16.00"
    }
  ]
}
```

---

### 4.13. Дашборд Group Manager

**Префикс:** `/api/v1/dashboards/gm`  
**Тег:** `Group Manager Dashboard`

#### `GET /api/v1/dashboards/gm/oee-summary`

Сводка OEE по линиям производства.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `period_days` | int | Нет | Окно просмотра в днях (1–365, по умолчанию: 30) |

**Ответ (200) — `OEESummaryResponse`:**

```json
{
  "period_days": 30,
  "period_from": "2026-04-11",
  "period_to": "2026-05-11",
  "lines": [
    {
      "production_line": "Line-1",
      "avg_oee": "82.50",
      "vs_target_pct": "7.50",
      "completed_orders": 45,
      "total_orders": 50,
      "avg_defect_rate": "2.35",
      "data_points": 30,
      "trend": [
        {
          "period_from": "2026-04-11",
          "period_to": "2026-04-12",
          "oee_value": "80.00"
        }
      ]
    }
  ],
  "oee_target": "75.00"
}
```

---

#### `GET /api/v1/dashboards/gm/plan-execution`

План vs факт по линиям производства.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `date_from` | date | Нет | Дата начала (по умолчанию: 30 дней назад) |
| `date_to` | date | Нет | Дата окончания (по умолчанию: сегодня) |

**Ответ (200) — `PlanExecutionResponse`:**

```json
{
  "period_from": "2026-04-11",
  "period_to": "2026-05-11",
  "lines": [
    {
      "production_line": "Line-1",
      "target_quantity": "5000.000",
      "actual_quantity": "4800.000",
      "fulfillment_pct": "96.00",
      "orders_planned": 5,
      "orders_in_progress": 3,
      "orders_completed": 15,
      "orders_cancelled": 1,
      "total_snapshots": 24
    }
  ],
  "total_target": "25000.000",
  "total_actual": "24000.000",
  "overall_fulfillment_pct": "96.00"
}
```

---

#### `GET /api/v1/dashboards/gm/downtime-ranking`

Pareto-рейтинг линий по времени простоя.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `date_from` | date | Нет | Дата начала (по умолчанию: 30 дней назад) |
| `date_to` | date | Нет | Дата окончания (по умолчанию: сегодня) |

**Ответ (200) — `DowntimeRankingResponse`:**

```json
{
  "period_from": "2026-04-11",
  "period_to": "2026-05-11",
  "lines": [
    {
      "production_line": "Line-2",
      "total_delay_hours": "25.00",
      "delayed_orders": 5,
      "avg_delay_hours": "5.00",
      "total_completed": 20,
      "delay_pct": "25.00"
    }
  ],
  "total_delay_hours": "45.50",
  "total_delayed_orders": 10
}
```

---

### 4.14. Дашборд Quality Engineer

**Префикс:** `/api/v1/dashboards/qe`  
**Тег:** `Quality Engineer Dashboard`

#### `GET /api/v1/dashboards/qe/parameter-trends`

Ежедневные тренды параметров качества с полосами спецификаций.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `date_from` | date | Нет | Дата начала (по умолчанию: 30 дней назад) |
| `date_to` | date | Нет | Дата окончания (по умолчанию: сегодня) |

**Ответ (200) — `ParameterTrendsResponse`** (см. раздел 4.5, endpoint `parameter-trends`)

---

#### `GET /api/v1/dashboards/qe/batch-analysis`

Анализ партий с отклонениями.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `date_from` | date | Нет | Дата начала (по умолчанию: 30 дней назад) |
| `date_to` | date | Нет | Дата окончания (по умолчанию: сегодня) |

**Ответ (200) — `BatchAnalysisResponse`:**

```json
{
  "period_from": "2026-04-11",
  "period_to": "2026-05-11",
  "lot_count": 5,
  "lots": [
    {
      "lot_number": "LOT-001",
      "product_name": "Масло подсолнечное",
      "production_date": "2026-05-01",
      "shift": "Shift 1",
      "fail_count": 2,
      "deviations": [
        {
          "parameter_name": "acidity",
          "result_value": "0.25",
          "lower_limit": "0.10",
          "upper_limit": "0.20",
          "deviation_magnitude": "0.05"
        }
      ]
    }
  ]
}
```

---

#### `GET /api/v1/dashboards/qe/defect-pareto`

Pareto-диаграмма брака с опциональным фильтром по продукту.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `date_from` | date | Нет | Дата начала (по умолчанию: 30 дней назад) |
| `date_to` | date | Нет | Дата окончания (по умолчанию: сегодня) |
| `product_id` | UUID | Нет | Фильтр по ID продукта |

**Ответ (200) — `DefectParetoResponse`** (см. раздел 4.5, endpoint `defect-pareto`)

---

### 4.15. Дашборд Finance Manager

**Префикс:** `/api/v1/dashboards/finance`  
**Тег:** `Finance Manager Dashboard`

#### `GET /api/v1/dashboards/finance/sales-breakdown`

Разбивка продаж по каналам/регионам/продуктам с процентами.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `date_from` | date | Нет | Дата начала (по умолчанию: 30 дней назад) |
| `date_to` | date | Нет | Дата окончания (по умолчанию: сегодня) |
| `group_by` | string | Нет | Группировка: `channel`, `region`, `product` (по умолчанию: `channel`) |

**Ответ (200) — `SalesBreakdownResponse`:**

```json
{
  "period_from": "2026-04-11",
  "period_to": "2026-05-11",
  "group_by": "channel",
  "total_amount": "500000.00",
  "total_quantity": "10000.000",
  "groups": [
    {
      "group_key": "wholesale",
      "total_amount": "300000.00",
      "total_quantity": "6000.000",
      "sales_count": 80,
      "avg_order_value": "3750.00",
      "amount_share_pct": "60.00"
    }
  ]
}
```

---

#### `GET /api/v1/dashboards/finance/revenue-trend`

Тренд выручки с процентом роста за период.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `date_from` | date | Нет | Дата начала (по умолчанию: 90 дней назад) |
| `date_to` | date | Нет | Дата окончания (по умолчанию: сегодня) |
| `interval` | string | Нет | Интервал: `day`, `week`, `month` (по умолчанию: `week`) |
| `region` | string | Нет | Фильтр по региону |
| `channel` | string | Нет | Фильтр по каналу |

**Ответ (200) — `RevenueTrendResponse`:**

```json
{
  "period_from": "2026-02-11",
  "period_to": "2026-05-11",
  "interval": "week",
  "region": null,
  "channel": null,
  "data": [
    {
      "trend_date": "2026-02-11",
      "total_amount": "50000.00",
      "total_quantity": "1000.000",
      "order_count": 20,
      "mom_growth_pct": null
    },
    {
      "trend_date": "2026-02-18",
      "total_amount": "55000.00",
      "total_quantity": "1100.000",
      "order_count": 22,
      "mom_growth_pct": "10.00"
    }
  ]
}
```

---

#### `GET /api/v1/dashboards/finance/top-products`

Топ продуктов по выручке или объёму.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `date_from` | date | Нет | Дата начала (по умолчанию: 30 дней назад) |
| `date_to` | date | Нет | Дата окончания (по умолчанию: сегодня) |
| `limit` | int | Нет | Максимум продуктов (1–50, по умолчанию: 10) |
| `sort_by` | string | Нет | Сортировка: `amount`, `quantity` (по умолчанию: `amount`) |

**Ответ (200) — `TopProductsResponse`:**

```json
{
  "period_from": "2026-04-11",
  "period_to": "2026-05-11",
  "sort_by": "amount",
  "total_amount": "500000.00",
  "products": [
    {
      "rank": 1,
      "product_name": "Масло подсолнечное",
      "total_amount": "200000.00",
      "total_quantity": "4000.000",
      "sales_count": 50,
      "amount_share_pct": "40.00"
    }
  ]
}
```

---

### 4.16. Отчёты (Reports)

**Префикс:** `/reports`  
**Тег:** `Reports`

#### `GET /reports/types`

Доступные типы отчётов и форматы.

**Ответ (200):** Список типов отчётов.

---

#### `POST /reports/generate/{report_type}`

Генерация и скачивание отчёта (CSV/XLSX).

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|---------|
| `report_type` | string | Да | Тип отчёта |
| `format_type` | string | Нет | Формат: `csv`, `xlsx` |
| `date_from` | date | Нет | Дата начала |
| `date_to` | date | Нет | Дата окончания |
| `period` | string | Нет | Период |
| `status` | string | Нет | Фильтр по статусу |
| `production_line` | string | Нет | Фильтр по линии |
| `region` | string | Нет | Фильтр по региону |
| `decision` | string | Нет | Фильтр по решению |

**Ответ (200):** Файл отчёта (CSV или XLSX).

---

## 5. Диаграммы взаимодействия

### 5.1. Диаграмма архитектуры (компоненты)

```mermaid
graph LR
    subgraph "Presentation Layer"
        Dashboard[Веб-дашборды]
        Swagger[Swagger UI]
    end

    subgraph "API Layer"
        FastAPI[FastAPI Application]
        Middleware[Middleware<br/>CORS, Logging]
        Routers[15 Routers]
    end

    subgraph "Service Layer"
        Services[16 Service Classes]
        GatewayClient[Gateway Client]
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL)]
        Alembic[Alembic Migrations]
    end

    subgraph "Infrastructure"
        Scheduler[APScheduler<br/>Hourly Cron]
        RabbitMQ[RabbitMQ<br/>Event Consumer]
        Docker[Docker / Docker Compose]
    end

    subgraph "External"
        GatewayAPI[EFKO Gateway API]
    end

    Dashboard --> FastAPI
    Swagger --> FastAPI
    FastAPI --> Middleware
    Middleware --> Routers
    Routers --> Services
    Services --> PostgreSQL
    Services --> GatewayClient
    GatewayClient --> GatewayAPI
    Scheduler --> Services
    RabbitMQ --> Services
```

### 5.2. Диаграмма жизненного цикла приложения

```mermaid
sequenceDiagram
    participant App as FastAPI App
    participant DB as PostgreSQL
    participant Scheduler as Cron Scheduler
    participant RabbitMQ as RabbitMQ Consumer

    Note over App: STARTUP PHASE
    App->>DB: init_db() — создание таблиц
    DB-->>App: OK
    App->>Scheduler: start_scheduler() — запуск cron
    Scheduler-->>App: OK
    App->>RabbitMQ: start_consumer() — подключение к RabbitMQ
    RabbitMQ-->>App: OK
    Note over App: READY

    Note over App: RUNTIME
    App->>App: Обработка HTTP-запросов
    loop Каждый час
        Scheduler->>Scheduler: Выполнение sync задач
    end
    loop Сообщения RabbitMQ
        RabbitMQ->>App: Обработка событий
    end

    Note over App: SHUTDOWN
    App->>RabbitMQ: stop_consumer() — отключение
    App->>Scheduler: stop_scheduler() — остановка cron
    App->>DB: close_db() — закрытие соединений
```

### 5.3. Диаграмма потока данных синхронизации

```mermaid
graph TD
    subgraph "Hourly Sync"
        Cron[Cron Scheduler] --> KPI[KPI Sync]
        Cron --> Sales[Sales Sync]
        Cron --> Orders[Orders Sync]
        Cron --> Quality[Quality Sync]
        Cron --> Products[Products Sync]
        Cron --> Output[Output Sync]
        Cron --> Sensors[Sensors Sync]
        Cron --> Inventory[Inventory Sync]
        Cron --> Personnel[Personnel Sync]
        Cron --> References[References Sync]
    end

    KPI --> Gateway[Gateway Client]
    Sales --> Gateway
    Orders --> Gateway
    Quality --> Gateway
    Products --> Gateway
    Output --> Gateway
    Sensors --> Gateway
    Inventory --> Gateway
    Personnel --> Gateway
    References --> Gateway

    Gateway --> ExternalAPI[EFKO Gateway API]

    KPI --> PostgreSQL[(PostgreSQL)]
    Sales --> PostgreSQL
    Orders --> PostgreSQL
    Quality --> PostgreSQL
    Products --> PostgreSQL
    Output --> PostgreSQL
    Sensors --> PostgreSQL
    Inventory --> PostgreSQL
    Personnel --> PostgreSQL
    References --> PostgreSQL
```

### 5.4. Диаграмма обработки событий RabbitMQ

```mermaid
graph TD
    RabbitMQ[RabbitMQ] --> Consumer[Event Consumer]
    Consumer --> Dispatcher[Event Dispatcher]
    Dispatcher --> ProductHandler[Product Handler]
    Dispatcher --> OrderHandler[Order Handler]
    Dispatcher --> OutputHandler[Output Handler]
    Dispatcher --> SaleHandler[Sale Handler]
    Dispatcher --> InventoryHandler[Inventory Handler]
    Dispatcher --> QualityHandler[Quality Handler]

    ProductHandler --> ProductService[Product Service]
    OrderHandler --> OrderService[Order Service]
    OutputHandler --> OutputService[Output Service]
    SaleHandler --> SalesService[Sales Service]
    InventoryHandler --> InventoryService[Inventory Service]
    QualityHandler --> QualityService[Quality Service]

    ProductService --> DB[(PostgreSQL)]
    OrderService --> DB
    OutputService --> DB
    SalesService --> DB
    InventoryService --> DB
    QualityService --> DB
```

### 5.5. Диаграмма зависимостей между моделями

```mermaid
graph TD
    Product --> UnitOfMeasure
    SaleRecord --> Customer
    SaleRecord --> Product
    QualityResult --> QualitySpec
    QualityResult --> Product
    ProductionOutput --> Product
    SensorReading --> Sensor
    Sensor --> SensorParameter
    InventorySnapshot --> Warehouse
    InventorySnapshot --> Product
    ProductionLine --> Location
    Department --> Location
    Department --> Department
    Position --> Department
    Workstation --> Location
    Workstation --> ProductionLine
    Employee --> Position
    Employee --> Workstation
    SyncError --> SyncLog
```

---

## 6. Приложения

### 6.1. Перечень зависимостей (requirements.txt)

| Пакет | Назначение |
|-------|-----------|
| `fastapi` | Веб-фреймворк |
| `uvicorn[standard]` | ASGI-сервер |
| `sqlalchemy[asyncio]` | ORM (async) |
| `asyncpg` | PostgreSQL драйвер (async) |
| `alembic` | Миграции БД |
| `httpx` | HTTP-клиент (async) |
| `apscheduler` | Планировщик задач |
| `aio-pika` | RabbitMQ клиент |
| `pydantic` | Валидация данных |
| `pydantic-settings` | Настройки из .env |
| `structlog` | Структурированное логирование |
| `python-multipart` | Поддержка multipart/form-data |
| `pytest` | Тестирование |
| `pytest-asyncio` | Async-тесты |
| `pytest-httpx` | HTTP-моки |
| `testcontainers[postgresql]` | Тестовый PostgreSQL |
| `psycopg2-binary` | PostgreSQL драйвер (sync) |
| `faker` | Генерация тестовых данных |
| `python-dateutil` | Утилиты дат |
| `psutil` | Мониторинг памяти |
| `openpyxl` | Генерация Excel-отчётов |

### 6.2. Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|-----------|---------|---------------------|
| `APP_NAME` | Название приложения | Dashboard Analytics API |
| `APP_VERSION` | Версия API | 1.0.0 |
| `DEBUG` | Режим отладки | false |
| `DATABASE_URL` | URL PostgreSQL | `postgresql+asyncpg://postgres:postgres@localhost:5432/dashboard_api` |
| `GATEWAY_URL` | URL Gateway API | `http://localhost:3000/api` |
| `GATEWAY_AUTH_EMAIL` | Email для авторизации в Gateway | `admin@efko.local` |
| `GATEWAY_AUTH_PASSWORD` | Пароль для Gateway | `Efko2024!` |
| `GATEWAY_TIMEOUT_CONNECT` | Таймаут подключения к Gateway (сек) | 10.0 |
| `GATEWAY_TIMEOUT_READ` | Таймаут чтения ответа Gateway (сек) | 30.0 |
| `GATEWAY_MAX_RETRIES` | Максимум повторных попыток | 3 |
| `SYNC_INTERVAL_MINUTES` | Интервал синхронизации (мин) | 60 |
| `RETENTION_DAYS` | Срок хранения данных (дни) | 90 |
| `LOG_LEVEL` | Уровень логирования | INFO |
| `LOG_FILE` | Путь к файлу логов | `logs/dashboard_api.log` |
| `RABBITMQ_URL` | URL RabbitMQ | `amqp://guest:guest@localhost:5672/` |
| `RABBITMQ_EXCHANGE` | Имя обмена | `efko.production.events` |
| `RABBITMQ_QUEUE_PREFIX` | Префикс очередей | `analytics` |
| `RABBITMQ_PREFETCH_COUNT` | Количество prefetch | 10 |
| `RABBITMQ_ENABLED` | Включить RabbitMQ | true |

### 6.3. Расписание синхронизации

| Минута | Задача | Описание |
|--------|-------|---------|
| 0 | `sync_kpi_task` | Агрегированные KPI |
| 2 | `sync_kpi_per_line_task` | KPI по линиям производства |
| 5 | `sync_sales_task` | Данные продаж |
| 10 | `sync_orders_task` | Заказы |
| 15 | `sync_quality_task` | Результаты качества |
| 20 | `sync_products_task` | Продукты (полный upsert) |
| 25 | `sync_output_task` | Выпуск продукции |
| 30 | `sync_sensors_task` | Показания датчиков |
| 35 | `sync_inventory_task` | Запасы (полный upsert) |
| 40 | `sync_personnel_task` | Персонал (полный upsert) |
| 45 | `sync_references_task` | Справочники (единицы, датчики, клиенты, склады) |

### 6.4. Команды проверки

```bash
pytest tests/ -v              # Запуск тестов (testcontainers PostgreSQL)
mypy app/                     # Проверка типов
ruff check app/               # Линтинг
uvicorn app.main:app --reload # Dev-сервер → http://localhost:8000/docs
```

### 6.5. Структура проекта

```
DiplomaAPI/
├── AGENTS.md                          # Правила работы
├── CLAUDE.md                          # Краткая справка по архитектуре
├── README.md                          # Краткое руководство
├── requirements.txt                   # Зависимости Python
├── Dockerfile                         # Контейнер Python 3.11-slim
├── docker-compose.yml                 # PostgreSQL 15 + API
├── alembic.ini                        # Конфигурация Alembic
├── alembic/
│   ├── env.py
│   └── versions/                      # 9 файлов миграций
├── app/
│   ├── main.py                        # Точка входа FastAPI (316 строк)
│   ├── config.py                      # Настройки из .env (70 строк)
│   ├── database.py                    # SQLAlchemy async (73 строки)
│   ├── logging_config.py              # structlog конфигурация (78 строк)
│   ├── models/                        # 14 ORM-моделей (12 файлов)
│   ├── schemas/                       # Pydantic схемы (14 файлов)
│   ├── services/                      # Бизнес-логика (16 сервисов)
│   ├── routers/                       # API-эндпоинты (17 файлов, 15 роутеров)
│   ├── cron/                          # Cron-задачи (scheduler + jobs)
│   ├── messaging/                     # RabbitMQ consumer + handlers
│   ├── middleware/                     # Middleware (logging, CORS)
│   └── utils/                         # Утилиты (LLM docs, logging)
├── tests/                             # Тесты
│   ├── conftest.py                    # Testcontainers fixtures
│   ├── unit/                          # ~47 unit-тестов
│   └── integration/                   # ~160 integration-тестов
└── docs/                              # Документация
```

---

*Документ подготовлен для приложения к дипломной работе по проекту Dashboard Analytics API.*
