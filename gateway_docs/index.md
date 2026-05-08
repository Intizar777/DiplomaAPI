# EFKO Kernel Documentation

**Добро пожаловать в техническую документацию EFKO Kernel!**

Полная документация микросервисной системы EFKO Kernel для разработчиков, DevOps инженеров и интеграторов.

## 🚀 Быстрый старт

- **Новый разработчик?** → [Быстрый старт](getting-started/quickstart.md) *(запланировано)*
- **Нужна помощь с установкой?** → [Установка окружения](getting-started/setup.md) *(запланировано)*
- **Готов писать код?** → [Архитектура системы](architecture/overview.md)

## 📚 Структура документации

Документация организована как **"чемодан с кубиками"** — каждый раздел можно читать отдельно:

### [🗺️ Полная навигация](INDEX.md)
Найди нужный раздел за секунду — все темы в одном месте.

### 🏗️ Архитектура
Понимание системы: как всё устроено, как компоненты взаимодействуют
- [Обзор системы](architecture/overview.md) — 5 сервисов, 3 библиотеки, стек технологий
- [Топология сервисов](architecture/services.md) — матрица взаимодействия, ответственность каждого
- [RabbitMQ коммуникация](architecture/communication.md) — RPC vs Events, exchanges, queues
- [Базы данных](architecture/database.md) — PostgreSQL, MongoDB, Outbox, миграции
- [3NF Нормализация](architecture/3nf-normalization.md) — структурные изменения v1.2.0

### 📊 Модели данных
Все таблицы и сущности в системе
- [Auth Service](data/auth-models.md) — User, RefreshToken
- [Personnel Service](data/personnel-models.md) — Department, Employee, Location, Workstation, ProductionLine
- [Production Service](data/production-models.md) — Product, ProductionLine, ProductionOrder, ProductionOutput, Quality, Sensor, Customer, Warehouse

### 🔌 REST API
Как вызывать API, примеры запросов и ответов
- [API Overview](api/overview.md) — Base URL, аутентификация, обработка ошибок
- [Пагинация & Фильтрация](api/pagination.md) — offset/limit, примеры на JS/TS

### ⚙️ Операции
Как работать с системой: безопасность, логирование, мониторинг
- [Аутентификация](operations/authentication.md) — JWT, Login/Logout, Token refresh, Security

### 🧪 Тестирование
Как писать, запускать и отлаживать тесты
- [Руководство по тестированию](09-testing.md) — Unit, Integration, E2E тесты; структура; примеры

## 🎯 Маршруты по ролям

**Я новый разработчик:**
→ [Архитектура](architecture/overview.md) → [API Overview](api/overview.md) → [Пагинация](api/pagination.md)

**Я DevOps инженер:**
→ [Архитектура](architecture/overview.md) → [Базы данных](architecture/database.md) → [Топология сервисов](architecture/services.md)

**Я фронтенд разработчик:**
→ [API Overview](api/overview.md) → [Пагинация](api/pagination.md) → [Аутентификация](operations/authentication.md)

**Я решаю проблему:**
→ [Архитектура](architecture/overview.md) → [Базы данных](architecture/database.md) → [Топология сервисов](architecture/services.md)

## 💡 Ключевые концепции

### Микросервисная архитектура
Система из 5 независимых сервисов, каждый со своей базой данных и ответственностью.

### Event-Driven
Сервисы общаются асинхронно через события (RabbitMQ), синхронно через RPC.

### Transactional Outbox
Надёжная публикация событий: событие отправляется только если основная БД транзакция успешна.

### 3NF Нормализация (v1.2.0)
Структурированная схема без транзитивных зависимостей. PostalArea, Customer, SensorParameter, Warehouse вынесены в справочники.

### Пагинация (v1.2.0)
Все GET-эндпоинты поддерживают offset/limit с возвратом total count.

## 📖 Документация на GitHub

**Repository:** [github.com/your-org/efko-kernel](https://github.com/your-org/efko-kernel)

**Исходники документации:** `/docs` в репозитории

**Contributes документации:** Pull Request в `/docs` → автоматическая сборка → публикация

## 🛠️ Технологический стек

- **Framework:** NestJS
- **Монорепо:** Nx
- **Брокер:** RabbitMQ
- **Databases:** PostgreSQL + MongoDB
- **ORM:** Prisma (SQL) + Mongoose (NoSQL)
- **Logging:** Pino + Loki
- **Tracing:** OpenTelemetry + Jaeger
- **Metrics:** Prometheus
- **Documentation:** MkDocs Material

## 🆘 Нужна помощь?

- **На простой вопрос?** → FAQ *(запланировано)*
- **Что-то сломалось?** → Диагностика *(запланировано)*
- **Нужно разобраться в коде?** → [Архитектура](architecture/overview.md)
- **Вопрос по API?** → [REST API](api/overview.md)

---

**Последнее обновление:** май 2026 (v1.2.0)  
**Версия документации:** 1.2.0  
**License:** MIT
