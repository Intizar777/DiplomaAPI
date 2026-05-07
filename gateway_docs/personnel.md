# Personnel Service

> **⚠️ v1.1.0 Update:** Database schema normalized to 3NF. `Employee.locationId` removed. See [migration guide](../changes/v1.1.0-3nf-normalization.md) for details.

## Назначение

`personnel` обслуживает кадровый домен: оргструктуру, локации, должности, сотрудников, производственные линии, рабочие места и шаблоны смен. Сервис построен на NestJS, хранит состояние в PostgreSQL через Prisma, принимает команды и queries через RabbitMQ RPC и публикует кадровые события в RabbitMQ.

## Как сервис встроен в систему

- Команды принимает через `efko.personnel.commands`.
- Запросы принимает через `efko.personnel.queries`.
- События публикует через `efko.personnel.events`.
- Очереди разделены на `personnel-service.commands.queue` и `personnel-service.queries.queue`.
- В `AppModule` подключён `RmqEventEmitterModule` с `sourceService: 'personnel'`; дополнительно подключён Prisma-based outbox.

## Основные модули

- `DepartmentsModule`: подразделения и иерархия оргструктуры.
- `LocationsModule`: локации с адресами.
- `PositionsModule`: должности внутри подразделений.
- `ProductionLinesModule`: производственные линии и их связь с локациями.
- `WorkstationsModule`: рабочие места и назначение сотрудников.
- `EmployeesModule`: сотрудники, изменение данных и увольнение.
- `ShiftTemplatesModule`: шаблоны сменных графиков.
- `PrismaModule`: доступ к БД и репозиториям.
- `OutboxModule`: публикация событий из `outbox_messages` в `efko.personnel.events`.
- `RabbitModule`: transport-конфигурация RabbitMQ.

## RabbitMQ Commands и Queries

Все команды отправляются в exchange `efko.personnel.commands`, очередь `personnel-service.commands.queue`.
Все запросы отправляются в exchange `efko.personnel.queries`, очередь `personnel-service.queries.queue`.

Все RabbitRPC handlers работают через `ValidationPipe` и `personnelRpcErrorInterceptor`, логируют topic и request metadata (`correlationId`, `userId`, `userRole`).

### Offices flow

Ниже описаны новые команды и запросы для офисов, складов, производственных линий и рабочих мест. Эти же контракты проксируются через `gateway-api` в маршрутах `/personnel/locations`, `/personnel/production-lines`, `/personnel/workstations` и `/personnel/workstations/assign`.

#### PersonnelCreateLocationCommand

Создать локацию.

**Exchange:** `efko.personnel.commands`

**Request Body:**

```typescript
{
  name: string;
  code: string;
  type: LocationType; // OFFICE | FACTORY
  country: string;
  region: string;
  city: string;
  postalCode: string;
  streetAddress: string;
  sourceSystemId?: string | null;
}
```

**Response:**

```typescript
{
  id: string;
  name: string;
  code: string;
  type: LocationType;
  country: string;
  region: string;
  city: string;
  postalCode: string;
  streetAddress: string;
  sourceSystemId: string | null;
}
```

**Ошибки:** `LOCATION_CODE_ALREADY_EXISTS` -> `409`

---

#### PersonnelUpdateLocationCommand

Обновить локацию.

**Exchange:** `efko.personnel.commands`

**Request Body:**

```typescript
{
  id: string;
  name?: string;
  type?: LocationType;
  address?: {
    country?: string;
    region?: string;
    city?: string;
    postalCode?: string;
    streetAddress?: string;
  };
}
```

**Response:** как у `PersonnelCreateLocationCommand`

**Ошибки:** `LOCATION_NOT_FOUND` -> `404`

---

#### PersonnelGetLocationsQuery

Получить список локаций.

**Exchange:** `efko.personnel.queries`

**Request Body:**

