# API Reference

Полный справочник по REST API EFKO Kernel с примерами запросов и ответов.

## Общие принципы

### Base URL

```
http://localhost:3000/api
```

Все эндпоинты доступны относительно этого базового URL.

### Формат данных

- **Request Format:** JSON (`Content-Type: application/json`)
- **Response Format:** JSON
- **Date Format:** ISO 8601 (`YYYY-MM-DD` или `YYYY-MM-DDTHH:mm:ss.sssZ`)
- **UUID Format:** Стандартный UUID v4

### Аутентификация

Система использует JWT токены:

- **Access Token:** Короткоживущий токен для аутентификации запросов
- **Refresh Token:** Долгоживущий токен для обновления сессии

Access токен передается в заголовке:

```
Authorization: Bearer <accessToken>
```

### CSRF Защита

**Для браузерных клиентов:**
- После логина устанавливается cookie `XSRF-TOKEN`
- Браузер должен читать эту cookie и передавать её значение в заголовке `X-CSRF-Token` при каждом мутирующем запросе (POST, PATCH, DELETE)
- GET, HEAD, OPTIONS запросы CSRF не проверяются

**Для мобильных клиентов:**
- CSRF проверка автоматически пропускается (нет cookie механизма)
- Refresh токен передается в теле запроса при обновлении сессии

### Пагинация

Список-эндпоинты поддерживают пагинацию через параметры:

- `offset` — Смещение от начала (default: 0)
- `limit` — Количество записей на странице (default: 20, max: 100 для personnel, 1000 для production)

Все список-ответы возвращают:
```typescript
{
  items: Array<T>;
  total: number; // Общее количество элементов (с учётом фильтров)
}
```

#### Примеры

```bash
# Первая страница (20 элементов)
GET /api/personnel/locations?offset=0&limit=20

# Вторая страница
GET /api/personnel/locations?offset=20&limit=20

# С фильтром и пагинацией
GET /api/personnel/workstations?locationId=<id>&offset=0&limit=50
```

### Rate Limiting

Три профиля лимитов применяются глобально:

| Профиль | Лимит |
|---------|-------|
| short | 20 req / 1 s |
| medium | 100 req / 10 s |
| long | 500 req / 60 s |

Auth endpoints (`/auth/register`, `/auth/login`) имеют более строгие отдельные лимиты.

### Корреляция запросов

Каждый запрос имеет `requestId` для трассировки:
- Автоматически генерируется через `RequestIdMiddleware`
- Может быть передан вручную через заголовок `x-request-id`
- Пропагируется через все сервисы

### Обработка ошибок

#### Стандартная структура ошибки

```json
{
  "statusCode": 400,
  "message": [
    "поле «parentId» должно быть валидным UUID",
    "поле «code» должно быть строкой"
  ],
  "error": "Bad Request"
}
```

> **Важно:** В системе включен строгий режим валидации (`forbidNonWhitelisted: true`). Это означает, что если в запросе (Query или Body) переданы поля, не описанные в соответствующем DTO, сервер вернет ошибку `400 Bad Request`.

#### Локализация сообщений

Все системные сообщения о валидации переведены на русский язык и имеют стандартизированный формат:
- Поля Query/Body: `поле «название» должно быть ...`
- Параметры пути (Params): `параметр «название» должен быть ...`

#### Типы валидации

| Тип | Сообщение (пример) |
|-----|-------------------|
| UUID | `поле «productId» должно быть валидным UUID` |
| ObjectId (ETL) | `параметр «id» должен быть валидным ObjectId (24 hex символов)` |
| Enum | `поле «status» должно быть одним из допустимых значений` |
| String | `поле «code» должно быть строкой` |
| Date | `поле «from» должно быть датой в формате ISO 8601` |


#### HTTP коды ошибок

| Код | Описание |
|-----|----------|
| `400` | Ошибка валидации |
| `401` | Не авторизован / невалидный токен |
| `403` | Недостаточно прав |
| `404` | Ресурс не найден |
| `409` | Конфликт (дубликат, недопустимый переход) |
| `429` | Rate limit превышен |
| `503` | Downstream сервис недоступен |
| `504` | Downstream сервис не ответил вовремя (timeout) |

---

## Auth API

Эндпоинты аутентификации и управления пользователями.

### POST /auth/register

Регистрация нового пользователя.

**Аутентификация:** Не требуется  
**CSRF:** Требуется для браузера  
**Rate Limit:** Отдельный строгий лимит

#### Request Body

```typescript
{
  email: string;        // Email пользователя
  password: string;     // Пароль (минимум 8 символов)
  fullName: string;     // Полное имя (формат: Фамилия Имя Отчество)
  role: UserRole;       // Роль
  employeeId?: string;  // UUID сотрудника (опционально)
}
```

#### Response

```typescript
{
  id: string;           // UUID пользователя
  email: string;        // Email
  fullName: string;     // Полное имя
  role: UserRole;       // Роль
  employeeId: string | null; // ID сотрудника (если привязан)
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "email": "ivan@example.com",
    "password": "SecurePass123!",
    "fullName": "Иванов Иван Иванович",
    "role": "admin"
  }'
```

#### Пример ответа

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "ivan@example.com",
  "fullName": "Иванов Иван",
  "role": "admin",
  "employeeId": null
}
```

#### Ошибки

- `400` — Некорректный формат email или имени
- `409` — Email уже занят (`USER_ALREADY_EXISTS`)

---

### POST /auth/login

Вход в систему.

**Аутентификация:** Не требуется  
**CSRF:** Требуется для браузера  
**Rate Limit:** Отдельный строгий лимит

#### Request Body

```typescript
{
  email: string;
  password: string;
}
```

#### Response

```typescript
{
  accessToken: string;   // JWT access токен
  refreshToken: string;  // Refresh токен
}
```

#### Cookies

Устанавливаются в ответе:
- `refreshToken` — httpOnly cookie для обновления сессии
- `XSRF-TOKEN` — читаемый JS cookie с CSRF токеном

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ivan@example.com",
    "password": "SecurePass123!"
  }' \
  -c cookies.txt
```

#### Пример ответа

```json
{
  "accessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Ошибки

- `400` — Некорректный формат
- `401` — Невалидные учетные данные или аккаунт деактивирован (`INVALID_CREDENTIALS`)

---

### GET /auth/me

Получить профиль текущего пользователя. Поле `employeeId` заполняется из JWT payload (включается при логине и refresh-session).

**Аутентификация:** Bearer accessToken  
**CSRF:** Не требуется

#### Response

```typescript
{
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  employeeId: string | null;
}
```

#### Пример запроса

```bash
curl -X GET http://localhost:3000/api/auth/me \
  -H "Authorization: Bearer <accessToken>"
```

#### Пример ответа

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "ivan@example.com",
  "fullName": "Иванов Иван",
  "role": "admin",
  "employeeId": "d4e5f6a7-b8c9-0123-defa-234567890123"
}
```

