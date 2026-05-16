# План: Добавить графики в отчеты

**Дата:** 2026-05-16  
**Статус:** Планирование  
**Приоритет:** P2 (улучшение качества отчетов)

---

## 1. Обзор задачи

Добавить визуализацию данных (графики) в Excel и Word отчеты для 4 ролей:
- Group Manager (3 отчета)
- Finance Manager (3 отчета)
- Quality Engineer (3 отчета)
- Line Master (3 отчета)

**Текущее состояние:** Отчеты содержат только таблицы с цветовой индексацией.  
**Целевое состояние:** Каждый отчет содержит 3 релевантных графика + таблица.

---

## 2. Стратегия реализации

### 2.1 Выбор инструментов
- **matplotlib** — генерация статичных PNG графиков (универсальное решение)
- **openpyxl** — встроение PNG в Excel через `Drawing` + `Image`
- **python-docx** — встроение PNG в Word через `add_picture()`

### 2.2 Архитектура
```
app/services/dashboard_export_service.py (существует)
├── Добавить методы-генераторы графиков:
│   ├── _chart_oee_bars()
│   ├── _chart_plan_combo()
│   ├── _chart_downtime_pareto()
│   └── ... еще 9 методов по ролям
│
└── Встроить графики в Excel/Word:
    ├── _excel_gm() — добавить 3 графика
    ├── _word_gm() — добавить 3 графика
    ├── _excel_finance() — добавить 3 графика
    ├── _word_finance() — добавить 3 графика
    ├── ... и т.д.
```

### 2.3 Процесс генерации PNG графиков
1. Функция `_generate_chart()` принимает:
   - Тип графика (bar, line, pie, pareto, combo, barh)
   - Данные (список x/y, список объектов или словарь)
   - Заголовок, оси, легенда
   - Размер, цвета (RGB или hex)
2. Возвращает: **bytes** (PNG в памяти, не сохраняем на диск)
3. Встраиваем PNG одинаково в Excel и Word

### 2.4 Word-специфичные детали
- **Встраивание:** `doc.add_picture(BytesIO(png_bytes), width=Inches(5.5))`
- **Размер:** 5.5 дюймов ширины (стандартный для A4)
- **Размещение:** После заголовка раздела, перед текстом вывода
- **Отступ:** добавлять `doc.add_paragraph()` перед/после для отступов
- **Легенда:** встроить в сам PNG (не использовать `doc.add_table()`)
- **Шрифт на графике:** использовать `plt.rcParams['font.family'] = 'DejaVu Sans'` для поддержки кириллицы

### 2.5 Excel-специфичные детали
- **Встраивание:** `ws.add_image(Image(BytesIO(png_bytes)), 'J2')`
- **Размер:** 8 дюймов ширины (может занимать 4-5 колонок)
- **Позиция:** справа от таблицы (колонка J) или на отдельном листе
- **Масштаб:** 100% (опционально: `img.width = Cm(15)`)
- **Перенос:** графики не должны перекрывать таблицы

---

## 3. Спецификация графиков

### Group Manager
| # | Лист | График | Тип | Данные |
|---|------|--------|-----|--------|
| 1 | OEE по линиям | Столбцы OEE + линия целей (75%) | bar + line | `oee.lines[].avg_oee` |
| 2 | Выполнение плана | План vs факт + % выполнения | combo | `plan.lines[].target/actual/pct` |
| 3 | Простои | Парето часов простоя | bar + cumsum | `downtime.lines[].hours` |

### Finance Manager
| # | Лист | График | Тип | Данные |
|---|------|--------|-----|--------|
| 4 | Разбивка продаж | Круг (доля) + столбцы (выручка) | pie + bar | `breakdown.groups[].pct + amount` |
| 5 | Тренд выручки | Линия выручки + столбцы MoM | line + bar | `trend.data[].amount + mom_growth` |
| 6 | Топ продукты | Горизонтальные столбцы топ-10 | barh | `products.products[0:10]` |

### Quality Engineer
| # | Лист | График | Тип | Данные |
|---|------|--------|-----|--------|
| 7 | Тренды параметров | Столбцы % + пороги (5%, 10%) | bar | `trends.parameters[].out_of_spec_pct` |
| 8 | Анализ партий | Спарклайн тренда партий | sparkline | `batches.lots[].fail_count` |
| 9 | Pareto дефектов | Классическая Парето (80%) | bar + line | `pareto.parameters[].cumulative_pct` |

