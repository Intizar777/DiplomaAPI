# Technical Debts

> Последнее обновление: 2026-05-04  
> Это живой документ, отслеживающий известные технические долги, архитектурные проблемы и улучшения.

## Легенда

| Символ | Severity   | Критерий                                              |
|--------|------------|-------------------------------------------------------|
| 🔴     | Критичный  | Уязвимость безопасности или потеря данных            |
| 🟠     | Высокий    | Нарушение надёжности или архитектурная некорректность |
| 🟡     | Средний    | Качество кода, поддерживаемость                       |
| 🟢     | Низкий     | Мелкие улучшения, косметика                          |

---

## 🔴 Критические

### DEBT-001 — Реальные секреты в git

**Расположение:** `envs/production/postgres.env`, `envs/production/auth.env`, `envs/production/services.env`, `apps/auth-service/.env.example`

**Описание:** Plaintext пароли БД (`authDesh4!`, `productionDesh10!`), JWT signing ключи и RabbitMQ пароли (`pass1`) коммитены в репозитории.

**Риск:** Компрометация production-систем при утечке исходного кода. JWT ключи позволяют подделывать токены доступа. Пароли БД открывают полный доступ к данным.

**Рекомендация:** Перенести все секреты в HashiCorp Vault, AWS Secrets Manager или GitHub Actions Secrets. Удалить `envs/production/` из git (git rm -r), добавить в `.gitignore`, переинициализировать git history (git filter-branch или git-filter-repo).

---

### ~~DEBT-002 — PostgreSQL `trust` auth в production~~ ✅ ИСПРАВЛЕНО

**Расположение:** `envs/production/postgres.env`, `envs/local_prod/postgres.env`

**Описание:** Переменная `POSTGRES_HOST_AUTH_METHOD=trust` отключает требование пароля для подключения к PostgreSQL внутри Docker-сети.

**Риск:** Любой контейнер или процесс внутри Docker-сети может подключиться и модифицировать БД без аутентификации.

**Решение:** Установлен `POSTGRES_HOST_AUTH_METHOD=scram-sha-256` во всех 4 файлах (`.env`, `.env.example`, `envs/production/postgres.env`, `envs/local_prod/postgres.env`). Добавлены флаги `--auth-host=scram-sha-256 --auth-local=scram-sha-256` в `POSTGRES_INITDB_ARGS` для применения при инициализации БД.

---

### DEBT-003 — CORS по умолчанию `'*'`

**Расположение:** `apps/gateway/src/main.ts` (строка с `corsOrigin`)

**Описание:** Переменная окружения `CORS_ORIGIN` дефолтится на `'*'`, что позволяет любому веб-приложению с любого домена отправлять запросы к API.

**Риск:** CSRF-атаки от вредоносных веб-сайтов. Утечка данных через CORS при недостаточной валидации прав доступа.

**Рекомендация:** Изменить дефолт на пустую строку `''` или конкретный домен; требовать явного указания `CORS_ORIGIN` в production. Использовать `credentials: 'include'` на фронте и проверять origin на бэке.

---

### DEBT-004 — CSRF отключён по умолчанию

**Расположение:** `.env.example` (строка `CSRF_ENABLED=false`), `apps/gateway/src/app/guards/csrf.guard.ts`

**Описание:** `CsrfGuard` отключается если `CSRF_ENABLED=false` или если переменная отсутствует. Guard также байпасится при отсутствии `XSRF-TOKEN` куки (для поддержки мобильных клиентов).

**Риск:** Без CSRF-защиты браузеры могут быть скомпрометированы для выполнения state-changing операций (удаление, обновление) от лица залогиненного пользователя.

**Рекомендация:** Установить `CSRF_ENABLED=true` в дефолте. Для мобильных клиентов использовать заголовок Authorization (Bearer token) вместо куки. Убедиться что guard проверяет CSRF для всех POST/PUT/DELETE.

---

## 🟠 Высокие

### DEBT-005 — Отсутствует шаг деплоя в CI/CD

**Расположение:** `.github/workflows/production.yml`

**Описание:** Pipeline строит Docker-образы, пушит в GHCR, но не обновляет running production-стек. Нет SSH-команд, kubectl rollout или docker compose pull && up.

