# Архитектура: Топология сервисов

Каждый сервис отвечает за свой домен и имеет собственную БД (Database per Service паттерн).

## Gateway (`apps/gateway`)

**Роль:** HTTP API Gateway, единая точка входа для внешних клиентов

**Ответственность:**
- Валидация HTTP запросов (DTO, типы параметров)
- Аутентификация (JWT токены)
- Авторизация (RoleGuard по ролям)
- CSRF защита для браузерных клиентов
- Трансляция HTTP → RabbitMQ RPC в доменные сервисы
- Трансляция HTTP → HTTP для ETL (прокси)

**HTTP Endpoints:** `/api/*`  
**Swagger:** `/api/swagger`  
**Prisma:** Нет (только прокси)

## Auth Service (`apps/auth-service`)

**Роль:** Сервис идентификации и аутентификации

**Ответственность:**
- Регистрация пользователей
- Логин (JWT + Refresh Token)
- Обновление токенов (refresh)
- Валидация JWT
- Управление ролями (admin, manager, analyst, shift_manager, employee)

**RabbitMQ Queues:**
- `auth-service.commands.queue` (register, change password)
- `auth-service.queries.queue` (get-users, validate-token)

**Database:** PostgreSQL (User, RefreshToken, OutboxMessage)  
**Миграции:** `apps/auth-service/prisma/migrations`

## Personnel Service (`apps/personnel`)

**Роль:** Кадровый домен (HR)

**Ответственность:**
- Структура организации (подразделения, должности)
- Данные о сотрудниках (назначения, локации, статусы)
- Рабочие места и производственные линии
- Шаблоны смен
- Локации и почтовые индексы

**RabbitMQ Queues:**
- `personnel-service.commands.queue` (create/update employee, assign workstation)
- `personnel-service.queries.queue` (get employees, get locations, get workstations)
- `personnel-service.events.queue` (listens to events from other services)

**Database:** PostgreSQL  
**Key Entities:** Department, Employee, Position, Location, PostalArea, Workstation, ShiftScheduleTemplate  
**Миграции:** `apps/personnel/prisma/migrations`

## Production Service (`apps/production`)

**Роль:** Производственный домен

**Ответственность:**
- Каталог продуктов и компонентов
- Производственные заказы и выпуск
- Контроль качества и спецификации
- Управление датчиками и показаниями
- Складские остатки
- Продажи и клиенты
- KPI и аналитика

**RabbitMQ Queues:**
- `production-service.commands.queue` (create order, record quality, record sale)
- `production-service.queries.queue` (get products, get orders, get sensors, get kpi)
- `production-service.events.queue`

**Database:** PostgreSQL  
**Key Entities:** Product, ProductionOrder, QualityResult, QualitySpec, Sensor, SensorParameter, Sale, Customer, Inventory, Warehouse  
**Миграции:** `apps/production/prisma/migrations`

## ETL Service (`apps/etl`)

**Роль:** Интеграция с внешними системами

**Ответственность:**
- Парсинг файлов (Excel, JSON) из внешних источников
- Трансформация данных в каноничный формат
- Импорт в Personnel/Production БД
- Синхронизация данных между системами

**HTTP Endpoints:** `/api/v1/etl/*` (file upload, API endpoints)  
**Database:** MongoDB (RawImport, TransformationLog, GridFS для файлов)  
**Sources:** ZUP (1C-зарплата), ERP (1C-бизнес), MES, SCADA, LIMS

## Sync Service (`apps/sync`)

**Роль:** Event Listener для синхронизации данных между сервисами

**Ответственность:**
- Слушает события из всех сервисов (Personnel, Production, Auth, ETL)
- Обновляет Sync таблицы для отчётов и аналитики
- Синхронизирует данные между сервисами (например, employee ID в production)
- Поддерживает adapter registry для внешних систем

**RabbitMQ Queues:**
- Слушает все `*.events` exchanges

**Database:** PostgreSQL (Sync таблицы)  
**Примечание:** Sync Service — вспомогательный сервис, не входит в основные 5 доменных сервисов.

---

## Матрица взаимодействия

```
           Auth  Personnel  Production  ETL   Sync
Gateway     ↔       ↔          ↔        ↔     -
Auth        -       →          →        -     →
Personnel   -       -          →        -     →
Production  -       ←          -        -     →
ETL         -       ↔          ↔        -     →
Sync        -       -          -        -     -
```

↔ = RPC (синхронный)  
→ = Events (асинхронный)  
← = RPC запрос в обе стороны

---

**Related:** [communication.md](communication.md), [services/](../services/)
