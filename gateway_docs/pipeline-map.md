# Pipeline Map: source → canonical → DTO → command → DB

> **Статус: реализовано в P1 (1C:ЗУП) + P2 (1c_erp / mes / scada / lims), 2026-04-20.**
> См. `specs/import-problems-done.md` секции [11] и [18] для curl-подтверждений.
>
> Единая карта соответствий для всех полей ETL-пайплайна. **Источник истины** при любых правках seed, IMPORT_SCHEMAS, DTO, contracts и use-cases.
>
> Принципы:
> - **Канонический ключ** — `camelCase` во всех DTO/payload/command (независимо от стиля источника).
> - **ETL DTO = ACL** — валидирует нативный формат источника (русские поля, русские enum-значения), превращает в canonical через mapper.
> - **Даты** — всегда **ISO-строки `YYYY-MM-DD`** (или ISO-8601 с `T`) по всему пайплайну; без конверсии в `Date`.
> - **Ссылочные поля** (`departmentId`, `positionId`, `productId`, `orderId`) — в команде **либо UUID, либо code**; target-сервис резолвит `code→UUID` через `findByCode`/`findBySourceSystemId`.
> - **`sourceSystemId`** прокидывается на всём пути для идемпотентного upsert.

---

## Условные обозначения

| Символ | Значение |
|--------|----------|
| 🔑 | primary key / discriminator |
| 🔗 | foreign reference (code в ETL, UUID в DB) |
| 📅 | дата (строка `YYYY-MM-DD`) |
| 🎯 | enum (значение в source ↔ key в canonical) |
| ⚠️ | расхождение / неполнота |

---

## 1. 1C:ЗУП → Personnel

### 1.1 Сотрудники (`1c_zup / employees`)

| Native 1C (seed XLSX) | Seed JSON ключ       | IMPORT_SCHEMAS alias → canonical | ETL DTO `ZupEmployeeDto`     | Mapper → payload       | Command `PersonnelCreateEmployeeCommand.Request` | Personnel DB (`employees`)     |
|------------------------|----------------------|----------------------------------|-------------------------------|------------------------|---------------------------------------------------|--------------------------------|
| `Код` 🔑               | `code`               | `Код → code`                     | `code: string`                | `sourceId`, `sourceSystemId` | `sourceSystemId`                                  | `source_system_id`             |
| `ФИО`                  | `fullName`           | `ФИО → fullName`                 | `fullName: string`            | `fullName`             | `fullName`                                        | `full_name`                    |
| `ТабельныйНомер`       | `personnelNumber`    | `ТабельныйНомер → personnelNumber` | `personnelNumber: string`   | `personnelNumber`      | `personnelNumber`                                 | `personnel_number`             |
| `ДатаРождения` 📅      | `dateOfBirth`        | `ДатаРождения → dateOfBirth`     | `@IsDateString dateOfBirth: string` | `dateOfBirth` (ISO string) | `@Matches(YYYY-MM-DD) dateOfBirth: string`   | `date_of_birth DATE`           |
| `ТекущееПодразделение` 🔗 | `currentDepartment.code` | `ТекущееПодразделение → currentDepartment` + nested `Код → code` | `currentDepartment: ZupDepartmentRefDto { code }` | `departmentId: emp.currentDepartment.code` | `departmentId: string` (code or UUID) | `department_id UUID FK`   |
| `ТекущаяДолжность` 🔗  | `currentPosition.code` | `ТекущаяДолжность → currentPosition` + nested `Код → code` | `currentPosition: ZupEmployeeRefDto { code }` | `positionId` | `positionId: string` (code or UUID) | `position_id UUID FK`          |
| `ДатаПриема` 📅        | `hireDate`           | `ДатаПриема → hireDate`          | `@IsDateString hireDate: string` | `hireDate`           | `@Matches(YYYY-MM-DD) hireDate`                   | `hire_date DATE`               |
| `ДатаУвольнения` 📅    | `terminationDate?`   | `ДатаУвольнения → terminationDate` | `@IsDateString @IsOptional`   | —                      | —                                                 | `termination_date DATE`        |
| `ВидЗанятости` 🎯      | `employmentType`     | `ВидЗанятости → employmentType`  | `@IsEnum(ZupEmploymentType)` (Основное/Совместительство) | `employmentType: EmploymentType.MAIN` | `@IsEnum(EmploymentType)` (main/part_time) | `employment_type ENUM`     |