**Риск:** Новые версии никогда не переходят в production. Continuous delivery остаётся невыполненным обещанием. Деплой требует ручного вмешательства.

**Рекомендация:** Добавить deploy-job после build: SSH на production-хост, запустить `docker compose pull && up -d`. Или использовать ArgoCD/Flux для GitOps-деплоя. Добавить smoke-тесты после деплоя.

---

### DEBT-006 — Нет сканирования уязвимостей в CI/CD

**Расположение:** `.github/workflows/production.yml`

**Описание:** Pipeline не запускает `npm audit`, Snyk, Trivy или другой SAST/DAST. Зависимость `xlsx: ^0.18.5` содержит известную CVE, но не обнаруживается автоматически.

**Риск:** Уязвимые зависимости попадают в production. Отсутствие контроля качества зависимостей.

**Рекомендация:** Добавить `npm audit --audit-level=moderate` (или Snyk CI) как обязательный шаг перед build. Включить GitHub Dependabot для auto-PRs. Заменить `xlsx` на `exceljs` или `SheetJS Pro`.

---

### DEBT-007 — RabbitMQ management port открыт на `0.0.0.0`

**Расположение:** `docker-compose.yml` (15672), `docker-compose.infrastructure.yml` (15672)

**Описание:** Порт RabbitMQ Management UI 15672 биндится на все интерфейсы (`0.0.0.0`) во всех compose-файлах.

**Риск:** Любой в локальной сети может получить доступ к RabbitMQ Management, просматривать очереди, перенаправлять сообщения, удалять очереди.

**Рекомендация:** Изменить на `127.0.0.1:15672:15672` для dev-окружения. В production использовать VPN/bastion-хост для доступа. Установить пароль вместо дефолтного `guest:guest`.

---

### DEBT-008 — Enum-касты `as unknown as` в domain-слое (19+ мест)

**Расположение:** Все personnel usecases (`apps/personnel/src/app/application/usecases/*.ts`), `apps/production/src/app/application/usecases/record-sensor-reading.usecase.ts`

**Описание:** Из-за дублирования enum-ов между `libs/interfaces` (uppercase: `DIVISION`) и domain-слоем (lowercase: `division`) код везде кастует `as unknown as DomainEnum`.

**Риск:** Двойная кастование байпасит TypeScript-типизацию. Если значения enum-ов когда-то разойдутся, runtime-ошибки будут невидимы.

**Рекомендация:** Синхронизировать enum-ы: выбрать единый исток истины (либо `libs/interfaces`, либо domain), удалить дублирование. Или создать маппер между интерфейсом и domain. Удалить все `as unknown as`.

---

### DEBT-009 — Зависимость `xlsx` 0.18.5 (2.5 года без обновлений, CVE-2023-30533)

**Расположение:** `package.json` (зависимость `xlsx`)

**Описание:** SheetJS Community Edition 0.18.5 (ноябрь 2022) имеет известную CVE и больше не обновляется на npm. Мейнтейнеры перешли на платную модель.

**Риск:** Уязвимости в обработке Excel-файлов, особенно при импорте untrusted источников в ETL.

**Рекомендация:** Заменить на `exceljs: ^4.x` (open-source) или приобрести SheetJS Pro. Обновить ETL-логику для новой библиотеки.

---

## 🟡 Средние

### DEBT-010 — Нулевое покрытие e2e-тестами

**Расположение:** Отсутствуют файлы `.e2e-spec.ts` во всех `apps/`

**Описание:** 43 unit spec файла, но 0 e2e spec. `supertest` в `dependencies` (не `devDependencies`). Gateway имеет только 1 spec (`auth-proxy.service.spec.ts`).

**Риск:** Поведение между сервисами (RMQ RPC, outbox, события) не тестируется. Регрессия незаметна.

**Рекомендация:** Добавить `*.e2e-spec.ts` для каждого app. Примеры: register-login-logout flow (auth), create-employee-to-production flow (personnel+production). Переместить `supertest` в `devDependencies`.

---

### ~~DEBT-011 — Отсутствует Circuit Breaker в gateway RMQ-прокси~~ ✅ ИСПРАВЛЕНО

