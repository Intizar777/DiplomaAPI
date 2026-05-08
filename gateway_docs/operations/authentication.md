# Операции: Аутентификация

Система использует JWT токены для аутентификации. Безопасная и масштабируемая схема.

## JWT структура

**Access Token:**
```
Header:    { "alg": "HS256", "typ": "JWT" }
Payload:   { "sub": "user-id", "email": "...", "role": "admin", "exp": 1234567890 }
Signature: HMACSHA256(base64(header) + "." + base64(payload), secret)
```

**Lifetime:** 1 час (3600 seconds)

**Refresh Token:**
```
Используется для получения нового Access Token
Lifetime: 30 дней
Хранится в БД (RefreshToken таблица) для отзыва при необходимости
```

## Процесс аутентификации

### 1. Регистрация

```bash
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "fullName": "Иванов Иван"
}

Response 201:
{
  "id": "user-id",
  "email": "user@example.com",
  "fullName": "Иванов Иван",
  "role": "employee",  // default
  "isActive": true
}
```

### 2. Логин

```bash
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response 200:
{
  "accessToken": "eyJhbGciOiJIUzI1NiI...",
  "refreshToken": "eyJhbGciOiJIUzI1NiI...",
  "expiresIn": 3600
}
```

**Браузер:** Refresh token устанавливается в HttpOnly cookie

### 3. Использование Access Token

```bash
GET /api/personnel/employees
-H "Authorization: Bearer <accessToken>"
```

### 4. Обновление токена (перед истечением)

```bash
POST /api/auth/refresh
{
  "refreshToken": "<refreshToken>"  // Для мобильных
}

# Или браузер использует cookie автоматически
POST /api/auth/refresh

Response 200:
{
  "accessToken": "eyJhbGciOiJIUzI1NiI...",
  "expiresIn": 3600
}
```

### 5. Logout

```bash
POST /api/auth/logout

# На сервере: отозвать Refresh Token (установить isRevoked=true)
```

## Хранение токенов

### Браузерные клиенты

**Access Token:**
- Хранится в памяти (переменная, localStorage)
- Отправляется в Authorization заголовке

**Refresh Token:**
- Хранится в HttpOnly cookie (защита от XSS)
- Отправляется автоматически браузером
- Не доступен JavaScript (защита от XSS)

**Процесс восстановления после перезагрузки:**
```typescript
// Page load
if (!accessToken) {
  // Try to refresh using stored refresh token (in cookie)
  const newToken = await fetch('/api/auth/refresh');
  // If 401 → redirect to login
}
```

### Мобильные клиенты

**Access Token:**
- Хранится в памяти приложения (не сохраняется на диск)
- Отправляется в Authorization заголовке

**Refresh Token:**
- Хранится в secure storage (Keychain/KeyStore)
- При перезапуске приложения → используется refresh endpoint

**Процесс:**
```typescript
// After login
storeInSecureStorage('refreshToken', refreshToken);
useInMemory('accessToken', accessToken);

// On app restart
const refreshToken = getFromSecureStorage('refreshToken');
const { accessToken } = await refresh(refreshToken);
useInMemory('accessToken', accessToken);
```

## Обновление пароля

```bash
POST /api/auth/change-password
{
  "currentPassword": "OldPass123!",
  "newPassword": "NewPass456!",
  "confirmPassword": "NewPass456!"
}

# Требует валидного Access Token
# Response: 200 OK (новый пароль применен)
```

## Ошибки аутентификации

| Ошибка | Код | Решение |
|--------|-----|--------|
| Invalid email/password | 401 | Проверить credentials, попробовать снова |
| Email not found | 404 | Зарегистрироваться или восстановить пароль |
| User inactive | 403 | Контактировать администратора |
| Token expired | 401 | Обновить token (refresh) |
| Invalid token | 401 | Зайти заново (logout + login) |
| Token revoked | 401 | Зайти заново (user был разлогинен) |

## Безопасность

**DO:**
- ✅ Используйте HTTPS (токены в plain text не отправляйте)
- ✅ Обновляйте token перед истечением
- ✅ Сохраняйте refresh token в secure storage
- ✅ Удаляйте токены при logout
- ✅ Используйте HttpOnly cookies для браузеров

**DON'T:**
- ❌ Не сохраняйте access token в localStorage (XSS risk)
- ❌ Не отправляйте refresh token в основных запросах
- ❌ Не используйте простые пароли
- ❌ Не игнорируйте SSL errors (MITM risk)

---

**Related:** [../api/overview.md](../api/overview.md), [authorization.md](authorization.md)