#### Ошибки

- `401` — Токен недействителен или истек
- `404` — Пользователь не найден или деактивирован (`USER_NOT_FOUND`)

---

### POST /auth/refresh-session

Обновить сессию по refresh токену.

**Аутентификация:** Refresh токен из httpOnly cookie `refreshToken`  
**CSRF:** Требуется для браузера (значение cookie `XSRF-TOKEN` в заголовке `X-CSRF-Token`)

> Endpoint читает refresh токен исключительно из httpOnly cookie. Клиенты без поддержки cookie (например, мобильные без WebView) не могут использовать этот endpoint в текущей реализации.

#### Response

```typescript
{
  accessToken: string;
  refreshToken: string;
}
```

#### Cookies

Обновляются в ответе:
- `refreshToken` — новый refresh токен (rotation)
- `XSRF-TOKEN` — новый CSRF токен

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/auth/refresh-session \
  -H "X-CSRF-Token: <value from XSRF-TOKEN cookie>" \
  -b cookies.txt \
  -c cookies.txt
```

#### Пример ответа

```json
{
  "accessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Ошибки

- `401` — Refresh токен отсутствует, отозван (`REFRESH_TOKEN_REVOKED`), истек (`REFRESH_TOKEN_EXPIRED`)

---

### POST /auth/logout

Завершение сессии.

**Аутентификация:** Bearer accessToken  
**CSRF:** Требуется для браузера

#### Response

```typescript
{
  success: boolean;
}
```

#### Cookies

Очищаются:
- `refreshToken`
- `XSRF-TOKEN`

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/auth/logout \
  -H "Authorization: Bearer <accessToken>" \
  -H "X-CSRF-Token: <value from XSRF-TOKEN cookie>" \
  -b cookies.txt \
  -c cookies.txt
```

#### Пример ответа

```json
{
  "success": true
}
```

---

### GET /users

Список всех пользователей.

**Аутентификация:** Bearer accessToken  
**Роль:** Требуется аутентификация; ограничение по роли ADMIN в текущем коде закомментировано  
**CSRF:** Не требуется

#### Response

```typescript
{
  users: Array<{
    id: string;
    email: string;
    fullName: string;
    role: UserRole;
    isActive: boolean;
    employeeId: string | null;
  }>;
  total: number;
}
```

#### Пример запроса

```bash
curl -X GET http://localhost:3000/api/users \
  -H "Authorization: Bearer <accessToken>"
```

#### Ошибки

- `403` — Недостаточно прав

---

### PATCH /users/:userId

Обновить данные пользователя.

**Аутентификация:** Bearer accessToken  
**Роль:** ADMIN (требуется)  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  email?: string;
  fullName?: string;
  role?: UserRole;
  employeeId?: string | null;
}
```

#### Response

```typescript
{
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  isActive: boolean;
  employeeId: string | null;
}
```

#### Пример запроса

```bash
curl -X PATCH http://localhost:3000/api/users/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "fullName": "Иванов Иван Петрович"
  }'
```

#### Ошибки

- `403` — Недостаточно прав
- `404` — Пользователь не найден

---

### POST /users/deactivate

Деактивировать пользователя.

**Аутентификация:** Bearer accessToken  
**Роль:** ADMIN (требуется)  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  userId: string;
}
```

#### Response

```typescript
{
  id: string;
  isActive: boolean;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/users/deactivate \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "userId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

---

## Personnel API

Управление кадровыми данными: почтовые зоны, подразделения, должности, сотрудники, шаблоны смен, локации, производственные линии, рабочие места.

### POST /personnel/postal-areas

Создать почтовую зону.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  postalCode: string;  // Почтовый индекс (уникальный)
  city: string;        // Город
  region: string;      // Регион
}
```

#### Response

```typescript
{
  id: string;          // UUID почтовой зоны
  postalCode: string;
  city: string;
  region: string;
  createdAt: string;   // ISO datetime
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/personnel/postal-areas \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "postalCode": "119991",
    "city": "Москва",
    "region": "Москва"
  }'
```

#### Ошибки

- `400` — Ошибка валидации
- `409` — Почтовый индекс уже существует (`POSTAL_CODE_ALREADY_EXISTS`)

---

### GET /personnel/postal-areas

Список почтовых зон с пагинацией.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER, ANALYST  
**CSRF:** Не требуется

#### Query Parameters

- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 20, min: 1, max: 100)

#### Response

```typescript
{
  postalAreas: Array<{
    id: string;
    postalCode: string;
    city: string;
    region: string;
    createdAt: string;
  }>;
  total: number; // Общее количество записей
}
```

#### Пример запроса

```bash
curl -X GET "http://localhost:3000/api/personnel/postal-areas?offset=0&limit=20" \
  -H "Authorization: Bearer <accessToken>"
```

---

### POST /personnel/locations

Создать локацию (офис или склад).

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  name: string;
  code: string;
  type: LocationType; // OFFICE | FACTORY
  country: string;
  region: string;
  city: string;
  postalCode: string;
  streetAddress: string;
  sourceSystemId?: string | null;
}
```

#### Response

```typescript
{
  id: string;
  name: string;
  code: string;
  type: LocationType;
  country: string;
  region: string;
  city: string;
  postalCode: string;
  streetAddress: string;
  sourceSystemId: string | null;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/personnel/locations \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "name": "Московский офис",
    "code": "MSK-01",
    "type": "office",
    "country": "Россия",
    "region": "Москва",
    "city": "Москва",
    "postalCode": "119991",
    "streetAddress": "ул. Ленина, 1"
  }'
```

#### Ошибки

- `400` — Ошибка валидации
- `409` — Код уже занят (`LOCATION_CODE_ALREADY_EXISTS`)

---

### GET /personnel/locations

Список локаций с опциональной фильтрацией.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER, ANALYST  
**CSRF:** Не требуется

#### Query Parameters

- `code?` — Код локации (точное совпадение)
- `type?` — Тип локации (OFFICE | FACTORY)
- `city?` — Город
- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 20, min: 1, max: 100)

#### Response

```typescript
{
  locations: Array<{
    id: string;
    name: string;
    code: string;
    type: LocationType;
    country: string;
    region: string;
    city: string;
    postalCode: string;
    streetAddress: string;
    sourceSystemId: string | null;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

#### Пример запроса

```bash
curl -X GET "http://localhost:3000/api/personnel/locations?type=OFFICE" \
  -H "Authorization: Bearer <accessToken>"
```

---

### PATCH /personnel/locations/:id

Обновить локацию.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  name?: string;
  type?: LocationType;
  address?: {
    country?: string;
    region?: string;
    city?: string;
    postalCode?: string;
    streetAddress?: string;
  };
}
```

#### Response

```typescript
{
  id: string;
  name: string;
  code: string;
  type: LocationType;
  country: string;
  region: string;
  city: string;
  postalCode: string;
  streetAddress: string;
  sourceSystemId: string | null;
}
```

