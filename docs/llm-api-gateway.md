API Documentation

Title: API Gateway API
Version: 1.0

Description: API documentation for the API Gateway

=== Endpoints ===

Endpoint: /api/health

Method: GET

Responses:
- 200: No description
---

Endpoint: /api/health/live

Method: GET

Responses:
- 200: No description
---

Endpoint: /api/health/ready

Method: GET

Responses:
- 200: No description
---

Endpoint: /api/metrics

Method: GET

Responses:
- 200: No description
---

Endpoint: /api/auth/register

Method: POST
Summary: Зарегистрировать нового пользователя
Description: Создаёт новый аккаунт. После регистрации пользователь может войти через `POST /auth/login`. Роль по умолчанию — WORKER.

Request Body:

Responses:
- 201: Пользователь зарегистрирован

- 400: Некорректный формат email или имени
- 409: Email уже занят (`USER_ALREADY_EXISTS`)
- 503: auth-service недоступен
---

Endpoint: /api/auth/login

Method: POST
Summary: Войти в систему
Description: Аутентифицирует пользователя и возвращает JWT access-токен + refresh-токен.

**Cookies, устанавливаемые в ответе:**
- `refreshToken` — httpOnly, используется для обновления сессии через `POST /auth/refresh-session`
- `XSRF-TOKEN` — читаемый JavaScript cookie с CSRF-токеном; браузерные клиенты обязаны передавать его значение в заголовке `X-CSRF-Token` при каждом мутирующем запросе (`POST`, `PATCH`, `DELETE`)

Request Body:

Responses:
- 201: Аутентификация успешна. Устанавливаются cookies `refreshToken` (httpOnly) и `XSRF-TOKEN` (читаемый JS).

- 400: Некорректный формат email или пароля
- 401: Неверные учётные данные или аккаунт деактивирован (`INVALID_CREDENTIALS`)
- 503: auth-service недоступен
---

Endpoint: /api/auth/logout

Method: POST
Summary: Выйти из системы
Description: Очищает httpOnly cookie `refreshToken` и `XSRF-TOKEN`, а также инвалидирует refresh-токен на сервере.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Responses:
- 201: Выход выполнен

- 401: Не авторизован или CSRF токен невалиден
- 503: auth-service недоступен
---

Endpoint: /api/auth/me

Method: GET
Summary: Текущий пользователь
Description: Возвращает профиль пользователя из валидного Bearer-токена.

Responses:
- 200: Профиль текущего пользователя

- 401: Токен недействителен или истёк
- 404: Пользователь из токена не найден или деактивирован (`USER_NOT_FOUND`)
- 503: auth-service недоступен
---

Endpoint: /api/auth/refresh-session

Method: POST
Summary: Обновить сессию
Description: Выдаёт новую пару токенов по refresh-токену из `httpOnly` cookie `refreshToken`. Старый refresh-токен аннулируется (rotation).

**CSRF:** браузерные клиенты обязаны передать заголовок `X-CSRF-Token` со значением из cookie `XSRF-TOKEN` (mobile-клиенты без cookie пропускаются автоматически).

**Cookies, обновляемые в ответе:** `refreshToken` и `XSRF-TOKEN` — оба ротируются.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Responses:
- 201: Сессия обновлена — новая пара токенов. Cookies `refreshToken` и `XSRF-TOKEN` ротируются.

- 401: Refresh-токен отсутствует, отозван (`REFRESH_TOKEN_REVOKED`), истёк (`REFRESH_TOKEN_EXPIRED`) или пользователь деактивирован
- 503: auth-service недоступен
---

Endpoint: /api/users

Method: GET
Summary: Список всех пользователей
Description: Доступно только администраторам. Возвращает полный список пользователей, включая деактивированных.

Parameters:
- offset (query):
  Description: No description
  Required: No
  Type: number
- limit (query):
  Description: No description
  Required: No
  Type: number
  Example: 20

Responses:
- 200: Список пользователей

- 401: Не авторизован
- 403: Требуется роль ADMIN
- 503: auth-service недоступен
---

Endpoint: /api/users/{userId}

Method: PATCH
Summary: Обновить пользователя
Description: Частичное обновление — передавайте только изменяемые поля. Позволяет сменить email, имя, роль и привязку к сотруднику.

Parameters:
- userId (path):
  Description: UUID пользователя
  Required: Yes
  Type: string
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 200: Пользователь обновлён

- 400: Некорректный формат email или имени
- 401: Не авторизован
- 403: Требуется роль ADMIN
- 404: Пользователь не найден (`USER_NOT_FOUND`)
- 503: auth-service недоступен
---

Endpoint: /api/users/deactivate

Method: POST
Summary: Деактивировать пользователя
Description: Устанавливает `isActive = false`. Деактивированный пользователь не может войти в систему.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 200: Пользователь деактивирован

- 400: Некорректный UUID
- 401: Не авторизован
- 403: Требуется роль ADMIN
- 404: Пользователь не найден (`USER_NOT_FOUND`)
- 409: Пользователь уже деактивирован (`USER_ALREADY_DEACTIVATED`)
- 503: auth-service недоступен
---

Endpoint: /api/personnel/departments

Method: POST
Summary: Создать подразделение
Description: Код подразделения должен быть уникальным. Допустимые типы: PRODUCTION, ADMINISTRATIVE, LOGISTICS, QUALITY, MAINTENANCE.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Подразделение создано

- 400: Ошибка валидации
- 401: Не авторизован
- 403: Недостаточно прав
- 409: Код уже занят (`DEPARTMENT_CODE_ALREADY_EXISTS`)
- 503: personnel-service недоступен
---

Method: GET
Summary: Список подразделений
Description: Опциональная фильтрация по типу и коду.

Parameters:
- code (query):
  Description: Код подразделения
  Required: No
  Type: string
  Example: PROD-001
- type (query):
  Description: Тип подразделения (PRODUCTION, ADMINISTRATIVE, LOGISTICS, QUALITY, MAINTENANCE)
  Required: No
  Type: undefined
- parentId (query):
  Description: No description
  Required: No
  Type: string
- offset (query):
  Description: Смещение для пагинации
  Required: No
  Type: number
- limit (query):
  Description: Лимит записей (макс. 100)
  Required: No
  Type: number

Responses:
- 200: Список подразделений

- 401: Не авторизован
- 403: Недостаточно прав
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/departments/{id}

Method: PATCH
Summary: Обновить подразделение
Description: Частичное обновление — передавайте только изменяемые поля.

Parameters:
- id (path):
  Description: UUID подразделения
  Required: Yes
  Type: string
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 200: Подразделение обновлено

- 400: Ошибка валидации
- 401: Не авторизован
- 403: Недостаточно прав
- 404: Подразделение не найдено (`DEPARTMENT_NOT_FOUND`)
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/locations

Method: POST
Summary: Создать локацию
Description: Код локации должен быть уникальным. Локация хранит адрес и тип площадки.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Локация создана

- 400: Ошибка валидации
- 401: Не авторизован
- 403: Недостаточно прав
- 409: Код локации уже занят (`LOCATION_CODE_ALREADY_EXISTS`)
- 503: personnel-service недоступен
---

Method: GET
Summary: Список локаций
Description: Опциональная фильтрация по коду, типу и городу.

Parameters:
- code (query):
  Description: Код локации
  Required: No
  Type: string
  Example: LOC-001
- type (query):
  Description: Тип локации (OFFICE, FACTORY)
  Required: No
  Type: undefined
- offset (query):
  Description: Смещение для пагинации
  Required: No
  Type: number
- limit (query):
  Description: Лимит записей
  Required: No
  Type: number
  Example: 20
- city (query):
  Description: Город
  Required: No
  Type: undefined
  Example: Домодедово

Responses:
- 200: Список локаций

- 401: Не авторизован
- 403: Недостаточно прав
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/locations/{id}

Method: PATCH
Summary: Обновить локацию
Description: Частичное обновление локации — передавайте только изменяемые поля.

Parameters:
- id (path):
  Description: UUID локации
  Required: Yes
  Type: string
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 200: Локация обновлена

