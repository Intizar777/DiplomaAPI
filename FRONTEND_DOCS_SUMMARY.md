# Frontend Documentation Summary

**Дата создания:** 2026-05-12  
**Версия API:** Phase 2-3 (Production)

---

## 📁 Созданные документы

| Файл | Размер | Назначение |
|------|--------|-----------|
| `docs/README_FRONTEND.md` | Индекс | Главный вход для фронтенд разработчиков |
| `docs/FRONTEND_QUICK_REFERENCE.md` | 2 стр | Краткая справка (5 минут чтения) |
| `docs/frontend-api-guide.md` | 50 стр | Полный гайд со всеми примерами |
| `docs/frontend-react-examples.tsx` | 400+ строк | Готовые React компоненты |
| `docs/frontend-api-types.ts` | 500+ строк | TypeScript типы + API класс |
| `docs/FRONTEND_INTEGRATION_CHECKLIST.md` | 30 стр | Чеклист для разработки и тестирования |

---

## 🎯 Что может использовать frontend

### KPI & Analytics (7 эндпоинтов)

```javascript
GET /api/production/kpi                    // OEE, дефекты, OTIF, тренд
GET /api/production/kpi/otif               // On-Time In-Full метрики
GET /api/production/kpi/breakdown          // Drill-down по линиям/продуктам
GET /api/production/kpi/line-productivity  // Производительность (т/ч)
GET /api/production/kpi/scrap-percentage   // Процент брака
GET /api/production/sales/margin           // Маржинальность по продуктам
GET /api/production/production-lines       // Справочник производственных линий
```

### Операционные данные (6 эндпоинтов)

```javascript
POST /api/production/batch-inputs          // Регистрация приёмки сырья
GET  /api/production/batch-inputs          // Список приёмок
GET  /api/production/batch-inputs/yield    // Выход готовой продукции
POST /api/production/downtime-events       // Регистрация простоя
GET  /api/production/downtime-events       // Список простоев
GET  /api/production/downtime-events/summary  // Сводка по категориям
```

### Маркетинг (3 эндпоинта)

```javascript
POST /api/production/promo-campaigns       // Создать промо-акцию
GET  /api/production/promo-campaigns       // Список кампаний
GET  /api/production/promo-campaigns/{id}/effectiveness  // ROI и эффективность
```

**Всего:** 16 эндпоинтов для использования фронтендом

---

## 📊 Структура данных

### Основной KPI ответ
```json
{
  "oee_estimate": 0.825,              // OEE (0-1)
  "defect_rate": 0.012,               // Брак (0-1)
  "total_output": 1250.5,             // Выпуск (т)
  "targets": {                         // Целевые значения
    "oee_estimate": { "target": 0.85, "status": "warning" }
  },
  "trend": [                           // Данные для графика
    { "period": "2026-05-01", "oee_estimate": 0.83 }
  ]
}
```

### Статусы (Traffic Light)
- 🟢 `ok` — в норме
- 🟡 `warning` — ниже target
- 🔴 `critical` — критичный

### Обязательные параметры
```
from_date: YYYY-MM-DD (обязательно для большинства GET)
to_date: YYYY-MM-DD
Authorization: Bearer <token>
```

---

## 💡 Примеры использования

### React Hook для KPI
```typescript
const { kpi, loading, error } = useKPI('2026-05-01', '2026-05-31', token);

if (loading) return <div>Загрузка...</div>;

return (
  <div>
    <h1>OEE: {(kpi.oee_estimate * 100).toFixed(1)}%</h1>
    <div style={{ color: kpi.targets.oee_estimate.status === 'ok' ? 'green' : 'red' }}>
      Target: {(kpi.targets.oee_estimate.target * 100).toFixed(1)}%
    </div>
  </div>
);
```

### TypeScript класс API
```typescript
import { ProductionAnalyticsAPI } from './api/types';

const api = new ProductionAnalyticsAPI(
  'http://localhost:3000/api/production',
  token
);

// Все методы типизированы
const kpi = await api.getKPI('2026-05-01', '2026-05-31');
const margin = await api.getSalesMargin('2026-05-01', '2026-05-31');
const downtime = await api.getDowntimeSummary('2026-05-01', '2026-05-31');
```

### Регистрация данных
```typescript
// Приёмка сырья
await api.createBatchInput({
  order_id: uuid,
  product_id: uuid,
  quantity: 1000.5,
  input_date: new Date().toISOString()
});

// Простой оборудования
await api.createDowntimeEvent({
  production_line_id: uuid,
  reason: 'Поломка вала',
  category: 'UNPLANNED_BREAKDOWN',
  started_at: '2026-05-10T08:30:00Z'
});

// Промо-акция
await api.createPromoCampaign({
  name: 'Скидка 10%',
  channel: 'DIRECT',
  discount_percent: 10,
  start_date: '2026-05-01'
});
```

---

## 🎨 Готовые компоненты

### Из `frontend-react-examples.tsx`

1. **`KPIDashboard`** — полный dashboard
   - KPI cards (OEE, брак, OTIF, выпуск)
   - Тренд-график
   - Date picker
   - Распределение простоев (pie chart)

2. **`SalesMarginTable`** — таблица маржи
   - По продуктам
   - Выручка, себестоимость, маржа
   - Агрегация по периоду