### Line Master
| # | Лист | График | Тип | Данные |
|---|------|--------|-----|--------|
| 10 | Прогресс смен | Столбцы кол-во + линия дефектности % | combo | `progress.shifts[].qty + defect_rate` |
| 11 | Сравнение смен | Линия динамики по дням | line | `comparison.shifts[].qty` |
| 12 | Сводка дефектов | Горизонтальные столбцы + порог | barh | `defects.items[].fail_rate` |

---

## 4. План реализации

### Этап 1: Инфраструктура (1-2 часа)

**Файл: `app/services/dashboard_export_service.py`**

1. Добавить импорты:
   ```python
   import matplotlib.pyplot as plt
   import matplotlib.dates as mdates
   from io import BytesIO
   from openpyxl.drawing.image import Image as XLImage
   from docx.shared import Inches
   ```

2. Настроить matplotlib для поддержки кириллицы:
   ```python
   plt.rcParams['font.family'] = 'DejaVu Sans'
   plt.rcParams['axes.unicode_minus'] = False
   ```

3. Добавить базовый метод генерации PNG:
   ```python
   def _generate_chart(self, chart_type: str, **kwargs) -> bytes:
       """Generate matplotlib chart → PNG bytes (no file save)."""
       fig, ax = plt.subplots(figsize=kwargs.get('figsize', (10, 6)))
       # ... рисование графика по chart_type ...
       buf = BytesIO()
       fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white')
       plt.close(fig)
       buf.seek(0)
       return buf
   ```

4. Добавить helper для встраивания в Excel:
   ```python
   def _add_chart_to_excel(self, ws, png_bytes: bytes, position: str = 'A1', width: int = 8):
       """Embed PNG in Excel sheet at position (width in cm)."""
       from openpyxl.drawing.image import Image
       from docx.shared import Cm
       img = XLImage(BytesIO(png_bytes))
       img.width = Cm(width)
       ws.add_image(img, position)
   ```

5. Добавить helper для встраивания в Word:
   ```python
   def _add_chart_to_word(self, doc, png_bytes: bytes, width: float = 5.5):
       """Embed PNG in Word document (width in inches)."""
       doc.add_picture(BytesIO(png_bytes), width=Inches(width))
       doc.add_paragraph()  # spacing
   ```

### Этап 2: Group Manager (2-3 часа)

**Методы добавить в `DashboardExportService`:**

```python
def _chart_gm_oee_bars(self, oee: OEESummaryResponse) -> bytes:
    """Bar chart: OEE by line + horizontal line at 75% target."""
    x = [l.production_line or f"Line {i}" for i, l in enumerate(oee.lines)]
    y = [float(l.avg_oee) for l in oee.lines]
    # ... matplotlib code с plt.barh() и plt.axhline(75) ...

def _chart_gm_plan_combo(self, plan: PlanExecutionResponse) -> bytes:
    """Combo: bars for plan/actual, line for fulfillment %."""
    # ... использовать ax.bar() + ax2.plot() ...

def _chart_gm_downtime_pareto(self, downtime: DowntimeRankingResponse) -> bytes:
    """Pareto: bars for delay hours, line for cumulative %."""
    # ... calculate cumulative, plot bars + line ...
```

**Обновить Excel метод `_excel_gm()`:**
```python
# После строк ws1 (OEE по линиям):
self._autofit(ws1)
chart_png = self._chart_gm_oee_bars(oee)
self._add_chart_to_excel(ws1, chart_png, position='J2', width=8)

# После ws2 (Выполнение плана):
chart_png = self._chart_gm_plan_combo(plan)
self._add_chart_to_excel(ws2, chart_png, position='J2', width=8)

# После ws3 (Простои):
chart_png = self._chart_gm_downtime_pareto(downtime)
self._add_chart_to_excel(ws3, chart_png, position='J2', width=8)
```

**Обновить Word метод `_word_gm()`:**
```python
# После section 1 (OEE) — добавить перед plan_conclusion:
chart_png = self._chart_gm_oee_bars(oee)
doc.add_picture(BytesIO(chart_png), width=Inches(5.5))
doc.add_paragraph()  # spacing перед "Вывод:"

# Аналогично для section 2 и 3:
chart_png = self._chart_gm_plan_combo(plan)
doc.add_picture(BytesIO(chart_png), width=Inches(5.5))
doc.add_paragraph()

chart_png = self._chart_gm_downtime_pareto(downtime)
doc.add_picture(BytesIO(chart_png), width=Inches(5.5))
doc.add_paragraph()
```