**Enum ZupEmploymentType ↔ EmploymentType:**

| 1С native value         | ZupEmploymentType key | EmploymentType value |
|-------------------------|------------------------|----------------------|
| `"Основное место работы"` | `MAIN`                | `"main"`             |
| `"Совместительство"`      | `PART_TIME`           | `"part_time"`        |

### 1.2 Подразделения (`1c_zup / departments`)

| Native 1C | Seed JSON | IMPORT_SCHEMAS alias | DTO `ZupDepartmentDto` | Mapper → payload | Command `PersonnelCreateDepartmentCommand` | DB `departments` |
|-----------|-----------|----------------------|-------------------------|------------------|--------------------------------------------|------------------|
| `Код` 🔑  | `code`    | `Код → code`         | `code: string`          | `code`, `sourceSystemId` | `code`, `sourceSystemId` | `code VARCHAR(20)`, `source_system_id` |
| `Наименование` | `name` | `Наименование → name` | `name: string` | `name` | `name` | `name VARCHAR(150)` |
| `Родитель` 🔗 | `parent.code` | `Родитель → parent` + nested `Код → code` | `parent?: ZupDepartmentRefDto { code }` | `parentId: dept.parent?.code \|\| null` | `parentId?: string \| null` (code or UUID) | `parent_id UUID FK` |
| `ТипПодразделения` 🎯 | `type` | `ТипПодразделения → type` | `@IsEnum(ZupDepartmentType)` | `type: DepartmentType.DIVISION\|DEPARTMENT\|SECTION\|UNIT` | `@IsEnum(DepartmentType)` | `type ENUM` |
| `Руководитель` 🔗 | `head.code?` | `Руководитель → head` | `head?: ZupEmployeeRefDto { code }` | `headEmployeeId: dept.head?.code \|\| null` | `headEmployeeId?: string \| null` (code or UUID) | `head_employee_id UUID FK` |

**Enum ZupDepartmentType ↔ DepartmentType:**

| 1С native | ZupDepartmentType key | DepartmentType value |
|-----------|------------------------|----------------------|
| `"Дивизион"`   | `DIVISION`   | `"division"`   |
| `"Управление"` | `DEPARTMENT` | `"department"` |
| `"Отдел"`      | `SECTION`    | `"section"`    |
| `"Участок"`    | `UNIT`       | `"unit"`       |

### 1.3 Должности (`1c_zup / positions`)

| Native 1C | Seed JSON | IMPORT_SCHEMAS alias | DTO `ZupPositionDto` (НОВАЯ) | Mapper → payload | Command `PersonnelCreatePositionCommand` | DB `positions` |
|-----------|-----------|----------------------|-------------------------------|------------------|------------------------------------------|----------------|
| `Код` 🔑 | `code` | `Код → code` | `code: string` | `code`, `sourceSystemId` | `code`, `sourceSystemId` | `code VARCHAR(20)`, `source_system_id` |
| `Наименование` | `name` | `Наименование → name` | `name: string` | `title: pos.name` | `title` | `title VARCHAR(150)` |
| `Подразделение` 🔗 | `department.code` | `Подразделение → department` + nested `Код → code` | `department: ZupDepartmentRefDto { code }` | ⚠️ **NOT IMPORTED** (v1.2.0: Position no longer has departmentId) | — | — |

**Примечание (v1.2.0):** Position больше не связана напрямую с Department. Relationship: Position → Employee → Department. Данные о подразделении для должности из источника игнорируются при импорте; связь определяется через сотрудника.

### 1.4 Шаблоны смен (`1c_zup / shift_templates`) — уже работает, включено для полноты

| Native | Seed | alias | DTO | Mapper | Command | DB |
|--------|------|-------|-----|--------|---------|-----|
| `Код` 🔑 | `code` | — | `code` | `sourceId` | — | — |
| `Наименование` | `name` | — | `name` | `name` | `name` | `name` |
| `ТипГрафика` 🎯 | `shiftType` | — | `@IsEnum(ZupShiftType)` (Пятидневка/Сменный 2/2/Сменный 3/3/Ночной) | `ShiftType.DAY_SHIFT/ROTATING/NIGHT_SHIFT` | `@IsEnum(ShiftType)` | `shift_type ENUM` |
| `ВремяНачала` | `startTime` | — | `startTime: string (HH:mm)` | `startTime` | `startTime` | `start_time TIME` |
| `ВремяОкончания` | `endTime` | — | `endTime` | `endTime` | `endTime` | `end_time TIME` |
| `ШаблонДней` | `workDaysPattern` | — | `workDaysPattern: string` | `workDaysPattern` | `workDaysPattern` | `work_days_pattern` |