#### Ошибки

- `404` — Локация не найдена (`LOCATION_NOT_FOUND`)

---

### POST /personnel/production-lines

Создать производственную линию.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  name: string;
  code: string;
  locationId: string;
  description?: string | null;
  capacity?: number | null;
  sourceSystemId?: string | null;
}
```

#### Response

```typescript
{
  id: string;
  name: string;
  code: string;
  locationId: string;
  description: string | null;
  capacity: number | null;
  isActive: boolean;
  sourceSystemId: string | null;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/personnel/production-lines \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "name": "Линия упаковки А",
    "code": "PACK-A",
    "locationId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "description": "Высокоскоростная линия упаковки",
    "capacity": 5000
  }'
```

#### Ошибки

- `404` — Локация не найдена (`LOCATION_NOT_FOUND`)
- `400` — Тип локации не поддерживает линии (`LOCATION_TYPE_MISMATCH`)
- `409` — Код уже занят (`PRODUCTION_LINE_CODE_ALREADY_EXISTS`)

---

### GET /personnel/production-lines

Список производственных линий с опциональной фильтрацией.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER, ANALYST  
**Rate Limit:** long (10 000 req / 60 s)  
**CSRF:** Не требуется

#### Query Parameters

- `code?` — Код производственной линии (точное совпадение)
- `locationId?` — UUID локации (фильтрация по локации)
- `isActive?` — Активна ли линия (boolean)
- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 20, min: 1, max: 100)

#### Response

```typescript
{
  productionLines: Array<{
    id: string;
    name: string;
    code: string;
    locationId: string;
    description: string | null;
    capacity: number | null;
    isActive: boolean;
    sourceSystemId: string | null;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

#### Пример запроса

```bash
# Фильтрация по коду
curl -X GET "http://localhost:3000/api/personnel/production-lines?code=PACK-A" \
  -H "Authorization: Bearer <accessToken>"

# Фильтрация по локации
curl -X GET "http://localhost:3000/api/personnel/production-lines?locationId=a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -H "Authorization: Bearer <accessToken>"

# Только активные линии
curl -X GET "http://localhost:3000/api/personnel/production-lines?isActive=true" \
  -H "Authorization: Bearer <accessToken>"

# Комбинированная фильтрация с пагинацией
curl -X GET "http://localhost:3000/api/personnel/production-lines?locationId=a1b2c3d4-e5f6-7890-abcd-ef1234567890&isActive=true&offset=0&limit=10" \
  -H "Authorization: Bearer <accessToken>"

# Все производственные линии (без фильтров)
curl -X GET "http://localhost:3000/api/personnel/production-lines" \
  -H "Authorization: Bearer <accessToken>"
```

---

### GET /personnel/production-lines/:id

Получить производственную линию по ID.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER, ANALYST  
**Rate Limit:** long (10 000 req / 60 s)  
**CSRF:** Не требуется

#### Response

```typescript
{
  id: string;
  name: string;
  code: string;
  locationId: string;
  description: string | null;
  capacity: number | null;
  isActive: boolean;
  sourceSystemId: string | null;
}
```

#### Пример запроса

```bash
curl -X GET "http://localhost:3000/api/personnel/production-lines/a7b8c9d0-e1f2-3456-abcd-567890123456" \
  -H "Authorization: Bearer <accessToken>"
```

#### Ошибки

- `404` — Производственная линия не найдена (`PRODUCTION_LINE_NOT_FOUND`)

---

### POST /personnel/workstations

Создать рабочее место.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  name: string;
  code: string;
  locationId: string;
  productionLineId?: string | null;
  workstationType: WorkstationType; // ASSEMBLY | PACKAGING | QUALITY_CONTROL | STORAGE | OFFICE
  sourceSystemId?: string | null;
}
```

#### Response

```typescript
{
  id: string;
  name: string;
  code: string;
  locationId: string;
  productionLineId: string | null;
  workstationType: WorkstationType;
  sourceSystemId: string | null;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/personnel/workstations \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "name": "Рабочее место упаковщика №1",
    "code": "WS-PACK-001",
    "locationId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "productionLineId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "workstationType": "packaging"
  }'
```

#### Ошибки

- `404` — Локация или производственная линия не найдены (`LOCATION_NOT_FOUND`, `PRODUCTION_LINE_NOT_FOUND`)
- `409` — Код уже занят (`WORKSTATION_CODE_ALREADY_EXISTS`)
- `400` — Ошибка назначения (`WORKSTATION_ASSIGNMENT_ERROR`)

---

### GET /personnel/workstations

Список рабочих мест с опциональной фильтрацией.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER, ANALYST  
**Rate Limit:** long (10 000 req / 60 s)  
**CSRF:** Не требуется

#### Query Parameters

- `code?` — Код рабочего места (точное совпадение)
- `locationId?` — UUID локации (фильтрация по локации)
- `productionLineId?` — UUID производственной линии (фильтрация по линии)
- `workstationType?` — Тип рабочего места (ASSEMBLY, PACKAGING, QUALITY_CONTROL, STORAGE, OFFICE)
- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 20, min: 1, max: 100)

#### Response

```typescript
{
  workstations: Array<{
    id: string;
    name: string;
    code: string;
    locationId: string;
    productionLineId: string | null;
    workstationType: WorkstationType;
    sourceSystemId: string | null;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

#### Пример запроса

```bash
# Фильтрация по коду
curl -X GET "http://localhost:3000/api/personnel/workstations?code=WS-PACK-001" \
  -H "Authorization: Bearer <accessToken>"

# Фильтрация по локации
curl -X GET "http://localhost:3000/api/personnel/workstations?locationId=a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -H "Authorization: Bearer <accessToken>"

# Фильтрация по типу
curl -X GET "http://localhost:3000/api/personnel/workstations?workstationType=PACKAGING" \
  -H "Authorization: Bearer <accessToken>"

# Рабочие места в определённой производственной линии
curl -X GET "http://localhost:3000/api/personnel/workstations?productionLineId=c3d4e5f6-a7b8-9012-cdef-123456789012" \
  -H "Authorization: Bearer <accessToken>"

# Комбинированная фильтрация с пагинацией
curl -X GET "http://localhost:3000/api/personnel/workstations?locationId=a1b2c3d4-e5f6-7890-abcd-ef1234567890&workstationType=PACKAGING&offset=0&limit=10" \
  -H "Authorization: Bearer <accessToken>"

# Все рабочие места (без фильтров)
curl -X GET "http://localhost:3000/api/personnel/workstations" \
  -H "Authorization: Bearer <accessToken>"
```

---

### GET /personnel/workstations/:id

Получить рабочее место по ID.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER, ANALYST  
**Rate Limit:** long (10 000 req / 60 s)  
**CSRF:** Не требуется

#### Response

```typescript
{
  id: string;
  name: string;
  code: string;
  locationId: string;
  productionLineId: string | null;
  workstationType: WorkstationType;
  sourceSystemId: string | null;
}
```

#### Пример запроса

```bash
curl -X GET "http://localhost:3000/api/personnel/workstations/b8c9d0e1-f234-4567-abcd-678901234567" \
  -H "Authorization: Bearer <accessToken>"
```

#### Ошибки

- `404` — Рабочее место не найдено (`WORKSTATION_NOT_FOUND`)

---

### POST /personnel/workstations/assign

Назначить сотрудника на рабочее место.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  employeeId: string;
  workstationId: string;
}
```

#### Response

```typescript
{
  employeeId: string;
  workstationId: string;
  locationId: string;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/personnel/workstations/assign \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "employeeId": "d4e5f6a7-b8c9-0123-defa-234567890123",
    "workstationId": "e5f6a7b8-c9d0-1234-efab-567890123456"
  }'
```

#### Ошибки

- `404` — Сотрудник или рабочее место не найдены (`EMPLOYEE_NOT_FOUND`, `WORKSTATION_NOT_FOUND`)
- `400` — Ошибка назначения (`WORKSTATION_ASSIGNMENT_ERROR`)

---

### POST /personnel/departments

Создать подразделение.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  name: string;
  code: string;
  type: DepartmentType;
  parentId?: string | null;
  headEmployeeId?: string | null;
}
```

#### Response

```typescript
{
  id: string;
  name: string;
  code: string;
  type: DepartmentType;
  parentId: string | null;
  headEmployeeId: string | null;
  sourceSystemId: string | null;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/personnel/departments \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "name": "Производственный цех №1",
    "code": "PROD-001",
    "type": "division"
  }'
```

#### Ошибки

- `400` — Ошибка валидации
- `409` — Код уже занят (`DEPARTMENT_CODE_ALREADY_EXISTS`)

---

### GET /personnel/departments

Список подразделений с опциональной фильтрацией.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER, ANALYST  
**CSRF:** Не требуется

#### Query Parameters

- `code?` — Код подразделения (точное совпадение)
- `type?` — Тип подразделения (DIVISION | DEPARTMENT | SECTION | UNIT)
- `parentId?` — UUID родительского подразделения (фильтрация по иерархии)
- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 20, min: 1, max: 100)

#### Response

```typescript
{
  departments: Array<{
    id: string;
    name: string;
    code: string;
    type: DepartmentType;
    parentId: string | null;
    headEmployeeId: string | null;
    sourceSystemId: string | null;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

#### Пример запроса

```bash
# Фильтрация по типу (DIVISION, DEPARTMENT, SECTION, UNIT)
curl -X GET "http://localhost:3000/api/personnel/departments?type=DIVISION" \
  -H "Authorization: Bearer <accessToken>"

# Фильтрация по коду
curl -X GET "http://localhost:3000/api/personnel/departments?code=PROD-001" \
  -H "Authorization: Bearer <accessToken>"

# Комбинированная фильтрация
curl -X GET "http://localhost:3000/api/personnel/departments?type=DIVISION&code=PROD-001" \
  -H "Authorization: Bearer <accessToken>"

# Все подразделения (без фильтров)
curl -X GET "http://localhost:3000/api/personnel/departments" \
  -H "Authorization: Bearer <accessToken>"
```

---

### PATCH /personnel/departments/:id

Обновить подразделение.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  name?: string;
  type?: DepartmentType;
  parentId?: string | null;
  headEmployeeId?: string | null;
}
```

#### Response

```typescript
{
  id: string;
  name: string;
  code: string;
  type: DepartmentType;
  parentId: string | null;
  headEmployeeId: string | null;
}
```

#### Пример запроса

```bash
curl -X PATCH http://localhost:3000/api/personnel/departments/<id> \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "headEmployeeId": "d4e5f6a7-b8c9-0123-defa-234567890123"
  }'
```

---

### POST /personnel/positions

Создать должность.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  title: string;
  code: string;
  departmentId: string;
}
```

#### Response

```typescript
{
  id: string;
  title: string;
  code: string;
  departmentId: string;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/personnel/positions \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "title": "Оператор станка",
    "code": "OP-001",
    "departmentId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

#### Ошибки

- `404` — Подразделение не найдено (`DEPARTMENT_NOT_FOUND`)
- `409` — Код должности уже занят (`POSITION_CODE_ALREADY_EXISTS`)

---

### GET /personnel/positions

Список должностей.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER, ANALYST  
**CSRF:** Не требуется

#### Query Parameters

- `departmentId?` — UUID подразделения
- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 20, min: 1, max: 100)