**Расположение:** `apps/gateway/src/app/` (proxy services для auth, personnel, production)

**Описание:** Proxy-сервисы gateway вызывали RMQ без circuit breaker, что ухудшало деградацию при нестабильности downstream-сервисов.

**Риск:** Если микросервис зависнет или будет перегружен, gateway будет бесконечно ждать ответа, исчерпав connection pool. Лавинообразный отказ.

**Решение:** Добавлен circuit breaker на базе `opossum` в `BaseProxyService` (в `libs/nest-utils`), один инстанс на каждый proxy-сервис (`AuthProxyService`, `PersonnelProxyService`, `ProductionProxyService`). При открытом состоянии возвращается HTTP 503 (`ServiceUnavailableException`), добавлено логирование переходов `open/halfOpen/close`. Также добавлен тест в `auth-proxy.service.spec.ts` на немедленный reject при открытом breaker.

---

### ~~DEBT-012 — Смешанная модель публикации событий в personnel и production~~ ✅ ИСПРАВЛЕНО

**Расположение:** `apps/personnel/src/app/application/usecases/`, `apps/production/src/app/application/usecases/`

**Описание:** Одни use cases публикуют события через Transactional Outbox (write в БД, потом cron публикует), другие через direct `RmqEventEmitterService.emit()`. Непоследовательность.

**Риск:** Некоторые события могут потеряться при крахе между emit и persist (race condition). Сложность при поддержке — hard понять какой паттерн когда использовать.

**Решение:** Все 12 use cases, использовавших direct `EventEmitterService.publish()`, переведены на `OutboxMessageRepository.save()`. Порты `event-emitter.service.ts` удалены из обоих сервисов. `RmqEventEmitterModule.forRoot()` убран из `ProductionInfrastructureModule`. Теперь все события публикуются исключительно через Transactional Outbox.

---

### ~~DEBT-013 — Мёртвый код: `@deprecated dispatchWithLinearRetry`~~ ✅ ИСПРАВЛЕНО

**Расположение:** `apps/etl/src/app/infrastructure/http/dispatch.service.ts`

**Описание:** Метод помечен `@deprecated` с примечанием "Use dispatch() with exponential backoff instead". Нет вызывателей в коде.

**Риск:** Код занимает место, сбивает с толку новых разработчиков.

**Решение:** Удалены `dispatchWithLinearRetry()` и вспомогательный приватный метод `delay()`, который использовался только им. Вызывателей в кодовой базе не было.

---

### ~~DEBT-014 — Scaffolding-артефакты в production app~~ ✅ ИСПРАВЛЕНО

**Расположение:** `apps/production/src/app/app.controller.ts`, `apps/production/src/app/app.service.ts`, и 2 спека `app.controller.spec.ts`, `app.service.spec.ts`

**Описание:** Nx-сгенерированные файлы с методом `getData()` возвращающим `{ message: 'Hello API' }`. Это шаблоны, которые должны были быть заменены на реальную логику.

**Риск:** Шум в API документации (Swagger), шум в тестовом выводе, запутание для новых разработчиков.

**Решение:** Удалены все 4 файла (`app.controller.ts`, `app.service.ts`, `app.controller.spec.ts`, `app.service.spec.ts`). В других сервисах аналогичных артефактов не обнаружено.

---

### DEBT-015 — ETL IMPORT_SCHEMAS отстают от mapper-ов

**Расположение:** `apps/etl/src/app/infrastructure/`, `docs/pipeline-map.md` (раздел 8)

**Описание:** Mapper-ы реализованы для shift_templates, ERP sales/inventory, MES output, LIMS usage_decisions, но эти импорт-типы не добавлены в `IMPORT_SCHEMAS` для валидации.

**Риск:** Импорт этих типов валидируется неполностью, ошибки в данных не ловятся на granice ingestion.

**Рекомендация:** Добавить недостающие типы импорта в `IMPORT_SCHEMAS` с полной валидацией полей. Обновить `pipeline-map.md` с заметкой о статусе (P1/P2/Future).

---

### DEBT-016 — SCADA алармы валидируются, но не диспетчеризуются

**Расположение:** `apps/etl/src/app/infrastructure/` (Scada transformer)