**Структура Word отчета (новая):**
```
1. ОБЩАЯ ЭФФЕКТИВНОСТЬ ОБОРУДОВАНИЯ (OEE)
   [ГРАФИК: столбцы OEE по линиям]
   • {line1}: OEE...
   • {line2}: OEE...
   Вывод: ...
   Рекомендации: ...

2. ВЫПОЛНЕНИЕ ПРОИЗВОДСТВЕННОГО ПЛАНА
   [ГРАФИК: комбинированная диаграмма]
   • {line1}: план...
   Вывод: ...
   
3. ПРОСТОИ И ЗАДЕРЖКИ ПРОИЗВОДСТВА
   [ГРАФИК: парето]
   • {line1}: часы...
   Вывод: ...

ИТОГОВЫЙ ВЫВОД И РЕКОМЕНДАЦИИ
```

### Этап 3: Finance Manager (2-3 часа)

**Методы добавить в `DashboardExportService`:**

```python
def _chart_finance_sales_pie(self, breakdown: SalesBreakdownResponse) -> bytes:
    """Pie chart: sales share by channel (with labels %)."""

def _chart_finance_trend_line(self, trend: RevenueTrendResponse) -> bytes:
    """Combo: line for revenue, bars for MoM growth %."""

def _chart_finance_top_barh(self, products: TopProductsResponse) -> bytes:
    """Horizontal bars: top 10 products by revenue."""
```

**Excel `_excel_finance()`:**
```python
# После ws1 (Разбивка продаж):
chart_png = self._chart_finance_sales_pie(breakdown)
self._add_chart_to_excel(ws1, chart_png, position='J2', width=8)

# После ws2 (Тренд выручки):
chart_png = self._chart_finance_trend_line(trend)
self._add_chart_to_excel(ws2, chart_png, position='J2', width=8)

# После ws3 (Топ продукты):
chart_png = self._chart_finance_top_barh(products)
self._add_chart_to_excel(ws3, chart_png, position='J2', width=8)
```

**Word `_word_finance()`:**
```python
# После заголовка "1. РАЗБИВКА ПРОДАЖ ПО КАНАЛАМ" и перед bullets:
chart_png = self._chart_finance_sales_pie(breakdown)
self._add_chart_to_word(doc, chart_png, width=5.5)

# После заголовка "2. ТРЕНД ВЫРУЧКИ":
chart_png = self._chart_finance_trend_line(trend)
self._add_chart_to_word(doc, chart_png, width=5.5)

# После заголовка "3. ТОП ПРОДУКТОВ ПО ВЫРУЧКЕ":
chart_png = self._chart_finance_top_barh(products)
self._add_chart_to_word(doc, chart_png, width=5.5)
```

### Этап 4: Quality Engineer (2-3 часа)

**Методы добавить в `DashboardExportService`:**

```python
def _chart_qe_params_bars(self, trends: ParameterTrendsResponse) -> bytes:
    """Bar chart: out-of-spec % by parameter + threshold lines (5%, 10%)."""

def _chart_qe_batches_timeline(self, batches: BatchAnalysisResponse) -> bytes:
    """Line chart: fail count trend across batches (x=batch_idx, y=fail_count)."""

def _chart_qe_pareto(self, pareto: DefectParetoResponse) -> bytes:
    """Pareto: bars for defects, line for cumulative % (80% marker)."""
```

**Excel `_excel_qe()`:**
```python
# После ws1 (Тренды параметров):
chart_png = self._chart_qe_params_bars(trends)
self._add_chart_to_excel(ws1, chart_png, position='J2', width=8)

# После ws2 (Анализ партий) — вместо спарклайнов использовать линию:
chart_png = self._chart_qe_batches_timeline(batches)
self._add_chart_to_excel(ws2, chart_png, position='J2', width=8)

# После ws3 (Pareto):
chart_png = self._chart_qe_pareto(pareto)
self._add_chart_to_excel(ws3, chart_png, position='J2', width=8)
```

