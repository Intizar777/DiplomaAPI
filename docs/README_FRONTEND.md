# Frontend Developer Guide

**Добро пожаловать!** Это ваш путеводитель по Production Analytics API.

Выберите нужный документ в зависимости от того, что вы хотите сделать.

---

## 🚀 Быстрый старт (5 минут)

Начните с **[FRONTEND_QUICK_REFERENCE.md](FRONTEND_QUICK_REFERENCE.md)**.

Там вы найдёте:
- Base URL и примеры запросов
- Top 5 эндпоинтов
- Параметры фильтрации
- Шаблон для fetch helper

```javascript
// Простой пример
const kpi = await fetch(
  '/api/production/kpi?from_date=2026-05-01&to_date=2026-05-31',
  { headers: { 'Authorization': `Bearer ${token}` } }
).then(r => r.json());

console.log(`OEE: ${(kpi.oee_estimate * 100).toFixed(1)}%`);
```

---

## 📚 Полная документация

### [Frontend API Guide](frontend-api-guide.md) — 50+ страниц примеров

Полный справочник всех эндпоинтов с примерами кода:

1. **KPI Метрики** (OEE, дефекты, OTIF)
   - Основные показатели
   - OTIF (On-Time In-Full)
   - Drill-down по линиям/продуктам/дивизионам
   - Производительность линии
   - Процент брака

2. **Продажи и маржа**
   - Маржинальность по продуктам

3. **Сырьевой учёт (Batch Input)**
   - Регистрация приёмки
   - Выход готовой продукции (yield)
   - Список приёмок

4. **Простои оборудования**
   - Регистрация простоя
   - Сводка по категориям
   - Список простоев

5. **Промо-акции**
   - Создание кампании
   - Список кампаний
   - ROI и эффективность

6. **Справочники**
   - Производственные линии
   - Фильтрация и параметры
   - Цветовая индикация (Traffic Light)

7. **Примеры**
   - cURL запросы
   - JavaScript примеры
   - Полный React dashboard

---

## 💻 React Компоненты

### [Frontend React Examples](frontend-react-examples.tsx) — Готовый код

Скопируй готовые компоненты:

```typescript
import { KPIDashboard, SalesMarginTable, CampaignEffectiveness } from './components';

export default function App({ token }) {
  return (
    <>
      <KPIDashboard token={token} />
      <SalesMarginTable token={token} />
    </>
  );
}
```

**Включает:**
- `KPIDashboard` — полный dashboard с KPI cards, трендом, простоями
- `SalesMarginTable` — таблица маржинальности
- `KPICard` — карточка с цветовой индикацией
- Кастомные hooks: `useKPI`, `useSalesMargin`, `useDowntime`
- Утилиты форматирования и преобразования

**Компоненты используют:**
- Recharts для графиков
- React hooks для состояния
- Встроенные стили (можно переделать на CSS)

---

## 📘 TypeScript типы

### [Frontend API Types](frontend-api-types.ts) — Типы + API класс

Полный набор типов для всех ответов API:

```typescript
import {
  KPIResponse,
  OTIFResponse,
  SalesMarginResponse,
  ProductionAnalyticsAPI,
  formatRuble,
  formatPercent
} from './api/types';

// Использование класса
const api = new ProductionAnalyticsAPI(
  'http://localhost:3000/api/production',
  token
);

const kpi: KPIResponse = await api.getKPI('2026-05-01', '2026-05-31');
const margin: SalesMarginResponse = await api.getSalesMargin(...);

// Форматирование
console.log(formatRuble(62500));      // ₽ 62,500
console.log(formatPercent(0.85));     // 85.0%
```

**API класс содержит методы для:**
- KPI (getKPI, getOTIF, getKPIBreakdown, getLineProductivity, getScrapPercentage)
- Sales (getSalesMargin)
- Batch Inputs (createBatchInput, listBatchInputs, getYield)
- Downtime Events (createDowntimeEvent, listDowntimeEvents, getDowntimeSummary)
- Promo Campaigns (createPromoCampaign, listPromoCampaigns, getCampaignEffectiveness)
- Reference Data (listProductionLines)

---

## ✅ Integration Checklist

### [Frontend Integration Checklist](FRONTEND_INTEGRATION_CHECKLIST.md) — Чеклист

Используй этот чеклист при разработке:

1. ✅ **Предварительная подготовка** (backend, JWT, зависимости)
2. ✅ **Структура проекта** (папки, компоненты, хуки)
3. ✅ **Аутентификация** (Bearer token, обработка 401)
4. ✅ **Dashboard** (KPI cards, тренд, цвета)
5. ✅ **Drill-down** (таблица, фильтры, сортировка)
6. ✅ **Маржа** (таблица, агрегация)
7. ✅ **Простои** (pie chart, сводка)
8. ✅ **Промо-акции** (список, ROI card)
9. ✅ **Формы** (batch input, downtime, campaign)
10. ✅ **Производительность** (кеш, параллельные запросы)
11. ✅ **Тестирование** (unit, integration, e2e)
12. ✅ **Адаптивность** (desktop, tablet, mobile)
13. ✅ **Доступность** (ARIA, контраст, keyboard)
14. ✅ **Финальная проверка** (ошибки, performance)

