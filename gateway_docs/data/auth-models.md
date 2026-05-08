# Модели данных: Auth Service

Минимальная схема для аутентификации и управления пользователями.

## User

**Таблица:** `users`  
**Назначение:** Аккаунты пользователей в системе

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный идентификатор |
| `email` | String @unique | Email (до 255 символов) |
| `passwordHash` | String | Bcrypt хеш пароля |
| `fullName` | String | Полное имя (до 150 символов) |
| `role` | UserRole | Роль (admin, manager, analyst, shift_manager, employee) |
| `isActive` | Boolean | Активен ли пользователь (default: true) |
| `employeeId` | UUID? | Привязка к Employee (nullable) |
| `createdAt` | DateTime | Дата создания |
| `updatedAt` | DateTime | Дата последнего обновления |

**Связи:**
- `refreshTokens` — один ко многим (пользователь может иметь несколько refresh токенов)

**Индексы:**
- `email` — уникальный (для быстрого поиска по email)
- Автоматический индекс на FK для `employeeId`

**Пример:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "ivan.petrov@example.com",
  "fullName": "Иванов Иван Петрович",
  "role": "manager",
  "isActive": true,
  "employeeId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "createdAt": "2026-05-01T10:00:00Z",
  "updatedAt": "2026-05-07T15:30:00Z"
}
```

## RefreshToken

**Таблица:** `refresh_tokens`  
**Назначение:** Токены для обновления сессии (отдельные от access token)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный идентификатор |
| `userId` | UUID | Foreign Key на User |
| `tokenHash` | String | Bcrypt хеш самого токена (не храним в plain text) |
| `expiresAt` | DateTime | Когда токен истекает |
| `isRevoked` | Boolean | Отозван ли (позволяет делать logout) |
| `createdAt` | DateTime | Когда токен был выдан |

**Связи:**
- `user` — многие к одному (каждый токен привязан к пользователю)

**Индексы:**
- `userId` — для быстрого поиска токенов пользователя
- `expiresAt` — для поиска истекших токенов (cleanup job)

**Пример:**
```json
{
  "id": "b2c3d4e5-f6a7-8901-2cde-f3456789012a",
  "userId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tokenHash": "$2b$10$...",
  "expiresAt": "2026-08-07T15:30:00Z",
  "isRevoked": false,
  "createdAt": "2026-05-07T15:30:00Z"
}
```

## UserRole (Enum)

**Таблица:** `user_role`

| Значение | Код БД | Описание |
|----------|--------|---------|
| ADMIN | `admin` | Администратор системы |
| MANAGER | `manager` | Менеджер (может управлять подразделениями) |
| ANALYST | `analyst` | Аналитик (может читать отчеты и данные) |
| SHIFT_MANAGER | `shift_manager` | Менеджер смены (управляет сменами и рабочими) |
| EMPLOYEE | `employee` | Обычный сотрудник (может видеть только свои данные) |

**Использование:**
```typescript
// Guard
@UseGuards(RoleGuard)
@Roles(UserRole.MANAGER, UserRole.ADMIN)
getEmployees() { ... }
```

## OutboxMessage

**Таблица:** `outbox_messages`  
**Назначение:** Надежная публикация событий (Transactional Outbox pattern)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный идентификатор события |
| `eventType` | String | Тип события (UserRegisteredEvent, и т.д.) |
| `payload` | Json | Данные события (JSON) |
| `status` | OutboxStatus | PENDING, SENT, FAILED |
| `retryCount` | Int | Количество попыток отправки |
| `createdAt`, `processedAt` | DateTime | Временные метки |

**Использование:**
```typescript
// В одной транзакции создаем User и OutboxMessage
await prisma.$transaction([
  prisma.user.create({ data: userData }),
  prisma.outboxMessage.create({
    data: {
      eventType: 'UserRegisteredEvent',
      payload: { userId, email },
    }
  })
]);
```

---

**Related:** [../architecture/database.md](../architecture/database.md), [all-models.md](all-models.md)