**Описание:** DTO-и для SCADA-алармов валидируются, DTO попадают в TransformationLog, но события не публикуются в production RMQ-exchange.

**Риск:** Информация о датчик-аномалиях теряется, не доходит до downstream потребителей для анализа.

**Рекомендация:** Добавить логику dispatch для алармов (обычно `ProductionSensorAnomalyDetectedEvent`). Убедиться что consumer в production-service слушает эти события.

---

### DEBT-017 — Jaeger all-in-one с in-memory storage

**Расположение:** `docker-compose.observability.yml` (образ `jaegertracing/all-in-one:1.57`)

**Описание:** Jaeger хранит трейсы в памяти. При рестарте контейнера все трейсы теряются.

**Риск:** Production observability неполна — не можем ретроспективно анализировать трейсы старше одного запуска.

**Рекомендация:** Настроить Jaeger с persistent backend: Elasticsearch, Cassandra или Badger с volume. Или использовать managed Jaeger-compatible service (напр., Grafana Cloud Traces).

---

### DEBT-018 — Source maps включены в production webpack-конфигах

**Расположение:** Все `apps/*/webpack.config.js`

**Описание:** Все webpack-конфиги имеют `sourceMap: true`, раскрывая оригинальный TypeScript исходник в production builds.

**Риск:** Безопасность через obscurity нарушена. Source maps легко находимы и позволяют обратный инженеринг.

**Рекомендация:** Отключить source maps в production (`sourceMap: false` или conditional), включить только для staging/dev для отладки. Или хранить source maps на отдельном protected сервере для отладки.

---

## 🟢 Низкие

### DEBT-019 — Отсутствуют `.env.example` для gateway и etl

**Расположение:** `apps/gateway/.env`, `apps/etl/.env`

**Описание:** Auth, personnel, production имеют `.env.example`, но gateway и etl — нет. Реальные `.env` файлы с真實 значениями лежат в репозитории без шаблонов.

**Риск:** Новые разработчики не знают какие env-переменные требуются, какие значения использовать.

**Рекомендация:** Создать `apps/gateway/.env.example` и `apps/etl/.env.example` с плейсхолдерами (localhost для БД, фейк JWT секреты, и т.д.). Удалить из git реальные `.env` файлы.

---

### DEBT-020 — Невалидные значения в auth `.env.example`

**Расположение:** `apps/auth-service/.env.example`

**Описание:** `JWT_ACCESS_TTL=some-value`, `JWT_REFRESH_TTL=some-thing` — эти значения не парсятся ms-библиотекой.

**Риск:** Если разработчик копирует `.env.example` без редактирования, JWT token issuance упадёт.

**Рекомендация:** Заменить на валидные значения: `JWT_ACCESS_TTL=15m`, `JWT_REFRESH_TTL=7d`.

---

### DEBT-021 — MongoDB URI через `process.env` минуя ConfigService

**Расположение:** `apps/etl/src/app/app.module.ts` (строка с `MongooseModule.forRoot`)

**Описание:** `MongooseModule.forRoot(process.env.MONGO_URI || 'mongodb://localhost:27017/etl_db')` читает env напрямую вместо использования `ConfigService`.

**Риск:** Отсутствует type-safety и валидация. ConfigService не видит это значение в логе.

**Рекомендация:** Использовать `configService.get<string>('MONGO_URI')` как в других app-модулях. Убедиться что `MONGO_URI` описана в `.env.example`.

---

### DEBT-022 — Версионная мисогласованность Prisma (7.6 vs 7.7)

**Расположение:** `package.json` (`prisma: ^7.6.0`, `@prisma/client: ^7.7.0`)

**Описание:** prisma-CLI версия 7.6, а @prisma/client — 7.7 (одна минорная версия выше).

**Риск:** Minor risk: несоответствие может привести к генерированию неправильного Prisma Client кода при миграциях.

**Рекомендация:** Обновить обе версии на одну: либо оба 7.7, либо оба на latest stable. Prisma рекомендует держать их синхронизированными.

---

### DEBT-023 — `PersonnelShiftAssignedEvent` не используется

**Расположение:** `libs/contracts/src/personnel/personnel.events.ts`

**Описание:** Event определён с полной структурой, но нет издателя (none of usecases publishes) и нет потребителя (no @RabbitSubscribe).