- 400: Ошибка валидации
- 401: Не авторизован
- 403: Недостаточно прав
- 404: Локация не найдена (`LOCATION_NOT_FOUND`)
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/workstations

Method: POST
Summary: Создать рабочее место
Description: Рабочее место может быть привязано к производственной линии или существовать отдельно в локации.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Рабочее место создано

- 400: Ошибка валидации или привязки к линии (`WORKSTATION_ASSIGNMENT_ERROR`)
- 401: Не авторизован
- 403: Недостаточно прав
- 404: Локация или производственная линия не найдены (`LOCATION_NOT_FOUND`, `PRODUCTION_LINE_NOT_FOUND`)
- 409: Код рабочего места уже занят (`WORKSTATION_CODE_ALREADY_EXISTS`)
- 503: personnel-service недоступен
---

Method: GET
Summary: Список рабочих мест
Description: Опциональная фильтрация по коду, локации, производственной линии и типу.

Parameters:
- code (query):
  Description: Код рабочего места
  Required: No
  Type: string
  Example: WS-001
- locationId (query):
  Description: UUID локации
  Required: No
  Type: string
- productionLineId (query):
  Description: UUID производственной линии
  Required: No
  Type: string
- workstationType (query):
  Description: Тип рабочего места
  Required: No
  Type: undefined
- offset (query):
  Description: Смещение для пагинации
  Required: No
  Type: number
- limit (query):
  Description: Лимит записей
  Required: No
  Type: number
  Example: 20

Responses:
- 200: Список рабочих мест

- 401: Не авторизован
- 403: Недостаточно прав
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/workstations/assign

Method: POST
Summary: Назначить сотрудника на рабочее место
Description: Привязывает сотрудника к рабочему месту и синхронизирует локацию.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 200: Назначение выполнено

- 400: Ошибка привязки к рабочему месту (`WORKSTATION_ASSIGNMENT_ERROR`)
- 401: Не авторизован
- 403: Недостаточно прав
- 404: Сотрудник или рабочее место не найдены (`EMPLOYEE_NOT_FOUND`, `WORKSTATION_NOT_FOUND`)
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/positions

Method: POST
Summary: Создать должность
Description: Код должности должен быть уникальным. Подразделение должно существовать.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Должность создана

- 400: Ошибка валидации
- 401: Не авторизован
- 403: Недостаточно прав
- 404: Подразделение не найдено (`DEPARTMENT_NOT_FOUND`)
- 409: Код должности уже занят (`POSITION_CODE_ALREADY_EXISTS`)
- 503: personnel-service недоступен
---

Method: GET
Summary: Список должностей
Description: Опциональная фильтрация по подразделению.

Parameters:
- offset (query):
  Description: Смещение (страничная отступка)
  Required: No
  Type: number
- limit (query):
  Description: Лимит записей (макс. 100)
  Required: No
  Type: number
- departmentId (query):
  Description: UUID подразделения
  Required: No
  Type: undefined

Responses:
- 200: Список должностей

- 401: Не авторизован
- 403: Недостаточно прав
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/positions/{id}

Method: PATCH
Summary: Обновить должность
Description: Частичное обновление должности.

Parameters:
- id (path):
  Description: UUID должности
  Required: Yes
  Type: string
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 200: Должность обновлена

- 400: Ошибка валидации
- 401: Не авторизован
- 403: Недостаточно прав
- 404: Должность не найдена (`POSITION_NOT_FOUND`) или подразделение не найдено (`DEPARTMENT_NOT_FOUND`)
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/employees

Method: POST
Summary: Принять сотрудника на работу
Description: Создаёт запись о сотруднике. Табельный номер генерируется автоматически.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Сотрудник создан

- 400: Некорректное имя или данные (`INVALID_FULL_NAME`)
- 401: Не авторизован
- 403: Недостаточно прав
- 404: Подразделение не найдено (`DEPARTMENT_NOT_FOUND`) или должность не найдена (`POSITION_NOT_FOUND`)
- 503: personnel-service недоступен
---

Method: GET
Summary: Список сотрудников
Description: Фильтрация по подразделению, должности, статусу и типу занятости.

Parameters:
- offset (query):
  Description: Смещение (страничная отступка)
  Required: No
  Type: number
- limit (query):
  Description: Лимит записей (макс. 100)
  Required: No
  Type: number
- departmentId (query):
  Description: UUID подразделения
  Required: No
  Type: string
- positionId (query):
  Description: UUID должности
  Required: No
  Type: string
- status (query):
  Description: Статус сотрудника (ACTIVE, TERMINATED, ON_LEAVE)
  Required: No
  Type: undefined
- employmentType (query):
  Description: Тип занятости (FULL_TIME, PART_TIME, CONTRACT)
  Required: No
  Type: undefined

Responses:
- 200: Список сотрудников

- 401: Не авторизован
- 403: Недостаточно прав
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/employees/{id}/terminate

Method: POST
Summary: Уволить сотрудника
Description: Переводит сотрудника в статус TERMINATED. Если дата не указана — используется текущая дата.

Parameters:
- id (path):
  Description: UUID сотрудника
  Required: Yes
  Type: string
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 200: Сотрудник уволен

- 400: Некорректный формат даты
- 401: Не авторизован
- 403: Недостаточно прав
- 404: Сотрудник не найден (`EMPLOYEE_NOT_FOUND`)
- 409: Сотрудник уже уволен (`EMPLOYEE_ALREADY_TERMINATED`)
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/employees/{id}

Method: PATCH
Summary: Обновить данные сотрудника
Description: Частичное обновление — передавайте только изменяемые поля.

Parameters:
- id (path):
  Description: UUID сотрудника
  Required: Yes
  Type: string
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 200: Данные обновлены

- 400: Некорректное имя (`INVALID_FULL_NAME`)
- 401: Не авторизован
- 403: Недостаточно прав
- 404: Сотрудник, подразделение или должность не найдены
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/shift-templates

Method: POST
Summary: Создать шаблон смены
Description: Время в формате HH:MM. workDaysPattern — бинарная строка (1=рабочий день, 0=выходной), например `1111100` — пн-пт.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Шаблон создан

- 400: Некорректный формат времени или паттерна (`INVALID_SHIFT_TIME`, `INVALID_WORK_DAYS_PATTERN`)
- 401: Не авторизован
- 403: Недостаточно прав
- 503: personnel-service недоступен
---

Method: GET
Summary: Список шаблонов смен

Responses:
- 200: Список шаблонов смен

- 401: Не авторизован
- 403: Недостаточно прав
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/shift-templates/{id}

Method: PATCH
Summary: Обновить шаблон смены
Description: Частичное обновление шаблона.

Parameters:
- id (path):
  Description: UUID шаблона смены
  Required: Yes
  Type: string
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 200: Шаблон обновлён

- 400: Некорректный формат (`INVALID_SHIFT_TIME`, `INVALID_WORK_DAYS_PATTERN`)
- 401: Не авторизован
- 403: Недостаточно прав
- 404: Шаблон не найден (`SHIFT_TEMPLATE_NOT_FOUND`)
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/workstations/{id}

Method: GET
Summary: Получить рабочее место по ID

Parameters:
- id (path):
  Description: UUID рабочего места
  Required: Yes
  Type: string

Responses:
- 200: Рабочее место

- 401: Не авторизован
- 403: Недостаточно прав
- 404: Рабочее место не найдено (`WORKSTATION_NOT_FOUND`)
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/production-line-views

Method: GET
Summary: Список производственных линий (view)
Description: Read-only копия production lines из Production service с пагинацией и фильтрацией.

Parameters:
- code (query):
  Description: Код линии
  Required: No
  Type: string
  Example: LINE-01
- name (query):
  Description: Название линии
  Required: No
  Type: string
  Example: Линия молока
- isActive (query):
  Description: Только активные
  Required: No
  Type: boolean
  Example: true
- limit (query):
  Description: Лимит записей
  Required: No
  Type: number
  Example: 20
- offset (query):
  Description: Смещение для пагинации
  Required: No
  Type: number

Responses:
- 200: Список production line views

- 401: Не авторизован
- 403: Недостаточно прав
- 503: personnel-service недоступен
---