```typescript
{
  code?: string;
  type?: LocationType;
  city?: string;
  offset?: number;
  limit?: number;
}
```

**Response:**

```typescript
{
  locations: Array<{
    id: string;
    name: string;
    code: string;
    type: LocationType;
    country: string;
    region: string;
    city: string;
    postalCode: string;
    streetAddress: string;
    sourceSystemId: string | null;
  }>;
}
```

---

#### PersonnelCreateProductionLineCommand

Создать производственную линию.

**Exchange:** `efko.personnel.commands`

**Request Body:**

```typescript
{
  name: string;
  code: string;
  locationId: string;
  description?: string | null;
  capacity?: number | null;
  sourceSystemId?: string | null;
}
```

**Response:**

```typescript
{
  id: string;
  name: string;
  code: string;
  locationId: string;
  description: string | null;
  capacity: number | null;
  isActive: boolean;
  sourceSystemId: string | null;
}
```

**Ошибки:**
- `LOCATION_NOT_FOUND` -> `404`
- `LOCATION_TYPE_MISMATCH` -> `400`
- `PRODUCTION_LINE_CODE_ALREADY_EXISTS` -> `409`

---

#### PersonnelCreateWorkstationCommand

Создать рабочее место.

**Exchange:** `efko.personnel.commands`

**Request Body:**

```typescript
{
  name: string;
  code: string;
  locationId: string;
  productionLineId?: string | null;
  workstationType: WorkstationType;
  sourceSystemId?: string | null;
}
```

**Response:**

```typescript
{
  id: string;
  name: string;
  code: string;
  locationId: string;
  productionLineId: string | null;
  workstationType: WorkstationType;
  sourceSystemId: string | null;
}
```

**Ошибки:**
- `LOCATION_NOT_FOUND` -> `404`
- `PRODUCTION_LINE_NOT_FOUND` -> `404`
- `WORKSTATION_CODE_ALREADY_EXISTS` -> `409`
- `WORKSTATION_ASSIGNMENT_ERROR` -> `400`

---

#### PersonnelAssignEmployeeWorkstationCommand

Назначить сотрудника на рабочее место.

**Exchange:** `efko.personnel.commands`

**Request Body:**

```typescript
{
  employeeId: string;
  workstationId: string;
}
```

**Response:**

```typescript
{
  employeeId: string;
  workstationId: string;
  locationId: string;
}
```

**Ошибки:**
- `EMPLOYEE_NOT_FOUND` -> `404`
- `WORKSTATION_NOT_FOUND` -> `404`
- `WORKSTATION_ASSIGNMENT_ERROR` -> `400`

### Commands

#### PersonnelCreateDepartmentCommand

Создать подразделение.

**Exchange:** `efko.personnel.commands`  
**Request Body:**

```typescript
{
  name: string;                    // Название подразделения
  code: string;                    // Уникальный код подразделения
  type: DepartmentType;            // Тип: DIVISION | DEPARTMENT | SECTION | UNIT
  parentId?: string | null;        // UUID родительского подразделения (опционально)
  headEmployeeId?: string | null;  // UUID руководителя (опционально)
  sourceSystemId?: string | null;  // ID из внешней системы (для ETL)
}
```

**Response:**

```typescript
{
  id: string;
  name: string;
  code: string;
  type: DepartmentType;
  parentId: string | null;
  headEmployeeId: string | null;
  sourceSystemId: string | null;
}
```

**Ошибки:** `DEPARTMENT_CODE_ALREADY_EXISTS` -> `409`

---

#### PersonnelUpdateDepartmentCommand

Обновить подразделение.

**Exchange:** `efko.personnel.commands`  
**Request Body:**

```typescript
{
  id: string;                      // UUID подразделения
  name?: string;
  type?: DepartmentType;
  parentId?: string | null;
  headEmployeeId?: string | null;
}
```

**Response:**