**Word `_word_qe()`:**
```python
# После заголовка "1. ТРЕНДЫ ПАРАМЕТРОВ КАЧЕСТВА":
chart_png = self._chart_qe_params_bars(trends)
self._add_chart_to_word(doc, chart_png, width=5.5)

# После заголовка "2. АНАЛИЗ ПАРТИЙ С ОТКЛОНЕНИЯМИ":
chart_png = self._chart_qe_batches_timeline(batches)
self._add_chart_to_word(doc, chart_png, width=5.5)

# После заголовка "3. PARETO-АНАЛИЗ ДЕФЕКТОВ":
chart_png = self._chart_qe_pareto(pareto)
self._add_chart_to_word(doc, chart_png, width=5.5)
```

### Этап 5: Line Master (2-3 часа)

**Методы добавить в `DashboardExportService`:**

```python
def _chart_lm_shift_combo(self, progress: ShiftProgressResponse) -> bytes:
    """Combo: bars for output (кг), line for defect rate % by shift."""

def _chart_lm_comparison_line(self, comparison: ShiftComparisonResponse) -> bytes:
    """Line chart: output (кг) trend over production dates."""

def _chart_lm_defects_barh(self, defects: DefectSummaryResponse) -> bytes:
    """Horizontal bars: fail rate % by parameter + 5%/10% thresholds."""
```

**Excel `_excel_line_master()`:**
```python
# После ws1 (Прогресс смен):
chart_png = self._chart_lm_shift_combo(progress)
self._add_chart_to_excel(ws1, chart_png, position='J2', width=8)

# После ws2 (Сравнение смен):
chart_png = self._chart_lm_comparison_line(comparison)
self._add_chart_to_excel(ws2, chart_png, position='J2', width=8)

# После ws3 (Сводка дефектов):
chart_png = self._chart_lm_defects_barh(defects)
self._add_chart_to_excel(ws3, chart_png, position='J2', width=8)
```

**Word `_word_line_master()`:**
```python
# После заголовка "1. ПРОГРЕСС СМЕН":
chart_png = self._chart_lm_shift_combo(progress)
self._add_chart_to_word(doc, chart_png, width=5.5)

# В section 2 — добавить график перед существующей таблицей:
# (переделать _word_section() или добавить график вручную)
doc.add_heading("2. СРАВНЕНИЕ СМЕН", 2)
chart_png = self._chart_lm_comparison_line(comparison)
self._add_chart_to_word(doc, chart_png, width=5.5)
# Далее существующий текст

# После заголовка "2. СВОДКА ДЕФЕКТОВ ПО ПАРАМЕТРАМ":
chart_png = self._chart_lm_defects_barh(defects)
self._add_chart_to_word(doc, chart_png, width=5.5)
```

### Этап 6: Тестирование (2-3 часа)

**Чек-лист для каждого отчета:**

**Для Excel:**
- ✅ Файл открывается в LibreOffice Calc/MS Excel без ошибок
- ✅ Все 3 листа присутствуют (OEE, План, Простои и т.д.)
- ✅ На каждом листе PNG график виден рядом с таблицей (справа)
- ✅ Графики не перекрывают друг друга и таблицы
- ✅ Размер PNG приемлемый (не размыт, не обрезан)
- ✅ Кириллица на осях графиков отображается корректно
- ✅ Диапазон значений на осях соответствует данным в таблице

**Для Word:**
- ✅ Файл открывается в LibreOffice Writer/MS Word без ошибок
- ✅ Все 4 раздела присутствуют
- ✅ Над каждым разделом или после заголовка есть соответствующий PNG
- ✅ Размер изображений одинаков (5.5 дюймов)
- ✅ Между графиком и текстом "Вывод:" есть отступ
- ✅ Кириллица на графиках читаема (DejaVu Sans)
- ✅ Текст (Вывод, Рекомендации) не накладывается на изображение

**Unit-тесты в `tests/test_dashboard_export_service.py`:**
```python
import zipfile

def test_export_gm_excel_has_images():
    """Check that images are embedded in .xlsx."""
    data = await service.export_gm('xlsx', 30, df, dt)
    with zipfile.ZipFile(BytesIO(data)) as z:
        # .xlsx это ZIP, images хранятся в xl/media/
        assert any('image' in f for f in z.namelist())

def test_export_gm_word_has_images():
    """Check that images are in .docx."""
    data = await service.export_gm('docx', 30, df, dt)
    with zipfile.ZipFile(BytesIO(data)) as z:
        # .docx это ZIP, images в word/media/
        media_files = [f for f in z.namelist() if 'media' in f]
        assert len(media_files) >= 3  # минимум 3 графика

def test_chart_generation_returns_bytes():
    """Test that chart generation methods return valid PNG bytes."""
    chart_bytes = service._chart_gm_oee_bars(mock_oee_data)
    assert isinstance(chart_bytes, bytes)
    assert chart_bytes[:4] == b'\x89PNG'  # PNG magic number
```

