# ETL Service

## Назначение

`etl` принимает сырые данные из внешних систем, валидирует и нормализует их, преобразует в canonical-команды доменной системы, диспатчит их в downstream сервисы через RabbitMQ RPC и сохраняет журнал импорта. Это интеграционный сервис между внешними системами (`ZUP`, `ERP`, `MES`, `SCADA`, `LIMS`) и внутренними сервисами `production` и `personnel`.

## Как сервис встроен в систему

- Поднимает HTTP API с глобальным префиксом `api/v1`.
- Основной контроллер расположен по маршруту `/etl`.
- Для импорта и просмотра истории использует JWT/authz (`@Auth(UserRole.admin)`).
- Для доставки в downstream сервисы использует RabbitMQ request/reply.
- Собственные события об импорте публикует в `efko.etl.events`.

## Основные модули

- `IngestionModule`: HTTP-вход, auth, приём JSON и файлов, запуск pipeline.
- `TransformModule`: реестр transformer-ов по source system.
- `ImportsModule`: журнал импортов и логов трансформации в Mongo.
- `DispatchModule`: RabbitMQ dispatch с retry/backoff.
- `RabbitModule`: Rabbit transport и `EventEmitterService`.
- `MongoModule` / Mongoose infrastructure: схемы `RawImport`, `TransformationLog`, GridFS-хранилище исходных файлов.

## HTTP API

Base URL: `http://localhost:4200/api/v1`

**Аутентификация:** Bearer accessToken (для всех эндпоинтов)  
**Роль:** admin (требуется для всех эндпоинтов)

Глобально включены `ValidationPipe`, `LoggingInterceptor`, `HttpExceptionFilter` и `RequestIdMiddleware`.

---

### POST /api/v1/etl/import

Импорт массива записей в JSON.

**Authentication:** Bearer accessToken  
**Role:** admin  
**CSRF:** Требуется для браузера

**Request Body:**

```typescript
{
  source_system: SourceSystem;  // '1c_zup' | '1c_erp' | 'mes' | 'scada' | 'lims'
  import_type: ImportType;      // 'employees' | 'departments' | 'positions' | 'products' | 'orders' | 'sensors' | 'quality'
  data: Array<Record<string, any>>;  // Массив записей для импорта
}
```

**Response:**

```typescript
{
  import_id: string;       // MongoDB ObjectId импорта
  status: ImportStatus;    // 'pending' | 'processing' | 'completed' | 'failed'
  records_count: number;
  source_file_id?: string;
  warnings?: string[];
  parse_errors?: Array<{ index: number; field: string; message: string }>;
}
```

**Пример запроса:**

```bash
curl -X POST http://localhost:4200/api/v1/etl/import \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "source_system": "1c_zup",
    "import_type": "employees",
    "data": [
      {
        "ТабельныйНомер": "EMP-0001",
        "ФИО": "Иванов Иван Иванович",
        "ДатаРождения": "1985-05-15"
      }
    ]
  }'
```

**Ошибки:**
- `400` — Некорректный формат или отсутствует обязательное поле
- `401` — Не авторизован
- `403` — Недостаточно прав

---

### POST /api/v1/etl/import/file

Импорт файла (xlsx или json) через multipart upload.

**Authentication:** Bearer accessToken  
**Role:** admin  
**CSRF:** Требуется для браузера  
**Max file size:** 20 MB

**Request Body (multipart/form-data):**

```
file: <binary file>          // xlsx или json файл
source_system: string        // ZUP | ERP | MES | SCADA | LIMS
import_type: string          // тип импорта
```

**Response:**

```typescript
{
  import_id: string;       // MongoDB ObjectId импорта
  status: 'processing';    // Файл принят и обрабатывается
  records_count: number;
  source_file_id?: string; // ID файла в GridFS
  format?: 'xlsx' | 'json';
  warnings?: string[];
  parse_errors?: Array<{ index: number; field: string; message: string }>;
}
```

**Пример запроса:**

```bash
curl -X POST http://localhost:4200/api/v1/etl/import/file \
  -H "Authorization: Bearer <accessToken>" \
  -F "file=@employees.xlsx" \
  -F "source_system=ZUP" \
  -F "import_type=employees"
```

**Ошибки:**
- `400` — Неподдерживаемый формат файла или превышен размер
- `401` — Не авторизован
- `403` — Недостаточно прав

---

### GET /api/v1/etl/imports

Получить список импортов.

**Authentication:** Bearer accessToken  
**Role:** admin  
**CSRF:** Не требуется

**Query Parameters:**

```typescript
{
  source_system?: SourceSystem;  // Фильтр: '1c_zup' | '1c_erp' | 'mes' | 'scada' | 'lims'
  status?: ImportStatus;         // Фильтр: 'pending' | 'processing' | 'completed' | 'failed'
  limit?: number;                // Максимальное количество записей (1–500, по умолчанию 20)
}
```

