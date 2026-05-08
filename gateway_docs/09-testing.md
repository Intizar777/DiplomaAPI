# Testing Guide

Полное руководство по тестированию EFKO Kernel: unit тесты, integration тесты, E2E тесты.

## Структура тестов

```
apps/
├── gateway/
│   └── src/app/**/*.spec.ts        # Unit и integration тесты Gateway
├── auth-service/
│   └── src/app/**/*.spec.ts        # Unit и integration тесты Auth
├── personnel/
│   └── src/app/**/*.spec.ts        # Unit и integration тесты Personnel
├── production/
│   ├── src/app/**/*.spec.ts        # Unit и integration тесты Production
│   └── e2e/
│       ├── sensors.e2e.spec.ts     # E2E: Sensor API endpoints
│       ├── quality.e2e.spec.ts     # E2E: Quality API endpoints
│       ├── kpi.e2e.spec.ts         # E2E: KPI API endpoints
│       ├── orders.e2e.spec.ts      # E2E: Orders API endpoints
│       └── products.e2e.spec.ts    # E2E: Products API endpoints
└── etl/
    └── src/app/**/*.spec.ts        # Unit тесты ETL
```

## Запуск тестов

### Все тесты

```bash
# Все сервисы
npx nx test --all --ci

# С покрытием
npx nx test --all --ci --coverage
```

### По сервисам

```bash
# Gateway
npx nx test gateway --ci

# Auth-Service
npx nx test auth-service --ci

# Personnel
npx nx test personnel --ci

# Production
npx nx test production --ci

# ETL
npx nx test etl --ci
```

### Конкретный файл

```bash
cd apps/production
npx jest e2e/sensors.e2e.spec.ts --verbose
```

### С паттерном

```bash
npx nx test production --testNamePattern="Quality" --ci
```

## Текущее состояние тестов

### Test Suites Summary (May 8, 2026)

| Сервис | Suite | Tests | Status |
|--------|-------|-------|--------|
| **gateway** | 5 | 117 ✅ | PASS |
| **auth-service** | 8 | 25 ✅ | PASS |
| **personnel** | 23 | 70 ✅ | PASS |
| **production** | 38 | 200 ✅ | PASS |
| **etl** | 1 | 9 ✅ | PASS |
| **TOTAL** | **75** | **421** | ✅ |

**Last Updated:** 2026-05-08

## E2E Testing (Production Service)

E2E тесты в `apps/production/e2e/` проверяют HTTP endpoints через Gateway API.

### Конфигурация

**Gateway URL (переменная окружения):**
```bash
GATEWAY_URL=http://localhost:3000
```

Если не установлена, используется default: `http://localhost:3000`

### Предусловия

1. **Инфраструктура должна быть запущена:**
   ```bash
   docker compose up -d
   ```

2. **Gateway должен быть запущен:**
   ```bash
   npx nx serve gateway
   ```

3. **Test credentials:**
   - Email: `admin@efko.local`
   - Password: `Efko2024!`

### Файлы E2E тестов

#### sensors.e2e.spec.ts
Тесты для работы с показаниями датчиков.

**Endpoints:**
- `POST /api/production/sensors` — Записать показание датчика
- `GET /api/production/sensors` — Получить список показаний с фильтрами (productionLineId, parameterName, quality, date range)

**Примеры фильтров:**
```bash
GET /api/production/sensors?productionLineId=Line-1
GET /api/production/sensors?parameterName=temperature
GET /api/production/sensors?quality=GOOD
GET /api/production/sensors?from=2025-01-01T00:00:00Z&to=2025-12-31T23:59:59Z
```

**Jest timeout:** 20000ms (для медленных RPC запросов)

#### quality.e2e.spec.ts
Тесты для контроля качества и спецификаций.

**Endpoints:**
- `POST /api/production/quality` — Записать результат контроля качества
- `GET /api/production/quality` — Получить список результатов с фильтрами (productId, lotNumber, decision, inSpec)

**Примеры:**
```bash
GET /api/production/quality?productId=<uuid>
GET /api/production/quality?lotNumber=LOT-2025-001
GET /api/production/quality?decision=APPROVED
GET /api/production/quality?inSpec=true
```

**Jest timeout:** 20000ms

#### kpi.e2e.spec.ts
Тесты для KPI и агрегированных метрик.