#### Response

```typescript
{
  positions: Array<{
    id: string;
    title: string;
    code: string;
    departmentId: string;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

---

### PATCH /personnel/positions/:id

Обновить должность.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  title?: string;
  departmentId?: string;
}
```

#### Response

```typescript
{
  id: string;
  title: string;
  code: string;
  departmentId: string;
}
```

---

### POST /personnel/employees

Создать сотрудника.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  personnelNumber: string;
  fullName: string;
  dateOfBirth: string; // ISO date
  positionId: string;
  locationId?: string | null;
  workstationId?: string | null;
  hireDate: string; // ISO date
  employmentType: EmploymentType;
  sourceSystemId?: string | null;
}
```

#### Response

```typescript
{
  id: string;
  personnelNumber: string;
  fullName: string;
  positionId: string;
  locationId: string | null;
  workstationId: string | null;
  status: EmployeeStatus;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/personnel/employees \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "personnelNumber": "EMP-0001",
    "fullName": "Иванов Иван Иванович",
    "dateOfBirth": "1985-05-15",
    "positionId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "hireDate": "2025-01-01",
    "employmentType": "main"
  }'
```

#### Ошибки

- `400` — Некорректное имя (`INVALID_FULL_NAME`)
- `404` — Подразделение или должность не найдены

---

### GET /personnel/employees

Список сотрудников с опциональной фильтрацией.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER, ANALYST  
**CSRF:** Не требуется

#### Query Parameters

- `departmentId?` — UUID подразделения
- `positionId?` — UUID должности
- `status?` — Статус (active, terminated, on_leave)
- `employmentType?` — Тип занятости (main, part_time)
- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 20, min: 1, max: 100)

#### Response

```typescript
{
  employees: Array<{
    id: string;
    personnelNumber: string;
    fullName: string;
    dateOfBirth: string;
    departmentId: string;
    positionId: string;
    locationId: string | null;
    workstationId: string | null;
    hireDate: string;
    terminationDate: string | null;
    employmentType: EmploymentType;
    status: EmployeeStatus;
    sourceSystemId: string | null;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

#### Пример запроса

```bash
# Фильтрация по подразделению
curl -X GET "http://localhost:3000/api/personnel/employees?departmentId=a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -H "Authorization: Bearer <accessToken>"

# Фильтрация по статусу
curl -X GET "http://localhost:3000/api/personnel/employees?status=active" \
  -H "Authorization: Bearer <accessToken>"

# Комбинированная фильтрация
curl -X GET "http://localhost:3000/api/personnel/employees?departmentId=a1b2c3d4-e5f6-7890-abcd-ef1234567890&status=active&employmentType=main" \
  -H "Authorization: Bearer <accessToken>"

# Все сотрудники (без фильтров)
curl -X GET "http://localhost:3000/api/personnel/employees" \
  -H "Authorization: Bearer <accessToken>"
```

---

### PATCH /personnel/employees/:id

Обновить данные сотрудника.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  fullName?: string;
  positionId?: string;
  locationId?: string | null;
  workstationId?: string | null;
  employmentType?: EmploymentType;
  dateOfBirth?: string; // ISO date
}
```

#### Response

```typescript
{
  id: string;
  personnelNumber: string;
  fullName: string;
  dateOfBirth: string;
  positionId: string;
  locationId: string | null;
  workstationId: string | null;
  hireDate: string;
  terminationDate: string | null;
  employmentType: EmploymentType;
  status: EmployeeStatus;
  sourceSystemId: string | null;
}
```

---

### POST /personnel/employees/:id/terminate

Уволить сотрудника.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  terminationDate?: string; // ISO date, опционально
}
```

#### Response

```typescript
{
  id: string;
  status: EmployeeStatus;
  terminationDate: string;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/personnel/employees/<id>/terminate \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "terminationDate": "2025-06-30"
  }'
```

#### Ошибки

- `409` — Сотрудник уже уволен (`EMPLOYEE_ALREADY_TERMINATED`)

---

### POST /personnel/shift-templates

Создать шаблон смены.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  name: string;
  shiftType: ShiftType;
  startTime: string; // HH:MM
  endTime: string; // HH:MM
  workDaysPattern: string; // Бинарная строка, например "1111100"
}
```

#### Response

```typescript
{
  id: string;
  name: string;
  shiftType: ShiftType;
  startTime: string;
  endTime: string;
  workDaysPattern: string;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/personnel/shift-templates \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "name": "Дневная смена",
    "shiftType": "day_shift",
    "startTime": "08:00",
    "endTime": "20:00",
    "workDaysPattern": "1111100"
  }'
