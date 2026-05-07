# API: Overview

Все REST API endpoints доступны через API Gateway. Единая точка входа для всех клиентов.

## Base URL

```
http://localhost:3000/api
```

Все примеры используют этот base URL.

## Format

- **Request:** JSON (`Content-Type: application/json`)
- **Response:** JSON
- **Date Format:** ISO 8601 (`YYYY-MM-DD` или `YYYY-MM-DDTHH:mm:ss.sssZ`)
- **UUID Format:** Стандартный UUID v4

## Аутентификация

**Механизм:** JWT (JSON Web Token)

**Получение токенов:**
```bash
POST /auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "accessToken": "eyJhbGc...",
  "refreshToken": "eyJhbGc...",
  "expiresIn": 3600
}
```

**Использование токена:**
```bash
GET /personnel/employees
-H "Authorization: Bearer <accessToken>"
```

**Обновление токена:**
```bash
POST /auth/refresh
{
  "refreshToken": "<refreshToken>"
}
```

## CSRF Защита

**Для браузерных клиентов:**
1. После логина сервер устанавливает cookie `XSRF-TOKEN`
2. Браузер должен читать эту cookie и передавать её в заголовке `X-CSRF-Token` для мутирующих запросов (POST, PATCH, DELETE)
3. GET запросы CSRF не требуют

**Для мобильных клиентов:**
- CSRF проверка не требуется (нет cookie механизма)

## Обработка ошибок

**Стандартная структура ошибки:**
```json
{
  "statusCode": 400,
  "message": [
    "поле «email» должно быть валидным email",
    "поле «password» должно быть минимум 8 символов"
  ],
  "error": "Bad Request"
}
```

**HTTP коды:**
| Код | Значение |
|-----|----------|
| 400 | Ошибка валидации |
| 401 | Не авторизован / невалидный токен |
| 403 | Недостаточно прав (role) |
| 404 | Ресурс не найден |
| 409 | Конфликт (дубликат, invalid state transition) |
| 429 | Rate limit превышен |
| 503 | Downstream сервис недоступен |

## Rate Limiting

Три профиля лимитов:
- **short:** 20 req / 1 sec
- **medium:** 100 req / 10 sec
- **long:** 500 req / 60 sec

Auth endpoints (`/auth/register`, `/auth/login`) имеют более строгие отдельные лимиты.

## Корреляция запросов

Каждый запрос имеет уникальный `requestId`:
- Автоматически генерируется через RequestIdMiddleware
- Можно передать вручную через заголовок `x-request-id`
- Пропагируется через все сервисы и логирование

```bash
curl -X GET http://localhost:3000/api/personnel/employees \
  -H "Authorization: Bearer <token>" \
  -H "x-request-id: my-unique-id"
```

## Версионирование

API не версионируется в URL. Все изменения backward-compatible или deprecation warning перед breaking change.

## Документация

**Swagger UI:**
```
GET /api/swagger
```

**Swagger JSON:**
```
GET /api/swagger/json
```

## Примеры интеграции

**cURL:**
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}'
```

**Fetch (JavaScript):**
```typescript
const response = await fetch('http://localhost:3000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'pass123'
  })
});

const { accessToken } = await response.json();

// Используем токен
fetch('http://localhost:3000/api/personnel/employees', {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});
```

## API Endpoints

**Personnel:**
- `POST /api/personnel/departments` — создать подразделение
- `GET /api/personnel/departments` — список подразделений
- `PATCH /api/personnel/departments/:id` — обновить подразделение
- `POST /api/personnel/positions` — создать должность
- `GET /api/personnel/positions` — список должностей
- `PATCH /api/personnel/positions/:id` — обновить должность
- `POST /api/personnel/employees` — принять сотрудника
- `GET /api/personnel/employees` — список сотрудников
- `PATCH /api/personnel/employees/:id` — обновить сотрудника
- `POST /api/personnel/employees/:id/terminate` — уволить сотрудника
- `POST /api/personnel/locations` — создать локацию
- `GET /api/personnel/locations` — список локаций
- `PATCH /api/personnel/locations/:id` — обновить локацию
- `POST /api/personnel/workstations` — создать рабочее место
- `GET /api/personnel/workstations` — список рабочих мест
- `GET /api/personnel/workstations/:id` — рабочее место по ID
- `POST /api/personnel/workstations/assign` — назначить сотрудника на рабочее место
- `POST /api/personnel/shift-templates` — создать шаблон смены
- `GET /api/personnel/shift-templates` — список шаблонов смен
- `PATCH /api/personnel/shift-templates/:id` — обновить шаблон смены
- `GET /api/personnel/production-line-views` — список производственных линий (view из Production Service)

**Auth:**
- `POST /api/auth/register` — регистрация
- `POST /api/auth/login` — вход
- `POST /api/auth/refresh` — обновить токен
- `GET /api/auth/users` — список пользователей (с пагинацией)

**Production:**
- `POST /api/production/products` — создать продукт
- `GET /api/production/products` — список продуктов
- `POST /api/production/orders` — создать заказ
- `GET /api/production/orders` — список заказов
- `GET /api/production/orders/:id` — заказ по ID
- `PATCH /api/production/orders/:id/status` — обновить статус заказа
- `POST /api/production/output` — зарегистрировать выпуск
- `GET /api/production/output` — список выпусков
- `POST /api/production/sales` — зарегистрировать продажу
- `GET /api/production/sales` — список продаж
- `GET /api/production/sales/summary` — сводка продаж
- `POST /api/production/inventory` — обновить остаток
- `GET /api/production/inventory` — остатки на складах
- `POST /api/production/quality` — зарегистрировать результат КК
- `GET /api/production/quality` — результаты КК
- `POST /api/production/sensors` — записать показание датчика
- `GET /api/production/sensors` — показания датчиков
- `GET /api/production/kpi` — KPI производства
- `GET /api/production/production-lines` — список производственных линий (с пагинацией)
- `POST /api/production/production-lines` — создать производственную линию
- `PUT /api/production/production-lines/:id` — обновить производственную линию

---

**Related:** [pagination.md](pagination.md), [../integration/client-guide.md](../integration/client-guide.md)