```typescript
{
  id: string;
  name: string;
  code: string;
  type: DepartmentType;
  parentId: string | null;
  headEmployeeId: string | null;
}
```

---

#### PersonnelGetDepartmentsQuery
#### PersonnelCreatePositionCommand

Создать должность.

**Exchange:** `efko.personnel.commands`  
**Request Body:**

```typescript
{
  title: string;            // Название должности
  code: string;             // Уникальный код должности
  departmentId: string;     // UUID подразделения
  sourceSystemId?: string;  // ID из внешней системы
}
```

**Response:**

```typescript
{
  id: string;
  title: string;
  code: string;
  departmentId: string;
}
```

**Ошибки:** 
- `POSITION_CODE_ALREADY_EXISTS` -> `409`
- `DEPARTMENT_NOT_FOUND` -> `404`

---

#### PersonnelUpdatePositionCommand

Обновить должность.

**Exchange:** `efko.personnel.commands`  
**Request Body:**

```typescript
{
  id: string;
  title?: string;
  departmentId?: string;
}
```

**Response:**

```typescript
{
  id: string;
  title: string;
  code: string;
  departmentId: string;
}
```

---

#### PersonnelCreateEmployeeCommand

Создать сотрудника.

**Exchange:** `efko.personnel.commands`  
**Request Body:**

```typescript
{
  personnelNumber: string;  // Табельный номер (уникальный)
  fullName: string;         // Полное имя (формат: Фамилия Имя Отчество)
  dateOfBirth: string;      // Дата рождения (ISO date: YYYY-MM-DD)
  departmentId: string;     // UUID подразделения
  positionId: string;       // UUID должности
  hireDate: string;         // Дата приема (ISO date)
  employmentType: EmploymentType; // MAIN | PART_TIME
  sourceSystemId?: string;  // ID из внешней системы
}
```

**Response:**

```typescript
{
  id: string;
  personnelNumber: string;
  fullName: string;
  departmentId: string;
  positionId: string;
  status: EmployeeStatus;  // ACTIVE | TERMINATED | ON_LEAVE
}
```

**Ошибки:**
- `INVALID_FULL_NAME` -> `400`
- `DEPARTMENT_NOT_FOUND` -> `404`
- `POSITION_NOT_FOUND` -> `404`

---

#### PersonnelUpdateEmployeeCommand

Обновить данные сотрудника.

**Exchange:** `efko.personnel.commands`  
**Request Body:**

```typescript
{
  id: string;
  fullName?: string;
  departmentId?: string;
  positionId?: string;
  employmentType?: EmploymentType;
  dateOfBirth?: string;  // ISO date
}
```

**Response:**

```typescript
{
  id: string;
  personnelNumber: string;
  fullName: string;
  dateOfBirth: string;
  departmentId: string;
  positionId: string;
  hireDate: string;
  terminationDate: string | null;
  employmentType: EmploymentType;
  status: EmployeeStatus;
  sourceSystemId: string | null;
}
```

---

#### PersonnelTerminateEmployeeCommand

Уволить сотрудника.

**Exchange:** `efko.personnel.commands`  
**Request Body:**

```typescript
{
  id: string;
  terminationDate?: string;  // ISO date, опционально (по умолчанию сегодня)
}
```

**Response:**

```typescript
{
  id: string;
  status: EmployeeStatus;  // TERMINATED
  terminationDate: string;
}
```

**Ошибки:**
- `EMPLOYEE_ALREADY_TERMINATED` -> `409`
- `EMPLOYEE_NOT_FOUND` -> `404`

---

#### PersonnelCreateShiftTemplateCommand

Создать шаблон смены.

**Exchange:** `efko.personnel.commands`  
**Request Body:**

```typescript
{
  name: string;                // Название шаблона
  shiftType: ShiftType;        // DAY_SHIFT | NIGHT_SHIFT | ROTATING
  startTime: string;           // Время начала (HH:MM)
  endTime: string;             // Время окончания (HH:MM)
  workDaysPattern: string;     // Бинарная строка (7 символов: 1111100)
}
```

