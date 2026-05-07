# Архитектура: Базы данных

EFKO использует Polyglot Persistence: разные БД для разных задач.

## PostgreSQL (Transactional)

**Когда:** Структурированные данные с ACID гарантиями (кадры, производство)

**Сервисы:**
- Auth Service — User, RefreshToken
- Personnel Service — Department, Employee, Position, Location, PostalArea, Workstation
- Production Service — Product, Order, Sale, Quality, Sensor, Customer, Inventory, Warehouse
- Sync Service — синхронизированные данные для отчетов

**ORM:** Prisma (type-safe database client)

**Schema per service:** Каждый сервис имеет свою schema
```
apps/auth-service/prisma/schema.prisma
apps/personnel/prisma/schema.prisma
apps/production/prisma/schema.prisma
```

**Generated Client:** `apps/<service>/src/generated/prisma`

**Миграции:** 
```bash
cd apps/<service>
npx prisma migrate dev --name <name>   # Develop
npx prisma migrate deploy               # Production
```

## MongoDB (NoSQL)

**Когда:** Полуструктурированные данные (импорты, трансформация, файлы)

**Сервис:** ETL Service

**Сущности:**
- **RawImport** — журнал импортов из внешних систем
- **TransformationLog** — логирование трансформации записей
- **GridFS** — хранение исходных файлов (.xlsx, .json)

**ORM:** Mongoose (schema-less, document-based)

**Collections:**
```
db.raw_imports
db.transformation_logs
db.fs.files, db.fs.chunks  (GridFS)
```

## Outbox Pattern

**Цель:** Надежная публикация событий (гарантирует at-least-once delivery)

**Таблица:** `outbox_messages` (во всех PostgreSQL БД)

**Поле:**
- `id` — UUID, уникальный идентификатор события
- `eventType` — тип события (EmployeeCreated, OrderPlaced, и т.д.)
- `payload` — JSON с данными события
- `status` — PENDING, SENT, FAILED
- `retryCount` — количество попыток отправки
- `createdAt`, `updatedAt`, `processedAt`

**Поток:**
```
1. Сервис создает основную запись + OutboxMessage в одной транзакции
2. Cron job (OutboxPeriodicPublisher) читает PENDING сообщения
3. Публикует в RabbitMQ
4. Если успешно, меняет статус на SENT
5. Если ошибка, increments retryCount и пересыпает позже
```

## Индексирование

**Стратегия:** Индекс на поля, используемые в WHERE/ORDER BY/JOIN

**Примеры:**
```prisma
// Частые фильтры
@@index([locationId])
@@index([status])

// Уникальные ограничения
@@unique([code])

// Составной индекс (для range queries)
@@index([productId, testDate])

// Foreign keys (обычно индексируются автоматически)
```

**Performance:**
- EXPLAIN ANALYZE для профилирования
- `pg_stat_user_indexes` для статистики использования

## Backup & Recovery

**PostgreSQL:**
```bash
# Backup
pg_dump -U user -d dbname > backup.sql

# Restore
psql -U user -d dbname < backup.sql

# Via Docker
docker exec postgres pg_dump -U efko efko_auth > backup.sql
```

**MongoDB:**
```bash
# Backup
mongodump --db etl --out /backups/

# Restore
mongorestore --db etl /backups/etl/
```

---

**Related:** [3nf-normalization.md](3nf-normalization.md), [../data/](../data/), [../operations/](../operations/)