3. **`CampaignEffectiveness`** — карточка ROI
   - ROI % с цветом
   - Бюджет, uplift, baseline

4. **Утилиты**
   - `useKPI()` — hook для KPI
   - `useSalesMargin()` — hook для маржи
   - `useDowntime()` — hook для простоев
   - `formatRuble()`, `formatPercent()` — форматирование

---

## 🛠️ Инструменты

### Swagger UI (интерактивное тестирование)
```
http://localhost:3000/docs
```

### API класс
```typescript
const api = new ProductionAnalyticsAPI(baseUrl, token);

// Все методы уже готовы:
api.getKPI(...)
api.getOTIF(...)
api.getKPIBreakdown(...)
api.getSalesMargin(...)
api.createBatchInput(...)
api.getDowntimeSummary(...)
api.createPromoCampaign(...)
api.getCampaignEffectiveness(...)
// и др.
```

---

## 📋 Чеклист по папкам

Frontend проект должен содержать:

```
src/
├── api/
│   ├── types.ts           # Скопировать из docs/frontend-api-types.ts
│   └── client.ts          # Создать класс ProductionAnalyticsAPI
├── components/
│   ├── KPIDashboard.tsx   # Скопировать из примеров
│   ├── SalesMargin.tsx    # Создать на основе примера
│   ├── Downtime.tsx       # Создать на основе примера
│   └── Campaigns.tsx      # Создать на основе примера
├── hooks/
│   ├── useKPI.ts          # Скопировать из примеров
│   ├── useSalesMargin.ts  # Скопировать из примеров
│   └── useDowntime.ts     # Скопировать из примеров
├── utils/
│   └── format.ts          # Утилиты форматирования
└── pages/
    ├── Dashboard.tsx      # KPI Dashboard
    ├── Analytics.tsx      # Drill-down, breakdown
    ├── Sales.tsx          # Маржинальность
    ├── Operations.tsx     # Формы ввода (batch, downtime)
    └── Marketing.tsx      # Промо-акции
```

---

## 🚀 Быстрый запуск фронтенда

1. **Копируем документы**
   ```bash
   cp docs/frontend-api-types.ts src/api/types.ts
   ```

2. **Создаём компоненты** на основе примеров из `frontend-react-examples.tsx`

3. **Интегрируем класс API**
   ```typescript
   import { ProductionAnalyticsAPI } from './api/types';
   
   const api = new ProductionAnalyticsAPI(
     'http://localhost:3000/api/production',
     localStorage.getItem('token')
   );
   ```

4. **Используем в компонентах**
   ```typescript
   useEffect(() => {
     api.getKPI('2026-05-01', '2026-05-31')
       .then(setKpi)
       .catch(setError);
   }, []);
   ```

5. **Следуем чеклисту** из `FRONTEND_INTEGRATION_CHECKLIST.md`

---

## 📊 What's Next

### Для backend (когда frontend будет готов):
- [ ] Интеграция с фронтенд репозиторием
- [ ] Настройка CORS для фронтенда
- [ ] API документация на фронтенд сайт
- [ ] Swagger OpenAPI schema для codegen

### Для фронтенда (Phase 4):
- [ ] Реал-тайм обновления (SSE/WebSocket)
- [ ] Кеширование с React Query/SWR
- [ ] Экспорт в PDF/Excel
- [ ] Расширенные фильтры
- [ ] Сохранение фильтров (localStorage)

---

## 📚 Где что искать

| Нужно | Документ |
|------|----------|
| Быстро начать | `FRONTEND_QUICK_REFERENCE.md` |
| Увидеть пример | `frontend-react-examples.tsx` |
| Полный гайд | `frontend-api-guide.md` |
| Типы и класс | `frontend-api-types.ts` |
| Чеклист | `FRONTEND_INTEGRATION_CHECKLIST.md` |
| Индекс | `README_FRONTEND.md` |

---

## ✅ Достижения

**Phase 2-3 реализована полностью:**

✅ OEE (Общая эффективность оборудования)  
✅ Выход масла с тонны семян (yield)  
✅ OTIF (On-Time In-Full)  
✅ Эффективность промо-акций (ROI)  
✅ Производительность линии (т/ч)  
✅ Процент брака (defect rate)  
✅ Время простоев (downtime summary)  
✅ Объём продаж и маржинальность  
✅ KPI Breakdown + Division (drill-down)  
✅ Batch Input + Downtime Events  
✅ Тренды и графики  
✅ Цветовая индикация (Traffic Light)  
✅ Полная документация для frontend  

---

## 🎯 Стартовая точка

**Для фронтенд разработчика:**

👉 Начните с **`docs/README_FRONTEND.md`**

Далее выбирайте:
- **5 минут?** → `FRONTEND_QUICK_REFERENCE.md`
- **30 минут?** → `frontend-api-guide.md`
- **Готовый код?** → `frontend-react-examples.tsx`
- **Типизация?** → `frontend-api-types.ts`
- **Разработка?** → `FRONTEND_INTEGRATION_CHECKLIST.md`

---

**Версия:** 2.0  
**Статус:** ✅ Production Ready  
**Дата:** 2026-05-12  
**Автор:** Backend Team
