# Архитектура: 3NF Нормализация (v1.2.0)

В версии 1.2.0 (май 2026) система приведена к третьей нормальной форме (3NF) для устранения транзитивных зависимостей и улучшения консистентности данных.

## Проблема (до нормализации)

**Транзитивные зависимости:**
- Employee → Location (locationId)
- Location → city, region, country
- Location был разложен (денормализирован) в Employee
- Изменение города требовало обновления всех сотрудников

**Встроенные справочники:**
- Sale содержал customerName (строку вместо FK)
- Sensor содержал parameterName + unit (вместо FK на SensorParameter)
- Inventory использовал warehouseCode (строку вместо FK)

## Решение (3NF структура)

### Personnel Service

**ДО:**
```
Employee (id, fullName, locationId, city, region, country)
Location (id, code, city, region, country, streetAddress)
```

**ПОСЛЕ:**
```
PostalArea (id, postalCode, city, region)
Location (id, code, streetAddress, postalAreaId) → PostalArea
Employee (id, fullName, positionId, workstationId) → Position, Workstation
Workstation (id, locationId) → Location
```

**Преимущества:**
- Локация сотрудника определяется через workstation (1 источник правды)
- Изменение города не затрагивает таблицу Employee
- PostalArea переиспользуется для разных Location

### Production Service

**ДО:**
```
Sale (id, productId, customerName, region, channel)
Sensor (id, deviceId, productionLine, parameterName, unit)
Inventory (id, productId, warehouseCode, quantity)
```

**ПОСЛЕ:**
```
Customer (id, code, name, region)
Sale (id, productId, customerId) → Customer, Product

SensorParameter (id, code, name, unit)
Sensor (id, deviceId, productionLineId, sensorParameterId) → ProductionLine, SensorParameter

Warehouse (id, code, name, location)
Inventory (id, productId, warehouseId) → Product, Warehouse
```

**Преимущества:**
- Customer переиспользуется (можно группировать по customer для аналитики)
- SensorParameter становится справочником (переиспользование в разных датчиках)
- Warehouse становится сущностью (можно добавить мощность, локацию, и т.д.)

## Миграция данных

**Если вы работали с данными до v1.2.0:**

```bash
# 1. Примените все миграции
cd apps/personnel
npx prisma migrate deploy

cd ../production
npx prisma migrate deploy

# 2. Пересоздайте данные с seed-скриптом
npm run seed:all

# 3. Генерируйте Prisma клиент
npx prisma generate

# 4. Перезапустите приложение
npm run serve
```

## Паттерн: Hierarchical Reference

**Локация в Personnel:**
```
PostalArea (почтовый индекс)
  ↓ (многие)
Location (локация)
  ↓ (многие)
Workstation (рабочее место)
  ↓ (многие)
Employee (сотрудник)
```

**Queries:**
```typescript
// Получить всех сотрудников в городе
const city = "Москва";
const employees = await prisma.employee.findMany({
  where: {
    workstation: {
      location: {
        postalArea: { city },
      },
    },
  },
  include: {
    workstation: {
      include: {
        location: {
          include: { postalArea: true },
        },
      },
    },
  },
});
```

## Паттерн: Reference Entities

**Справочник → множество основных записей:**

```
SensorParameter (справочник параметров)
  ↑ (один)
Sensor (конкретный датчик)
  ↓ (множество)
SensorReading (показания)
```

**Преимущество:** Измените имя параметра в SensorParameter → все датчики видят новое имя

## Сохраненные запросы (views)

После нормализации, иногда нужны "плоские" виды для отчетов:

```sql
-- View: employees_with_location
CREATE VIEW employees_with_location AS
SELECT 
  e.id,
  e.full_name,
  l.name AS location_name,
  pa.city,
  pa.region
FROM employees e
LEFT JOIN workstations w ON e.workstation_id = w.id
LEFT JOIN locations l ON w.location_id = l.id
LEFT JOIN postal_areas pa ON l.postal_area_id = pa.id;

-- Usage: Prisma (через raw SQL или view-как-таблица)
const result = await prisma.$queryRaw`
  SELECT * FROM employees_with_location WHERE region = 'Москва'
`;
```

---

**Related:** [database.md](database.md), [../data/all-models.md](../data/all-models.md)