```

---

### GET /personnel/shift-templates

Список шаблонов смен.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER, ANALYST  
**CSRF:** Не требуется

#### Response

```typescript
{
  templates: Array<{
    id: string;
    name: string;
    shiftType: ShiftType;
    startTime: string;
    endTime: string;
    workDaysPattern: string;
  }>;
  total: number;
}
```

---

### PATCH /personnel/shift-templates/:id

Обновить шаблон смены.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, SHIFT_MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  name?: string;
  shiftType?: ShiftType;
  startTime?: string;
  endTime?: string;
  workDaysPattern?: string;
}
```

#### Response

```typescript
{
  id: string;
  name: string;
  shiftType: ShiftType;
  startTime: string;
  endTime: string;
  workDaysPattern: string;
}
```

---

## Production API

Управление производственными данными: клиенты, склады, спецификации качества, продукты, заказы, выпуск, качество, датчики, KPI.

### POST /production/customers

Создать клиента.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  name: string;  // Название клиента
}
```

#### Response

```typescript
{
  id: string;           // UUID клиента
  name: string;
  createdAt: string;    // ISO datetime
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/production/customers \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "name": "ООО Торговый центр"
  }'
```

#### Ошибки

- `400` — Ошибка валидации

---

### GET /production/customers

Список клиентов с пагинацией.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, ANALYST  
**CSRF:** Не требуется

#### Query Parameters

- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 20, min: 1, max: 1000)

#### Response

```typescript
{
  customers: Array<{
    id: string;
    name: string;
    createdAt: string;
  }>;
  total: number; // Общее количество записей
}
```

#### Пример запроса

```bash
curl -X GET "http://localhost:3000/api/production/customers?offset=0&limit=20" \
  -H "Authorization: Bearer <accessToken>"
```

---

### POST /production/warehouses

Создать склад.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  name: string;   // Название склада
  code: string;   // Уникальный код склада
}
```

#### Response

```typescript
{
  id: string;      // UUID склада
  name: string;
  code: string;
  createdAt: string; // ISO datetime
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/production/warehouses \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "name": "Основной склад",
    "code": "WH-001"
  }'
```

#### Ошибки

- `400` — Ошибка валидации
- `409` — Код склада уже занят (`WAREHOUSE_CODE_ALREADY_EXISTS`)

---

### GET /production/warehouses

Список складов с пагинацией.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, ANALYST  
**CSRF:** Не требуется

#### Query Parameters

- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 20, min: 1, max: 1000)

#### Response

```typescript
{
  warehouses: Array<{
    id: string;
    name: string;
    code: string;
    createdAt: string;
  }>;
  total: number; // Общее количество записей
}
```

#### Пример запроса

```bash
curl -X GET "http://localhost:3000/api/production/warehouses?offset=0&limit=20" \
  -H "Authorization: Bearer <accessToken>"
```

---

### POST /production/quality-specs

Создать спецификацию качества для продукта.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  productId: string;      // UUID продукта
  parameterName: string;  // Название параметра (например, "влажность")
  lowerLimit: number;     // Нижний предел
  upperLimit: number;     // Верхний предел
}
```

#### Response

```typescript
{
  id: string;
  productId: string;
  parameterName: string;
  lowerLimit: number;
  upperLimit: number;
  createdAt: string;      // ISO datetime
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/production/quality-specs \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "productId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "parameterName": "влажность",
    "lowerLimit": 10.0,
    "upperLimit": 14.0
  }'
