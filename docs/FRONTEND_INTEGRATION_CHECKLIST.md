# Frontend Integration Checklist

Используй этот чеклист при интеграции с Production Analytics API.

---

## 📋 Предварительная подготовка

- [ ] Backend запущен локально: `uvicorn app.main:app --reload`
- [ ] Frontend может обращаться к `http://localhost:3000/api/production`
- [ ] Получен JWT token для аутентификации
- [ ] Установлены зависимости: `npm install recharts` (для графиков)

**Проверка доступа:**
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:3000/api/production/production-lines
# Ответ: { "production_lines": [...], "total": N }
```

---

## 🏗️ Структура проекта

- [ ] Скопирована папка `docs/` с документацией:
  - `frontend-api-guide.md` — полный гайд
  - `FRONTEND_QUICK_REFERENCE.md` — краткая справка
  - `frontend-react-examples.tsx` — примеры компонентов
  - `frontend-api-types.ts` — TypeScript типы

- [ ] Создана структура фронтенд проекта:
  ```
  src/
    api/
      client.ts           # Класс ProductionAnalyticsAPI
      types.ts            # TypeScript типы (скопировать)
    components/
      KPIDashboard.tsx    # Основной dashboard
      SalesMargin.tsx     # Таблица маржи
      DowntimeChart.tsx   # Простои
      CampaignCard.tsx    # Промо-акции
    hooks/
      useKPI.ts           # Кастомные хуки
      useSalesMargin.ts
      useDowntime.ts
    utils/
      format.ts           # Форматирование (из types.ts)
  ```

---

## 🔐 Аутентификация

- [ ] JWT token правильно передаётся в заголовке:
  ```typescript
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
  ```

- [ ] Обработка expired token (401):
  ```typescript
  if (response.status === 401) {
    // Перенаправить на логин
  }
  ```

- [ ] Токен обновляется перед истечением

---

## 📊 Dashboard (Основная страница)

### KPI Cards

- [ ] Отображаются карточки:
  - OEE (%)
  - Брак (%)
  - OTIF (%)
  - Выпуск (т)

- [ ] Цветовая индикация статуса:
  - 🟢 ok — зелёный
  - 🟡 warning — жёлтый
  - 🔴 critical — красный

- [ ] Date picker для выбора периода:
  - По умолчанию: последние 30 дней
  - Кнопки "Today", "This Month", "Last Month"

- [ ] Отображение целевых значений (target)

### Тренд-график

- [ ] Линейный график с:
  - OEE на левой оси Y
  - Total Output на правой оси Y
  - Периоды на оси X

- [ ] Интерактивная tooltip при наведении

- [ ] Кнопки переключения гранулярности:
  - Day
  - Week
  - Month

### Change Percent (Сравнение с предпериодом)

- [ ] Отображение изменения:
  - `↑ +5.2%` (зелёный) если улучшение
  - `↓ -2.1%` (красный) если ухудшение

- [ ] Включается при включении флага `compare_with_previous=true`

---

## 🔍 KPI Breakdown (Drill-down)

- [ ] Таблица с:
  - Group key (LINE-01, Product-1, Division)
  - Value (OEE, defect rate, etc.)
  - Target (целевое значение)
  - Status (статус)
  - Deviation (отклонение от target)

- [ ] Select для выбора:
  - Group by: productionLine | product | division
  - Metric: oeeEstimate | defectRate | lineThroughput | otifRate

- [ ] Сортировка таблицы:
  - По value (по умолчанию)
  - По deviation (отклонение)
  - По status

- [ ] Пагинация (limit=20, макс 100)

---

## 💰 Продажи и Маржа

### Таблица маржинальности

- [ ] Столбцы:
  - Product Name
  - Total Quantity
  - Total Revenue (₽)
  - Total Margin (₽)
  - Margin % (с условным форматированием)
  - Margin per Unit (₽)

- [ ] Форматирование:
  - Числа с разделителем тысяч: 62,500
  - Валюта: ₽ (рубль)
  - Проценты: 50.0%

- [ ] Highlight строк с margin < 40% (жёлтый)

- [ ] Footer (Aggregated):
  - Total Revenue
  - Total Cost
  - Total Margin
  - Avg Margin %

- [ ] Date picker для фильтра по периоду

---

## ⏸️ Простои оборудования

### Pie Chart

- [ ] Круговая диаграмма с:
  - Категориями простоев
  - Общим временем (в часах)
  - Количеством событий

- [ ] Легенда с переводом категорий:
  - UNPLANNED_BREAKDOWN → "Аварийный отказ"
  - PLANNED_MAINTENANCE → "Плановое ТО"
  - QUALITY_ISSUE → "Проблемы качества"
  - MATERIAL_SHORTAGE → "Нехватка материала"
  - OTHER → "Прочее"

### Сводка

- [ ] Total events (всего событий)
- [ ] Total downtime (всего часов:минут)
- [ ] List по категориям:
  - Category: X hours (Y events)

---

## 🎯 Промо-акции

### Список кампаний

- [ ] Таблица с колонками:
  - Name
  - Channel (DIRECT, DISTRIBUTOR, etc.)
  - Discount %
  - Start Date – End Date
  - Budget (₽)

- [ ] Кнопка "View ROI" для каждой кампании

- [ ] Фильтры:
  - Channel (select)
  - Period (date range)

### ROI Card

- [ ] Отображается при клике на кампанию:
  - Campaign name
  - ROI % (большой шрифт, с цветом)
  - Budget
  - Baseline Sales
  - Sales During Campaign
  - Uplift (зелёный цвет)
  - Cost per Uplift Unit

- [ ] Цветовая индикация ROI:
  - Зелёный: ROI > 100%
  - Жёлтый: 50% ≤ ROI ≤ 100%
  - Красный: ROI < 50%

---

## 📝 Форм для регистрации

### Batch Input (Приёмка сырья)

- [ ] Поля:
  - Order ID (UUID select или input)
  - Product ID (UUID select или input)
  - Quantity (decimal input, 3 знака)
  - Input Date (datetime picker)

- [ ] Валидация:
  - Quantity > 0
  - Input Date ≤ now

- [ ] При успехе:
  - Toast: "Batch input #ID created"
  - Очистить форму

### Downtime Event (Простой)

- [ ] Поля:
  - Production Line (select)
  - Reason (text input)
  - Category (select: PLANNED_MAINTENANCE, UNPLANNED_BREAKDOWN, etc.)
  - Started At (datetime picker)
  - Ended At (datetime picker, опционально)
  - Duration (auto-calculate если есть ended_at)

- [ ] Валидация:
  - Reason не пусто
  - Started At < Ended At

- [ ] При успехе:
  - Toast: "Downtime event created"
  - Обновить список простоев

### Promo Campaign (Промо-акция)

- [ ] Поля:
  - Name (text input)
  - Description (textarea, опционально)
  - Channel (select: DIRECT, DISTRIBUTOR, RETAIL, ONLINE)
  - Product (select, опционально)
  - Discount % (number input, опционально)
  - Start Date (date picker)
  - End Date (date picker, опционально)
  - Budget (number input, опционально)

- [ ] Валидация:
  - Name не пусто
  - Start Date ≤ End Date
  - Discount 0-100 %

- [ ] При успехе:
  - Toast: "Campaign 'Name' created"
  - Перейти на страницу кампании

---

## 🚀 Производительность

- [ ] Кеширование ответов (если нужно):
  - KPI: 30 сек кеш
  - Margin: 60 сек кеш
  - Breakdown: 2 мин кеш

- [ ] Параллельные запросы:
  ```typescript
  // Загружать все данные параллельно
  const [kpi, margin, downtime] = await Promise.all([
    apiCall('/kpi?...'),
    apiCall('/sales/margin?...'),
    apiCall('/downtime-events/summary?...')
  ]);
  ```

- [ ] Ленивая загрузка:
  - Breakdown таблица загружается по требованию
  - Детали кампании загружаются при клике

- [ ] Оптимизация рендера:
  - Мемоизация компонентов (React.memo)
  - useMemo для тяжелых вычислений
  - Виртуализация больших таблиц (react-window)

---

## 🧪 Тестирование

### Unit Tests

- [ ] Тесты для утилит форматирования:
  - formatRuble(62500) → "₽ 62,500"
  - formatPercent(0.85) → "85.0%"

- [ ] Тесты для преобразования данных:
  - Проверка статусов (ok/warning/critical)
  - Расчёт deviation

### Integration Tests

- [ ] Тесты для API вызовов:
  ```typescript
  test('getKPI returns data with trend', async () => {
    const result = await api.getKPI('2026-05-01', '2026-05-31');
    expect(result.oee_estimate).toBeDefined();
    expect(result.trend).toHaveLength(31);
  });
  ```

### E2E Tests

- [ ] Сценарии:
  - Открыть dashboard → отображаются KPI cards
  - Выбрать период → обновляются графики
  - Кликнуть на кампанию → открывается ROI card
  - Заполнить форму простоя → регистрируется и обновляется pie chart

### Manual Testing

- [ ] Проверить все комбинации фильтров:
  - KPI с разными granularity (day/week/month)
  - Breakdown по разным dimensions
  - Фильтры по production_line, product, channel

- [ ] Проверить пограничные случаи:
  - Пустой период (нет данных)
  - Очень большой период (много данных)
  - Клик быстро несколько раз (дублирование запросов)

- [ ] Проверить ошибки:
  - 401 при expired token
  - 400 при неверных параметрах
  - 503 при недоступности backend

---

## 📱 Адаптивность

- [ ] Desktop (> 1200px):
  - KPI cards в 4 колонки
  - Графики полной ширины
  - Таблица со скроллом

- [ ] Tablet (768px - 1200px):
  - KPI cards в 2 колонки
  - Графики адаптивные
  - Таблица со скроллом или стекирование

- [ ] Mobile (< 768px):
  - KPI cards в 1 колонку
  - Графики с масштабированием
  - Таблица горизонтальный скролл

---

## ♿ Доступность

- [ ] ARIA labels для всех интерактивных элементов
- [ ] Контрастность текста:
  - Тёмный текст на светлом фоне (4.5:1)
  - Зелёный/жёлтый/красный доступны для дальтоников
- [ ] Keyboard навигация:
  - Tab переход между элементами
  - Enter/Space для кнопок и чекбоксов
  - Esc для закрытия модалов

---

## 🐛 Отладка

### Включить логирование

```typescript
// api/client.ts
const DEBUG = true; // Set from env