---

## 📍 Структура документов

```
docs/
├── README_FRONTEND.md                     ← Вы здесь
├── FRONTEND_QUICK_REFERENCE.md            ← Краткая справка (5 мин)
├── frontend-api-guide.md                  ← Полный гайд (50+ стр)
├── frontend-react-examples.tsx            ← Готовые компоненты
├── frontend-api-types.ts                  ← TypeScript типы
├── FRONTEND_INTEGRATION_CHECKLIST.md       ← Чеклист
├── analytics-api.md                       ← Основная документация
├── kpi-assessment.md                      ← KPI описание
└── ...
```

---

## 🔗 Как начать

### Вариант 1: Быстро (30 мин)

1. Прочитайте **[FRONTEND_QUICK_REFERENCE.md](FRONTEND_QUICK_REFERENCE.md)**
2. Скопируйте **[frontend-api-types.ts](frontend-api-types.ts)** в ваш проект как `src/api/types.ts`
3. Используйте класс `ProductionAnalyticsAPI` для запросов
4. Протестируйте на Swagger: `http://localhost:3000/docs`

### Вариант 2: Подробно (2-3 часа)

1. Прочитайте **[Frontend API Guide](frontend-api-guide.md)** полностью
2. Посмотрите примеры в **[frontend-react-examples.tsx](frontend-react-examples.tsx)**
3. Скопируйте готовые компоненты
4. Используйте **[Integration Checklist](FRONTEND_INTEGRATION_CHECKLIST.md)** при разработке
5. Следуйте паттернам для каждой страницы/компонента

### Вариант 3: С нуля

1. Создайте структуру папок (см. Integration Checklist)
2. Установите зависимости: `npm install recharts`
3. Скопируйте типы и класс API
4. Скопируйте компоненты из примеров
5. Адаптируйте под ваш дизайн и требования

---

## 🎯 API Endpoint Map

| Фичча | Эндпоинт | Метод | Для кого |
|-------|----------|-------|---------|
| KPI карточки | `/kpi` | GET | Dashboard |
| OTIF метрика | `/kpi/otif` | GET | Dashboard |
| Drill-down | `/kpi/breakdown` | GET | Analytics |
| Производительность | `/kpi/line-productivity` | GET | Analytics |
| Брак % | `/kpi/scrap-percentage` | GET | Analytics |
| Маржа | `/sales/margin` | GET | Sales page |
| Приёмка сырья | `/batch-inputs` | POST/GET | Operations |
| Выход продукции | `/batch-inputs/yield` | GET | Operations |
| Простой | `/downtime-events` | POST/GET | Operations |
| Сводка простоев | `/downtime-events/summary` | GET | Dashboard |
| Промо-акция | `/promo-campaigns` | POST/GET | Marketing |
| ROI акции | `/promo-campaigns/{id}/effectiveness` | GET | Marketing |
| Линии | `/production-lines` | GET | Reference |

---

## 🐛 Частые вопросы

### Q: Какой token использовать?
**A:** Bearer token из JWT. Получите от backend в процессе логина.

### Q: Какой период по умолчанию?
**A:** Если не указан, используйте последние 30 дней.

### Q: Как обновлять данные в реальном времени?
**A:** Используйте polling через `setInterval` или React Query/SWR. SSE планируется в Phase 4.

### Q: Какой maximum limit для пагинации?
**A:** 100 записей максимум (le=100 в параметрах).

### Q: Как форматировать денежные значения?
**A:** Используйте `formatRuble()` из types.ts: `formatRuble(62500)` → "₽ 62,500"

### Q: Как интерпретировать status?
**A:** 
- 🟢 `ok` — значение соответствует target
- 🟡 `warning` — ниже target, но выше min
- 🔴 `critical` — ниже min или выше max

### Q: Можно ли экспортировать данные?
**A:** Функции экспорта планируются в будущих версиях. Сейчас можно скопировать таблицу вручную или использовать API напрямую.

---

## 📞 Support

Если что-то непонятно:

1. Проверьте **[FRONTEND_QUICK_REFERENCE.md](FRONTEND_QUICK_REFERENCE.md)**
2. Посмотрите примеры в **[frontend-api-guide.md](frontend-api-guide.md)**
3. Протестируйте эндпоинт на **Swagger UI**: `http://localhost:3000/docs`
4. Проверьте типы в **[frontend-api-types.ts](frontend-api-types.ts)**

---

## 🚀 Next Steps

- [ ] Прочитать Quick Reference
- [ ] Скопировать types.ts в проект
- [ ] Создать первый компонент KPIDashboard
- [ ] Протестировать на Swagger
- [ ] Интегрировать с вашей аутентификацией
- [ ] Следовать Integration Checklist
- [ ] Запустить тесты
- [ ] Деплоить в production

---

**Версия:** 2.0 (Phase 2-3)  
**Дата:** 2026-05-12  
**Статус:** Production Ready ✅

Удачи! 🎉