Endpoint: /api/personnel/postal-areas

Method: POST
Summary: Создать почтовую зону
Description: Создаёт новую почтовую зону с уникальным почтовым кодом.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Почтовая зона создана

- 400: Ошибка валидации
- 401: Не авторизован
- 403: Недостаточно прав
- 409: Почтовый код уже занят (`POSTAL_CODE_ALREADY_EXISTS`)
- 503: personnel-service недоступен
---

Method: GET
Summary: Список почтовых зон
Description: Получить список всех почтовых зон с пагинацией.

Parameters:
- limit (query):
  Description: Лимит записей
  Required: No
  Type: number
  Example: 20
- offset (query):
  Description: Смещение для пагинации
  Required: No
  Type: number

Responses:
- 200: Список почтовых зон

- 401: Не авторизован
- 403: Недостаточно прав
- 503: personnel-service недоступен
---

Endpoint: /api/production/products

Method: POST
Summary: Создать продукт
Description: Регистрирует новый продукт. Код должен быть уникальным.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Продукт создан

- 400: Ошибка валидации
- 401: Не авторизован
- 409: Код продукта уже занят (`PRODUCT_CODE_ALREADY_EXISTS`)
- 503: production-service недоступен
---

Method: GET
Summary: Список продуктов
Description: Каталог продуктов с опциональной фильтрацией.

Parameters:
- category (query):
  Description: Категория (FINISHED_PRODUCT, RAW_MATERIAL, PACKAGING, SEMI_FINISHED)
  Required: No
  Type: undefined
- brand (query):
  Description: Бренд
  Required: No
  Type: string
  Example: Домик в деревне
- limit (query):
  Description: No description
  Required: No
  Type: number
  Example: 100
- offset (query):
  Description: No description
  Required: No
  Type: number

Responses:
- 200: Список продуктов

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/production/production-lines

Method: GET
Summary: Список производственных линий
Description: Опциональная фильтрация по коду, названию и активности.

Parameters:
- code (query):
  Description: Код линии
  Required: No
  Type: string
  Example: LINE-01
- name (query):
  Description: Название линии
  Required: No
  Type: string
  Example: Линия молока
- isActive (query):
  Description: Только активные
  Required: No
  Type: boolean
  Example: true
- limit (query):
  Description: Лимит записей
  Required: No
  Type: number
  Example: 20
- offset (query):
  Description: Смещение для пагинации
  Required: No
  Type: number

Responses:
- 200: Список производственных линий

- 401: Не авторизован
- 503: production-service недоступен
---

Method: POST
Summary: Создать производственную линию
Description: Регистрирует новую производственную линию. Код должен быть уникальным.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Производственная линия создана

- 400: Ошибка валидации
- 401: Не авторизован
- 409: Код линии уже занят (`PRODUCTION_LINE_CODE_ALREADY_EXISTS`)
- 503: production-service недоступен
---

Endpoint: /api/production/production-lines/{id}

Method: PUT
Summary: Обновить производственную линию
Description: Обновляет данные производственной линии. Код должен оставаться уникальным.

Parameters:
- id (path):
  Description: UUID производственной линии
  Required: Yes
  Type: string
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 200: Производственная линия обновлена

- 400: Ошибка валидации
- 401: Не авторизован
- 404: Производственная линия не найдена (`PRODUCTION_LINE_NOT_FOUND`)
- 409: Код линии уже занят (`PRODUCTION_LINE_CODE_ALREADY_EXISTS`)
- 503: production-service недоступен
---

Endpoint: /api/production/orders

Method: POST
Summary: Создать производственный заказ
Description: Открывает новый заказ в статусе PLANNED.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Заказ создан

- 400: Ошибка валидации
- 401: Не авторизован
- 404: Продукт не найден (`PRODUCT_NOT_FOUND`)
- 503: production-service недоступен
---

Method: GET
Summary: Список заказов
Description: Фильтрация по статусу, продукту, линии и датам.

Parameters:
- status (query):
  Description: Статус (PLANNED, IN_PROGRESS, COMPLETED, CANCELLED)
  Required: No
  Type: undefined
- productId (query):
  Description: UUID продукта
  Required: No
  Type: string
- productionLineId (query):
  Description: Производственная линия
  Required: No
  Type: string
  Example: Line-1
- from (query):
  Description: Начало периода (ISO date)
  Required: No
  Type: string
  Example: 2025-01-01
- to (query):
  Description: Конец периода (ISO date)
  Required: No
  Type: string
  Example: 2025-12-31
- limit (query):
  Description: No description
  Required: No
  Type: number
  Example: 100
- offset (query):
  Description: No description
  Required: No
  Type: number

Responses:
- 200: Список заказов

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/production/orders/{id}

Method: GET
Summary: Заказ по ID с выпусками
Description: Возвращает полные данные заказа включая все зарегистрированные выпуски.

Parameters:
- id (path):
  Description: UUID производственного заказа
  Required: Yes
  Type: string

Responses:
- 200: Данные заказа с выпусками

- 401: Не авторизован
- 404: Заказ не найден (`PRODUCTION_ORDER_NOT_FOUND`)
- 503: production-service недоступен
---

Endpoint: /api/production/orders/{id}/status

Method: PATCH
Summary: Обновить статус заказа
Description: Допустимые переходы: PLANNED→IN_PROGRESS (`start`), IN_PROGRESS→COMPLETED (`complete`), PLANNED/IN_PROGRESS→CANCELLED (`cancel`).

Parameters:
- id (path):
  Description: UUID производственного заказа
  Required: Yes
  Type: string
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 200: Статус обновлён

- 401: Не авторизован
- 404: Заказ не найден (`PRODUCTION_ORDER_NOT_FOUND`)
- 409: Недопустимый переход статуса (`INVALID_ORDER_STATUS_TRANSITION`)
- 503: production-service недоступен
---

Endpoint: /api/production/output

Method: POST
Summary: Зарегистрировать выпуск продукции
Description: Фиксирует партию выпущенной продукции в рамках производственного заказа.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Выпуск зарегистрирован

- 401: Не авторизован
- 404: Заказ не найден (`PRODUCTION_ORDER_NOT_FOUND`) или продукт не найден (`PRODUCT_NOT_FOUND`)
- 503: production-service недоступен
---

Method: GET
Summary: Список выпусков
Description: Фильтрация по заказу, продукту, партии и датам.

Parameters:
- orderId (query):
  Description: UUID производственного заказа
  Required: No
  Type: string
- productId (query):
  Description: UUID продукта
  Required: No
  Type: string
- lotNumber (query):
  Description: Номер партии
  Required: No
  Type: string
  Example: LOT-2025-001
- from (query):
  Description: Дата производства от (ISO date)
  Required: No
  Type: string
  Example: 2025-01-01
- to (query):
  Description: Дата производства до (ISO date)
  Required: No
  Type: string
  Example: 2025-12-31
- limit (query):
  Description: No description
  Required: No
  Type: number
  Example: 100
- offset (query):
  Description: No description
  Required: No
  Type: number

Responses:
- 200: Список выпусков

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/production/sales

Method: POST
Summary: Зарегистрировать продажу
Description: Фиксирует факт продажи партии продукции клиенту.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Продажа зарегистрирована

- 401: Не авторизован
- 404: Продукт не найден (`PRODUCT_NOT_FOUND`)
- 503: production-service недоступен
---

Method: GET
Summary: Список продаж
Description: Фильтрация по продукту, региону, каналу и датам.

Parameters:
- productId (query):
  Description: UUID продукта
  Required: No
  Type: string
- region (query):
  Description: Регион
  Required: No
  Type: string
  Example: Краснодарский край
- channel (query):
  Description: Канал (RETAIL, WHOLESALE, ONLINE, EXPORT)
  Required: No
  Type: undefined
- from (query):
  Description: Дата продажи от (ISO date)
  Required: No
  Type: string
  Example: 2025-01-01
- to (query):
  Description: Дата продажи до (ISO date)
  Required: No
  Type: string
  Example: 2025-12-31
- limit (query):
  Description: No description
  Required: No
  Type: number
  Example: 100