**Response:**

```typescript
Array<{
  import_id: string;
  source_system: SourceSystem;
  import_type: ImportType;
  status: ImportStatus;
  records_count: number;
  source_file_id?: string;
  source_file_format?: 'xlsx' | 'json';
  created_at: string;
  processed_at: string | null;
}>
```

**Пример запроса:**

```bash
curl -X GET "http://localhost:4200/api/v1/etl/imports?source_system=ZUP&limit=10" \
  -H "Authorization: Bearer <accessToken>"
```

---

### GET /api/v1/etl/imports/:id

Получить детали импорта.

**Authentication:** Bearer accessToken  
**Role:** admin  
**CSRF:** Не требуется

**Response:**

```typescript
{
  import_id: string;
  source_system: SourceSystem;
  import_type: ImportType;
  status: ImportStatus;
  records_count: number;
  source_file_id?: string;
  source_file_format?: 'xlsx' | 'json';
  created_at: string;
  processed_at: string | null;
  stats: {
    total: number;
    success: number;
    error: number;
    skipped: number;
  };
  errors: Array<{ field: string; message: string; record_index?: number }>;
}
```

**Пример запроса:**

```bash
curl -X GET http://localhost:4200/api/v1/etl/imports/507f1f77bcf86cd799439011 \
  -H "Authorization: Bearer <accessToken>"
```

**Ошибки:**
- `404` — Импорт не найден

---

### GET /api/v1/etl/imports/:id/file

Скачать исходный файл импорта.

**Authentication:** Bearer accessToken  
**Role:** admin  
**CSRF:** Не требуется

**Response:**

Бинарный поток файла (application/octet-stream или исходный MIME-type)

**Пример запроса:**

```bash
curl -X GET http://localhost:4200/api/v1/etl/imports/507f1f77bcf86cd799439011/file \
  -H "Authorization: Bearer <accessToken>" \
  -o employees.xlsx
```

**Ошибки:**
- `404` — Импорт или файл не найден

---

### POST /api/v1/etl/imports/:id/retry

Повторить импорт (только для импортов со статусом `failed`).

**Authentication:** Bearer accessToken  
**Role:** admin  
**CSRF:** Требуется для браузера

**Request Body:**

```typescript
{}
```

**Response:**

```typescript
{
  import_id: string;
  status: 'processing';  // Импорт переведен в повторную обработку
}
```

**Пример запроса:**

