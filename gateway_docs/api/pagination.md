# API: Пагинация & Фильтрация

Все список-эндпоинты поддерживают пагинацию для больших наборов данных.

## Пагинация параметры

```
offset    - Смещение от начала (default: 0, min: 0)
limit     - Количество записей на странице (default: 20, max: 100 для personnel, 1000 для production)
```

## Структура ответа

Все список-эндпоинты возвращают объект с массивом и total count:

```typescript
{
  items: Array<T>;        // Массив записей
  total: number;          // Общее количество записей (с учётом фильтров)
}
```

**Пример ответа:**
```json
{
  "employees": [
    { "id": "...", "fullName": "Иванов Иван", ... },
    { "id": "...", "fullName": "Петров Петр", ... }
  ],
  "total": 250
}
```

## Примеры

**Первая страница (20 записей по умолчанию):**
```bash
GET /api/personnel/employees

Response:
{
  "employees": [...],
  "total": 250
}
```

**Вторая страница:**
```bash
GET /api/personnel/employees?offset=20&limit=20

# items 21-40
```

**Третья страница с меньшим лимитом:**
```bash
GET /api/personnel/employees?offset=40&limit=10

# items 41-50
```

**Последняя страница для 250 записей:**
```bash
GET /api/personnel/employees?offset=240&limit=20

# items 241-250
```

## Фильтрация

Большинство список-эндпоинтов поддерживают фильтры:

```bash
# По типу
GET /api/personnel/locations?type=OFFICE

# По статусу
GET /api/personnel/employees?status=ACTIVE

# По диапазону дат
GET /api/production/sales?from=2026-05-01&to=2026-05-07

# По нескольким критериям
GET /api/production/inventory?productId=<id>&warehouseId=<id>
```

## Комбинированная пагинация и фильтрация

```bash
# Фильтруем + пагинируем
GET /api/production/sales?channel=retail&offset=0&limit=50

# Multiple фильтры + пагинация
GET /api/personnel/workstations?locationId=<id>&workstationType=OPERATOR_POST&offset=0&limit=25
```

## Правильный расчет offset'а

**Формула:**
```
offset = (page_number - 1) * limit

Примеры:
- page 1, limit 20  → offset = 0
- page 2, limit 20  → offset = 20
- page 3, limit 20  → offset = 40
- page 5, limit 100 → offset = 400
```

## JavaScript/TypeScript примеры

**Fetch всех записей поабзацам:**
```typescript
async function getAllRecords() {
  const limit = 100;
  let offset = 0;
  let allRecords = [];

  while (true) {
    const response = await fetch(
      `http://localhost:3000/api/production/products?offset=${offset}&limit=${limit}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );

    const { products, total } = await response.json();
    allRecords.push(...products);

    if (allRecords.length >= total) break;
    offset += limit;
  }

  return allRecords;
}
```

**Пагинация в React:**
```typescript
const [items, setItems] = useState([]);
const [total, setTotal] = useState(0);
const [offset, setOffset] = useState(0);
const limit = 20;

const fetchPage = async (newOffset) => {
  const resp = await fetch(
    `${API_URL}/personnel/employees?offset=${newOffset}&limit=${limit}`
  );
  const { employees, total } = await resp.json();
  setItems(employees);
  setTotal(total);
  setOffset(newOffset);
};

const handleNextPage = () => {
  if (offset + limit < total) {
    fetchPage(offset + limit);
  }
};

const handlePrevPage = () => {
  if (offset > 0) {
    fetchPage(Math.max(0, offset - limit));
  }
};
```

## Лучшие практики

1. **Выбирайте правильный лимит:**
   - Mobile: 20-50 (экран вмещает мало)
   - Web: 50-100 (стол больше)
   - Export/Batch: до 1000

2. **Кэшируйте результаты:**
   ```typescript
   const cache = new Map();
   const getCachedPage = async (offset, limit) => {
     const key = `${offset}-${limit}`;
     if (!cache.has(key)) {
       cache.set(key, await fetch(...));
     }
     return cache.get(key);
   };
   ```

3. **Обрабатывайте изменение total:**
   - Если во время пагинации добавились новые записи, total может измениться
   - Пересчитайте количество страниц при каждом запросе

---

**Related:** [overview.md](overview.md), [../integration/client-guide.md](../integration/client-guide.md)