- offset (query):
  Description: No description
  Required: No
  Type: number

Responses:
- 200: Список продаж

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/production/sales/summary

Method: GET
Summary: Сводка продаж
Description: Агрегированные данные с группировкой по region | channel | product.

Parameters:
- from (query):
  Description: Начало периода (ISO date)
  Required: No
  Type: string
  Example: 2025-01-01
- to (query):
  Description: Конец периода (ISO date)
  Required: No
  Type: string
  Example: 2025-12-31
- groupBy (query):
  Description: Ось группировки (region | channel | product)
  Required: No
  Type: string
  Example: region
- offset (query):
  Description: Смещение для пагинации
  Required: No
  Type: number
- limit (query):
  Description: Лимит групп
  Required: No
  Type: number
  Example: 20

Responses:
- 200: Сводка продаж

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/production/inventory

Method: POST
Summary: Обновить/создать остаток на складе
Description: Upsert по сочетанию productId + warehouseId + lotNumber.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Остаток создан или обновлён

- 401: Не авторизован
- 404: Продукт не найден (`PRODUCT_NOT_FOUND`)
- 503: production-service недоступен
---

Method: GET
Summary: Остатки на складах
Description: Фильтрация по продукту и складу.

Parameters:
- productId (query):
  Description: UUID продукта
  Required: No
  Type: string
- warehouseId (query):
  Description: Код склада
  Required: No
  Type: string
  Example: WH-01
- limit (query):
  Description: No description
  Required: No
  Type: number
  Example: 100
- offset (query):
  Description: No description
  Required: No
  Type: number

Responses:
- 200: Список остатков

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/production/quality

Method: POST
Summary: Зарегистрировать результат КК
Description: Фиксирует результат лабораторного контроля для партии продукции.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Результат КК зарегистрирован

- 401: Не авторизован
- 404: Продукт не найден (`PRODUCT_NOT_FOUND`)
- 503: production-service недоступен
---

Method: GET
Summary: Результаты КК
Description: Фильтрация по продукту, партии, решению и соответствию норме.

Parameters:
- productId (query):
  Description: UUID продукта
  Required: No
  Type: string
- lotNumber (query):
  Description: Номер партии
  Required: No
  Type: string
  Example: LOT-2025-001
- qualityStatus (query):
  Description: No description
  Required: No
  Type: undefined
- limit (query):
  Description: No description
  Required: No
  Type: number
  Example: 100
- offset (query):
  Description: No description
  Required: No
  Type: number
- inSpec (query):
  Description: Только в норме
  Required: No
  Type: boolean
- decision (query):
  Description: Решение (APPROVED, REJECTED, QUARANTINE)
  Required: No
  Type: undefined
  Example: APPROVED

Responses:
- 200: Список результатов КК

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/production/sensors

Method: POST
Summary: Записать показание датчика
Description: Сохраняет IoT-показание с производственной линии: температура, давление, влажность и т.д.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Показание датчика записано

- 401: Не авторизован
- 503: production-service недоступен
---

Method: GET
Summary: Показания датчиков
Description: Фильтрация по линии, параметру, качеству сигнала и датам.

Parameters:
- productionLineId (query):
  Description: Производственная линия
  Required: No
  Type: string
  Example: Line-1
- parameterName (query):
  Description: Название параметра (temperature, pressure, humidity)
  Required: No
  Type: string
  Example: temperature
- quality (query):
  Description: Качество сигнала (GOOD, UNCERTAIN, BAD)
  Required: No
  Type: undefined
- from (query):
  Description: Начало диапазона (ISO datetime)
  Required: No
  Type: string
  Example: 2025-01-01T00:00:00Z
- to (query):
  Description: Конец диапазона (ISO datetime)
  Required: No
  Type: string
  Example: 2025-01-01T23:59:59Z
- limit (query):
  Description: No description
  Required: No
  Type: number
  Example: 500
- offset (query):
  Description: No description
  Required: No
  Type: number

Responses:
- 200: Список показаний датчиков

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/production/kpi

Method: GET
Summary: KPI производства
Description: Агрегированные показатели: объём выпуска, процент брака, OEE, выполнение заказов.

Parameters:
- from (query):
  Description: Начало периода (ISO date)
  Required: No
  Type: string
  Example: 2025-01-01
- to (query):
  Description: Конец периода (ISO date)
  Required: No
  Type: string
  Example: 2025-12-31
- productionLineId (query):
  Description: Фильтр по производственной линии
  Required: No
  Type: string
  Example: Line-1

Responses:
- 200: KPI производства

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/production/customers

Method: POST
Summary: Создать клиента
Description: Регистрирует нового клиента.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Клиент создан

- 400: Ошибка валидации
- 401: Не авторизован
- 503: production-service недоступен
---

Method: GET
Summary: Список клиентов
Description: Получить список всех клиентов с пагинацией.

Parameters:
- limit (query):
  Description: Лимит записей
  Required: No
  Type: number
  Example: 20
- offset (query):
  Description: Смещение для пагинации
  Required: No
  Type: number

Responses:
- 200: Список клиентов

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/production/warehouses

Method: POST
Summary: Создать склад
Description: Регистрирует новый склад с уникальным кодом.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Склад создан

- 400: Ошибка валидации
- 401: Не авторизован
- 409: Код склада уже занят (`WAREHOUSE_CODE_ALREADY_EXISTS`)
- 503: production-service недоступен
---

Method: GET
Summary: Список складов
Description: Получить список всех складов с пагинацией.

Parameters:
- limit (query):
  Description: Лимит записей
  Required: No
  Type: number
  Example: 20
- offset (query):
  Description: Смещение для пагинации
  Required: No
  Type: number

Responses:
- 200: Список складов

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/production/quality-specs

Method: POST
Summary: Создать спецификацию качества
Description: Определяет параметры качества для продукта с верхним и нижним пределами.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Спецификация качества создана

- 400: Ошибка валидации
- 401: Не авторизован
- 404: Продукт не найден (`PRODUCT_NOT_FOUND`)
- 503: production-service недоступен
---

Method: GET
Summary: Список спецификаций качества
Description: Получить список спецификаций с опциональной фильтрацией по продукту.

Parameters:
- productId (query):
  Description: UUID продукта для фильтрации
  Required: No
  Type: string
  Example: a1b2c3d4-e5f6-7890-abcd-ef1234567890
- limit (query):
  Description: Лимит записей
  Required: No
  Type: number
  Example: 20
- offset (query):
  Description: Смещение для пагинации
  Required: No
  Type: number

Responses:
- 200: Список спецификаций качества

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/production/units-of-measure

Method: POST
Summary: Создать единицу измерения
Description: Регистрирует новую единицу измерения. Код должен быть уникальным.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Единица измерения создана

- 400: Ошибка валидации
- 401: Не авторизован
- 409: Код единицы измерения уже занят (`UNIT_OF_MEASURE_CODE_ALREADY_EXISTS`)
- 503: production-service недоступен
---

Method: GET
Summary: Список единиц измерения
Description: Каталог единиц измерения с опциональной фильтрацией.

Parameters:
- code (query):
  Description: Код единицы измерения
  Required: No
  Type: string
  Example: kg
- name (query):
  Description: Название единицы измерения
  Required: No
  Type: string
  Example: Килограмм
- limit (query):
  Description: Лимит записей
  Required: No
  Type: number
  Example: 20
- offset (query):
  Description: Смещение для пагинации
  Required: No
  Type: number

Responses:
- 200: Список единиц измерения

- 401: Не авторизован
- 503: production-service недоступен
---

Endpoint: /api/etl/import

Method: POST
Summary: Загрузить пакет данных (JSON body)
Description: Принимает данные из внешних систем (1С:ЗУП, 1С:ERP, MES, SCADA, LIMS) для ETL-обработки. Данные проходят валидацию, трансформацию в канонический формат и отправку в целевые сервисы через RabbitMQ.

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Request Body:

Responses:
- 201: Пакет принят в обработку

- 400: Ошибка валидации (неверный source_system, import_type или формат данных)
- 401: Не авторизован
- 403: Недостаточно прав (требуется роль ADMIN)
- 503: etl-service недоступен
---

