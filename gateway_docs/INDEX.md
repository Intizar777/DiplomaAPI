# EFKO Kernel - Навигация по документации

Документация организована по темам. Каждый файл — 50-150 строк, сфокусирован на одной теме.

## 🚀 Начало работы

- [**Quickstart**](getting-started/quickstart.md) — 5 минут до первого запуска
- [**Настройка окружения**](getting-started/setup.md) — Docker, зависимости, env vars
- [**Первый шаг**](getting-started/first-request.md) — Первый HTTP запрос в API

## 🏗️ Архитектура

- [**Обзор системы**](architecture/overview.md) — Сервисы и библиотеки
- [**Топология сервисов**](architecture/services.md) — Какой сервис за что отвечает
- [**RabbitMQ коммуникация**](architecture/communication.md) — RPC, события, exchanges
- [**Базы данных**](architecture/database.md) — PostgreSQL, MongoDB, Prisma
- [**3NF Нормализация**](architecture/3nf-normalization.md) — Структурные изменения v1.2.0

## 📊 Модели данных

- [**Auth models**](data/auth-models.md) — User, RefreshToken
- [**Personnel models**](data/personnel-models.md) — Department, Employee, Workstation, Location
- [**Production models**](data/production-models.md) — Product, Order, Sale, Quality, Sensor
- [**ETL models**](data/etl-models.md) — RawImport, TransformationLog, GridFS
- [**Полный справочник**](data/all-models.md) — Все сущности со всеми полями

## 🔌 REST API

- [**API Overview**](api/overview.md) — Base URL, аутентификация, обработка ошибок
- [**Пагинация & фильтрация**](api/pagination.md) — offset, limit, фильтры
- [**Auth endpoints**](api/auth-endpoints.md) — register, login, refresh, users
- [**Personnel endpoints**](api/personnel-endpoints.md) — departments, employees, workstations
- [**Production endpoints**](api/production-endpoints.md) — products, orders, sales, quality, sensors
- [**ETL endpoints**](api/etl-endpoints.md) — импорт из внешних систем

## 🔐 Безопасность

- [**Аутентификация**](operations/authentication.md) — JWT, токены, refresh
- [**Авторизация**](operations/authorization.md) — Роли, RoleGuard, доступы
- [**CSRF защита**](operations/csrf-protection.md) — Cookies, X-CSRF-Token
- [**Лучшие практики**](operations/security-best-practices.md) — Что делать и не делать

## ⚙️ Эксплуатация

- [**Диагностика**](operations/troubleshooting.md) — Типовые проблемы и решения
- [**Логирование**](operations/logging.md) — Pino, структурированные логи, Loki
- [**Health checks**](operations/health-checks.md) — Как проверить что всё работает
- [**Мониторинг**](operations/monitoring.md) — Prometheus, Grafana, OpenTelemetry

## 📱 Интеграция

- [**Гайд для клиентов**](integration/client-guide.md) — Веб и мобильные приложения
- [**События**](integration/events.md) — Доменные события, подписка, обработка
- [**Интеграция с 1C**](integration/1c-integration.md) — ZUP, ERP, синхронизация
- [**ETL pipeline**](integration/etl-pipeline.md) — Импорт файлов, трансформация

## 🔗 Сервисы

- [**Auth Service**](services/auth-service.md) — Аутентификация, пользователи, JWT
- [**Gateway**](services/gateway.md) — API Gateway, прокси, валидация
- [**Personnel Service**](services/personnel.md) — Кадры, структура, подразделения
- [**Production Service**](services/production.md) — Производство, качество, KPI
- [**ETL Service**](services/etl.md) — Интеграция с внешними системами

## 📚 Справочники

- [**Глоссарий**](reference/glossary.md) — Определение терминов
- [**FAQ**](reference/faq.md) — Частые вопросы
- [**Changelog**](reference/changelog.md) — История версий
- [**Внешние ресурсы**](reference/resources.md) — Ссылки на инструменты

## 📖 Как пользоваться этой документацией

**Структура как "чемодан с кубиками":**
- Ищите нужную тему по категориям выше
- Каждый файл автономен (не надо читать всё подряд)
- Содержит определение, примеры, ссылки на соответствующие гайды

**Стартовые маршруты:**
- 👨‍💻 **Новый разработчик:** Quickstart → Архитектура → API
- 🔧 **DevOps/Деплой:** Setup → Database → Monitoring
- 📱 **Фронтенд интеграция:** Client Guide → API Overview → Auth
- 🛠️ **Проблема в боевой:** Troubleshooting → Logging → Monitoring

---

**Последнее обновление:** май 2026 (v1.2.0 с 3NF нормализацией)  
**Версия системы:** 1.2.0  
**Лучшие практики:** Всегда обновляй docs когда меняешь архитектуру или API