**Response:**

```typescript
{
  id: string;
  name: string;
  shiftType: ShiftType;
  startTime: string;
  endTime: string;
  workDaysPattern: string;
}
```

---

#### PersonnelUpdateShiftTemplateCommand

Обновить шаблон смены.

**Exchange:** `efko.personnel.commands`  
**Request Body:**

```typescript
{
  id: string;
  name?: string;
  shiftType?: ShiftType;
  startTime?: string;
  endTime?: string;
  workDaysPattern?: string;
}
```

**Response:**

```typescript
{
  id: string;
  name: string;
  shiftType: ShiftType;
  startTime: string;
  endTime: string;
  workDaysPattern: string;
}
```

---

### Queries

#### PersonnelGetDepartmentsQuery

Получить список подразделений.

**Exchange:** `efko.personnel.queries`  
**Request Body:**

```typescript
{
  type?: DepartmentType;  // Фильтр по типу подразделения (опционально)
  code?: string;          // Фильтр по коду (опционально)
}
```

**Response:**

```typescript
{
  departments: Array<{
    id: string;
    name: string;
    code: string;
    type: DepartmentType;
    parentId: string | null;
    headEmployeeId: string | null;
    sourceSystemId: string | null;
  }>;
}
```

---

#### PersonnelGetPositionsQuery

Получить список должностей.

**Exchange:** `efko.personnel.queries`  
**Request Body:**

```typescript
{
  departmentId?: string;  // Фильтр по подразделению (опционально)
}
```

**Response:**

```typescript
{
  positions: Array<{
    id: string;
    title: string;
    code: string;
    departmentId: string;
  }>;
}
```

---

#### PersonnelGetEmployeesQuery

Получить список сотрудников.

**Exchange:** `efko.personnel.queries`  
**Request Body:**

```typescript
{
  departmentId?: string;      // Фильтр по подразделению
  positionId?: string;        // Фильтр по должности
  status?: EmployeeStatus;    // ACTIVE | TERMINATED | ON_LEAVE
  employmentType?: EmploymentType;  // MAIN | PART_TIME
}
```

**Response:**

```typescript
{
  employees: Array<{
    id: string;
    personnelNumber: string;
    fullName: string;
    status: EmployeeStatus;
    employmentType: EmploymentType;
    departmentId: string;
    positionId: string;
    hireDate: string;
    dateOfBirth: string;
    terminationDate: string | null;
  }>;
}
```

---

#### PersonnelGetShiftTemplatesQuery

Получить список шаблонов смен.

**Exchange:** `efko.personnel.queries`  
**Request Body:**

```typescript
{}
```

**Response:**

```typescript
{
  templates: Array<{
    id: string;
    name: string;
    shiftType: ShiftType;
    startTime: string;
    endTime: string;
    workDaysPattern: string;
  }>;
}
```

---

## Основная бизнес-логика

- Подразделения поддерживают иерархию `parent -> children`; при создании/обновлении `parentId` и `headEmployeeId` можно передавать не только UUID, но и бизнес-идентификаторы, которые резолвятся через `resolveEntityId(...)`.
- Локации являются верхнеуровневой привязкой для подразделений, производственных линий, рабочих мест и части сотрудников.
- Производственная линия доступна только для `LocationType.FACTORY`; use case валидирует тип локации и уникальность кода в пределах локации.
- Рабочее место может быть создано в локации и, опционально, связано с производственной линией; назначение сотрудника на рабочее место также синхронизирует `locationId`.
- Должность жёстко привязана к подразделению; create flow валидирует уникальность `code` и существование подразделения.
- Сотрудник связан и с подразделением, и с должностью; `CreateEmployeeUseCase` валидирует оба reference и использует value objects `PersonnelNumber` и `FullName`.
- Увольнение реализовано отдельным use case: меняет статус сотрудника и ставит дату увольнения.
- Шаблоны смен содержат тип смены, время начала/окончания и `workDaysPattern`; время и паттерн валидируются value object-ами.
- Для ETL-импортов `create` use case-ы по подразделениям, должностям и сотрудникам сначала пытаются делать upsert по `sourceSystemId`.