```bash
curl -X POST http://localhost:4200/api/v1/etl/imports/507f1f77bcf86cd799439011/retry \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Ошибки:**
- `400` — Импорт не может быть повторен (не в статусе `failed`)
- `404` — Импорт не найден

---

## Ingestion

- `IngestionController` извлекает request metadata из HTTP headers и передаёт их дальше в pipeline.
- `IngestionService.processImport(...)`:
  - проверяет корректность `sourceSystem`;
  - создаёт новую запись импорта или переиспользует существующую при retry;
  - поднимает статус `processing`;
  - получает import schema по паре `source_system` + `import_type`;
  - нормализует и валидирует входные записи через `validateRecords`.
- Поддерживаемые source system и import types по коду:
  - `1c_zup`: `employees`, `departments`, `positions`
  - `1c_erp`: `products`
  - `mes`: `orders`
  - `scada`: `sensors`
  - `lims`: `quality`
- Схемы поддерживают alias-ы входных полей, включая 1C-ключи на русском, и coercion типов (`string`, `number`, `date-string`, `boolean`).

## Transform

- `TransformerRegistry` выбирает transformer по `SourceSystem`.
- Реализованы transformer-ы:
  - `ZupTransformer`
  - `ErpTransformer`
  - `MesTransformer`
  - `ScadaTransformer`
  - `LimsTransformer`
- Трансформация идёт в canonical records вида:
  - `entityType`
  - `sourceId`
  - `canonicalId`
  - `payload`
  - `exchange`
  - `routingKey`
- Важные маршруты downstream:
  - `ZUP` -> команды `personnel`
  - `ERP`, `MES`, `SCADA`, `LIMS` -> команды `production`
- Mapper-ы в коде переводят внешние enum-ы в внутренние доменные enum-ы и выставляют routing key из `@efko-kernel/contracts`.
- Особый случай `SCADA`: alarms распознаются на уровне transformer-а, но в комментарии явно указано, что alarms только логируются и не диспатчатся как сущности.

## Imports

- `ImportsService` хранит запись импорта в коллекции `RawImport`.
- `RawImport` содержит:
  - `source_system`
  - `import_type`
  - `raw_payload`
  - `status`
  - `records_count`
  - массив `errors`
  - `processed_at`
  - ссылку на исходный файл и его формат, если импорт шёл из файла.
- Каждый dispatch логируется в `TransformationLog`:
  - `import_id`
  - `entity_type`
  - `source_id`
  - `canonical_id`
  - `transformation_result` (`success` / `error` / `skipped`)
  - `error_message`
- Для retry старые transformation logs удаляются, а импорт переводится обратно в `processing`.

## Dispatch

- `DispatchService` использует `amqpConnection.request(...)`.
- Доставка идёт с exponential backoff:
  - `maxRetries: 3`
  - `baseDelayMs: 1000`
  - `maxDelayMs: 30000`
  - `backoffMultiplier: 2`
- В headers передаётся `correlationId`, если он есть в request metadata.
- Если dispatch конкретной canonical-записи падает, сервис:
  - фиксирует ошибку в `TransformationLog`;
  - добавляет запись в `errors` импорта;
  - продолжает обработку остальных записей.
- Итоговый статус импорта:
  - `failed`, если transform не дал ни одной canonical-записи;
  - `failed`, если все dispatch-операции упали;
  - `completed`, если есть хотя бы частичный успех.

## Хранение данных

MongoDB / Mongoose:

- `RawImport`: журнал сырых импортов и их статусов.
- `TransformationLog`: построчный лог трансформации и dispatch результата.
- GridFS bucket `etl_source_files`: хранение исходных файлов импорта.

GridFS metadata включает:

- `sourceSystem`
- `importType`
- `format`
- `uploadedBy`
- `mime`
- `uploadedAt`

## Интеграции

- Входящие системы (значения `SourceSystem` enum):
  - `1c_zup` (1С:ЗУП)
  - `1c_erp` (1С:ERP)
  - `mes` (MES)
  - `scada` (SCADA)
  - `lims` (LIMS)
- Исходящие сервисы:
  - `personnel` через `efko.personnel.commands`
  - `production` через `efko.production.commands`
- Собственные события ETL:
  - `EtlImportCompletedEvent`
  - `EtlImportFailedEvent`
  - публикуются в `efko.etl.events`

### Примеры бизнес-маршрутизации

- `1c_zup employees` -> `PersonnelCreateEmployeeCommand`
- `1c_zup departments` -> `PersonnelCreateDepartmentCommand`
- `1c_zup positions` -> `PersonnelCreatePositionCommand`
- `1c_zup shift templates` поддерживаются mapper-ом, но отдельная schema для такого `import_type` в `IMPORT_SCHEMAS` в текущем файле не описана
- `1c_erp products` -> `ProductionCreateProductCommand`
- `1c_erp sales` и `inventory` поддерживаются mapper-ом, но в `IMPORT_SCHEMAS` для них сейчас нет отдельных схем
- `mes orders` -> `ProductionCreateOrderCommand`
- `mes output` поддерживается mapper-ом, но отдельная schema/import type в `IMPORT_SCHEMAS` сейчас не описаны
- `scada sensors` -> `ProductionRecordSensorReadingCommand`
- `lims quality` -> `ProductionRecordQualityResultCommand`

## Обработка ошибок

- HTTP ошибки идут через глобальный `HttpExceptionFilter`.
- Пустой upload-файл, отсутствие import schema и невалидный retry-status дают `BadRequestException`/`NotFoundException`.
- Ошибки transform и dispatch не обязательно валят весь импорт немедленно: сервис стремится обработать максимум записей и сохраняет частичные ошибки в журнал.
- Если файл уже сохранён в GridFS, но импорт дальше не создался, `FileIngestionService` выполняет compensating delete.

## Observability и logging

- Логирование через `nestjs-pino`, dev-лог в `logs/etl.log`.
- `RequestIdMiddleware` навешивается на все маршруты.
- `LoggingInterceptor` пишет HTTP request metadata и duration.
- Сервис насыщенно использует `buildLogContext(...)` для связи логов по `correlationId`/request metadata.
- Логируются:
  - старт импорта;
  - результат трансформации;
  - ошибки dispatch конкретных записей;
  - финальный статус импорта;
  - сохранение/получение/удаление файлов в GridFS.

## Зависимости

- NestJS
- Mongoose + MongoDB + GridFS
- RabbitMQ
- JWT auth из `@efko-kernel/nest-utils`
- `xlsx` для Excel parsing
- `@efko-kernel/contracts`
- `@efko-kernel/interfaces`

## Наблюдения и пробелы по коду

- `IMPORT_SCHEMAS` и mapper-ы покрывают разные множества import types: mapper-ы уже умеют больше, чем разрешает текущая схема в ingestion.
- В документации по supported imports выше отражено именно то, что реально следует из `IMPORT_SCHEMAS` и mapper-ов на текущий момент.
- ETL не хранит доменные сущности downstream; его персистентность ограничена журналом импортов, логом трансформации и исходными файлами.