**Ручное тестирование:**
```bash
# Скачать отчеты
curl 'http://localhost:8000/api/v1/export/gm?format=xlsx' -o /tmp/report_gm.xlsx
curl 'http://localhost:8000/api/v1/export/gm?format=docx' -o /tmp/report_gm.docx
curl 'http://localhost:8000/api/v1/export/finance?format=xlsx' -o /tmp/report_fin.xlsx
# ... и т.д.

# Проверить что это валидные файлы
file /tmp/report_gm.xlsx   # должен быть ZIP
file /tmp/report_gm.docx   # должен быть ZIP

# Распаковать и проверить наличие media
unzip -l /tmp/report_gm.xlsx | grep -i media
unzip -l /tmp/report_gm.docx | grep media

# Открыть в LibreOffice
libreoffice --calc /tmp/report_gm.xlsx
libreoffice --writer /tmp/report_gm.docx
```

---

## 5. Временная оценка

| Этап | Часы | Примечание |
|------|------|-----------|
| 1. Инфраструктура | 2 | matplotlib setup + helpers для Excel/Word |
| 2. Group Manager | 3 | 3 графика + Excel + Word (2 разных подхода) |
| 3. Finance Manager | 3 | Круговая может быть сложной, 2 формата |
| 4. Quality Engineer | 3 | Парето + timeline, Cyrillic testing |
| 5. Line Master | 3 | Combo chart, 2 формата отчета |
| 6. Word-специфичные подробности | 1 | Обработка кириллицы, отступы, размеры |
| 7. Тестирование | 3 | Unit-тесты на PNG + ручное в LibreOffice |
| **ИТОГО** | **≈18 часов** | ~2.5 дня работы |

*Примечание:* Оценка учитывает работу как с Excel, так и с Word для каждого отчета, плюс тестирование кириллицы и проверку встраивания в оба формата.

---

## 6. Риски и смягчение

| Риск | Вероятность | Смягчение |
|------|-------------|----------|
| Matplotlib медленный для больших отчетов | Средняя | Кэширование, оптимизация DPI |
| PNG не встраивается в Excel/Word | Низкая | Использовать openpyxl/docx примеры из docs |
| Графики выходят за границы листа | Средняя | Тестировать размеры, position параметры |
| Нужно пересчитывать данные для Парето | Низкая | Данные уже есть в response (cumulative_pct) |

---

## 7. Определение готовности (Definition of Done)

**Код и тесты:**
- ✅ Все 12 методов `_chart_*()` реализованы
- ✅ Все helper методы добавлены (`_add_chart_to_excel()`, `_add_chart_to_word()`)
- ✅ Все 4 отчета обновлены (GM, Finance, QE, Line Master)
- ✅ `pytest tests/ -v` проходит без ошибок (включая новые тесты на PNG)
- ✅ `mypy app/ --ignore-missing-imports` чистый

**Excel:**
- ✅ Все 12 отчетов открываются в LibreOffice Calc без ошибок
- ✅ Каждый лист содержит таблицу + PNG график
- ✅ PNG встроены корректно (видны в UI, не обрезаны)
- ✅ Кириллица на осях графиков отображается правильно
- ✅ Размер PNG соответствует плану (8 см ширина)

**Word:**
- ✅ Все 4 отчета открываются в LibreOffice Writer без ошибок
- ✅ Каждый отчет содержит 3-4 PNG графика (после заголовков разделов)
- ✅ Изображения встроены корректно (видны, не обрезаны)
- ✅ Размер изображений одинаков (5.5 дюймов)
- ✅ Кириллица на графиках читаема (DejaVu Sans)
- ✅ Между графиком и текстом есть отступы (doc.add_paragraph())