async function apiCall(endpoint, options) {
  if (DEBUG) console.log(`>> ${endpoint}`, options);
  
  const response = await fetch(...);
  
  if (DEBUG) console.log(`<< ${response.status}`, data);
  
  return response.json();
}
```

### Swagger документация

- [ ] Открыть `http://localhost:3000/docs` для интерактивного тестирования эндпоинтов

### DevTools

```javascript
// В браузере Console
import { ProductionAnalyticsAPI } from './api/types.ts';

const api = new ProductionAnalyticsAPI(
  'http://localhost:3000/api/production',
  localStorage.getItem('token')
);

// Протестировать
api.getKPI('2026-05-01', '2026-05-31').then(d => console.table(d));
```

---

## 📚 Документация для backend

Если что-то непонятно:

1. **Полный гайд:** `docs/frontend-api-guide.md`
2. **Краткая справка:** `docs/FRONTEND_QUICK_REFERENCE.md`
3. **React примеры:** `docs/frontend-react-examples.tsx`
4. **TypeScript типы:** `docs/frontend-api-types.ts`
5. **Swagger UI:** `http://localhost:3000/docs`

---

## ✅ Финальная проверка

Перед заливкой в production:

- [ ] Все компоненты работают без ошибок в консоли
- [ ] Все запросы возвращают 200/201 (нет 5xx ошибок)
- [ ] Обработаны все ошибочные статусы (400, 401, 404, 429, 503)
- [ ] Данные кешируются/обновляются корректно
- [ ] Адаптивность на всех размерах экрана
- [ ] Доступность (keyboard, screen readers, contrast)
- [ ] Performance (lighthouse > 80)
- [ ] Все тесты проходят
- [ ] Zero console errors/warnings

---

**Версия:** 2.0 | **Дата:** 2026-05-12 | **Автор:** Backend Team