---

## 2. 1C:ERP → Production

### 2.1 Продукты (`1c_erp / products`)

| Native 1C | Seed JSON | IMPORT_SCHEMAS alias | DTO `ErpProductDto` | Mapper | Command `ProductionCreateProductCommand` | DB `products` |
|-----------|-----------|----------------------|----------------------|--------|-------------------------------------------|---------------|
| `Код` 🔑 | `code` | `Код → code` | `code: string` | `code`, `sourceSystemId` | `code`, `sourceSystemId` | `code`, `source_system_id` |
| `Наименование` | `name` | `Наименование → name` | `name: string` | `name` | `name` | `name` |
| `ВидНоменклатуры` 🎯 | `category` | `ВидНоменклатуры → category` | `@IsEnum(ErpProductCategory)` | `category: ProductCategory.*` | `@IsEnum(ProductCategory)` | `category ENUM` |
| `ЕдиницаИзмерения.Наименование` | `unitOfMeasure.name` | `ЕдиницаИзмерения → unitOfMeasure` | `unitOfMeasure: ErpUnitOfMeasureDto { name }` | `unitOfMeasure: prod.unitOfMeasure.name` | `unitOfMeasure: string` | `unit_of_measure VARCHAR(20)` |
| `Бренд?` | `brand?` | — | `brand?: string` | `brand` | `brand?` | `brand` |
| `СрокГодности?` | — ⚠️ | — | — | — | `shelfLifeDays?` | `shelf_life_days` |
| `КонтролируетсяЛИМС?` | `requiresQualityCheck?` | — | `requiresQualityCheck?: boolean` | `requiresQualityCheck` | `requiresQualityCheck?` | `requires_quality_check` |

**Enum ErpProductCategory ↔ ProductCategory:**

| 1С ВидНоменклатуры | ErpProductCategory key | ProductCategory value |
|--------------------|-------------------------|-----------------------|
| `"Сырьё"` | `RAW_MATERIAL` | `"raw_material"` |
| `"Полуфабрикат"` | `SEMI_FINISHED` | `"semi_finished"` |
| `"Готовая продукция"` | `FINISHED_PRODUCT` | `"finished_product"` |
| `"Материал"` | `MATERIAL` | `"raw_material"` (фолбэк) |
| `"Тара"` | `PACKAGING` | `"packaging"` |

### 2.2 Продажи (`1c_erp / sales`) — будущее

⚠️ Seed пока отсутствует. DTO `ErpSaleDto` существует, mapper раскрывает sale на строки (одна строка → одна команда `ProductionRecordSaleCommand`).

### 2.3 Остатки на складе (`1c_erp / inventory`) — будущее

⚠️ Seed отсутствует. DTO `ErpInventoryDto` + mapper → `ProductionUpsertInventoryCommand`.

---

## 3. MES → Production

### 3.1 Наряды (`mes / orders`)

| Native MES | Seed JSON | alias | DTO `MesWorkOrderDto` | Mapper | Command `ProductionCreateOrderCommand` | DB `production_orders` |
|-----------|-----------|-------|------------------------|--------|----------------------------------------|-------------------------|
| `WorkOrderID` 🔑 | `workOrderId` | `WorkOrderID → workOrderId` | `workOrderId: string` | `externalOrderId`, `sourceId` | `externalOrderId` | `external_order_id` |
| `ERPOrderID?` | `erpOrderId?` | — | — | — | — | — ⚠️ |
| `ProductCode` 🔗 | `productCode` | `ProductCode → productCode` | `productCode: string` | `productId: order.productCode` (code) | `productId: string` (code or UUID) | `product_id UUID FK` |
| `TargetQuantity` | `targetQuantity` | `TargetQuantity → targetQuantity` | `@IsNumber targetQuantity` | `targetQuantity` | `@IsNumber targetQuantity` | `target_quantity DECIMAL` |
| `UnitOfMeasure` | `unitOfMeasure` | `UnitOfMeasure → unitOfMeasure` | `unitOfMeasure: string` | `unitOfMeasure` | `unitOfMeasure` | `unit_of_measure` |
| `Status` 🎯 | `status` | `Status → status` | `@IsEnum(MesWorkOrderStatus)` | — (не пробрасывается) | ⚠️ status выставляется use-case | `status ENUM` |
| `Priority` | `priority` | `Priority → priority` | `@IsNumber priority` | — | — | `priority` |
| `PlannedStartTime` 📅 | `plannedStartTime` | `PlannedStartTime → plannedStartTime` | `@IsDateString plannedStartTime: string` | `plannedStart` (ISO) | `@IsDateString plannedStart` | `planned_start TIMESTAMP` |
| `PlannedEndTime` 📅 | `plannedEndTime` | `PlannedEndTime → plannedEndTime` | `@IsDateString plannedEndTime: string` | `plannedEnd` | `@IsDateString plannedEnd` | `planned_end TIMESTAMP` |
| `ProductionLineID` | `productionLineId` | `ProductionLineID → productionLineId` | `productionLineId: string` | `productionLine` | `productionLine` | `production_line` |

