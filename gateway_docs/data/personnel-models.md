# Модели данных: Personnel Service

Кадровый домен: структура организации, сотрудники, локации.

## Department

**Таблица:** `departments`  
**Назначение:** Подразделения организации (иерархическая структура)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `name` | String | Название подразделения |
| `code` | String @unique | Уникальный код (например, "IT-001") |
| `type` | DepartmentType | DIVISION, DEPARTMENT, SECTION, UNIT |
| `parentId` | UUID? | Родительское подразделение (для иерархии) |
| `locationId` | UUID? | Локация подразделения |
| `headEmployeeId` | UUID? | Руководитель (Employee FK) |
| `sourceSystemId` | String? | ID во внешней системе (1C) |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Связи:** parent/children (саморекурсия), location, employees, headEmployee

**Примеры:**
```
Компания
  └─ Отдел IT (parentId=Компания)
      └─ Отдел Frontend (parentId=Отдел IT)
      └─ Отдел Backend (parentId=Отдел IT)
```

## Position

**Таблица:** `positions`  
**Назначение:** Должности в организации

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `title` | String | Название должности (например, "Senior Developer") |
| `code` | String @unique | Код должности |
| `sourceSystemId` | String? | ID во внешней системе |
| `createdAt` | DateTime | Дата создания |

**Связи:** employees (обратная связь)

**Примеры:** Engineer, Manager, Analyst, Director

## Employee

**Таблица:** `employees`  
**Назначение:** Сотрудники организации

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `personnelNumber` | String @unique | Табельный номер (например, "000001") |
| `fullName` | String | Полное имя |
| `dateOfBirth` | Date | Дата рождения |
| `positionId` | UUID | Текущая должность (FK Position) |
| `departmentId` | UUID | Текущее подразделение (FK Department) |
| `workstationId` | UUID? | Рабочее место (FK Workstation, nullable) |
| `hireDate` | Date | Дата приема на работу |
| `terminationDate` | Date? | Дата увольнения (nullable) |
| `employmentType` | EmploymentType | main, part_time |
| `status` | EmployeeStatus | active, terminated, on_leave |
| `sourceSystemId` | String? | ID в ZUP (1C-зарплата) |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Связи:** position (FK), department (FK), workstation (FK), headOfDepartments (обратная для Department.headEmployeeId)

**Локация сотрудника:** Определяется через `workstation.location` или `department.location` (или `department.parent.location` для иерархии)

## Workstation

**Таблица:** `workstations`  
**Назначение:** Рабочие места (посты, столы, контрольные точки)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `name` | String | Название рабочего места |
| `code` | String | Код (уникален в локации) |
| `locationId` | UUID | Где находится (FK Location) |
| `productionLineId` | UUID? | К какой линии привязано (nullable) |
| `workstationType` | WorkstationType | operator_post, control_point, loading_area, lab_station, office_desk |
| `sourceSystemId` | String? | ID в MES |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Связи:** location (FK), productionLine (FK), employees (обратная)

## Location

**Таблица:** `locations`  
**Назначение:** Физические локации (офисы, заводы, склады)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `name` | String | Название локации |
| `code` | String @unique | Код локации |
| `type` | LocationType | office, factory |
| `streetAddress` | String | Адрес |
| `postalAreaId` | UUID? | Почтовый индекс (FK PostalArea) |
| `sourceSystemId` | String? | ID в 1C |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Связи:** postalArea (FK), departments, workstations

## PostalArea

**Таблица:** `postal_areas`  
**Назначение:** Справочник почтовых индексов (3NF нормализация)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `postalCode` | String @unique | Почтовый индекс |
| `city` | String | Город |
| `region` | String | Регион/область |
| `createdAt` | DateTime | Дата создания |

**Связи:** locations (обратная)

## ProductionLine (Cross-Service Reference)

**Таблица:** `production_lines` (в **Production Service**)  
**Назначение:** Производственные линии, на которые ссылаются рабочие места в Personnel

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID |
| `name` | String @unique | Название линии |
| `code` | String @unique | Код линии |
| `description` | String? | Описание |
| `isActive` | Boolean | Активна ли (default: true) |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Важно:** `Workstation.productionLineId` — это cross-service foreign key. На уровне БД constraint отсутствует (разные сервисы). Целостность обеспечивается на уровне приложения через события.

**Связи:** orders (ProductionOrder), sensors (Sensor) — в Production Service.

## ProductionLineView

**Таблица:** `production_line_views`  
**Назначение:** Read-only копия (view) производственных линий из Production Service. Позволяет делать joins на стороне Personnel без cross-service RPC.

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | UUID | Уникальный ID в Personnel |
| `productionLineId` | UUID @unique | ID из Production Service |
| `name` | String | Название линии |
| `code` | String @unique | Код линии |
| `description` | String? | Описание |
| `isActive` | Boolean | Активна ли |
| `lastSyncedAt` | DateTime | Когда последний раз синхронизировано |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Синхронизация (3 канала):**
1. **Cron** — `SyncProductionLinesUseCase.executeFullSync()` каждые 6 часов (`@Cron('0 */6 * * *')`). Полная пересинхронизация через RPC.
2. **Event-driven** — `ProductionLineEventListener` слушает `production.production-line.changed.event` из Production Service. Инкрементальный sync через `executeIncrementalSync()`.
3. **Ручной** — RPC endpoint `personnel.get.production-line-views.query` для чтения view.

**Важно:** FK constraint отсутствует (cross-service reference). `workstations.production_line_id` не ссылается на `production_line_views` на уровне БД.

**Пример использования:**
```typescript
// Join workstation + production line name одним запросом
const workstations = await prisma.workstation.findMany({
  include: {
    productionLineView: true,
  },
});
```

## Enums

| Enum | Значения |
|------|----------|
| **DepartmentType** | DIVISION, DEPARTMENT, SECTION, UNIT |
| **LocationType** | office, factory |
| **EmploymentType** | main, part_time |
| **EmployeeStatus** | active, terminated, on_leave |
| **WorkstationType** | operator_post, control_point, loading_area, lab_station, office_desk |

---

**Related:** [../architecture/3nf-normalization.md](../architecture/3nf-normalization.md), [all-models.md](all-models.md)