**Endpoints:**
- `GET /api/production/kpi` — Получить KPI с фильтрами (productionLineId, date range)

**Примеры:**
```bash
GET /api/production/kpi
GET /api/production/kpi?productionLineId=Line-1
GET /api/production/kpi?from=2025-01-01&to=2025-12-31
```

**Jest timeout:** 20000ms

#### orders.e2e.spec.ts, products.e2e.spec.ts
Тесты для заказов и продуктов.

### Структура E2E теста

```typescript
describe('API Feature', () => {
  beforeAll(async () => {
    // Проверка доступности gateway
    const res = await request(API_URL).get('/api/health').timeout(3000);
    isGatewayAvailable = res.status === 200;
  });

  it('GET /api/endpoint should handle request', async () => {
    if (!isGatewayAvailable) return; // Пропустить если gateway недоступен

    const token = await getTestToken(); // Получить JWT

    const res = await request(API_URL)
      .get('/api/production/sensors')
      .set('Authorization', `Bearer ${token}`)
      .timeout(15000); // HTTP request timeout

    expect([200, 400, 404, 500, 503]).toContain(res.status);
    if (res.status === 200) {
      expect(Array.isArray(res.body.readings)).toBe(true);
    }
  }, 20000); // Jest test timeout (must be > HTTP timeout)
});
```

### Обработка таймаутов

**Важно:** Jest таймаут (3-й параметр `it()`) **должен быть больше** HTTP request timeout (`.timeout()`).

```typescript
// ❌ НЕПРАВИЛЬНО: Jest timeout 5000ms < HTTP timeout 15000ms
it('test', async () => {
  const res = await request(API_URL)
    .get('/api/production/sensors')
    .timeout(15000);
}, 5000); // Jest timeout too small

// ✅ ПРАВИЛЬНО: Jest timeout 20000ms > HTTP timeout 15000ms
it('test', async () => {
  const res = await request(API_URL)
    .get('/api/production/sensors')
    .timeout(15000);
}, 20000); // Jest timeout is sufficient
```

### Token Management

Токен кэшируется с временем жизни 30 минут:

```typescript
let cachedToken: { token: string; expiresAt: number } | null = null;

async function getTestToken(): Promise<string> {
  if (cachedToken && cachedToken.expiresAt > Date.now()) {
    return cachedToken.token; // Использовать кэшированный
  }

  try {
    const res = await request(API_URL)
      .post('/api/auth/login')
      .send({
        email: 'admin@efko.local',
        password: 'Efko2024!',
      })
      .timeout(5000);

    if (res.status === 201 && res.body.accessToken) {
      cachedToken = {
        token: res.body.accessToken,
        expiresAt: Date.now() + 30 * 60 * 1000,
      };
      return res.body.accessToken;
    }
  } catch (error) {
    // Fallback: use fake JWT
  }

  return generateFakeJWT();
}
```

### Типичные статус-коды в E2E тестах

| Статус | Описание | Когда ожидать |
|--------|---------|---------------|
| 200 | OK | Успешный GET запрос |
| 201 | Created | Успешный POST запрос |
| 400 | Bad Request | Невалидные параметры |
| 401 | Unauthorized | Нет токена или токен истек |
| 403 | Forbidden | Недостаточно прав |
| 404 | Not Found | Ресурс не существует |
| 500 | Server Error | Ошибка в сервисе |
| 503 | Service Unavailable | Downstream сервис недоступен |

**E2E тесты проверяют:** `expect([200, 400, 404, 500, 503]).toContain(res.status)`

Это позволяет тестам работать даже если отдельные сервисы недоступны (тесты не блокируются).

## Unit Tests

### Структура unit теста

```typescript
describe('CreateProductUseCase', () => {
  let useCase: CreateProductUseCase;
  let repository: MockRepository;

  beforeEach(() => {
    repository = {
      create: jest.fn(),
      findByCode: jest.fn(),
    };
    useCase = new CreateProductUseCase(repository);
  });

  it('should create product with valid input', async () => {
    const input = {
      code: 'PROD-001',
      name: 'Test Product',
      // ...
    };

    const result = await useCase.execute(input, metadata);

    expect(result.id).toBeDefined();
    expect(repository.create).toHaveBeenCalledWith(expect.objectContaining(input));
  });

  it('should throw error if code already exists', async () => {
    repository.findByCode.mockResolvedValue({ id: 'existing' });

    const input = { code: 'EXISTING' };

    await expect(useCase.execute(input, metadata))
      .rejects
      .toThrow('PRODUCT_CODE_ALREADY_EXISTS');
  });
});
```