### 3.2 Выпуски (`mes / production_output`) — будущее

⚠️ Seed отсутствует. DTO `MesProductionOutputDto` → `ProductionRecordOutputCommand`.

### 3.3 Расход материалов (`mes / material_consumption`)

⚠️ Нет command contract'а; DTO валидируется, но запись skipped с debug-логом.

---

## 4. SCADA → Production

### 4.1 Показания датчиков (`scada / sensors`)

| Native SCADA | Seed JSON | alias | DTO `ScadaSensorReadingDto` | Mapper | Command `ProductionRecordSensorReadingCommand` | DB |
|-------------|-----------|-------|------------------------------|--------|------------------------------------------------|-----|
| `TagID` 🔑 | `tagId` | `TagID → tagId` | `tagId: string` | `deviceId` | `deviceId` | `device_id` |
| `Timestamp` 📅 | `timestamp` | `Timestamp → timestamp` | `@IsDateString timestamp` | `recordedAt` | `@IsDateString recordedAt` | `recorded_at` |
| `Value` | `value` | `Value → value` | `@IsNumber value` | `value` | `value` | `value DECIMAL` |
| `Quality` 🎯 | `quality` | `Quality → quality` | `@IsEnum(ScadaQuality)` | `SensorQuality.GOOD/DEGRADED/BAD` (computed) | `@IsEnum(SensorQuality)` | `quality ENUM` |
| `TagConfiguration?` | `tagConfiguration?` | — | nested `ScadaTagConfigurationDto` | `productionLine: tagConfig.lineId`, `unit: engUnit` | `productionLine`, `unit` | — |

### 4.2 Сигнализация (`scada / alarms`) — debug-only

⚠️ DTO валидируется, события не публикуются.

---

## 5. LIMS → Production

### 5.1 Результаты испытаний (`lims / quality`)

| Native LIMS | Seed JSON | alias | DTO `LimsTestResultDto` | Mapper | Command `ProductionRecordQualityResultCommand` | DB |
|-------------|-----------|-------|--------------------------|--------|------------------------------------------------|-----|
| `ResultID` 🔑 | `resultId` | `ResultID → resultId` | `resultId: string` | `sourceId` | — | `id UUID` |
| `SampleID` 🔗 | `sampleId` | `SampleID → sampleId` | `sampleId: string` | `lotNumber: result.lotNumber \|\| sampleId` | `lotNumber` | `lot_number` |
| `ParameterCode` | `parameterCode` | `ParameterCode → parameterCode` | `parameterCode: string` | — | — | — |
| `ParameterName` | `parameterName` | `ParameterName → parameterName` | `parameterName: string` | `parameterName` | `parameterName` | `parameter_name` |
| `ResultValue` | `resultValue` | `ResultValue → resultValue` | `@IsNumber resultValue` | `resultValue` | `resultValue` | `result_value` |
| `UnitOfMeasure` | `unitOfMeasure` | — | `unitOfMeasure: string` | — | — | — |
| `InSpec` | `inSpec` | — | `@IsBoolean inSpec` | — | — (inSpec вычисляется) | `in_spec` |
| `Status` 🎯 | `status` | `Status → status` | `@IsEnum(LimsTestResultStatus)` | `QualityStatus.APPROVED/REJECTED/PENDING` | `@IsEnum(QualityStatus) qualityStatus` | `quality_status ENUM` |
| `TestDate` 📅 | `testDate` | `TestDate → testDate` | `@IsDateString testDate` | `testDate` | `@IsDateString testDate` | `test_date` |
| `ProductCode?` 🔗 | `productCode?` | — | `productCode?: string` | `productId: result.productCode \|\| ''` | `productId: string` (code or UUID) | `product_id UUID FK` |
| `LowerLimit?` | `lowerLimit?` | — | `@IsNumber @IsOptional` | — | — (вынесено в QualitySpec) | — |
| `UpperLimit?` | `upperLimit?` | — | `@IsNumber @IsOptional` | — | — (вынесено в QualitySpec) | — |