Endpoint: /api/etl/import/file

Method: POST
Summary: Загрузить файл (xlsx/json)
Description: Принимает файл .xlsx или .json (макс. 20MB) с данными для ETL-обработки. Файл парсится по схеме, валидируется, сохраняется в GridFS и передаётся в pipeline. Заголовки XLSX могут быть как на русском (с применением алиасов схемы), так и на английском (каноничные имена полей).

Parameters:
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Responses:
- 201: Файл принят в обработку

- 400: Ошибка валидации файла или параметров
- 401: Не авторизован
- 403: Недостаточно прав (требуется роль ADMIN)
- 503: etl-service недоступен
---

Endpoint: /api/etl/imports

Method: GET
Summary: Список импортов
Description: Возвращает список операций импорта с опциональной фильтрацией по источнику, статусу и пагинацией.

Parameters:
- source_system (query):
  Description: Источник данных
  Required: No
  Type: undefined
- status (query):
  Description: Статус импорта
  Required: No
  Type: undefined
- limit (query):
  Description: Лимит записей
  Required: No
  Type: number
  Example: 20
- offset (query):
  Description: Смещение для пагинации
  Required: No
  Type: number

Responses:
- 200: Список импортов
Type: array

- 401: Не авторизован
- 403: Недостаточно прав (требуется роль ADMIN)
- 503: etl-service недоступен
---

Endpoint: /api/etl/imports/{id}

Method: GET
Summary: Детали импорта
Description: Возвращает подробную информацию об операции импорта, включая статистику трансформаций по типам сущностей.

Parameters:
- id (path):
  Description: ID операции импорта (MongoDB ObjectId)
  Required: Yes
  Type: string
  Example: 507f1f77bcf86cd799439011

Responses:
- 200: Детали импорта со статистикой трансформаций

- 401: Не авторизован
- 403: Недостаточно прав (требуется роль ADMIN)
- 404: Импорт не найден
- 503: etl-service недоступен
---

Endpoint: /api/etl/imports/{id}/file

Method: GET
Summary: Скачать исходный файл импорта
Description: Возвращает оригинальный файл (xlsx/json), загруженный для указанного импорта. Ответ — поток (application/octet-stream или исходный MIME) с заголовком Content-Disposition.

Parameters:
- id (path):
  Description: ID операции импорта
  Required: Yes
  Type: string
  Example: 507f1f77bcf86cd799439011

Responses:
- 200: Бинарный поток файла
- 401: Не авторизован
- 403: Недостаточно прав (требуется роль ADMIN)
- 404: Импорт или файл не найден
- 503: etl-service недоступен
---

Endpoint: /api/etl/imports/{id}/retry

Method: POST
Summary: Повторить импорт
Description: Перезапускает ETL-обработку ранее неудавшегося импорта. Старые записи transformation_log удаляются, данные из raw_payload трансформируются заново и отправляются в целевые сервисы.

Parameters:
- id (path):
  Description: ID неудавшегося импорта (MongoDB ObjectId)
  Required: Yes
  Type: string
  Example: 507f1f77bcf86cd799439011
- X-CSRF-Token (header):
  Description: CSRF токен из cookie XSRF-TOKEN
  Required: No
  Type: string

Responses:
- 200: Импорт запущен повторно

- 400: Импорт не может быть повторен (не в статусе failed)
- 401: Не авторизован
- 403: Недостаточно прав (требуется роль ADMIN)
- 404: Импорт не найден
- 503: etl-service недоступен
---

=== Schemas ===

Schema: UserRole
Type: string

Possible Values: admin, manager, shift_manager, analyst, employee

Schema: RegisterUserCommandDTO
Type: object

Properties:
- email:
  Type: string
- password:
  Type: string
- role:
  Type: any
- fullName:
  Type: string
- employeeId:
  Type: string

Schema: RegisterUserResponseDTO
Type: object

Properties:
- id:
  Type: string
- email:
  Type: string
- role:
  Type: any
- fullName:
  Type: string
- employeeId:
  Type: string

Schema: LoginUserCommandDTO
Type: object

Properties:
- email:
  Type: string
- password:
  Type: string

Schema: LoginUserResponseDTO
Type: object

Properties:
- accessToken:
  Type: string
  Description: Access token JWT
- refreshToken:
  Type: string
  Description: Refresh token

Schema: LogoutUserResponseDTO
Type: object

Properties:
- success:
  Type: boolean

Schema: ApiUserSchema
Type: object

Properties:
- id:
  Type: string
- email:
  Type: string
- role:
  Type: any
- isActive:
  Type: boolean
- fullName:
  Type: string
- employeeId:
  Type: string

Schema: RefreshSessionResponseDTO
Type: object

Properties:
- accessToken:
  Type: string
- refreshToken:
  Type: string

Schema: GetUsersResponseDTO
Type: object

Properties:
- users:
  Type: array
- total:
  Type: number
  Description: Общее количество записей

Schema: UpdateUserCommandDTO
Type: object

Properties:
- email:
  Type: string
- fullName:
  Type: string
- role:
  Type: any
- employeeId:
  Type: string

Schema: UpdateUserResponseDTO
Type: object

Properties:
- id:
  Type: string
- email:
  Type: string
- role:
  Type: any
- fullName:
  Type: string
- employeeId:
  Type: string
- isActive:
  Type: boolean

Schema: DeactivateUserCommandDTO
Type: object

Properties:
- userId:
  Type: string

Schema: DeactivateUserResponseDTO
Type: object

Properties:
- id:
  Type: string
- email:
  Type: string
- role:
  Type: any
- isActive:
  Type: boolean
- fullName:
  Type: string
- employeeId:
  Type: string

Schema: DepartmentType
Type: string

Possible Values: DIVISION, DEPARTMENT, SECTION, UNIT

Schema: CreateDepartmentCommandDTO
Type: object

Properties:
- name:
  Type: string
  Example: Производственный цех №1
- code:
  Type: string
  Example: PROD-001
- type:
  Type: any
- parentId:
  Type: string
- headEmployeeId:
  Type: string
- sourceSystemId:
  Type: string
  Example: ERP-001

Schema: CreateDepartmentResponseDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- type:
  Type: any
- parentId:
  Type: string
- headEmployeeId:
  Type: string
- sourceSystemId:
  Type: string

Schema: UpdateDepartmentBodyDTO
Type: object

Properties:
- name:
  Type: string
  Example: Производственный цех №2
- headEmployeeId:
  Type: string

Schema: UpdateDepartmentResponseDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- type:
  Type: any
- parentId:
  Type: string
- headEmployeeId:
  Type: string
- sourceSystemId:
  Type: string

Schema: LocationType
Type: string

Possible Values: office, factory

Schema: CreateLocationCommandDTO
Type: object

Properties:
- name:
  Type: string
  Example: Склад №1
- code:
  Type: string
  Example: LOC-001
- type:
  Type: any
- streetAddress:
  Type: string
  Example: ул. Примерная, 1
- postalAreaId:
  Type: string
  Description: ID почтового района
- sourceSystemId:
  Type: string
  Example: ERP-001

Schema: CreateLocationResponseDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- type:
  Type: any
- streetAddress:
  Type: string
- postalAreaId:
  Type: string
- sourceSystemId:
  Type: string

Schema: UpdateLocationBodyDTO
Type: object

Properties:
- name:
  Type: string
  Example: Склад №2
- type:
  Type: any
- streetAddress:
  Type: string
  Example: ул. Примерная, 1
- postalAreaId:
  Type: string
  Description: ID почтового района

Schema: UpdateLocationResponseDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- type:
  Type: any
- streetAddress:
  Type: string
- postalAreaId:
  Type: string
- sourceSystemId:
  Type: string

Schema: LocationItemDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- type:
  Type: any
- streetAddress:
  Type: string
- postalAreaId:
  Type: string
- sourceSystemId:
  Type: string

Schema: GetLocationsResponseDTO
Type: object

Properties:
- locations:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: WorkstationType
Type: string

Possible Values: operator_post, control_point, loading_area, lab_station, office_desk