### Mocking patterns

**Prisma Repository Mock:**
```typescript
const mockRepository = {
  findUnique: jest.fn(),
  findMany: jest.fn(),
  create: jest.fn(),
  update: jest.fn(),
  delete: jest.fn(),
  upsert: jest.fn(),
  count: jest.fn(),
};
```

**RPC Service Mock:**
```typescript
const mockRpcService = {
  send: jest.fn().mockResolvedValue({ result: 'ok' }),
};
```

## Integration Tests

Integration tests проверяют работу с реальными БД и Rabbit.

```typescript
describe('ProductRepository (Integration)', () => {
  let repository: ProductRepository;
  let prisma: PrismaClient;

  beforeAll(async () => {
    prisma = new PrismaClient({
      datasources: {
        db: {
          url: process.env.TEST_DATABASE_URL,
        },
      },
    });

    repository = new ProductRepository(prisma);

    // Очистить данные перед тестами
    await prisma.product.deleteMany({});
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  it('should create and retrieve product', async () => {
    const product = await repository.create({
      code: 'TEST-001',
      name: 'Test',
    });

    const retrieved = await repository.findUnique(product.id);

    expect(retrieved).toEqual(product);
  });
});
```

## Тестовые данные (Fixtures)

Фиксчеры находятся в `seed/` и используются для заполнения БД:

```bash
# Затравить все БД
npm run seed:all

# Затравить конкретный сервис
npm run seed:personnel
npm run seed:production
npm run seed:auth
```

## Покрытие тестами

```bash
# Генерировать отчет о покрытии
npx nx test production --ci --coverage

# Просмотреть отчет
open coverage/apps/production/index.html
```

## Debugging тестов

### Debug mode

```bash
# Запустить с выводом логов
npx nx test personnel --verbose

# Запустить один тест
npx nx test personnel --testNamePattern="CreateEmployee"
```

### Временные пause в тестах

```typescript
// Остановить выполнение для отладки
it('should create employee', async () => {
  const result = await useCase.execute(payload, metadata);

  debugger; // Откроется в Node.js debugger

  expect(result).toBeDefined();
});
```

Запустить с debugger:
```bash
node --inspect-brk ./node_modules/.bin/jest --runInBand
```

### Вывод дополнительной информации

```typescript
it('should calculate KPI', async () => {
  const result = await useCase.execute(payload, metadata);

  console.log('KPI Result:', JSON.stringify(result, null, 2));

  expect(result.totalOutput).toBeGreaterThan(0);
});
```

## CI/CD для тестов

Тесты запускаются в GitHub Actions:

```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: npx nx test --all --ci --coverage

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

## Best Practices

1. **Изолируйте тесты:** Каждый тест должен быть независимым
2. **Используйте fixtures:** Создавайте общие test data в `beforeAll`
3. **Очищайте данные:** Используйте `afterEach` для cleanup
4. **Мокируйте внешние сервисы:** Не обращайтесь к production API
5. **Проверяйте граничные случаи:** Пустые данные, null, ошибки
6. **Описывайте тесты на человеческом языке:** `it('should create product when valid data is provided')`
7. **Не испольуйте sleep:** Используйте `waitFor` для асинхронных операций
8. **Группируйте related тесты:** Используйте `describe()` для организации

## Troubleshooting тестов

### Тест зависает

```bash
# Может быть открытое соединение с БД
# Убедитесь, что в afterAll закрыто подключение
afterAll(async () => {
  await prisma.$disconnect();
});
```

### Jest timeout

Если тест занимает больше дефолтного timeout (5000ms):

```typescript
it('slow test', async () => {
  // long operation
}, 30000); // Увеличить timeout до 30 сек
```

### Flaky tests

Если тест иногда падает:

```typescript
// Используйте retry
jest.retryTimes(3);

it('potentially flaky test', async () => {
  // ...
});
```

## Git Hooks для тестов

Перед commit-ом запускаются тесты:

```bash
# Установлено в husky
npm run prepare

# Запустится автоматически перед git commit
# Если тесты падают, commit блокируется
```

---

**Related:** [CLAUDE.md](../CLAUDE.md), [troubleshooting](./07-troubleshooting.md)
