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

**Связи:** parent/children (саморекурсия), location, positions, headEmployee

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
| `departmentId` | UUID | Какое подразделение (FK Department) |
| `sourceSystemId` | String? | ID во внешней системе |
| `createdAt` | DateTime | Дата создания |

**Связи:** department (FK), employees (обратная связь)

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
| `workstationId` | UUID? | Рабочее место (FK Workstation, nullable) |
| `hireDate` | Date | Дата приема на работу |
| `terminationDate` | Date? | Дата увольнения (nullable) |
| `employmentType` | EmploymentType | MAIN, PART_TIME |
| `status` | EmployeeStatus | ACTIVE, TERMINATED, ON_LEAVE |
| `sourceSystemId` | String? | ID в ZUP (1C-зарплата) |
| `createdAt`, `updatedAt` | DateTime | Временные метки |

**Связи:** position (FK), workstation (FK), user (обратная через User.employeeId)

**Локация сотрудника:** Определяется через `workstation.location` или `position.department.location`

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
| `workstationType` | WorkstationType | OPERATOR_POST, CONTROL_POINT, LOADING_AREA, LAB_STATION, OFFICE_DESK |
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
| `type` | LocationType | OFFICE, FACTORY |
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

## Enums

| Enum | Значения |
|------|----------|
| **DepartmentType** | DIVISION, DEPARTMENT, SECTION, UNIT |
| **LocationType** | OFFICE, FACTORY |
| **EmploymentType** | MAIN, PART_TIME |
| **EmployeeStatus** | ACTIVE, TERMINATED, ON_LEAVE |
| **WorkstationType** | OPERATOR_POST, CONTROL_POINT, LOADING_AREA, LAB_STATION, OFFICE_DESK |

---

**Related:** [../architecture/3nf-normalization.md](../architecture/3nf-normalization.md), [all-models.md](all-models.md)