## Хранение данных

PostgreSQL/Prisma, основные таблицы:

- `departments`: имя, код, тип, `parent_id`, `head_employee_id`, `source_system_id`.
- `locations`: имя, код, тип, адресные поля, `source_system_id`.
- `production_lines`: имя, код, `location_id`, описание, capacity, `is_active`, `source_system_id`.
- `workstations`: имя, код, `location_id`, `production_line_id`, `workstation_type`, `source_system_id`.
- `positions`: title, code, `department_id`, `source_system_id`.
- `employees`: табельный номер, ФИО, дата рождения, подразделение, должность, `location_id`, `workstation_id`, даты приёма/увольнения, тип занятости, статус, `source_system_id`.
- `shift_schedule_templates`: имя шаблона, тип смены, время начала/окончания, паттерн рабочих дней.
- `outbox_messages`: события кадрового домена для асинхронной публикации.

## Интеграции

- RabbitMQ RPC для всех кадровых команд и queries.
- RabbitMQ events:
  - подразделения, должности и сотрудники при create/update часто пишут события через outbox;
  - увольнение и часть операций используют `EventEmitterService` напрямую.
- ETL является важным upstream:
  - ZUP mapper направляет данные в `PersonnelCreateDepartmentCommand`, `PersonnelCreatePositionCommand`, `PersonnelCreateEmployeeCommand`, `PersonnelCreateShiftTemplateCommand`;
  - create use case-ы умеют обновлять существующие записи по `sourceSystemId`, что снижает дубли при повторном импорте.

## Обработка ошибок

- Доменные ошибки наследуются от `PersonnelError`.
- Для RPC используется `personnelRpcErrorInterceptor`, который приводит доменные и HTTP ошибки к структуре `{ error: { code, message, statusCode } }`.
- Для HTTP-слоя подключён `AllExceptionsFilter`; в HTTP-контексте он возвращает JSON с `statusCode` и `message`.
- Основные маппинги:
  - ошибки формата (`INVALID_*`) -> `400`
  - ошибки отсутствующих сущностей -> `404`
  - конфликтные состояния (`*_ALREADY_EXISTS`, `EMPLOYEE_ALREADY_TERMINATED`, `EMPLOYEE_NOT_ACTIVE`) -> `409`

## Observability и logging

- Логирование через `nestjs-pino`.
- В dev-режиме лог пишется в `logs/personnel.log` и очищается на старте.
- Bootstrap включает `enableShutdownHooks()` и глобальный exception filter.
- Контроллеры логируют RPC topic и request metadata.
- В `EmployeesController` есть дополнительный debug/error лог для `PersonnelCreateEmployeeCommand`, включая сериализацию payload и ошибки выполнения.

## Зависимости

- NestJS
- Prisma + PostgreSQL
- `@golevelup/nestjs-rabbitmq`
- `nestjs-pino`
- `@efko-kernel/contracts`
- `@efko-kernel/interfaces`
- `@efko-kernel/nest-utils`

## Наблюдения и пробелы по коду

- Use case-ы используют смешанную схему публикации событий: outbox для части create/update операций и direct publish для части команд.
- В `DepartmentsModule`, `EmployeesModule`, `PositionsModule` явно не импортируется `OutboxModule`, хотя create use case-ы зависят от `OutboxMessageRepository`; корректность разрешения зависимости предполагает наличие глобального провайдера в общем composition root.
- Как и в `production`, внешний HTTP-сервер поднимается, но бизнес-операции экспонированы как RabbitRPC, а не REST.