**Общее:**
- ✅ Миграция БД НЕ требуется
- ✅ feature_list.json обновлен (статус → "in_progress" → "done")
- ✅ Commit message: `feat: add charts to all dashboard export reports (excel + word)`
- ✅ Нет hardcoded путей, все графики генерируются в памяти (BytesIO)
- ✅ Нет закомментированного кода или debug print()

---

## 8. Word-специфичные подробности

### Структура встраивания в Word

Каждый отчет Word состоит из разделов с графиками. Новая структура:

```
_word_gm():
  ├── _word_header() — уже есть
  ├── Section 1: "1. ОБЩАЯ ЭФФЕКТИВНОСТЬ (OEE)"
  │   ├── [ГРАФИК: столбцы OEE]  ← НОВОЕ
  │   ├── Bullets (• линия 1, OEE 80%...)
  │   ├── "Вывод: ..."
  │   └── "Рекомендации: ..."
  ├── Section 2: "2. ВЫПОЛНЕНИЕ ПЛАНА"
  │   ├── [ГРАФИК: комбинированная]  ← НОВОЕ
  │   └── ... 
  └── Section 3: "3. ПРОСТОИ"
      ├── [ГРАФИК: Парето]  ← НОВОЕ
      └── ...
```

### Реализация через `_word_section()` + график

Вариант 1 (рекомендуется): Не менять `_word_section()`, добавить график вручную **перед вызовом**:

```python
# В _word_gm():
chart_png = self._chart_gm_oee_bars(oee)
doc.add_heading("1. ОБЩАЯ ЭФФЕКТИВНОСТЬ ОБОРУДОВАНИЯ (OEE)", 2)
self._add_chart_to_word(doc, chart_png, width=5.5)

# Затем добавить пункты и вывод через bullets и текст
oee_bullets = [f"• Line1: {l.avg_oee:.1f}%" for l in oee.lines]
for bullet in oee_bullets:
    doc.add_paragraph(bullet, style="List Bullet")
# ... вывод и рекомендации ...
```

Вариант 2 (альтернатива): Модифицировать `_word_section()` чтобы принимать опциональный chart_bytes:

```python
def _word_section(self, doc, title, bullets, conclusion, recommendation, chart_bytes=None):
    doc.add_heading(title, 2)
    if chart_bytes:
        self._add_chart_to_word(doc, chart_bytes)
    for bullet in bullets:
        doc.add_paragraph(bullet, style="List Bullet")
    # ... вывод/рекомендации ...
```

### Обработка кириллицы в matplotlib

В `__init__` или в начало методов:

```python
plt.rcParams['font.family'] = 'DejaVu Sans'  # или 'Liberation Sans'
plt.rcParams['axes.unicode_minus'] = False
```

Проверить на локальной машине:
```python
import matplotlib.font_manager as fm
print([f.name for f in fm.fontManager.ttflist])  # список доступных шрифтов
```

Если DejaVu недоступен, установить:
```bash
apt-get install fonts-dejavu  # Linux
# или скачать шрифт и добавить в ~/.matplotlib/fonts/ttf/
```

### Размер изображений для Word

- **Стандартная ширина:** 5.5 дюймов (соответствует A4 с полями)
- **Максимум:** 6 дюймов (край листа)
- **Минимум:** 4 дюймов (может быть мелко)
- **Рекомендуемое соотношение сторон:** 16:9 или 4:3

Пример размеров matplotlib:
```python
figsize=(10, 6)  # 10 дюймов ширина, 6 дюйм высота
# После масштабирования при вставке в Word (5.5 дюйм) высота будет ~3.3 дюйма
```

### Отступы и spacing в Word

```python
def _add_chart_to_word(self, doc, png_bytes: bytes, width: float = 5.5):
    doc.add_picture(BytesIO(png_bytes), width=Inches(width))
    doc.add_paragraph()  # добавить пустой paragraph для spacing
```

---

## 9. Дополнительные улучшения (post-MVP)

1. **Кэширование графиков** — если один и тот же отчет запрашивают дважды
2. **Темизирование** — параметры цвета для легкой смены паттерна (корпоративные цвета)
3. **Интерактивные графики в HTML** — экспорт в HTML с Plotly/Bokeh
4. **Русские метки** — убедиться, что Cyrillic рендерится без проблем (font семейство)

---

## 10. Документация и следующие шаги

Обновить после реализации:
- `docs/architecture.md` — добавить раздел про визуализацию
- `CHANGELOG.md` (если существует)
- This plan file — обновить статус на "Complete"

