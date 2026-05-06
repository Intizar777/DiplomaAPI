# Dashboard Analytics API

FastAPI сервис для агрегации и аналитики данных из микросервисного ядра ЭФКО.

## Возможности

- **Агрегация данных:** KPI производства, продажи, заказы, качество
- **Аналитика:** Сравнение периодов, тренды, сводки
- **Cron-синхронизация:** Автоматический сбор данных каждый час
- **PostgreSQL:** Хранение агрегированных данных

## Быстрый старт

### Локальная разработка

```bash
# 1. Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить переменные окружения
copy .env.example .env
# Отредактировать .env

# 4. Запустить миграции
alembic upgrade head

# 5. Запустить приложение
uvicorn app.main:app --reload
```

### Docker Compose

```bash
# 1. Настроить переменные окружения
copy .env.example .env

# 2. Запустить
docker-compose up --build
```

## API Endpoints

### KPI
- `GET /api/v1/kpi/current` — Текущие метрики
- `GET /api/v1/kpi/history` — История KPI
- `GET /api/v1/kpi/compare` — Сравнение периодов

### Sales
- `GET /api/v1/sales/summary` — Сводка продаж
- `GET /api/v1/sales/trends` — Тренды
- `GET /api/v1/sales/top-products` — Топ товаров
- `GET /api/v1/sales/regions` — По регионам

### Orders
- `GET /api/v1/orders/status-summary` — По статусам
- `GET /api/v1/orders/list` — Список заказов
- `GET /api/v1/orders/{id}` — Детали заказа

### Quality
- `GET /api/v1/quality/summary` — Сводка качества
- `GET /api/v1/quality/defect-trends` — Тренды дефектов
- `GET /api/v1/quality/lots` — Партии

### Sync
- `GET /api/v1/sync/status` — Статус синхронизации
- `POST /api/v1/sync/trigger` — Ручной запуск

### System
- `GET /health` — Health check
- `GET /docs` — Swagger UI

## Конфигурация

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `DATABASE_URL` | URL PostgreSQL | `postgresql+asyncpg://...` |
| `GATEWAY_URL` | URL Gateway API | `http://localhost:3000/api` |
| `GATEWAY_TOKEN` | JWT токен для Gateway | - |
| `SYNC_INTERVAL_MINUTES` | Интервал синхронизации | 60 |
| `RETENTION_DAYS` | Хранение данных | 90 |

## Структура проекта

```
dashboard_api/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Настройки
│   ├── database.py          # SQLAlchemy
│   ├── models/              # ORM модели
│   ├── schemas/             # Pydantic схемы
│   ├── routers/             # API endpoints
│   ├── services/            # Бизнес-логика
│   └── cron/                # Cron задачи
├── alembic/                 # Миграции
├── tests/                   # Тесты
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Лицензия

MIT
