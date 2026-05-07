# Архитектура: RabbitMQ коммуникация

Все межсервисное взаимодействие происходит через RabbitMQ. Есть два паттерна: RPC (синхронный) и Events (асинхронный).

## RPC (Request/Reply)

**Когда:** Gateway вызывает доменный сервис синхронно (HTTP запрос ожидает ответ)

**Поток:**
```
1. Gateway отправляет message в Exchange (команда или запрос)
2. Domain Service получает из Queue
3. Domain Service обрабатывает, отправляет reply в особую reply queue
4. Gateway получает reply и возвращает клиенту ответ
```

**Exchanges по типам:**
- `efko.auth.commands` — команды auth-service
- `efko.auth.queries` — запросы к auth-service
- `efko.personnel.commands` — команды personnel-service
- `efko.personnel.queries` — запросы к personnel-service
- `efko.production.commands` — команды production-service
- `efko.production.queries` — запросы к production-service

**Timeout:** 5000ms (настраивается в `requestWithTimeout`)

## Events (Publish/Subscribe)

**Когда:** Доменный сервис хочет уведомить остальных об изменении (асинхронный)

**Поток:**
```
1. Domain Service создает событие (DomainEvent)
2. Событие сохраняется в OutboxMessage в БД вместе с основными данными
3. Periodic publisher (cron) читает неотправленные события из Outbox
4. Публикует события в RabbitMQ Exchange
5. Все Subscribers (другие сервисы, Sync) получают события из своих Queues
```

**Exchanges:**
- `efko.auth.events` — события auth-service
- `efko.personnel.events` — события personnel-service
- `efko.production.events` — события production-service
- `efko.etl.events` — события etl-service

**Гарантии:**
- ✅ At-least-once delivery (события могут прийти дважды)
- ✅ Transactional (событие отправляется только если БД транзакция успешна)
- ❌ Ordering (события могут прийти в другом порядке)

## Queues конфигурация

**Все очереди — Quorum Queues:**
- Репликация на 3 ноды (высокая доступность)
- Automatic message deletion после обработки
- Prefetch count = 32 (одновременно обрабатываем 32 сообщения)

**Naming convention:**
```
{service}-{type}.queue

Примеры:
auth-service.commands.queue
personnel-service.queries.queue
production-service.events.queue
sync-service.events.queue
```

## Connection settings

```javascript
{
  wait: false,        // Быстрое подключение, не ждем инициализации
  persistent: true,   // Сообщения сохраняются на диск
  isGlobal: false,    // Каждый модуль имеет свое соединение
}
```

## Обработка ошибок

**Что происходит если сервис упал:**
- RPC: Клиент получает 503 ошибку ("Downstream service unavailable")
- Events: События остаются в Outbox, пересылаются при восстановлении

**Retry logic:**
- RPC: Нет встроенного retry (реализуется на уровне Gateway)
- Events: Автоматический retry (Outbox publisher пересыпает каждые N минут)

**Dead letter queue:**
- Если сервис не может обработать сообщение, оно идет в DLQ
- Требуется ручное вмешательство для анализа и исправления

## Типизированные контракты

Все команды, запросы и события определены в `libs/contracts`:

```typescript
// Команда
export class CreateEmployeeCommand {
  constructor(
    public readonly fullName: string,
    public readonly positionId: string,
  ) {}
}

// Запрос
export class GetEmployeesQuery {
  constructor(
    public readonly departmentId?: string,
    public readonly offset?: number,
    public readonly limit?: number,
  ) {}
}

// Событие
export class EmployeeCreatedEvent {
  constructor(
    public readonly employeeId: string,
    public readonly fullName: string,
  ) {}
}
```

---

**Related:** [services.md](services.md), [../integration/events.md](../integration/events.md)