```

#### Ошибки

- `400` — Ошибка валидации
- `404` — Продукт не найден (`PRODUCT_NOT_FOUND`)

---

### GET /production/quality-specs

Список спецификаций качества с опциональной фильтрацией по продукту.

**Аутентификация:** Bearer accessToken  
**Роли:** ADMIN, MANAGER, ANALYST  
**CSRF:** Не требуется

#### Query Parameters

- `productId?` — UUID продукта (фильтр)
- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 20, min: 1, max: 1000)

#### Response

```typescript
{
  qualitySpecs: Array<{
    id: string;
    productId: string;
    parameterName: string;
    lowerLimit: number;
    upperLimit: number;
    createdAt: string;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

#### Пример запроса

```bash
# Все спецификации качества
curl -X GET "http://localhost:3000/api/production/quality-specs?offset=0&limit=20" \
  -H "Authorization: Bearer <accessToken>"

# Спецификации для конкретного продукта
curl -X GET "http://localhost:3000/api/production/quality-specs?productId=a1b2c3d4-e5f6-7890-abcd-ef1234567890&offset=0&limit=20" \
  -H "Authorization: Bearer <accessToken>"
```

---

### POST /production/products

Создать продукт.

**Аутентификация:** Bearer accessToken  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  code: string;
  name: string;
  category: ProductCategory;
  brand?: string;
  unitOfMeasure: string;
  shelfLifeDays?: number;
  requiresQualityCheck?: boolean;
}
```

#### Response

```typescript
{
  id: string;
  code: string;
  name: string;
  category: ProductCategory;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/production/products \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "code": "PROD-001",
    "name": "Творог 5%",
    "category": "finished_product",
    "brand": "Домик в деревне",
    "unitOfMeasure": "kg",
    "shelfLifeDays": 30,
    "requiresQualityCheck": true
  }'
```

#### Ошибки

- `409` — Код продукта уже занят (`PRODUCT_CODE_ALREADY_EXISTS`)

---

### GET /production/products

Список продуктов.

**Аутентификация:** Bearer accessToken  
**CSRF:** Не требуется

#### Query Parameters

- `category?` — Категория продукта
- `brand?` — Бренд
- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 100, min: 1, max: 1000)

#### Response

```typescript
{
  products: Array<{
    id: string;
    code: string;
    name: string;
    category: ProductCategory;
    brand: string | null;
    unitOfMeasure: string;
    shelfLifeDays: number | null;
    requiresQualityCheck: boolean;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

---

### POST /production/orders

Создать производственный заказ.

**Аутентификация:** Bearer accessToken  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  externalOrderId?: string;
  productId: string;
  targetQuantity: number;
  unitOfMeasure: string;
  productionLine: string;
  plannedStart: string; // ISO datetime
  plannedEnd: string; // ISO datetime
}
```

#### Response

```typescript
{
  id: string;
  externalOrderId: string | null;
  productId: string;
  status: OrderStatus;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/production/orders \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "externalOrderId": "EXT-ORDER-001",
    "productId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "targetQuantity": 1000,
    "unitOfMeasure": "kg",
    "productionLine": "Line-1",
    "plannedStart": "2025-01-01T06:00:00Z",
    "plannedEnd": "2025-01-10T18:00:00Z"
  }'
```

#### Ошибки

- `404` — Продукт не найден (`PRODUCT_NOT_FOUND`)

---

### GET /production/orders

Список заказов.

**Аутентификация:** Bearer accessToken  
**CSRF:** Не требуется

#### Query Parameters

- `status?` — Статус заказа
- `productId?` — UUID продукта
- `productionLine?` — Производственная линия
- `from?` — Начало периода (ISO date)
- `to?` — Конец периода (ISO date)
- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 100, min: 1, max: 1000)

#### Response

```typescript
{
  orders: Array<{
    id: string;
    externalOrderId: string | null;
    productId: string;
    targetQuantity: number;
    actualQuantity: number | null;
    unitOfMeasure: string;
    status: OrderStatus;
    productionLine: string;
    plannedStart: string;
    plannedEnd: string;
    actualStart: string | null;
    actualEnd: string | null;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

---

### GET /production/orders/:id

Заказ по ID с выпусками.

**Аутентификация:** Bearer accessToken  
**CSRF:** Не требуется

#### Response

```typescript
{
  id: string;
  externalOrderId: string | null;
  productId: string;
  targetQuantity: number;
  actualQuantity: number | null;
  unitOfMeasure: string;
  status: OrderStatus;
  productionLine: string;
  plannedStart: string;
  plannedEnd: string;
  actualStart: string | null;
  actualEnd: string | null;
  outputs: Array<{
    id: string;
    orderId: string;
    productId: string;
    lotNumber: string;
    quantity: number;
    qualityStatus: QualityStatus;
    productionDate: string;
    shift: string;
  }>;
}
```

---

### PATCH /production/orders/:id/status

Обновить статус заказа.

**Аутентификация:** Bearer accessToken  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  action: 'start' | 'complete' | 'cancel';
  actualQuantity?: number;
}
```

#### Response

```typescript
{
  id: string;
  status: OrderStatus;
  actualQuantity: number | null;
  actualStart: string | null;
  actualEnd: string | null;
}
```

#### Пример запроса

```bash
curl -X PATCH http://localhost:3000/api/production/orders/<id>/status \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "action": "start"
  }'
```

#### Ошибки

- `409` — Недопустимый переход статуса (`INVALID_ORDER_STATUS_TRANSITION`)

---

### POST /production/output

Зарегистрировать выпуск продукции.

**Аутентификация:** Bearer accessToken  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  orderId: string;
  productId: string;
  lotNumber: string;
  quantity: number;
  shift: string;
}
```

#### Response

```typescript
{
  id: string;
  orderId: string;
  lotNumber: string;
  quantity: number;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/production/output \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "orderId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "productId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "lotNumber": "LOT-2025-001",
    "quantity": 500,
    "shift": "morning"
  }'
```

---

### GET /production/output

Список выпусков.

**Аутентификация:** Bearer accessToken  
**CSRF:** Не требуется

#### Query Parameters

- `orderId?` — UUID заказа
- `productId?` — UUID продукта
- `lotNumber?` — Номер партии
- `from?` — Дата производства от
- `to?` — Дата производства до
- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 100, min: 1, max: 1000)

#### Response

```typescript
{
  outputs: Array<{
    id: string;
    orderId: string;
    productId: string;
    lotNumber: string;
    quantity: number;
    qualityStatus: QualityStatus;
    productionDate: string;
    shift: string;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

---

### POST /production/sales

Зарегистрировать продажу.

**Аутентификация:** Bearer accessToken  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  externalId: string;
  productId: string;
  customerId?: string;   // UUID клиента (опционально)
  quantity: number;
  amount: number;
  saleDate: string;      // ISO date
  channel: SaleChannel;  // retail | wholesale | horeca | export
}
```

#### Response

```typescript
{
  id: string;
  externalId: string;
  productId: string;
  customerId: string | null;
  quantity: number;
  amount: number;
  saleDate: string;
  channel: SaleChannel;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/production/sales \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "externalId": "SALE-001",
    "productId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "customerId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "quantity": 100,
    "amount": 50000,
    "saleDate": "2026-05-01",
    "channel": "retail"
  }'
```

---

### GET /production/sales

Список продаж.

**Аутентификация:** Bearer accessToken  
**CSRF:** Не требуется

#### Query Parameters

- `productId?` — UUID продукта
- `customerId?` — UUID клиента
- `channel?` — Канал продаж (retail | wholesale | horeca | export)
- `from?` — Дата продажи от (ISO date)
- `to?` — Дата продажи до (ISO date)
- `offset?` — Смещение для пагинации (default: 0)
- `limit?` — Лимит записей (default: 100, max: 1000)

#### Response

```typescript
{
  sales: Array<{
    id: string;
    externalId: string;
    productId: string;
    customerId: string | null;
    quantity: number;
    amount: number;
    saleDate: string;
    channel: SaleChannel;
    customer?: {
      id: string;
      name: string;
      code: string;
      region: string;
    };
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

#### Примеры запроса

```bash
# Все продажи за период
curl -X GET "http://localhost:3000/api/production/sales?from=2026-05-01&to=2026-05-07" \
  -H "Authorization: Bearer <accessToken>"

# Продажи конкретного продукта
curl -X GET "http://localhost:3000/api/production/sales?productId=<id>&channel=retail" \
  -H "Authorization: Bearer <accessToken>"

# Продажи конкретного клиента
curl -X GET "http://localhost:3000/api/production/sales?customerId=<id>&offset=0&limit=50" \
  -H "Authorization: Bearer <accessToken>"
```

---

### GET /production/sales/summary

Сводка продаж.

**Аутентификация:** Bearer accessToken  
**CSRF:** Не требуется

#### Query Parameters

- `from?` — Начало периода
- `to?` — Конец периода
- `groupBy?` — Ось группировки (region | channel | product)

#### Response

```typescript
{
  summary: Array<{
    groupKey: string;
    totalQuantity: number;
    totalAmount: number;
    salesCount: number;
  }>;
  totalAmount: number;
  totalQuantity: number;
}
```

---

### POST /production/inventory

Обновить/создать остаток на складе.

**Аутентификация:** Bearer accessToken  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  productId: string;          // UUID продукта
  warehouseId: string;        // UUID склада
  lotNumber?: string;         // Номер партии (опционально)
  quantity: number;           // Количество
  unitOfMeasure: string;      // Единица измерения
}
```

#### Response

```typescript
{
  id: string;
  productId: string;
  warehouseId: string;
  quantity: number;
  lastUpdated: string;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/production/inventory \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "productId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "warehouseId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "lotNumber": "LOT-2026-001",
    "quantity": 200,
    "unitOfMeasure": "kg"
  }'
```

---

### GET /production/inventory

Остатки на складах.

**Аутентификация:** Bearer accessToken  
**CSRF:** Не требуется

#### Query Parameters

- `productId?` — UUID продукта
- `warehouseId?` — UUID склада
- `lotNumber?` — Номер партии
- `offset?` — Смещение для пагинации (default: 0)
- `limit?` — Лимит записей (default: 100, max: 1000)

#### Response

```typescript
{
  inventory: Array<{
    id: string;
    productId: string;
    warehouseId: string;
    lotNumber: string | null;
    quantity: number;
    unitOfMeasure: string;
    lastUpdated: string;
    warehouse?: {
      id: string;
      code: string;
      name: string;
      location: string;
    };
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

---

### POST /production/quality

Зарегистрировать результат контроля качества.

**Аутентификация:** Bearer accessToken  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  lotNumber: string;
  productId: string;
  parameterName: string;
  resultValue: number;
  lowerLimit: number;
  upperLimit: number;
  testDate: string; // ISO date
}
```

#### Response

```typescript
{
  id: string;
  lotNumber: string;
  productId: string;
  inSpec: boolean;
  qualityStatus: QualityStatus;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/production/quality \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "lotNumber": "LOT-2025-001",
    "productId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "parameterName": "moisture",
    "resultValue": 12.5,
    "lowerLimit": 10.0,
    "upperLimit": 14.0,
    "testDate": "2025-01-06"
  }'
```

---

### GET /production/quality

Результаты контроля качества.

**Аутентификация:** Bearer accessToken  
**CSRF:** Не требуется

#### Query Parameters

- `productId?` — UUID продукта
- `lotNumber?` — Номер партии
- `decision?` — Решение (APPROVED | REJECTED | QUARANTINE)
- `inSpec?` — Только в норме (boolean)
- `offset?` — Смещение для пагинации (default: 0, min: 0)
- `limit?` — Лимит записей (default: 100, min: 1, max: 1000)

#### Response

```typescript
{
  results: Array<{
    id: string;
    lotNumber: string;
    productId: string;
    parameterName: string;
    resultValue: number;
    lowerLimit: number;
    upperLimit: number;
    inSpec: boolean;
    qualityStatus: QualityStatus;
    testDate: string;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

---

### POST /production/sensors

Записать показание датчика.

**Аутентификация:** Bearer accessToken  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  deviceId: string;
  productionLine: string;
  parameterName: string;
  value: number;
  unit: string;
  quality: SensorQuality;
}
```

#### Response

```typescript
{
  id: string;
  deviceId: string;
  productionLine: string;
  parameterName: string;
  quality: SensorQuality;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/production/sensors \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
  -d '{
    "deviceId": "SENSOR-01",
    "productionLine": "Line-1",
    "parameterName": "temperature",
    "value": 72.5,
    "unit": "°C",
    "quality": "good"
  }'
```

---

### GET /production/sensors

Список датчиков.

**Аутентификация:** Bearer accessToken  
**CSRF:** Не требуется

#### Query Parameters

- `productionLineId?` — UUID производственной линии
- `sensorParameterId?` — UUID параметра датчика
- `isActive?` — Активен (true | false)
- `offset?` — Смещение для пагинации (default: 0)
- `limit?` — Лимит записей (default: 100, max: 1000)

#### Response

```typescript
{
  sensors: Array<{
    id: string;
    deviceId: string;
    productionLineId: string;
    sensorParameter: {
      id: string;
      name: string;
      code: string;
      unit: string;
    };
    isActive: boolean;
    createdAt: string;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

#### Пример запроса

```bash
# Все датчики
curl -X GET "http://localhost:3000/api/production/sensors" \
  -H "Authorization: Bearer <accessToken>"

# Датчики в определённой производственной линии
curl -X GET "http://localhost:3000/api/production/sensors?productionLineId=<id>" \
  -H "Authorization: Bearer <accessToken>"

# Датчики конкретного параметра (например, температуры)
curl -X GET "http://localhost:3000/api/production/sensors?sensorParameterId=<id>&offset=0&limit=50" \
  -H "Authorization: Bearer <accessToken>"
```

---

### GET /production/sensor-readings

Показания датчиков.

**Аутентификация:** Bearer accessToken  
**CSRF:** Не требуется

#### Query Parameters

- `sensorId?` — UUID датчика (фильтр по датчику)
- `quality?` — Качество сигнала (GOOD | DEGRADED | BAD)
- `from?` — Начало диапазона (ISO datetime)
- `to?` — Конец диапазона (ISO datetime)
- `offset?` — Смещение для пагинации (default: 0)
- `limit?` — Лимит записей (default: 500, max: 1000)

#### Response

```typescript
{
  readings: Array<{
    id: string;
    sensorId: string;
    deviceId: string;
    parameterName: string;
    value: number;
    unit: string;
    quality: SensorQuality;
    recordedAt: string;
  }>;
  total: number; // Общее количество записей (с учётом фильтров)
}
```

#### Пример запроса

```bash
# Все показания за период
curl -X GET "http://localhost:3000/api/production/sensor-readings?from=2026-05-01T00:00:00Z&to=2026-05-07T23:59:59Z" \
  -H "Authorization: Bearer <accessToken>"

# Показания конкретного датчика
curl -X GET "http://localhost:3000/api/production/sensor-readings?sensorId=<id>&quality=GOOD" \
  -H "Authorization: Bearer <accessToken>"
```

---

### GET /production/kpi

KPI производства.

**Аутентификация:** Bearer accessToken  
**CSRF:** Не требуется

#### Query Parameters

- `from?` — Начало периода
- `to?` — Конец периода
- `productionLine?` — Производственная линия

#### Response

```typescript
{
  totalOutput: number;
  defectRate: number;
  completedOrders: number;
  totalOrders: number;
  oeeEstimate: number;
}
```

#### Пример запроса

```bash
curl -X GET "http://localhost:3000/api/production/kpi?from=2025-01-01&to=2025-12-31" \
  -H "Authorization: Bearer <accessToken>"
```

---

## ETL API

Интеграция с внешними системами (1C-ZUP, 1C-ERP, MES, SCADA, LIMS).

### POST /etl/import

Загрузить пакет данных (JSON body).

**Аутентификация:** Bearer accessToken  
**Роль:** ADMIN (требуется)  
**CSRF:** Требуется для браузера

#### Request Body

```typescript
{
  source_system: SourceSystem; // '1c_zup' | '1c_erp' | 'mes' | 'scada' | 'lims'
  import_type: ImportType;     // 'employees' | 'departments' | 'positions' | 'products' | 'orders' | 'sensors' | 'quality'
  data: Array<Record<string, any>>;
}
```

#### Response

```typescript
{
  import_id: string;           // MongoDB ObjectId операции импорта
  status: ImportStatus;        // 'pending' | 'processing' | 'completed' | 'failed'
  records_count: number;
  source_file_id?: string;     // ID файла в GridFS (только при file upload)
  warnings?: string[];         // Предупреждения парсера
  parse_errors?: Array<{ index: number; field: string; message: string }>; // Ошибки валидации
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/etl/import \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <value>" \
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

---

### POST /etl/import/file

Загрузить файл (xlsx/json).

**Аутентификация:** Bearer accessToken  
**Роль:** ADMIN (требуется)  
**CSRF:** Требуется для браузера  
**Max file size:** 20 MB

#### Request Body (multipart/form-data)

```
file: <file>
source_system: string
import_type: string
```

#### Response

```typescript
{
  import_id: string;           // MongoDB ObjectId операции импорта
  status: 'processing';
  records_count: number;
  source_file_id?: string;     // ID файла в GridFS
  format?: 'xlsx' | 'json';
  warnings?: string[];
  parse_errors?: Array<{ index: number; field: string; message: string }>;
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/etl/import/file \
  -H "Authorization: Bearer <accessToken>" \
  -H "X-CSRF-Token: <value>" \
  -F "file=@data.xlsx" \
  -F "source_system=1c_zup" \
  -F "import_type=employees"
```

#### Ошибки

- `400` — Неподдерживаемый формат файла или превышен размер

---

### GET /etl/imports

Список импортов.

**Аутентификация:** Bearer accessToken  
**Роль:** ADMIN (требуется)  
**CSRF:** Не требуется

#### Query Parameters

- `source_system?` — Источник: `1c_zup` | `1c_erp` | `mes` | `scada` | `lims`
- `status?` — Статус: `pending` | `processing` | `completed` | `failed`
- `limit?` — Количество записей (1–500, по умолчанию 20)

#### Response

```typescript
Array<{
  import_id: string;           // MongoDB ObjectId
  source_system: SourceSystem;
  import_type: ImportType;
  status: ImportStatus;
  records_count: number;
  source_file_id?: string;     // ID файла в GridFS (если был file upload)
  source_file_format?: 'xlsx' | 'json';
  created_at: string;          // ISO datetime
  processed_at: string | null;
}>
```

---

### GET /etl/imports/:id

Детали импорта.

**Аутентификация:** Bearer accessToken  
**Роль:** ADMIN (требуется)  
**CSRF:** Не требуется

#### Response

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

#### Ошибки

- `404` — Импорт не найден

---

### GET /etl/imports/:id/file

Скачать исходный файл импорта.

**Аутентификация:** Bearer accessToken  
**Роль:** ADMIN (требуется)  
**CSRF:** Не требуется

#### Response

Бинарный поток файла (application/octet-stream или исходный MIME)

#### Ошибки

- `404` — Импорт или файл не найден

---

### POST /etl/imports/:id/retry

Повторить импорт.

**Аутентификация:** Bearer accessToken  
**Роль:** ADMIN (требуется)  
**CSRF:** Требуется для браузера

#### Response

```typescript
{
  import_id: string;
  status: 'processing';
}
```

#### Пример запроса

```bash
curl -X POST http://localhost:3000/api/etl/imports/<id>/retry \
  -H "Authorization: Bearer <accessToken>" \
  -H "X-CSRF-Token: <value>"
```

#### Ошибки

- `400` — Импорт не может быть повторен (не в статусе failed)
- `404` — Импорт не найден

---

## Enum значения

### LocationType

- `OFFICE` — Офис
- `FACTORY` — Производственный цех/завод

### WorkstationType

- `ASSEMBLY` — Сборка
- `PACKAGING` — Упаковка
- `QUALITY_CONTROL` — Контроль качества
- `STORAGE` — Хранение
- `OFFICE` — Офисное рабочее место

### UserRole

- `ADMIN` — Администратор
- `MANAGER` — Менеджер
- `SHIFT_MANAGER` — Менеджер смены
- `ANALYST` — Аналитик
- `EMPLOYEE` — Сотрудник

### DepartmentType

- `DIVISION` — Дивизион
- `DEPARTMENT` — Отдел
- `SECTION` — Секция
- `UNIT` — Юнит

### EmploymentType

- `main` — Основной
- `part_time` — Неполный

### EmployeeStatus

- `active` — Активен
- `terminated` — Уволен
- `on_leave` — В отпуске

### ShiftType

- `day_shift` — Дневная смена
- `night_shift` — Ночная смена
- `rotating` — Ротирующаяся

### ProductCategory

- `raw_material` — Сырье
- `semi_finished` — Полуфабрикат
- `finished_product` — Готовый продукт
- `packaging` — Упаковка

### OrderStatus

- `planned` — Запланирован
- `in_progress` — В работе
- `completed` — Завершен
- `cancelled` — Отменен

### QualityStatus

- `pending` — Ожидает
- `approved` — Одобрен
- `rejected` — Отклонен


### SaleChannel

- `retail` — Розница
- `wholesale` — Опт
- `horeca` — HoReCa
- `export` — Экспорт

### SensorQuality

- `good` — Хорошее
- `degraded` — Ухудшенное
- `bad` — Плохое