**Риск:** Мёртвый код, сбивает с толку при чтении контрактов.

**Рекомендация:** Либо реализовать издание события в `shift-assignment` use case, либо удалить из contracts если функция не требуется.

---

### DEBT-024 — `ProductionSensorAnomalyDetectedEvent` опубликован, но не потреблен

**Расположение:** Выпускается в `apps/production/src/app/application/usecases/record-sensor-reading.usecase.ts`, нигде не обрабатывается

**Описание:** SensorAnomalyDetector публикует событие при выходе значения за границы, но нет никого кто это событие слушает.

**Риск:** Информация о аномалиях генерируется, но теряется. Никакие оповещения/логирование не срабатывают.

**Рекомендация:** Либо добавить consumer в production-service для логирования/алерт-генерации, либо добавить потребителя в отдельный alerting-сервис. Или удалить если аномалии не требуются.

---

### DEBT-025 — Отсутствуют resource limits в docker-compose

**Расположение:** Все `docker-compose*.yml` (gateway, auth, personnel, production, etl, postgres, rabbitmq, mongo)

**Описание:** Никакой контейнер не имеет `deploy.resources.limits` для CPU или памяти.

**Риск:** Runaway процесс (ETL с большим импортом, ползующий query) может запросить всю доступную память/CPU хоста, вызвав OOM-kill или зависание.

**Рекомендация:** Добавить limits: `memory: 512M`, `cpus: 0.5` для каждого сервиса (отрегулировать под реальные нужды). Для баз: `memory: 1G`, `cpus: 1`.

---

### DEBT-026 — `GET /users` ADMIN guard закомментирован

**Расположение:** `apps/gateway/src/app/auth/auth.controller.ts` (декоратор @UseGuards)

**Описание:** `@UseGuards(RoleGuard(UserRole.ADMIN))` закомментирован, endpoint доступен всем авторизованным пользователям.

**Риск:** Любой user может список всех пользователей (email, names, roles). Potential privacy/security issue.

**Рекомендация:** Раскомментировать guard или явно задокументировать почему endpoint public. Если public — добавить пагинацию/лимит результатов.

---

### DEBT-027 — OEE estimate упрощён

**Расположение:** `apps/production/src/app/application/usecases/get-kpi.usecase.ts`

**Описание:** `oeeEstimate` вычисляется как отношение завершённых заказов к общему количеству, не как полная OEE = (Availability × Performance × Quality).

**Риск:** Метрика KPI некорректна и введёт в заблуждение, когда данные пойдут в аналитику или дашборды.

**Рекомендация:** Реализовать полную OEE-формулу: сбор Availability (uptime), Performance (actual vs planned output), Quality (scrap/rework %). Заменить упрощённый estimate на корректный расчёт.

---

### DEBT-028 — Rate limiting дефолты очень высокие

**Расположение:** `apps/gateway/src/app/app.module.ts`, `.env.example`

**Описание:** Дефолты: `short: 20/1s`, `medium: 100/10s`, `long: 500/60s`. `.env.example` переопределяет на `short: 100/1s`, `medium: 1000/10s`, `long: 10000/60s` — чрезвычайно permissive.

**Риск:** Rate limits не защищают от brute-force (5 попыток логина в секунду легко автоматизировать). DDoS-защита неэффективна.

**Рекомендация:** Установить более строгие лимиты: `short: 10/60s` (для auth endpoints), `medium: 100/60s`, `long: 1000/3600s`. Убедиться что лимиты в production отличаются от dev и соответствуют ожидаемой нагрузке.

---

## Итого

**28 технических долгов**, распределённых по severity:
- 4 критические (безопасность, auth)
- 5 высоких (надёжность, архитектура)
- 9 средних (качество кода, тестирование)
- 10 низких (minor улучшения)

**Рекомендуемый порядок работ:**
1. DEBT-001, DEBT-002 (секреты и auth) — критично для production
2. DEBT-003, DEBT-004 (CORS, CSRF) — безопасность
3. DEBT-005, DEBT-006 (CI/CD, security scanning) — процесс
4. DEBT-008 (enum-касты) — качество кода
5. Остальные в порядке importance для вашего случая
