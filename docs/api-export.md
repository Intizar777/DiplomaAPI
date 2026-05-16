# API Документация: Экспорт отчётов

## Обзор

Endpoints для скачивания аналитических отчётов в формате Excel (XLSX) или Word (DOCX). Каждый endpoint предназначен для конкретной роли пользователя.

**Base URL:** `/api/v1/export`

---

## Endpoints

### 1. Group Manager Report (`/gm`)

Аналитический отчёт для Group Manager.

```
GET /api/v1/export/gm
```

#### Параметры запроса

| Параметр | Тип | По умолчанию | Диапазон | Описание |
|----------|-----|--------------|----------|---------|
| `format` | string | `xlsx` | `xlsx`, `docx` | Формат файла (XLSX или DOCX) |
| `period_days` | integer | 30 | 1–365 | Период для расчёта OEE в днях |
| `date_from` | date | *вычисляется* | YYYY-MM-DD | Начало периода для плана/простоев |
| `date_to` | date | сегодня | YYYY-MM-DD | Конец периода |

#### Содержимое файла

**Excel (XLSX):**
- Лист 1: OEE по линиям
- Лист 2: Выполнение плана
- Лист 3: Простои
- Каждая строка подсвечена цветом, содержит столбец «Вывод»

**Word (DOCX):**
- Аналитический текст с выводами и рекомендациями

#### Примеры запросов

```bash
# Экспорт в Excel (30 дней)
GET /api/v1/export/gm?format=xlsx&period_days=30

# Экспорт в Word с пользовательским периодом
GET /api/v1/export/gm?format=docx&date_from=2026-04-16&date_to=2026-05-16

# Только период с расчётом OEE за 60 дней
GET /api/v1/export/gm?period_days=60
```

#### Ответ

- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (XLSX)
  или `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX)
- **Content-Disposition:** `attachment; filename="report_gm_YYYY-MM-DD.xlsx"`
- **Body:** Бинарные данные файла

---

### 2. Finance Manager Report (`/finance`)

Аналитический отчёт для Finance Manager.

```
GET /api/v1/export/finance
```

#### Параметры запроса

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|---------|
| `format` | string | `xlsx` | `xlsx` или `docx` |
| `date_from` | date | 30 дней назад | Начало периода (YYYY-MM-DD) |
| `date_to` | date | сегодня | Конец периода (YYYY-MM-DD) |

#### Содержимое файла

**Excel (XLSX):**
- Лист 1: Разбивка продаж
- Лист 2: Тренд выручки
- Лист 3: Топ продукты

**Word (DOCX):**
- Аналитический текст с выводами и рекомендациями

#### Примеры запросов

```bash
# Экспорт в Excel (последние 30 дней)
GET /api/v1/export/finance?format=xlsx

# Экспорт в Word за период
GET /api/v1/export/finance?format=docx&date_from=2026-01-01&date_to=2026-05-16
```

#### Ответ

- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (XLSX)
  или `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX)
- **Content-Disposition:** `attachment; filename="report_finance_YYYY-MM-DD.xlsx"`
- **Body:** Бинарные данные файла

---

### 3. Quality Engineer Report (`/qe`)

Аналитический отчёт для Quality Engineer.

```
GET /api/v1/export/qe
```

#### Параметры запроса

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|---------|
| `format` | string | `xlsx` | `xlsx` или `docx` |
| `date_from` | date | 30 дней назад | Начало периода (YYYY-MM-DD) |
| `date_to` | date | сегодня | Конец периода (YYYY-MM-DD) |

#### Содержимое файла

**Excel (XLSX):**
- Лист 1: Тренды параметров
- Лист 2: Анализ партий
- Лист 3: Pareto дефектов

**Word (DOCX):**
- Аналитический текст с выводами и рекомендациями

#### Примеры запросов

```bash
# Экспорт в Excel
GET /api/v1/export/qe?format=xlsx

# Экспорт в Word за период
GET /api/v1/export/qe?format=docx&date_from=2026-04-01&date_to=2026-05-16
```

#### Ответ

- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (XLSX)
  или `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX)
- **Content-Disposition:** `attachment; filename="report_qe_YYYY-MM-DD.xlsx"`
- **Body:** Бинарные данные файла

---

### 4. Line Master Report (`/line-master`)

Аналитический отчёт для Line Master.

```
GET /api/v1/export/line-master
```

#### Параметры запроса

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|---------|
| `format` | string | `xlsx` | `xlsx` или `docx` |
| `production_date` | date | сегодня | Дата для прогресса смен (YYYY-MM-DD) |
| `date_from` | date | 7 дней назад | Начало периода для сравнения/дефектов (YYYY-MM-DD) |
| `date_to` | date | сегодня | Конец периода (YYYY-MM-DD) |

#### Содержимое файла

**Excel (XLSX):**
- Лист 1: Прогресс смен
- Лист 2: Сравнение смен
- Лист 3: Сводка дефектов

**Word (DOCX):**
- Аналитический текст с выводами и рекомендациями

#### Примеры запросов

```bash
# Экспорт в Excel на сегодняшний день
GET /api/v1/export/line-master?format=xlsx

# Экспорт в Word с пользовательским периодом
GET /api/v1/export/line-master?format=docx&production_date=2026-05-15&date_from=2026-05-08&date_to=2026-05-16
```

#### Ответ

- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (XLSX)
  или `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX)
- **Content-Disposition:** `attachment; filename="report_line_master_YYYY-MM-DD.xlsx"`
- **Body:** Бинарные данные файла

---

## Общие сведения

### Форматы файлов

| Формат | MIME Type | Расширение | Применение |
|--------|-----------|-----------|-----------|
| Excel | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | `.xlsx` | Табличные данные, анализ, фильтрация |
| Word | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `.docx` | Аналитический текст, выводы, печать |

### Обработка ответа на фронтенде

#### JavaScript/TypeScript пример

```javascript
// Базовое скачивание
async function downloadReport(endpoint, format = 'xlsx', params = {}) {
  const queryParams = new URLSearchParams({
    format,
    ...params
  });
  
  const response = await fetch(`/api/v1/export/${endpoint}?${queryParams}`);
  
  if (!response.ok) {
    throw new Error(`Ошибка загрузки: ${response.statusText}`);
  }
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = response.headers.get('content-disposition')
    .split('filename=')[1]
    .replace(/"/g, '');
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

// Использование
downloadReport('gm', 'xlsx', { period_days: 60 });
downloadReport('finance', 'docx', { date_from: '2026-04-01', date_to: '2026-05-16' });
```

#### React пример с кнопкой

```jsx
import { useState } from 'react';

function ExportButton({ endpoint, label, format = 'xlsx', params = {} }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleExport = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const queryParams = new URLSearchParams({
        format,
        ...params
      });
      
      const response = await fetch(`/api/v1/export/${endpoint}?${queryParams}`);
      
      if (!response.ok) {
        throw new Error('Ошибка при загрузке отчёта');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `report_${endpoint}_${new Date().toISOString().split('T')[0]}.${format}`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={handleExport} disabled={loading}>
        {loading ? 'Загрузка...' : `Скачать ${label}`}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}
```

### Обработка ошибок

Все endpoints возвращают:

- **200 OK** — Файл успешно сгенерирован
- **400 Bad Request** — Неверные параметры (например, неправильный формат даты)
- **422 Unprocessable Entity** — Ошибка валидации (например, `period_days` вне диапазона 1-365)
- **500 Internal Server Error** — Ошибка сервера при генерации отчёта

---

## Рекомендации

1. **Кэширование:** Результаты не кэшируются на сервере. Каждый запрос генерирует новый отчёт.
2. **Таймаут:** Для больших периодов (90+ дней) может потребоваться больше времени на генерацию.
3. **Размер файла:** Word-отчёты могут быть объёмными из-за аналитического текста.
4. **Валидация дат:** Используйте формат `YYYY-MM-DD`. Если `date_from > date_to`, вернётся пустой отчёт.
5. **Параметр `period_days` (только для `/gm`):** Используется для расчёта OEE. Если указаны `date_from`/`date_to`, они переопределяют этот период.