Schema: CreateWorkstationCommandDTO
Type: object

Properties:
- name:
  Type: string
  Example: Пост оператора 1
- code:
  Type: string
  Example: WS-001
- locationId:
  Type: string
- productionLineId:
  Type: string
- workstationType:
  Type: any
- sourceSystemId:
  Type: string
  Example: ERP-001

Schema: CreateWorkstationResponseDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- locationId:
  Type: string
- productionLineId:
  Type: string
- workstationType:
  Type: any
- sourceSystemId:
  Type: string

Schema: AssignEmployeeWorkstationCommandDTO
Type: object

Properties:
- employeeId:
  Type: string
- workstationId:
  Type: string

Schema: AssignEmployeeWorkstationResponseDTO
Type: object

Properties:
- employeeId:
  Type: string
- workstationId:
  Type: string
- locationId:
  Type: string

Schema: DepartmentItemDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- type:
  Type: any
- parentId:
  Type: string
- headEmployeeId:
  Type: string
- sourceSystemId:
  Type: string

Schema: GetDepartmentsResponseDTO
Type: object

Properties:
- departments:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: CreatePositionCommandDTO
Type: object

Properties:
- title:
  Type: string
  Example: Оператор станка
- code:
  Type: string
  Example: OP-001
- departmentId:
  Type: string

Schema: CreatePositionResponseDTO
Type: object

Properties:
- id:
  Type: string
- title:
  Type: string
- code:
  Type: string
- departmentId:
  Type: string

Schema: UpdatePositionBodyDTO
Type: object

Properties:
- title:
  Type: string
  Example: Старший оператор станка
- departmentId:
  Type: string

Schema: UpdatePositionResponseDTO
Type: object

Properties:
- id:
  Type: string
- title:
  Type: string
- code:
  Type: string
- departmentId:
  Type: string

Schema: PositionItemDTO
Type: object

Properties:
- id:
  Type: string
- title:
  Type: string
- code:
  Type: string

Schema: GetPositionsResponseDTO
Type: object

Properties:
- positions:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: EmploymentType
Type: string

Possible Values: main, part_time

Schema: CreateEmployeeCommandDTO
Type: object

Properties:
- personnelNumber:
  Type: string
  Example: EMP-001
- fullName:
  Type: string
  Example: Иванов Иван Иванович
- dateOfBirth:
  Type: string
  Example: 1990-01-15
- positionId:
  Type: string
- departmentId:
  Type: string
- workstationId:
  Type: string
- hireDate:
  Type: string
  Example: 2024-01-01
- employmentType:
  Type: any
- sourceSystemId:
  Type: string
  Example: ERP-001

Schema: EmployeeStatus
Type: string

Possible Values: active, terminated, on_leave

Schema: CreateEmployeeResponseDTO
Type: object

Properties:
- id:
  Type: string
- personnelNumber:
  Type: string
- fullName:
  Type: string
- positionId:
  Type: string
- departmentId:
  Type: string
- workstationId:
  Type: string
- status:
  Type: any

Schema: TerminateEmployeeBodyDTO
Type: object

Properties:
- terminationDate:
  Type: string
  Example: 2024-12-31

Schema: TerminateEmployeeResponseDTO
Type: object

Properties:
- id:
  Type: string
- status:
  Type: any
- terminationDate:
  Type: string

Schema: UpdateEmployeeBodyDTO
Type: object

Properties:
- fullName:
  Type: string
  Example: Петров Пётр Петрович
- positionId:
  Type: string
- departmentId:
  Type: string
- workstationId:
  Type: string
- employmentType:
  Type: any
- dateOfBirth:
  Type: string
  Example: 1990-01-15

Schema: UpdateEmployeeResponseDTO
Type: object

Properties:
- id:
  Type: string
- personnelNumber:
  Type: string
- fullName:
  Type: string
- dateOfBirth:
  Type: string
- positionId:
  Type: string
- departmentId:
  Type: string
- workstationId:
  Type: string
- hireDate:
  Type: string
- terminationDate:
  Type: string
- employmentType:
  Type: any
- status:
  Type: any
- sourceSystemId:
  Type: string

Schema: EmployeeItemDTO
Type: object

Properties:
- id:
  Type: string
- personnelNumber:
  Type: string
- fullName:
  Type: string
- dateOfBirth:
  Type: string
- departmentId:
  Type: string
- positionId:
  Type: string
- locationId:
  Type: string
- workstationId:
  Type: string
- hireDate:
  Type: string
- terminationDate:
  Type: string
- employmentType:
  Type: any
- status:
  Type: any
- sourceSystemId:
  Type: string

Schema: GetEmployeesResponseDTO
Type: object

Properties:
- employees:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: ShiftType
Type: string

Possible Values: day_shift, night_shift, rotating

Schema: CreateShiftTemplateCommandDTO
Type: object

Properties:
- name:
  Type: string
  Example: Дневная смена
- shiftType:
  Type: any
- startTime:
  Type: string
  Example: 08:00
- endTime:
  Type: string
  Example: 20:00
- workDaysPattern:
  Type: string
  Description: Binary string: 1=work day, 0=day off
  Example: 1111100

Schema: CreateShiftTemplateResponseDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- shiftType:
  Type: any
- startTime:
  Type: string
- endTime:
  Type: string
- workDaysPattern:
  Type: string

Schema: UpdateShiftTemplateBodyDTO
Type: object

Properties:
- name:
  Type: string
  Example: Ночная смена
- shiftType:
  Type: any
- startTime:
  Type: string
  Example: 20:00
- endTime:
  Type: string
  Example: 08:00
- workDaysPattern:
  Type: string
  Description: Binary string: 1=work day, 0=day off
  Example: 0000011

Schema: UpdateShiftTemplateResponseDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- shiftType:
  Type: any
- startTime:
  Type: string
- endTime:
  Type: string
- workDaysPattern:
  Type: string

Schema: ShiftTemplateItemDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- shiftType:
  Type: any
- startTime:
  Type: string
- endTime:
  Type: string
- workDaysPattern:
  Type: string

Schema: GetShiftTemplatesResponseDTO
Type: object

Properties:
- templates:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: WorkstationItemDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- locationId:
  Type: string
- productionLineId:
  Type: string
- workstationType:
  Type: any
- sourceSystemId:
  Type: string

Schema: GetWorkstationsResponseDTO
Type: object

Properties:
- workstations:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: GetWorkstationResponseDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- locationId:
  Type: string
- productionLineId:
  Type: string
- workstationType:
  Type: any
- sourceSystemId:
  Type: string

Schema: GetProductionLineViewsResponseItemDTO
Type: object

Properties:
- id:
  Type: string
- productionLineId:
  Type: string
- name:
  Type: string
- code:
  Type: string
- description:
  Type: string
- isActive:
  Type: boolean
- lastSyncedAt:
  Type: string

Schema: GetProductionLineViewsResponseDTO
Type: object

Properties:
- productionLineViews:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: CreatePostalAreaCommandDTO
Type: object

Properties:
- postalCode:
  Type: string
  Example: 141000
- city:
  Type: string
  Example: Домодедово
- region:
  Type: string
  Example: Московская область

Schema: CreatePostalAreaResponseDTO
Type: object

Properties:
- id:
  Type: string
- postalCode:
  Type: string
- city:
  Type: string
- region:
  Type: string
- createdAt:
  Type: string

Schema: GetPostalAreasResponseDTO
Type: object

Properties:
- postalAreas:
  Type: array
- total:
  Type: number
  Example: 10

Schema: ProductCategory
Type: string

Possible Values: raw_material, semi_finished, finished_product, packaging

Schema: CreateProductCommandDTO
Type: object

Properties:
- code:
  Type: string
  Example: PROD-001
- name:
  Type: string
  Example: Творог 5%
- category:
  Type: any
- brand:
  Type: string
  Example: Домик в деревне
- unitOfMeasureId:
  Type: string
  Example: a1b2c3d4-e5f6-7890-abcd-ef1234567890
- unitOfMeasureCode:
  Type: string
  Example: kg
- shelfLifeDays:
  Type: number
  Example: 30