### 5.2 Решение об использовании (`lims / usage_decisions`) — будущее

⚠️ Seed отсутствует. DTO `LimsUsageDecisionDto` → `ProductionRecordQualityResultCommand` (совместное использование).

---

## 6. Контракты резолюции ссылок (code ↔ UUID)

### 6.1 Алгоритм `resolveEntityId(idOrCode: string, repo)`

```text
if (uuidV4.test(idOrCode)) {
  entity = await repo.findById(idOrCode)
  if (entity) return entity
  // если UUID не найден — падаем с NotFoundError
}
entity = await repo.findByCode(idOrCode)
if (entity) return entity
// для ETL-импорта: если сущность не найдена и есть sourceSystemId на команде —
// use-case может отложить создание (см. upsert-ветку) или бросить NotFoundError
throw EntityNotFoundError
```

### 6.2 Команды, где требуется резолюция

| Command | Поля для резолюции | Target repo |
|---------|---------------------|-------------|
| `PersonnelCreateEmployeeCommand`    | `departmentId`, `positionId` | `DepartmentRepository`, `PositionRepository` |
| `PersonnelUpdateEmployeeCommand`    | `departmentId`, `positionId` | те же |
| `PersonnelCreateDepartmentCommand`  | `parentId?`, `headEmployeeId?` | `DepartmentRepository`, `EmployeeRepository` |
| `PersonnelUpdateDepartmentCommand`  | `parentId?`, `headEmployeeId?` | те же |
| `PersonnelCreatePositionCommand`    | `departmentId` | `DepartmentRepository` |
| `PersonnelUpdatePositionCommand`    | `departmentId` | `DepartmentRepository` |
| `ProductionCreateOrderCommand`      | `productId` | `ProductRepository` |
| `ProductionRecordOutputCommand`     | `orderId`, `productId` | `ProductionOrderRepository`, `ProductRepository` |
| `ProductionRecordSaleCommand`       | `productId` | `ProductRepository` |
| `ProductionRecordQualityResultCommand` | `productId` | `ProductRepository` |
| `ProductionUpsertInventoryCommand`  | `productId` | `ProductRepository` |

---

## 7. Порядок импорта (рекомендуемый)

1. `1c_zup / departments` — сначала, т.к. positions и employees на него ссылаются.
2. `1c_zup / positions` — после departments.
3. `1c_zup / employees` — после departments + positions.
4. `1c_erp / products` — независимо.
5. `1c_erp / inventory`, `mes / orders`, `scada / sensors`, `lims / quality` — после products.

ETL **не должен** падать, если ссылаемая сущность ещё не импортирована — use-case должен вернуть доменную ошибку `DepartmentNotFoundError` с понятным сообщением, чтобы оператор мог перезапустить импорт в правильном порядке.

---

## 8. Инварианты форматов дат и enum

- **Даты — только строки ISO** по всему пайплайну (`YYYY-MM-DD` для date-only, `YYYY-MM-DDTHH:mm:ssZ` для timestamp). Конвертация в `Date` происходит **только в use-case** при создании `EmployeeEntity` / `ProductionOrderEntity`.
- **Enum в команде** — canonical-значение (`"main"`, `"division"`, `"raw_material"` и т.д.), не 1С-строка. Перевод 1С → canonical выполняется **в mapper** (ETL DTO держит 1С-enum, команда — canonical).

---

## 9. Источник истины при расхождениях

1. `specs/efko_data_structures.md` — нативные структуры источников.
2. `specs/efko_microservices.md` — схемы DB / business-logic.
3. Этот файл (`pipeline-map.md`) — bridge between 1 и 2.

При изменении любого из слоёв **обязательно** обновить соответствующую строку таблицы и `specs/import-problems-done.md`.
