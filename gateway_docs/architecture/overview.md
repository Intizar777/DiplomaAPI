# Архитектура: Обзор системы

EFKO Kernel — Nx-монорепозиторий с микросервисной архитектурой на NestJS. Система состоит из 5 доменных сервисов, 3 общих библиотек и несколько infra компонентов.

## 5 Доменных сервисов

| Сервис | Домен | Отвечает за |
|--------|-------|-----------|
| **gateway** | API Gateway | Единая точка входа, валидация, аутентификация, прокси в сервисы |
| **auth-service** | Идентификация | Пользователи, JWT токены, refresh, роли |
| **personnel** | Кадры | Подразделения, должности, сотрудники, смены, локации |
| **production** | Производство | Продукты, заказы, выпуск, качество, датчики, KPI, продажи |
| **etl** | Интеграция | Импорт из 1C (ZUP, ERP), MES, SCADA, LIMS |

## 3 Общие библиотеки

| Библиотека | Содержит |
|-----------|----------|
| **contracts** | Типизированные контракты: Commands, Queries, Events для RabbitMQ |
| **interfaces** | Общие TypeScript интерфейсы, enum-ы, DTO |
| **nest-utils** | Инфра-утилиты: логирование, метрики, трассировка, auth, RPC helpers |

## Стек технологий

| Слой | Технология |
|------|-----------|
| **Framework** | NestJS, Nx (монорепо) |
| **Message Broker** | RabbitMQ (RPC + Events) |
| **Databases** | PostgreSQL (Prisma) + MongoDB (Mongoose) |
| **Logging** | Pino + Loki (production) |
| **Tracing** | OpenTelemetry + Jaeger |
| **Metrics** | Prometheus |
| **Documentation** | Swagger/OpenAPI |

## Ключевые паттерны

- **CQRS** — разделение команд (write) и запросов (read)
- **Event Sourcing** — асинхронная коммуникация через события
- **Transactional Outbox** — надежная публикация событий в транзакции
- **DDD** — каждый сервис имеет свой домен с Aggregates, Entities, Value Objects
- **Contracts-First** — контракты определены в libs/contracts, используются везде

## Сквозной поток данных

```
1. Client HTTP Request → Gateway (валидация, auth, CSRF)
2. Gateway RabbitMQ RPC → Domain Service (бизнес-логика)
3. Domain Service DB → Prisma/Mongoose (изменение состояния)
4. Domain Service Event → Outbox (запись события в БД)
5. Outbox Cron → RabbitMQ (публикация события)
6. Event Listeners → Sync Service (обновление данных в других сервисах)
```

## Развертывание

- **Dev** — `docker compose up -d` (Postgres, RabbitMQ, MongoDB)
- **Local** — `npm run obs:up` (+ Grafana, Loki, Prometheus, Tempo)
- **Prod** — Railway, Docker images, Prisma migrations (см. RAILWAY_SETUP.md)

## Что дальше?

- [Топология сервисов](services.md) — детали каждого сервиса
- [RabbitMQ коммуникация](communication.md) — exchanges, queues, RPC
- [Базы данных](database.md) — схемы, миграции, индексы

---

**Related:** [README.md](../README.md), [CLAUDE.md](../../CLAUDE.md)