- requiresQualityCheck:
  Type: boolean
  Example: true
- sourceSystemId:
  Type: string
  Example: ERP-001

Schema: CreateProductResponseDTO
Type: object

Properties:
- id:
  Type: string
- code:
  Type: string
- name:
  Type: string
- category:
  Type: any

Schema: UnitOfMeasureDTO
Type: object

Properties:
- id:
  Type: string
- code:
  Type: string
- name:
  Type: string

Schema: GetProductsResponseItemDTO
Type: object

Properties:
- id:
  Type: string
- code:
  Type: string
- name:
  Type: string
- category:
  Type: any
- brand:
  Type: string
- unitOfMeasure:
  Type: any
- shelfLifeDays:
  Type: number
- requiresQualityCheck:
  Type: boolean

Schema: GetProductsResponseDTO
Type: object

Properties:
- products:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: GetProductionLinesResponseItemDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- description:
  Type: string
- isActive:
  Type: boolean
- createdAt:
  Type: string
- updatedAt:
  Type: string

Schema: GetProductionLinesResponseDTO
Type: object

Properties:
- productionLines:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: CreateProductionLineCommandDTO
Type: object

Properties:
- name:
  Type: string
  Example: Линия молока
- code:
  Type: string
  Example: LINE-01
- description:
  Type: string
  Example: Основная линия производства молока
- isActive:
  Type: boolean
  Example: true

Schema: CreateProductionLineResponseDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- description:
  Type: string
- isActive:
  Type: boolean

Schema: UpdateProductionLineCommandDTO
Type: object

Properties:
- name:
  Type: string
  Example: Линия молока
- code:
  Type: string
  Example: LINE-01
- description:
  Type: string
  Example: Основная линия производства молока
- isActive:
  Type: boolean
  Example: true

Schema: UpdateProductionLineResponseDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- description:
  Type: string
- isActive:
  Type: boolean

Schema: CreateOrderCommandDTO
Type: object

Properties:
- externalOrderId:
  Type: string
  Example: EXT-ORDER-001
- productId:
  Type: string
- targetQuantity:
  Type: number
  Example: 1000
- productionLineId:
  Type: string
  Example: Line-1
- plannedStart:
  Type: string
  Example: 2025-01-01
- plannedEnd:
  Type: string
  Example: 2025-01-10

Schema: OrderStatus
Type: string

Possible Values: planned, in_progress, completed, cancelled

Schema: CreateOrderResponseDTO
Type: object

Properties:
- id:
  Type: string
- externalOrderId:
  Type: string
- productId:
  Type: string
- status:
  Type: any

Schema: GetOrdersResponseItemDTO
Type: object

Properties:
- id:
  Type: string
- externalOrderId:
  Type: string
- productId:
  Type: string
- targetQuantity:
  Type: number
- actualQuantity:
  Type: number
- status:
  Type: any
- productionLineId:
  Type: string
- plannedStart:
  Type: string
- plannedEnd:
  Type: string
- actualStart:
  Type: string
- actualEnd:
  Type: string

Schema: GetOrdersResponseDTO
Type: object

Properties:
- orders:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: QualityStatus
Type: string

Possible Values: pending, approved, rejected

Schema: GetOrderOutputItemDTO
Type: object

Properties:
- id:
  Type: string
- orderId:
  Type: string
- productId:
  Type: string
- lotNumber:
  Type: string
- quantity:
  Type: number
- qualityStatus:
  Type: any
- productionDate:
  Type: string
- shift:
  Type: string

Schema: GetOrderResponseDTO
Type: object

Properties:
- id:
  Type: string
- externalOrderId:
  Type: string
- productId:
  Type: string
- targetQuantity:
  Type: number
- actualQuantity:
  Type: number
- status:
  Type: any
- productionLineId:
  Type: string
- plannedStart:
  Type: string
- plannedEnd:
  Type: string
- actualStart:
  Type: string
- actualEnd:
  Type: string
- outputs:
  Type: array

Schema: OrderAction
Type: string

Possible Values: start, complete, cancel

Schema: UpdateOrderStatusBodyDTO
Type: object

Properties:
- action:
  Type: any
- actualQuantity:
  Type: number
  Example: 950

Schema: UpdateOrderStatusResponseDTO
Type: object

Properties:
- id:
  Type: string
- status:
  Type: any
- actualQuantity:
  Type: number
- actualStart:
  Type: string
- actualEnd:
  Type: string

Schema: RecordOutputCommandDTO
Type: object

Properties:
- orderId:
  Type: string
- lotNumber:
  Type: string
  Example: LOT-2025-001
- quantity:
  Type: number
  Example: 500
- productionDate:
  Type: string
  Example: 2025-01-05
- shift:
  Type: string
  Example: morning

Schema: RecordOutputResponseDTO
Type: object

Properties:
- id:
  Type: string
- orderId:
  Type: string
- lotNumber:
  Type: string
- quantity:
  Type: number

Schema: GetOutputResponseItemDTO
Type: object

Properties:
- id:
  Type: string
- orderId:
  Type: string
- productId:
  Type: string
- lotNumber:
  Type: string
- quantity:
  Type: number
- qualityStatus:
  Type: any
- productionDate:
  Type: string
- shift:
  Type: string

Schema: GetOutputResponseDTO
Type: object

Properties:
- outputs:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: SaleChannel
Type: string

Possible Values: retail, wholesale, horeca, export

Schema: RecordSaleCommandDTO
Type: object

Properties:
- externalId:
  Type: string
  Example: SALE-001
- productId:
  Type: string
- customerId:
  Type: string
  Example: ООО Ромашка
- quantity:
  Type: number
  Example: 100
- amount:
  Type: number
  Example: 50000
- saleDate:
  Type: string
  Example: 2025-02-01
- region:
  Type: string
  Example: Краснодарский край
- channel:
  Type: any

Schema: RecordSaleResponseDTO
Type: object

Properties:
- id:
  Type: string
- externalId:
  Type: string
- productId:
  Type: string
- amount:
  Type: number

Schema: GetSalesResponseItemDTO
Type: object

Properties:
- id:
  Type: string
- externalId:
  Type: string
- productId:
  Type: string
- customerId:
  Type: string
- quantity:
  Type: number
- amount:
  Type: number
- saleDate:
  Type: string
- region:
  Type: string
- channel:
  Type: any

Schema: GetSalesResponseDTO
Type: object

Properties:
- sales:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: GetSalesSummaryItemDTO
Type: object

Properties:
- groupKey:
  Type: string
- totalQuantity:
  Type: number
- totalAmount:
  Type: number
- salesCount:
  Type: number

Schema: GetSalesSummaryResponseDTO
Type: object

Properties:
- summary:
  Type: array
- totalAmount:
  Type: number
- totalQuantity:
  Type: number
- total:
  Type: number
  Description: Общее количество групп (с учётом фильтров)

Schema: UpsertInventoryCommandDTO
Type: object

Properties:
- productId:
  Type: string
- warehouseId:
  Type: string
- lotNumber:
  Type: string
  Example: LOT-001
- quantity:
  Type: number
  Example: 200

Schema: UpsertInventoryResponseDTO
Type: object

Properties:
- id:
  Type: string
- productId:
  Type: string
- warehouseId:
  Type: string
- quantity:
  Type: number

Schema: GetInventoryResponseItemDTO
Type: object

Properties:
- id:
  Type: string
- productId:
  Type: string
- warehouseId:
  Type: string
- lotNumber:
  Type: string
- quantity:
  Type: number
- lastUpdated:
  Type: string

Schema: GetInventoryResponseDTO
Type: object

Properties:
- inventory:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: RecordQualityResultCommandDTO
Type: object

Properties:
- lotNumber:
  Type: string
  Example: LOT-2025-001
- productId:
  Type: string
- parameterName:
  Type: string
  Example: moisture
- resultValue:
  Type: number
  Example: 12.5
- qualityStatus:
  Type: any
- testDate:
  Type: string
  Example: 2025-01-06

Schema: RecordQualityResultResponseDTO
Type: object

Properties:
- id:
  Type: string
- lotNumber:
  Type: string
- productId:
  Type: string
- qualityStatus:
  Type: any

Schema: GetQualityResponseItemDTO
Type: object

Properties:
- id:
  Type: string
- lotNumber:
  Type: string
- productId:
  Type: string
- parameterName:
  Type: string
- resultValue:
  Type: number
- lowerLimit:
  Type: number
- upperLimit:
  Type: number
- qualityStatus:
  Type: any
- testDate:
  Type: string

Schema: GetQualityResponseDTO
Type: object

Properties:
- results:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: SensorQuality
Type: string

Possible Values: good, degraded, bad

Schema: RecordSensorReadingCommandDTO
Type: object

Properties:
- deviceId:
  Type: string
  Example: SENSOR-01
- productionLineId:
  Type: string
  Example: Line-1
- parameterName:
  Type: string
  Example: temperature
- value:
  Type: number
  Example: 72.5
- unit:
  Type: string
  Example: °C
- quality:
  Type: any
- recordedAt:
  Type: string
  Example: 2025-01-05T10:00:00.000Z
- lowerLimit:
  Type: number
  Example: 60
- upperLimit:
  Type: number
  Example: 95

Schema: RecordSensorReadingResponseDTO
Type: object

Properties:
- id:
  Type: string
- deviceId:
  Type: string
- productionLineId:
  Type: string
- parameterName:
  Type: string
- quality:
  Type: any

Schema: GetSensorsResponseItemDTO
Type: object

Properties:
- id:
  Type: string
- deviceId:
  Type: string
- productionLineId:
  Type: string
- parameterName:
  Type: string
- value:
  Type: number
- unit:
  Type: string
- quality:
  Type: any
- recordedAt:
  Type: string

Schema: GetSensorsResponseDTO
Type: object

Properties:
- readings:
  Type: array
- total:
  Type: number
  Description: Общее количество записей (с учётом фильтров)

Schema: GetKpiResponseDTO
Type: object

Properties:
- totalOutput:
  Type: number
- defectRate:
  Type: number
- completedOrders:
  Type: number
- totalOrders:
  Type: number
- oeeEstimate:
  Type: number

Schema: CreateCustomerCommandDTO
Type: object

Properties:
- name:
  Type: string
  Example: ООО Молочная фабрика

Schema: CreateCustomerResponseDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- createdAt:
  Type: string

Schema: GetCustomersResponseDTO
Type: object

Properties:
- customers:
  Type: array
- total:
  Type: number
  Example: 5

Schema: CreateWarehouseCommandDTO
Type: object

Properties:
- name:
  Type: string
  Example: Главный склад
- code:
  Type: string
  Example: WH-001

Schema: CreateWarehouseResponseDTO
Type: object

Properties:
- id:
  Type: string
- name:
  Type: string
- code:
  Type: string
- createdAt:
  Type: string

Schema: GetWarehousesResponseDTO
Type: object

Properties:
- warehouses:
  Type: array
- total:
  Type: number
  Example: 3

Schema: CreateQualitySpecCommandDTO
Type: object

Properties:
- productId:
  Type: string
  Example: a1b2c3d4-e5f6-7890-abcd-ef1234567890
- parameterName:
  Type: string
  Example: жирность
- lowerLimit:
  Type: number
  Example: 4.5
- upperLimit:
  Type: number
  Example: 5.5

Schema: CreateQualitySpecResponseDTO
Type: object

Properties:
- id:
  Type: string
- productId:
  Type: string
- parameterName:
  Type: string
- lowerLimit:
  Type: number
- upperLimit:
  Type: number
- createdAt:
  Type: string

Schema: GetQualitySpecsResponseDTO
Type: object

Properties:
- qualitySpecs:
  Type: array
- total:
  Type: number
  Example: 8

Schema: CreateUnitOfMeasureCommandDTO
Type: object

Properties:
- code:
  Type: string
  Example: kg
- name:
  Type: string
  Example: Килограмм

Schema: CreateUnitOfMeasureResponseDTO
Type: object

Properties:
- id:
  Type: string
- code:
  Type: string
- name:
  Type: string

Schema: UnitOfMeasureItemDTO
Type: object

Properties:
- id:
  Type: string
- code:
  Type: string
- name:
  Type: string
- createdAt:
  Type: string

Schema: GetUnitOfMeasuresResponseDTO
Type: object

Properties:
- unitsOfMeasure:
  Type: array
- total:
  Type: number
  Description: Общее количество записей

Schema: SourceSystem
Type: string
Description: Внешняя система-источник

Possible Values: 1c_zup, 1c_erp, mes, scada, lims

Schema: ImportType
Type: string
Description: Тип импортируемой сущности

Possible Values: employees, departments, positions, products, orders, sensors, quality

Schema: ImportDataCommandDTO
Type: object

Properties:
- source_system:
  Type: any
  Description: Внешняя система-источник
  Example: 1c_zup
- import_type:
  Type: any
  Description: Тип импортируемой сущности
  Example: employees
- data:
  Type: array
  Description: Массив записей в формате источника. Обязательные поля зависят от (source_system, import_type). Пример для 1c_zup + employees: { employee_id, full_name, position_code, department_code }.
  Example: [object Object]

Schema: ImportStatus
Type: string

Possible Values: pending, processing, completed, failed

Schema: SourceFileFormat
Type: string

Possible Values: xlsx, json

Schema: ImportResponseDTO
Type: object

Properties:
- import_id:
  Type: string
  Description: MongoDB ObjectId операции импорта
  Example: 507f1f77bcf86cd799439011
- status:
  Type: any
  Example: processing
- records_count:
  Type: number
  Description: Количество валидных записей, принятых в обработку
  Example: 150
- source_file_id:
  Type: string
  Description: ID исходного файла в GridFS (только при загрузке файла)
- format:
  Type: any
- warnings:
  Type: array
  Description: Предупреждения парсера
- parse_errors:
  Type: array
  Description: Ошибки валидации записей

Schema: ImportFileCommandDTO
Type: object

Properties:
- file:
  Type: string
  Description: Файл .xlsx или .json (максимум 20MB)
- source_system:
  Type: any
  Description: Внешняя система-источник
  Example: 1c_zup
- import_type:
  Type: any
  Description: Тип импортируемой сущности. Допустимые комбинации: 1c_zup→(employees, departments, positions); 1c_erp→(products); mes→(orders); scada→(sensors); lims→(quality).
  Example: employees

Schema: ImportListItemDTO
Type: object

Properties:
- import_id:
  Type: string
  Example: 507f1f77bcf86cd799439011
- source_system:
  Type: any
- import_type:
  Type: any
- status:
  Type: any
- records_count:
  Type: number
  Example: 150
- source_file_id:
  Type: string
  Description: ID исходного файла в GridFS
- source_file_format:
  Type: any
- created_at:
  Type: string
  Example: 2026-04-11T10:00:00.000Z
- processed_at:
  Type: string

Schema: ImportErrorDTO
Type: object

Properties:
- field:
  Type: string
  Example: employmentType
- message:
  Type: string
  Example: Invalid employment type
- record_index:
  Type: number
  Example: 42

Schema: ImportStatsDTO
Type: object

Properties:
- total:
  Type: number
  Example: 150
- success:
  Type: number
  Example: 148
- error:
  Type: number
  Example: 2
- skipped:
  Type: number

Schema: ImportDetailsDTO
Type: object

Properties:
- import_id:
  Type: string
  Example: 507f1f77bcf86cd799439011
- source_system:
  Type: any
- import_type:
  Type: any
- status:
  Type: any
- records_count:
  Type: number
  Example: 150
- source_file_id:
  Type: string
  Description: ID исходного файла в GridFS
- source_file_format:
  Type: any
- created_at:
  Type: string
  Example: 2026-04-11T10:00:00.000Z
- processed_at:
  Type: string
- errors:
  Type: array
- stats:
  Type: any

Schema: RetryImportResponseDTO
Type: object

Properties:
- import_id:
  Type: string
  Example: 507f1f77bcf86cd799439011
- status:
  Type: any
  Example: processing
- message:
  Type: string
  Example: Import retry started

