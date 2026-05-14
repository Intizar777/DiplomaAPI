# Gateway API Responses

Generated: 2026-05-14

## Successful Responses

### Batch Inputs

**Endpoint:** `GET /production/batch-inputs`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "items": [
    {
      "id": "700e8226-d464-4739-845a-52a53271a3f6",
      "orderId": "6dddc9fc-8231-4c3f-a172-bdcf8bcb5fea",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "quantity": 2561.03,
      "inputDate": "2026-05-04T21:13:20.033Z",
      "createdAt": "2026-05-12T05:28:09.754Z"
    },
    {
      "id": "32f3135c-ef7d-41ac-8e49-22740b83cfe6",
      "orderId": "2931174a-89d5-4ec1-9aaa-d56cb33df308",
      "productId": "fd2079d6-6e13-4bb9-a0a9-07dea22cdefa",
      "quantity": 17711.326,
      "inputDate": "2026-05-04T17:22:42.816Z",
      "createdAt": "2026-05-12T05:28:09.769Z"
    },
    {
      "id": "d875ec36-57f0-408e-8d98-2ac6f77d015f",
      "orderId": "2931174a-89d5-4ec1-9aaa-d56cb33df308",
      "productId": "fd2079d6-6e13-4bb9-a0a9-07dea22cdefa",
      "quantity": 17711.326,
      "inputDate": "2026-05-04T17:22:42.816Z",
      "createdAt": "2026-05-12T05:28:09.769Z"
    },
    {
      "id": "11376162-a884-4d9d-b20a-9630a4673063",
      "orderId": "5377ab47-19d0-4140-a20d-af7fcb55f140",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "quantity": 70592.977,
      "inputDate": "2026-05-04T10:01:27.835Z",
      "createdAt": "2026-05-12T05:28:09.754Z"
    },
    {
      "id": "a460e3c1-e60c-4d37-890c-e794cfc5053f",
      "orderId": "c9b0b8d6-cdbd-453d-8bf4-c258ba998db9",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "quantity": 70926.276,
      "inputDate": "2026-05-04T00:23:21.602Z",
      "createdAt": "2026-05-12T05:28:09.754Z"
    },
    {
      "id": "5cd482bd-570d-4e02-8e22-76cbbd6c4d13",
      "orderId": "6dddc9fc-8231-4c3f-a172-bdcf8bcb5fea",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "quantity": 2561.03,
      "inputDate": "2026-05-03T21:13:20.033Z",
      "createdAt": "2026-05-12T05:28:09.754Z"
    },
    {
      "id": "3c8f6a6b-5f77-4c39-8819-0b9aea5a54d4",
      "orderId": "6dddc9fc-8231-4c3f-a172-bdcf8bcb5fea",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "quantity": 2561.03,
      "inputDate": "2026-05-03T21:13:20.033Z",
      "createdAt": "2026-05-12T05:28:09.754Z"
    },
    {
      "id": "ceb8e7e7-03f1-4668-ad04-c810b9ffa00d",
      "orderId": "97424ee1-f1cb-49fd-92af-5ac30132340f",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "quantity": 53742.404,
      "inputDate": "2026-05-03T21:04:31.850Z",
      "createdAt": "2026-05-12T05:28:09.754Z"
    },
    {
      "id": "457f4a43-fb09-4d21-9c14-8c4c49032396",
      "orderId": "39dc90d6-567b-4b1d-9dce-f429991b2b5f",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "quantity": 3815.736,
      "inputDate": "2026-05-03T18:30:57.746Z",
      "createdAt": "2026-05-12T05:28:09.754Z"
    },
    {
      "id": "e2e1910c-953d-4973-8db6-a0f0d8401ca5",
      "orderId": "39dc90d6-567b-4b1d-9dce-f429991b2b5f",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "quantity": 3815.736,
      "inputDate": "2026-05-03T18:30:57.746Z",
      "createdAt": "2026-05-12T05:28:09.754Z"
    }
  ],
  "total": 4453
}
```

### Current User

**Endpoint:** `GET /auth/me`

**Status:** 200

**Response:**

```json
{
  "id": "0c21a010-d696-4828-969a-5e47a7c46aee",
  "role": "admin",
  "email": "admin@efko.local",
  "fullName": "Куликов Петр Евгеньевич",
  "employeeId": "282b6565-fbad-4011-8c0d-616c3d102ff9",
  "isActive": true
}
```

### Customers

**Endpoint:** `GET /production/customers`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "customers": [
    {
      "id": "93706a78-9986-4351-8f1d-387600dfa589",
      "name": "ООО Монетка",
      "createdAt": "2026-05-08T15:02:39.806Z"
    },
    {
      "id": "25514e63-cb82-4836-b455-cbabc364271d",
      "name": "ООО Бристол",
      "createdAt": "2026-05-08T15:02:39.803Z"
    },
    {
      "id": "de219684-ecaa-4945-a8d5-b4982e9c3d0d",
      "name": "ООО Копейка",
      "createdAt": "2026-05-08T15:02:39.800Z"
    },
    {
      "id": "cceef3f1-7a47-47fc-accb-663e7c5e7caf",
      "name": "ООО Виктория",
      "createdAt": "2026-05-08T15:02:39.797Z"
    },
    {
      "id": "5b092ae7-094a-4b0d-b38b-8cb7843aa1f4",
      "name": "ООО Перекресток",
      "createdAt": "2026-05-08T15:02:39.794Z"
    },
    {
      "id": "84e3670d-ac58-4824-8656-fb5c5ce9cad2",
      "name": "ООО Ашан",
      "createdAt": "2026-05-08T15:02:39.791Z"
    },
    {
      "id": "904682fa-385b-4b05-8574-fad654bd95c9",
      "name": "АО Тандер",
      "createdAt": "2026-05-08T15:02:39.788Z"
    },
    {
      "id": "f5f0b374-f5e3-4852-8501-bd5eac95a199",
      "name": "ООО Лента",
      "createdAt": "2026-05-08T15:02:39.785Z"
    },
    {
      "id": "41a2bce9-1a6e-42a8-aa60-98153ddfca27",
      "name": "ПАО X5 Retail Group",
      "createdAt": "2026-05-08T15:02:39.782Z"
    },
    {
      "id": "5d9014fd-4439-4332-95e2-a2e41faaa735",
      "name": "ООО Магнит-Ритейл",
      "createdAt": "2026-05-08T15:02:39.778Z"
    }
  ],
  "total": 10
}
```

### Departments

**Endpoint:** `GET /personnel/departments`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "departments": [
    {
      "id": "f3a6501e-30aa-4b8c-bcce-b37ad3ed8100",
      "name": "IT-отдел",
      "code": "DEP-UPR-ITD",
      "type": "department",
      "parentId": "bcae1e9f-9af3-43cb-a741-4de48774f8a9",
      "headEmployeeId": "0eec37e8-728d-4a80-8c36-cf4873dd1cab",
      "sourceSystemId": null
    },
    {
      "id": "4a307927-2ff6-4909-b58c-fc15221ecb72",
      "name": "Автопарк",
      "code": "SEC-TRN-AVT",
      "type": "section",
      "parentId": "21e4e62b-5be0-4146-8685-fdb162f04ee5",
      "headEmployeeId": "1c1df3a8-35d6-4823-949d-ab647588c828",
      "sourceSystemId": null
    },
    {
      "id": "e7f04ade-6662-4117-b4fc-0b3bf3a69a6c",
      "name": "Департамент кадров и HR",
      "code": "DEP-UPR-KDR",
      "type": "department",
      "parentId": "bcae1e9f-9af3-43cb-a741-4de48774f8a9",
      "headEmployeeId": "316e3f78-0ef5-4a02-ba6d-e3a3e7575b41",
      "sourceSystemId": null
    },
    {
      "id": "c4d6a0c5-25d6-485a-9e4b-c4d170cc2da1",
      "name": "Дивизион инфраструктуры и логистики",
      "code": "DIV-LOG",
      "type": "division",
      "parentId": null,
      "headEmployeeId": "6d19da70-cce4-4b69-863f-bdd383e602cf",
      "sourceSystemId": null
    },
    {
      "id": "d65c0e3a-10a8-4df0-be88-a9642487f322",
      "name": "Дивизион майонезов и соусов",
      "code": "DIV-MYN",
      "type": "division",
      "parentId": null,
      "headEmployeeId": "632bcef8-33c3-476f-9987-c007d25c69b8",
      "sourceSystemId": null
    },
    {
      "id": "177da171-c206-4d9c-857e-30aee26f61f3",
      "name": "Дивизион спецжиров и маргаринов",
      "code": "DIV-SZH",
      "type": "division",
      "parentId": null,
      "headEmployeeId": "2ed5946c-79eb-4218-8ba8-a67b04cc96fc",
      "sourceSystemId": null
    },
    {
      "id": "bcae1e9f-9af3-43cb-a741-4de48774f8a9",
      "name": "Дивизион управления и поддержки",
      "code": "DIV-UPR",
      "type": "division",
      "parentId": null,
      "headEmployeeId": "588e29d7-b51c-43e9-b3cb-b193dc5b64c2",
      "sourceSystemId": null
    },
    {
      "id": "eecdbe29-e3bd-43b2-945e-1096f78274e2",
      "name": "Лаборатория масложирового контроля",
      "code": "DEP-MZH-LAB",
      "type": "department",
      "parentId": "a56ed230-691b-4407-b9f0-ebc86677a11f",
      "headEmployeeId": "1fce6f6f-0048-452b-97b5-9383f8f5fe25",
      "sourceSystemId": null
    },
    {
      "id": "8e667794-464a-4893-a30d-98a8a2ed484f",
      "name": "Лаборатория спецжиров",
      "code": "DEP-SZH-LAB",
      "type": "department",
      "parentId": "177da171-c206-4d9c-857e-30aee26f61f3",
      "headEmployeeId": "3e32e992-e9be-4828-acd3-5fb1e5c54963",
      "sourceSystemId": null
    },
    {
      "id": "aff99b7e-1357-484d-ae6f-b197999d0240",
      "name": "Лаборатория эмульсионных продуктов",
      "code": "DEP-MYN-LAB",
      "type": "department",
      "parentId": "d65c0e3a-10a8-4df0-be88-a9642487f322",
      "headEmployeeId": "107e962c-50b3-401c-b374-15fdd1247fec",
      "sourceSystemId": null
    }
  ],
  "total": 49
}
```

### Downtime Events

**Endpoint:** `GET /production/downtime-events`

**Parameters:** `{"from": "2026-04-14", "to": "2026-05-14", "limit": 10}`

**Status:** 200

**Response:**

```json
{
  "items": [
    {
      "id": "a63ce886-6a54-4da9-bcf9-786358322389",
      "productionLineId": "1aebc8ae-4374-f95a-8ec9-b80f1375d3c6",
      "reason": "Нехватка упаковочного материала",
      "category": "MATERIAL_SHORTAGE",
      "startedAt": "2026-05-04T23:02:42.284Z",
      "endedAt": "2026-05-05T02:19:42.284Z",
      "durationMinutes": 197,
      "createdAt": "2026-05-12T05:28:09.790Z"
    },
    {
      "id": "6df28699-182e-428e-bf0a-4efb9703b672",
      "productionLineId": "1aebc8ae-4374-f95a-8ec9-b80f1375d3c6",
      "reason": "Технологический перерыв (санитарная обработка)",
      "category": "OTHER",
      "startedAt": "2026-05-04T14:59:43.524Z",
      "endedAt": "2026-05-04T16:48:43.524Z",
      "durationMinutes": 109,
      "createdAt": "2026-05-12T05:28:09.790Z"
    },
    {
      "id": "41079f1c-809f-4efc-8ddc-a9636e8f9085",
      "productionLineId": "a0a65c5f-bb95-e4a8-e1be-3b6dff660b2d",
      "reason": "Неисправность электродвигателя",
      "category": "UNPLANNED_BREAKDOWN",
      "startedAt": "2026-05-03T23:12:41.196Z",
      "endedAt": "2026-05-04T00:54:41.196Z",
      "durationMinutes": 102,
      "createdAt": "2026-05-12T05:28:09.820Z"
    },
    {
      "id": "798f495e-f883-4ffa-856c-297d289d93d0",
      "productionLineId": "596c3638-89d3-1d32-8529-8207984638e7",
      "reason": "Плановая чистка реактора",
      "category": "PLANNED_MAINTENANCE",
      "startedAt": "2026-05-03T18:18:02.859Z",
      "endedAt": "2026-05-03T20:42:02.859Z",
      "durationMinutes": 144,
      "createdAt": "2026-05-12T05:28:09.790Z"
    },
    {
      "id": "c39b0647-5d58-40d9-8f57-2520abd4312b",
      "productionLineId": "596c3638-89d3-1d32-8529-8207984638e7",
      "reason": "Повышенная кислотность сырья",
      "category": "QUALITY_ISSUE",
      "startedAt": "2026-05-03T06:20:46.304Z",
      "endedAt": "2026-05-03T07:52:46.304Z",
      "durationMinutes": 92,
      "createdAt": "2026-05-12T05:28:09.790Z"
    },
    {
      "id": "8a4d1d0f-d466-4a7d-8149-bf26ab2440c4",
      "productionLineId": "3d57ea5f-fcd5-3a77-24cb-7996f830f190",
      "reason": "Плановое ТО оборудования",
      "category": "PLANNED_MAINTENANCE",
      "startedAt": "2026-05-02T15:25:06.618Z",
      "endedAt": "2026-05-02T17:48:06.618Z",
      "durationMinutes": 143,
      "createdAt": "2026-05-12T05:28:09.820Z"
    },
    {
      "id": "756c0835-6daf-4d18-8711-485186f56171",
      "productionLineId": "3d57ea5f-fcd5-3a77-24cb-7996f830f190",
      "reason": "Неисправность электродвигателя",
      "category": "UNPLANNED_BREAKDOWN",
      "startedAt": "2026-05-02T10:47:59.106Z",
      "endedAt": "2026-05-02T11:43:59.106Z",
      "durationMinutes": 56,
      "createdAt": "2026-05-12T05:28:09.820Z"
    },
    {
      "id": "1e0d9962-18f3-4a11-8371-0a1027c0a4d3",
      "productionLineId": "a25e7bc7-221e-1376-0bc0-f30299a83ff1",
      "reason": "Переналадка линии под другой продукт",
      "category": "OTHER",
      "startedAt": "2026-05-02T05:31:13.170Z",
      "endedAt": "2026-05-02T07:38:13.170Z",
      "durationMinutes": 127,
      "createdAt": "2026-05-12T05:28:09.805Z"
    },
    {
      "id": "45ab6b29-5f28-4dc5-a1ce-40b0fbf64c99",
      "productionLineId": "a25e7bc7-221e-1376-0bc0-f30299a83ff1",
      "reason": "Технологический перерыв (санитарная обработка)",
      "category": "OTHER",
      "startedAt": "2026-04-30T16:23:07.031Z",
      "endedAt": "2026-04-30T17:40:07.031Z",
      "durationMinutes": 77,
      "createdAt": "2026-05-12T05:28:09.805Z"
    },
    {
      "id": "c7fcac8c-c747-4328-bb93-90f4529d7cf4",
      "productionLineId": "49a5ba6f-3838-3d85-6310-cf1ec432864d",
      "reason": "Технологический перерыв (санитарная обработка)",
      "category": "OTHER",
      "startedAt": "2026-04-30T11:23:18.242Z",
      "endedAt": "2026-04-30T11:39:18.242Z",
      "durationMinutes": 16,
      "createdAt": "2026-05-12T05:28:09.805Z"
    }
  ],
  "total": 54
}
```

### Employees

**Endpoint:** `GET /personnel/employees`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "employees": [
    {
      "id": "db47cb8b-c89d-426f-a97d-42db434135a3",
      "personnelNumber": "EMP-00335",
      "fullName": "Абрамов Александр Евгеньевич",
      "dateOfBirth": "1977-06-30T00:00:00.000Z",
      "positionId": "6fe174ea-b6f5-4c03-a1cb-d1a911732c6f",
      "departmentId": "6511d6e6-637a-4f51-8375-4ac53248f58a",
      "workstationId": null,
      "hireDate": "2016-04-06T00:00:00.000Z",
      "terminationDate": null,
      "employmentType": "main",
      "status": "active",
      "sourceSystemId": null
    },
    {
      "id": "4f51695f-88cd-48a6-914a-097177eeba96",
      "personnelNumber": "EMP-00751",
      "fullName": "Абрамов Артем Григорьевич",
      "dateOfBirth": "1998-10-01T00:00:00.000Z",
      "positionId": "c576e9c5-b998-497d-8b87-fd552d2d2c03",
      "departmentId": "9c85507d-c328-4252-876a-1431bfd74ee2",
      "workstationId": null,
      "hireDate": "2022-06-23T00:00:00.000Z",
      "terminationDate": null,
      "employmentType": "main",
      "status": "active",
      "sourceSystemId": null
    },
    {
      "id": "01364b24-158e-4e66-994e-811d8b396758",
      "personnelNumber": "EMP-01655",
      "fullName": "Абрамов Василий Федорович",
      "dateOfBirth": "1984-10-04T00:00:00.000Z",
      "positionId": "c0e47ee8-b31c-4107-abcd-2683918079db",
      "departmentId": "d65c0e3a-10a8-4df0-be88-a9642487f322",
      "workstationId": "704c3e6a-5847-4053-a332-cd746ab6dc39",
      "hireDate": "2024-03-31T00:00:00.000Z",
      "terminationDate": null,
      "employmentType": "main",
      "status": "active",
      "sourceSystemId": null
    },
    {
      "id": "a40519bd-5c4c-4634-8580-a6e9809621f7",
      "personnelNumber": "EMP-01263",
      "fullName": "Абрамов Геннадий Евгеньевич",
      "dateOfBirth": "1998-07-12T00:00:00.000Z",
      "positionId": "f364b781-8b50-4462-9d65-8f74628f7946",
      "departmentId": "099178e1-f3b3-4c80-9d83-64c790c968ca",
      "workstationId": "80a06199-ae90-4bcd-aad1-6bb9875fe054",
      "hireDate": "2025-09-04T00:00:00.000Z",
      "terminationDate": null,
      "employmentType": "main",
      "status": "active",
      "sourceSystemId": null
    },
    {
      "id": "d04387ae-519c-4813-b5af-ecad9d3bc167",
      "personnelNumber": "EMP-00040",
      "fullName": "Абрамов Григорий Игоревич",
      "dateOfBirth": "1993-11-19T00:00:00.000Z",
      "positionId": "9fa3672f-c88d-45e5-ad2a-1cdcf2665b7b",
      "departmentId": "f3a6501e-30aa-4b8c-bcce-b37ad3ed8100",
      "workstationId": null,
      "hireDate": "2020-09-30T00:00:00.000Z",
      "terminationDate": null,
      "employmentType": "main",
      "status": "active",
      "sourceSystemId": null
    },
    {
      "id": "f465eac3-7e35-4158-9f91-5f3b06a728b7",
      "personnelNumber": "EMP-00837",
      "fullName": "Абрамов Иван Иванович",
      "dateOfBirth": "1964-03-15T00:00:00.000Z",
      "positionId": "47881d42-52b6-4d54-b857-dbf7206b76d8",
      "departmentId": "9c85507d-c328-4252-876a-1431bfd74ee2",
      "workstationId": "704c3e6a-5847-4053-a332-cd746ab6dc39",
      "hireDate": "2024-01-11T00:00:00.000Z",
      "terminationDate": null,
      "employmentType": "main",
      "status": "active",
      "sourceSystemId": null
    },
    {
      "id": "27ce954e-a591-4441-bd99-765747838556",
      "personnelNumber": "EMP-00787",
      "fullName": "Абрамов Максим Константинович",
      "dateOfBirth": "1986-06-20T00:00:00.000Z",
      "positionId": "a78756c8-dc4a-4faa-9f5c-45ba7daa442c",
      "departmentId": "1d17a093-6a45-4754-9b1d-f18682686e0d",
      "workstationId": "339de44c-3245-41a0-adc7-80d2d68ea8d0",
      "hireDate": "2018-02-08T00:00:00.000Z",
      "terminationDate": null,
      "employmentType": "main",
      "status": "active",
      "sourceSystemId": null
    },
    {
      "id": "caeeb247-96eb-4fb5-af69-4ced13a57c69",
      "personnelNumber": "EMP-00190",
      "fullName": "Абрамов Михаил Романович",
      "dateOfBirth": "1996-06-20T00:00:00.000Z",
      "positionId": "76cbadb4-4e84-4233-9c7e-b2660711ae2f",
      "departmentId": "099178e1-f3b3-4c80-9d83-64c790c968ca",
      "workstationId": "aa843495-e952-4025-80c4-d6ecdc2edddc",
      "hireDate": "2026-03-20T00:00:00.000Z",
      "terminationDate": null,
      "employmentType": "main",
      "status": "active",
      "sourceSystemId": null
    },
    {
      "id": "5c372257-3e83-41b4-9082-905a5e5c4ada",
      "personnelNumber": "EMP-00478",
      "fullName": "Абрамов Никита Борисович",
      "dateOfBirth": "1973-12-29T00:00:00.000Z",
      "positionId": "5527670a-ee84-497f-9bef-39623304a09f",
      "departmentId": "6511d6e6-637a-4f51-8375-4ac53248f58a",
      "workstationId": "d8322012-94ed-4b2b-86e1-14980a584084",
      "hireDate": "2022-10-19T00:00:00.000Z",
      "terminationDate": "2025-12-23T00:00:00.000Z",
      "employmentType": "main",
      "status": "terminated",
      "sourceSystemId": null
    },
    {
      "id": "cb6dd24b-4bf8-4ff1-a04e-2a1ea3b1a70f",
      "personnelNumber": "EMP-01179",
      "fullName": "Абрамов Никита Федорович",
      "dateOfBirth": "1991-06-29T00:00:00.000Z",
      "positionId": "f865d074-820f-455f-9ff4-d9f56f7ac6ed",
      "departmentId": "073c9c9b-2679-4219-b0b7-1241bac6b3dd",
      "workstationId": "aa843495-e952-4025-80c4-d6ecdc2edddc",
      "hireDate": "2016-10-18T00:00:00.000Z",
      "terminationDate": null,
      "employmentType": "part_time",
      "status": "active",
      "sourceSystemId": null
    }
  ],
  "total": 2000
}
```

### Inventory

**Endpoint:** `GET /production/inventory`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "inventory": [
    {
      "id": "ad7582c5-f888-4cf6-b09e-ef904a070f7b",
      "productId": "39ba0136-fa55-4218-aa12-5966fcedaa27",
      "warehouseId": "0d2acc44-bc74-4d84-9285-18fb9662810e",
      "lotNumber": "LOT-20260423-016",
      "quantity": 32842.047,
      "lastUpdated": "2026-04-23T01:33:54.522Z"
    },
    {
      "id": "87951b52-c2f9-4054-abc7-99047f6fe84c",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "warehouseId": "0d2acc44-bc74-4d84-9285-18fb9662810e",
      "lotNumber": "LOT-20260304-005",
      "quantity": 7331.38,
      "lastUpdated": "2026-03-04T17:07:21.723Z"
    },
    {
      "id": "4e867295-0c90-4b3a-96f5-01902940c7a1",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "warehouseId": "0d2acc44-bc74-4d84-9285-18fb9662810e",
      "lotNumber": "LOT-20260430-009",
      "quantity": 24255.231,
      "lastUpdated": "2026-04-30T17:36:16.942Z"
    },
    {
      "id": "6ea38ea7-7aa9-446a-9dac-406044767fd7",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "warehouseId": "0d2acc44-bc74-4d84-9285-18fb9662810e",
      "lotNumber": "LOT-20260429-014",
      "quantity": 37451.923,
      "lastUpdated": "2026-04-29T02:21:11.424Z"
    },
    {
      "id": "037d72a3-133c-4e1e-9f02-4c7639b0e394",
      "productId": "b0bcc1ed-c4c7-4c25-9d30-c6766ba51dca",
      "warehouseId": "0d2acc44-bc74-4d84-9285-18fb9662810e",
      "lotNumber": "LOT-20260415-037",
      "quantity": 47784.48,
      "lastUpdated": "2026-04-15T21:04:01.958Z"
    },
    {
      "id": "e7043788-5f84-41c9-8de7-5b73d7bd5303",
      "productId": "74bce996-1536-4968-be02-667b4dd71a5e",
      "warehouseId": "20abf47f-3703-4ca2-ac58-6a6f4632a595",
      "lotNumber": "LOT-20260420-028",
      "quantity": 40548.225,
      "lastUpdated": "2026-04-20T13:38:42.250Z"
    },
    {
      "id": "3923ed76-0020-44b2-8b95-4a4a0e78ed42",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "warehouseId": "20abf47f-3703-4ca2-ac58-6a6f4632a595",
      "lotNumber": "LOT-20260305-008",
      "quantity": 26480.141,
      "lastUpdated": "2026-03-05T12:56:38.778Z"
    },
    {
      "id": "f3a51be0-40d1-422f-8d37-e256e0d36ed6",
      "productId": "dc3f8ec0-47be-48b4-b4ea-724759d99848",
      "warehouseId": "20abf47f-3703-4ca2-ac58-6a6f4632a595",
      "lotNumber": "LOT-20260321-033",
      "quantity": 42182.876,
      "lastUpdated": "2026-03-21T23:11:23.227Z"
    },
    {
      "id": "9175cf70-9728-4283-afc1-99e6d06d1836",
      "productId": "ee23eb53-c31e-4b45-a60e-c2c5856a5e38",
      "warehouseId": "20abf47f-3703-4ca2-ac58-6a6f4632a595",
      "lotNumber": "LOT-20260417-031",
      "quantity": 31600.173,
      "lastUpdated": "2026-04-17T10:16:28.218Z"
    },
    {
      "id": "6e788717-2c0c-4b59-9766-ebb0a2b0e854",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "warehouseId": "2624b3d0-d5f4-4c63-a520-0b65cf7a6803",
      "lotNumber": "LOT-20260501-007",
      "quantity": 7819.108,
      "lastUpdated": "2026-05-01T13:52:18.132Z"
    }
  ],
  "total": 38
}
```

### KPI

**Endpoint:** `GET /production/kpi`

**Parameters:** `{"from": "2026-04-14", "to": "2026-05-14"}`

**Status:** 200

**Response:**

```json
{
  "totalOutput": 2195253.258,
  "defectRate": 0.1065418275306803,
  "completedOrders": 109,
  "totalOrders": 145,
  "availability": 1.0614973262032086,
  "performance": 1.7586520882339955,
  "oeeEstimate": 1.6679117274408306,
  "lineThroughput": 73175.10859999999,
  "targets": {
    "oeeEstimate": {
      "target": 0.85,
      "min": 0.75,
      "max": 1,
      "status": "ok",
      "deviation": 0.8179117274408306
    },
    "defectRate": {
      "target": 0.015,
      "min": 0.005,
      "max": 0.03,
      "status": "critical",
      "deviation": 0.0915418275306803
    },
    "lineThroughput": {
      "target": 150,
      "min": 100,
      "max": 250,
      "status": "ok",
      "deviation": 73025.10859999999
    }
  }
}
```

### KPI Breakdown

**Endpoint:** `GET /production/kpi/breakdown`

**Parameters:** `{"from": "2026-04-14", "to": "2026-05-14", "groupBy": "productionLine", "metric": "totalOutput"}`

**Status:** 400

**Response:**

```json
{
  "statusCode": 400,
  "message": [
    "поле «metric» должно быть одной из допустимых метрик"
  ],
  "error": "Bad Request",
  "requestId": "a9744b5c-fc61-4fd6-adaf-44cf67cd97c2",
  "path": "/api/production/kpi/breakdown?from=2026-04-14&to=2026-05-14&groupBy=productionLine&metric=totalOutput",
  "timestamp": "2026-05-14T16:51:38.137Z"
}
```

### Locations

**Endpoint:** `GET /personnel/locations`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "locations": [
    {
      "id": "7a348077-d55b-4d5b-b1e3-9df6c2363b58",
      "name": "Жировой комбинат (ЕЖК) - Майонезы",
      "code": "EKB_PLANT",
      "type": "factory",
      "streetAddress": "ул. Титова, 27",
      "postalAreaId": "2ec3efe9-ae99-46f1-975d-c905f61b049a",
      "sourceSystemId": null
    },
    {
      "id": "efd540d2-8f00-4c7f-8b7a-3cd0fb1b48ed",
      "name": "Зерновая компания ЭФКО",
      "code": "ZRN_OFFICE",
      "type": "office",
      "streetAddress": "ул. Героев Красной Армии, 7",
      "postalAreaId": "0c208347-ac72-448f-abfb-a0ac7ff64296",
      "sourceSystemId": null
    },
    {
      "id": "41ad9f8b-fcfe-4c50-9a18-49fa6e8db0de",
      "name": "Инновационный центр Бирюч",
      "code": "BLG_OFFICE",
      "type": "office",
      "streetAddress": "ул. Академика Ливанова, д. 1",
      "postalAreaId": "bc894d5d-a84f-4580-b288-611df029e3d9",
      "sourceSystemId": null
    },
    {
      "id": "76c4fc37-72b2-4b43-9360-a8ffd7267d06",
      "name": "Московский майонезный завод",
      "code": "NOG_PLANT",
      "type": "factory",
      "streetAddress": "ул. Бетонная, д. 1, офис 2",
      "postalAreaId": "aa01ce94-8946-4101-b811-a7bc807af3e6",
      "sourceSystemId": null
    },
    {
      "id": "046414d0-7f59-4283-a329-bb5f5ab159a5",
      "name": "Офис Алматы (ТОО ЭФКО АЛМАТЫ)",
      "code": "ALM_OFFICE",
      "type": "office",
      "streetAddress": "ул. Бекмаханова, 96/5",
      "postalAreaId": "32c65524-ea05-431e-9aa7-84fe1f297529",
      "sourceSystemId": null
    },
    {
      "id": "0e012cc5-2310-458f-b236-97205dde6de3",
      "name": "Офис Воронеж (основной)",
      "code": "VRN_OFFICE",
      "type": "office",
      "streetAddress": "ул. Таранченко, 40",
      "postalAreaId": "3dafd745-aea6-4da0-95ac-03549e75432c",
      "sourceSystemId": null
    },
    {
      "id": "e017eeeb-6a81-45a0-89e9-accb7b2dcfc7",
      "name": "Офис Каменка",
      "code": "KMK_OFFICE",
      "type": "office",
      "streetAddress": "ул. Мира, д. 30",
      "postalAreaId": "c55c3b35-ca32-476c-94fe-60c13e7952ed",
      "sourceSystemId": null
    },
    {
      "id": "48eb4305-5190-4446-b4e3-e15b44221b1e",
      "name": "Офис Москва (ЦА)",
      "code": "MSK_OFFICE",
      "type": "office",
      "streetAddress": "Овчинниковская набережная, 20, стр. 1",
      "postalAreaId": "33d390e2-1949-432d-ad74-8edff84e3b1a",
      "sourceSystemId": null
    },
    {
      "id": "cfe181c9-a260-421a-bfc5-f05d6b61ac31",
      "name": "Офис Тамань",
      "code": "TAM_OFFICE",
      "type": "office",
      "streetAddress": "Темрюкский район, морской порт",
      "postalAreaId": "720ee8c6-d7fb-4e32-8e94-56f66a8568b0",
      "sourceSystemId": null
    },
    {
      "id": "3c79f1a0-0740-4a7b-a64d-2ddd9a0eb2a2",
      "name": "ТОО ЭФКО АЛМАТЫ - Завод",
      "code": "ALM_PLANT",
      "type": "factory",
      "streetAddress": "ул. Бекмаханова, 96",
      "postalAreaId": "32c65524-ea05-431e-9aa7-84fe1f297529",
      "sourceSystemId": null
    }
  ],
  "total": 13
}
```

### OTIF

**Endpoint:** `GET /production/kpi/otif`

**Parameters:** `{"from": "2026-04-14", "to": "2026-05-14"}`

**Status:** 200

**Response:**

```json
{
  "otifRate": 0.12844036697247707,
  "onTimeOrders": 55,
  "inFullQuantityOrders": 26,
  "otifOrders": 14,
  "totalOrders": 109
}
```

### Orders

**Endpoint:** `GET /production/orders`

**Parameters:** `{"from": "2026-04-14", "to": "2026-05-14", "limit": 10}`

**Status:** 200

**Response:**

```json
{
  "orders": [
    {
      "id": "6dddc9fc-8231-4c3f-a172-bdcf8bcb5fea",
      "externalOrderId": "ORD-004899",
      "productId": "ee23eb53-c31e-4b45-a60e-c2c5856a5e38",
      "targetQuantity": 5406.819,
      "actualQuantity": 5163.325,
      "status": "COMPLETED",
      "productionLineId": "9330f683-f62b-5e4a-7877-6d2f13d19384",
      "plannedStart": "2026-05-04T21:13:20.033Z",
      "plannedEnd": "2026-05-09T21:13:20.033Z",
      "actualStart": "2026-05-05T21:13:20.033Z",
      "actualEnd": "2026-05-11T21:13:20.033Z"
    },
    {
      "id": "5ea49bc4-b529-41c9-881a-55e4a56ab928",
      "externalOrderId": "ORD-004930",
      "productId": "bfd01152-1bc4-4f8b-b7dd-30213f50ac3f",
      "targetQuantity": 44755.652,
      "actualQuantity": null,
      "status": "IN_PROGRESS",
      "productionLineId": "4d1b5527-2315-0129-4000-409c8f901120",
      "plannedStart": "2026-05-04T19:02:27.761Z",
      "plannedEnd": "2026-05-05T19:02:27.761Z",
      "actualStart": "2026-05-05T19:02:27.761Z",
      "actualEnd": null
    },
    {
      "id": "5e62434e-4547-4b20-a6b1-d822262ea537",
      "externalOrderId": "ORD-004813",
      "productId": "ee23eb53-c31e-4b45-a60e-c2c5856a5e38",
      "targetQuantity": 46756.015,
      "actualQuantity": null,
      "status": "IN_PROGRESS",
      "productionLineId": "9330f683-f62b-5e4a-7877-6d2f13d19384",
      "plannedStart": "2026-05-04T18:40:10.171Z",
      "plannedEnd": "2026-05-09T18:40:10.171Z",
      "actualStart": "2026-05-04T18:40:10.171Z",
      "actualEnd": null
    },
    {
      "id": "39dc90d6-567b-4b1d-9dce-f429991b2b5f",
      "externalOrderId": "ORD-004820",
      "productId": "ee23eb53-c31e-4b45-a60e-c2c5856a5e38",
      "targetQuantity": 8182.422,
      "actualQuantity": 7988.567,
      "status": "COMPLETED",
      "productionLineId": "4d1b5527-2315-0129-4000-409c8f901120",
      "plannedStart": "2026-05-04T18:30:57.746Z",
      "plannedEnd": "2026-05-05T18:30:57.746Z",
      "actualStart": "2026-05-03T18:30:57.746Z",
      "actualEnd": "2026-05-06T18:30:57.746Z"
    },
    {
      "id": "90293036-bc07-499d-b903-d24a42b13ea8",
      "externalOrderId": "ORD-004955",
      "productId": "39ba0136-fa55-4218-aa12-5966fcedaa27",
      "targetQuantity": 23898.719,
      "actualQuantity": 24303.497,
      "status": "COMPLETED",
      "productionLineId": "49a5ba6f-3838-3d85-6310-cf1ec432864d",
      "plannedStart": "2026-05-04T18:24:26.997Z",
      "plannedEnd": "2026-05-05T18:24:26.997Z",
      "actualStart": "2026-05-05T18:24:26.997Z",
      "actualEnd": "2026-05-05T18:24:26.997Z"
    },
    {
      "id": "2931174a-89d5-4ec1-9aaa-d56cb33df308",
      "externalOrderId": "ORD-004949",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "targetQuantity": 24892.939,
      "actualQuantity": 24475.098,
      "status": "COMPLETED",
      "productionLineId": "596c3638-89d3-1d32-8529-8207984638e7",
      "plannedStart": "2026-05-04T17:22:42.816Z",
      "plannedEnd": "2026-05-08T17:22:42.816Z",
      "actualStart": "2026-05-04T17:22:42.816Z",
      "actualEnd": "2026-05-10T17:22:42.816Z"
    },
    {
      "id": "e76fb497-6e37-4c27-9683-c934dafc42ed",
      "externalOrderId": "ORD-004818",
      "productId": "39ba0136-fa55-4218-aa12-5966fcedaa27",
      "targetQuantity": 26326.71,
      "actualQuantity": null,
      "status": "IN_PROGRESS",
      "productionLineId": "a25e7bc7-221e-1376-0bc0-f30299a83ff1",
      "plannedStart": "2026-05-04T16:54:08.394Z",
      "plannedEnd": "2026-05-05T16:54:08.394Z",
      "actualStart": "2026-05-05T16:54:08.394Z",
      "actualEnd": null
    },
    {
      "id": "23eef5e4-5bd3-4586-89f3-74e55ae969a0",
      "externalOrderId": "ORD-004940",
      "productId": "74bce996-1536-4968-be02-667b4dd71a5e",
      "targetQuantity": 18161.707,
      "actualQuantity": 17031.895,
      "status": "COMPLETED",
      "productionLineId": "596c3638-89d3-1d32-8529-8207984638e7",
      "plannedStart": "2026-05-04T15:17:43.799Z",
      "plannedEnd": "2026-05-05T15:17:43.799Z",
      "actualStart": "2026-05-03T15:17:43.799Z",
      "actualEnd": "2026-05-04T15:17:43.799Z"
    },
    {
      "id": "f4e62425-fdcd-4ecf-941b-ccf5b6cb3789",
      "externalOrderId": "ORD-004848",
      "productId": "ee23eb53-c31e-4b45-a60e-c2c5856a5e38",
      "targetQuantity": 24103.863,
      "actualQuantity": null,
      "status": "CANCELLED",
      "productionLineId": "9330f683-f62b-5e4a-7877-6d2f13d19384",
      "plannedStart": "2026-05-04T13:22:45.762Z",
      "plannedEnd": "2026-05-06T13:22:45.762Z",
      "actualStart": null,
      "actualEnd": null
    },
    {
      "id": "5457e22f-6807-49d3-96fc-cac4e6a1e6f3",
      "externalOrderId": "ORD-004964",
      "productId": "23a4979c-cec8-4e0a-8f1a-bda18baaf7af",
      "targetQuantity": 26888.821,
      "actualQuantity": 26970.383,
      "status": "COMPLETED",
      "productionLineId": "3d57ea5f-fcd5-3a77-24cb-7996f830f190",
      "plannedStart": "2026-05-04T13:08:54.059Z",
      "plannedEnd": "2026-05-07T13:08:54.059Z",
      "actualStart": "2026-05-04T13:08:54.059Z",
      "actualEnd": "2026-05-09T13:08:54.059Z"
    }
  ],
  "total": 145
}
```

### Output

**Endpoint:** `GET /production/output`

**Parameters:** `{"from": "2026-04-14", "to": "2026-05-14", "limit": 10}`

**Status:** 200

**Response:**

```json
{
  "outputs": [
    {
      "id": "98bfcdd2-65ab-4ccf-9f3d-bbf725c7f446",
      "orderId": "5ea49bc4-b529-41c9-881a-55e4a56ab928",
      "productId": "bfd01152-1bc4-4f8b-b7dd-30213f50ac3f",
      "lotNumber": "LOT-20260508-027",
      "quantity": 3786.246,
      "qualityStatus": "APPROVED",
      "productionDate": "2026-05-08T19:02:27.761Z",
      "shift": "Утренняя"
    },
    {
      "id": "2eb540ff-6fff-44e3-8080-02ffb8fe1099",
      "orderId": "e76fb497-6e37-4c27-9683-c934dafc42ed",
      "productId": "39ba0136-fa55-4218-aa12-5966fcedaa27",
      "lotNumber": "LOT-20260508-670",
      "quantity": 4909.668,
      "qualityStatus": "APPROVED",
      "productionDate": "2026-05-08T16:54:08.394Z",
      "shift": "Вечерняя"
    },
    {
      "id": "029aa3d0-e19e-4491-a787-d43b652fe407",
      "orderId": "504535dd-86d5-4a4a-8f10-6ff74f122481",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "lotNumber": "LOT-20260507-742",
      "quantity": 3420.142,
      "qualityStatus": "APPROVED",
      "productionDate": "2026-05-07T22:34:31.235Z",
      "shift": "Вечерняя"
    },
    {
      "id": "fd7a628b-be7f-441d-aa5a-c643e4b1cae1",
      "orderId": "504535dd-86d5-4a4a-8f10-6ff74f122481",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "lotNumber": "LOT-20260507-744",
      "quantity": 5574.437,
      "qualityStatus": "APPROVED",
      "productionDate": "2026-05-07T22:34:31.235Z",
      "shift": "Вечерняя"
    },
    {
      "id": "1f3ff859-967b-4710-89da-d252ddad1028",
      "orderId": "504535dd-86d5-4a4a-8f10-6ff74f122481",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "lotNumber": "LOT-20260507-745",
      "quantity": 2928.671,
      "qualityStatus": "PENDING",
      "productionDate": "2026-05-07T22:34:31.235Z",
      "shift": "Вечерняя"
    },
    {
      "id": "f946f5a9-1759-4524-baa8-98d7d275ec34",
      "orderId": "50e20e5b-5126-410f-b018-9cd120875f79",
      "productId": "23a4979c-cec8-4e0a-8f1a-bda18baaf7af",
      "lotNumber": "LOT-20260507-697",
      "quantity": 6649.832,
      "qualityStatus": "APPROVED",
      "productionDate": "2026-05-07T21:36:30.135Z",
      "shift": "Вечерняя"
    },
    {
      "id": "0c8e5c40-9694-44ba-af21-9359f1bcd033",
      "orderId": "50e20e5b-5126-410f-b018-9cd120875f79",
      "productId": "23a4979c-cec8-4e0a-8f1a-bda18baaf7af",
      "lotNumber": "LOT-20260507-701",
      "quantity": 7881.479,
      "qualityStatus": "APPROVED",
      "productionDate": "2026-05-07T21:36:30.135Z",
      "shift": "Утренняя"
    },
    {
      "id": "119208de-bae1-41a8-987c-c791936824b4",
      "orderId": "6dddc9fc-8231-4c3f-a172-bdcf8bcb5fea",
      "productId": "ee23eb53-c31e-4b45-a60e-c2c5856a5e38",
      "lotNumber": "LOT-20260507-916",
      "quantity": 3588.668,
      "qualityStatus": "APPROVED",
      "productionDate": "2026-05-07T21:13:20.033Z",
      "shift": "Вечерняя"
    },
    {
      "id": "354a7ae3-cfaf-4492-8d03-0059419d4746",
      "orderId": "97424ee1-f1cb-49fd-92af-5ac30132340f",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "lotNumber": "LOT-20260507-893",
      "quantity": 7859.073,
      "qualityStatus": "REJECTED",
      "productionDate": "2026-05-07T21:04:31.850Z",
      "shift": "Утренняя"
    },
    {
      "id": "ddab848f-c748-40b6-ad9e-06a6e8445346",
      "orderId": "97424ee1-f1cb-49fd-92af-5ac30132340f",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "lotNumber": "LOT-20260507-894",
      "quantity": 6661.705,
      "qualityStatus": "PENDING",
      "productionDate": "2026-05-07T21:04:31.850Z",
      "shift": "Вечерняя"
    }
  ],
  "total": 505
}
```

### Positions

**Endpoint:** `GET /personnel/positions`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "positions": [
    {
      "id": "6d325fd1-df2b-49f9-a804-e8ddb9c7af75",
      "title": "HR-менеджер",
      "code": "POS-0250"
    },
    {
      "id": "ae212919-08b4-40a4-9075-dca5087f2734",
      "title": "IT-аналитик",
      "code": "POS-0301"
    },
    {
      "id": "54df26e6-b1dc-4df1-a486-4809f09c5b11",
      "title": "IT-специалист",
      "code": "POS-0299"
    },
    {
      "id": "d4b35aa3-af28-4b74-a629-32d60db5b783",
      "title": "Администратор кадрового отдела",
      "code": "POS-0256"
    },
    {
      "id": "dfe361c7-4d41-4ca3-b221-ffc30948b82c",
      "title": "Аналитик",
      "code": "POS-0076"
    },
    {
      "id": "98bc2ca5-d5ff-4314-b4e4-eea117a495e1",
      "title": "Аналитик",
      "code": "POS-0051"
    },
    {
      "id": "f210d23a-af38-4942-b74c-74b4d6514b6b",
      "title": "Аналитик",
      "code": "POS-0129"
    },
    {
      "id": "4001afef-df2c-4146-9aaf-8ea716f0c922",
      "title": "Аналитик",
      "code": "POS-0005"
    },
    {
      "id": "321b5984-4dda-4e70-8d3b-79d689e85a99",
      "title": "Аналитик",
      "code": "POS-0045"
    },
    {
      "id": "65b967b5-825c-4f1c-afec-6b1b2582ccec",
      "title": "Аналитик",
      "code": "POS-0105"
    }
  ],
  "total": 302
}
```

### Postal Areas

**Endpoint:** `GET /personnel/postal-areas`

**Parameters:** `{"limit": 10}`

**Status:** 400

**Response:**

```json
{
  "statusCode": 400,
  "message": [
    "поле «limit» должно быть не менее 1",
    "поле «limit» должно быть числом"
  ],
  "error": "Bad Request",
  "requestId": "25281683-6b2b-494d-83b2-09ab93737a13",
  "path": "/api/personnel/postal-areas?limit=10",
  "timestamp": "2026-05-14T16:51:40.571Z"
}
```

### Production Line Views

**Endpoint:** `GET /personnel/production-line-views`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "productionLineViews": [
    {
      "id": "87307692-8946-48e2-a308-674f7131e703",
      "productionLineId": "3d57ea5f-fcd5-3a77-24cb-7996f830f190",
      "name": "Линия А - Основное производство (Алматы)",
      "code": "ALM_LINE_A",
      "description": "Линия А - Основное производство (Алматы)",
      "isActive": true,
      "lastSyncedAt": "2026-05-13T06:00:00.085Z"
    },
    {
      "id": "d54e158b-7bb3-4efc-a56a-0e05cb2e7584",
      "productionLineId": "596c3638-89d3-1d32-8529-8207984638e7",
      "name": "Линия А - Производство майонеза (ЕЖК)",
      "code": "EKB_LINE_A",
      "description": "Линия А - Производство майонеза (ЕЖК)",
      "isActive": true,
      "lastSyncedAt": "2026-05-13T06:00:00.115Z"
    },
    {
      "id": "3ce64f14-4772-4f9c-9673-385e759baefa",
      "productionLineId": "a25e7bc7-221e-1376-0bc0-f30299a83ff1",
      "name": "Линия Б - Кетчуп и горчица (ЕЖК)",
      "code": "EKB_LINE_B",
      "description": "Линия Б - Кетчуп и горчица (ЕЖК)",
      "isActive": true,
      "lastSyncedAt": "2026-05-13T06:00:00.121Z"
    },
    {
      "id": "863893ec-cc61-43dc-ba9b-c1b15398068d",
      "productionLineId": "49a5ba6f-3838-3d85-6310-cf1ec432864d",
      "name": "Линия А - Производство маргарина (Хохольский)",
      "code": "HOH_LINE_A",
      "description": "Линия А - Производство маргарина (Хохольский)",
      "isActive": true,
      "lastSyncedAt": "2026-05-13T06:00:00.127Z"
    },
    {
      "id": "a999ca70-b7b4-4044-b17f-c496de175552",
      "productionLineId": "9330f683-f62b-5e4a-7877-6d2f13d19384",
      "name": "Линия Б - Мыловарение (Хохольский)",
      "code": "HOH_LINE_B",
      "description": "Линия Б - Мыловарение (Хохольский)",
      "isActive": true,
      "lastSyncedAt": "2026-05-13T06:00:00.131Z"
    },
    {
      "id": "b21b430a-a42f-4102-a815-66471f2c1cb8",
      "productionLineId": "a0a65c5f-bb95-e4a8-e1be-3b6dff660b2d",
      "name": "Линия А - Производство майонеза (Ногинск)",
      "code": "NOG_LINE_A",
      "description": "Линия А - Производство майонеза (Ногинск)",
      "isActive": true,
      "lastSyncedAt": "2026-05-13T06:00:00.135Z"
    },
    {
      "id": "95c54aaf-411f-4585-8f39-d5e7a934eb8a",
      "productionLineId": "4d1b5527-2315-0129-4000-409c8f901120",
      "name": "Линия А - Рафинация маслосемян (Тамань)",
      "code": "TAM_LINE_A",
      "description": "Линия А - Рафинация маслосемян (Тамань)",
      "isActive": true,
      "lastSyncedAt": "2026-05-13T06:00:00.139Z"
    },
    {
      "id": "41cbbb9f-fffb-4276-9922-a0675b1c4cf3",
      "productionLineId": "1aebc8ae-4374-f95a-8ec9-b80f1375d3c6",
      "name": "Линия Б - Упаковка масел (Тамань)",
      "code": "TAM_LINE_B",
      "description": "Линия Б - Упаковка масел (Тамань)",
      "isActive": true,
      "lastSyncedAt": "2026-05-13T06:00:00.145Z"
    }
  ],
  "total": 8
}
```

### Production Lines

**Endpoint:** `GET /production/production-lines`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "productionLines": [
    {
      "id": "3d57ea5f-fcd5-3a77-24cb-7996f830f190",
      "name": "Линия А - Основное производство (Алматы)",
      "code": "ALM_LINE_A",
      "description": "Линия А - Основное производство (Алматы)",
      "isActive": true,
      "createdAt": "2026-05-08T15:02:39.734Z",
      "updatedAt": "2026-05-12T05:26:12.005Z"
    },
    {
      "id": "596c3638-89d3-1d32-8529-8207984638e7",
      "name": "Линия А - Производство майонеза (ЕЖК)",
      "code": "EKB_LINE_A",
      "description": "Линия А - Производство майонеза (ЕЖК)",
      "isActive": true,
      "createdAt": "2026-05-08T15:02:39.722Z",
      "updatedAt": "2026-05-12T05:26:11.989Z"
    },
    {
      "id": "a25e7bc7-221e-1376-0bc0-f30299a83ff1",
      "name": "Линия Б - Кетчуп и горчица (ЕЖК)",
      "code": "EKB_LINE_B",
      "description": "Линия Б - Кетчуп и горчица (ЕЖК)",
      "isActive": true,
      "createdAt": "2026-05-08T15:02:39.725Z",
      "updatedAt": "2026-05-12T05:26:11.993Z"
    },
    {
      "id": "49a5ba6f-3838-3d85-6310-cf1ec432864d",
      "name": "Линия А - Производство маргарина (Хохольский)",
      "code": "HOH_LINE_A",
      "description": "Линия А - Производство маргарина (Хохольский)",
      "isActive": true,
      "createdAt": "2026-05-08T15:02:39.728Z",
      "updatedAt": "2026-05-12T05:26:11.997Z"
    },
    {
      "id": "9330f683-f62b-5e4a-7877-6d2f13d19384",
      "name": "Линия Б - Мыловарение (Хохольский)",
      "code": "HOH_LINE_B",
      "description": "Линия Б - Мыловарение (Хохольский)",
      "isActive": true,
      "createdAt": "2026-05-08T15:02:39.731Z",
      "updatedAt": "2026-05-12T05:26:12.001Z"
    },
    {
      "id": "a0a65c5f-bb95-e4a8-e1be-3b6dff660b2d",
      "name": "Линия А - Производство майонеза (Ногинск)",
      "code": "NOG_LINE_A",
      "description": "Линия А - Производство майонеза (Ногинск)",
      "isActive": true,
      "createdAt": "2026-05-08T15:02:39.737Z",
      "updatedAt": "2026-05-12T05:26:12.009Z"
    },
    {
      "id": "4d1b5527-2315-0129-4000-409c8f901120",
      "name": "Линия А - Рафинация маслосемян (Тамань)",
      "code": "TAM_LINE_A",
      "description": "Линия А - Рафинация маслосемян (Тамань)",
      "isActive": true,
      "createdAt": "2026-05-08T15:02:39.716Z",
      "updatedAt": "2026-05-12T05:26:11.959Z"
    },
    {
      "id": "1aebc8ae-4374-f95a-8ec9-b80f1375d3c6",
      "name": "Линия Б - Упаковка масел (Тамань)",
      "code": "TAM_LINE_B",
      "description": "Линия Б - Упаковка масел (Тамань)",
      "isActive": true,
      "createdAt": "2026-05-08T15:02:39.719Z",
      "updatedAt": "2026-05-12T05:26:11.984Z"
    }
  ],
  "total": 8
}
```

### Products

**Endpoint:** `GET /production/products`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "products": [
    {
      "id": "dc3f8ec0-47be-48b4-b4ea-724759d99848",
      "code": "PKG-BOTTLE-500ML",
      "name": "Бутылка ПЭТ 500мл",
      "category": "PACKAGING",
      "brand": null,
      "unitOfMeasure": {
        "id": "4a76a6bb-10d1-45ba-9784-7580bbc624e4",
        "code": "шт",
        "name": "шт"
      },
      "shelfLifeDays": null,
      "requiresQualityCheck": false
    },
    {
      "id": "a5af789d-a3d5-4e30-9386-accf43e7b736",
      "code": "PKG-BUCKET-5KG",
      "name": "Ведро ПЭ 5кг",
      "category": "PACKAGING",
      "brand": null,
      "unitOfMeasure": {
        "id": "4a76a6bb-10d1-45ba-9784-7580bbc624e4",
        "code": "шт",
        "name": "шт"
      },
      "shelfLifeDays": null,
      "requiresQualityCheck": false
    },
    {
      "id": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "code": "SEM-HYDROGENATED",
      "name": "Гидрогенизированный жир полуфабрикат",
      "category": "SEMI_FINISHED",
      "brand": null,
      "unitOfMeasure": {
        "id": "8a764a79-7604-4bab-bfd3-071558d8dd52",
        "code": "кг",
        "name": "кг"
      },
      "shelfLifeDays": 180,
      "requiresQualityCheck": true
    },
    {
      "id": "ee23eb53-c31e-4b45-a60e-c2c5856a5e38",
      "code": "FIN-MUSTARD",
      "name": "Горчица острая",
      "category": "FINISHED_PRODUCT",
      "brand": "ЭФКО",
      "unitOfMeasure": {
        "id": "4a76a6bb-10d1-45ba-9784-7580bbc624e4",
        "code": "шт",
        "name": "шт"
      },
      "shelfLifeDays": 180,
      "requiresQualityCheck": true
    },
    {
      "id": "c963b8f4-aded-4bea-8c4f-559fc3934946",
      "code": "FIN-SOAP-LIQUID",
      "name": "Жидкое мыло",
      "category": "FINISHED_PRODUCT",
      "brand": "ЭФКО Косметик",
      "unitOfMeasure": {
        "id": "6f5741b4-57a4-46c8-a87e-abb29947aff6",
        "code": "л",
        "name": "л"
      },
      "shelfLifeDays": 365,
      "requiresQualityCheck": true
    },
    {
      "id": "b0bcc1ed-c4c7-4c25-9d30-c6766ba51dca",
      "code": "PKG-CARTON-1KG",
      "name": "Картонная упаковка 1кг",
      "category": "PACKAGING",
      "brand": null,
      "unitOfMeasure": {
        "id": "4a76a6bb-10d1-45ba-9784-7580bbc624e4",
        "code": "шт",
        "name": "шт"
      },
      "shelfLifeDays": null,
      "requiresQualityCheck": false
    },
    {
      "id": "74bce996-1536-4968-be02-667b4dd71a5e",
      "code": "FIN-KETCHUP",
      "name": "Кетчуп томатный",
      "category": "FINISHED_PRODUCT",
      "brand": "ЭФКО",
      "unitOfMeasure": {
        "id": "4a76a6bb-10d1-45ba-9784-7580bbc624e4",
        "code": "шт",
        "name": "шт"
      },
      "shelfLifeDays": 180,
      "requiresQualityCheck": true
    },
    {
      "id": "9fddd328-a163-4935-95dc-da66484a5a35",
      "code": "FIN-MAON-EFKO",
      "name": "Майонез ЭФКО Провансаль",
      "category": "FINISHED_PRODUCT",
      "brand": "ЭФКО",
      "unitOfMeasure": {
        "id": "4a76a6bb-10d1-45ba-9784-7580bbc624e4",
        "code": "шт",
        "name": "шт"
      },
      "shelfLifeDays": 90,
      "requiresQualityCheck": true
    },
    {
      "id": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "code": "FIN-MAON-OLIVE",
      "name": "Майонез с оливковым маслом",
      "category": "FINISHED_PRODUCT",
      "brand": "ЭФКО",
      "unitOfMeasure": {
        "id": "4a76a6bb-10d1-45ba-9784-7580bbc624e4",
        "code": "шт",
        "name": "шт"
      },
      "shelfLifeDays": 90,
      "requiresQualityCheck": true
    },
    {
      "id": "23a4979c-cec8-4e0a-8f1a-bda18baaf7af",
      "code": "FIN-MARG-BAKING",
      "name": "Маргарин для выпечки",
      "category": "FINISHED_PRODUCT",
      "brand": "ЭФКО",
      "unitOfMeasure": {
        "id": "8a764a79-7604-4bab-bfd3-071558d8dd52",
        "code": "кг",
        "name": "кг"
      },
      "shelfLifeDays": 60,
      "requiresQualityCheck": true
    }
  ],
  "total": 16
}
```

### Promo Campaigns

**Endpoint:** `GET /production/promo-campaigns`

**Parameters:** `{"from": "2026-04-14", "to": "2026-05-14", "limit": 10}`

**Status:** 200

**Response:**

```json
{
  "items": [],
  "total": 0
}
```

### Quality

**Endpoint:** `GET /production/quality`

**Status:** 200

**Response:**

```json
{
  "results": [
    {
      "id": "15009085-784f-40ca-ac3b-cfcd0497a013",
      "lotNumber": "LOT-20260508-027",
      "qualitySpecId": "facc64f9-2ce3-4894-9def-2187f8db7582",
      "productId": "bfd01152-1bc4-4f8b-b7dd-30213f50ac3f",
      "parameterName": "Влажность",
      "resultValue": 0.164835,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-09T19:02:27.761Z"
    },
    {
      "id": "80c68ffa-49e4-4a64-bbf3-9c3c98a0436a",
      "lotNumber": "LOT-20260508-670",
      "qualitySpecId": "bff3e3d1-811d-4fbc-a5e4-ab46a96ae83f",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Кислотное число",
      "resultValue": 1.082116,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-09T16:54:08.394Z"
    },
    {
      "id": "ac256f56-7d13-4a63-a074-279a81e08b92",
      "lotNumber": "LOT-20260507-744",
      "qualitySpecId": "e4b66e1d-1a36-4107-8787-5551afb75e8d",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Перекисное число",
      "resultValue": 4.083159,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-08T22:34:31.235Z"
    },
    {
      "id": "cffce163-0b03-464a-b5c8-5a821887ca84",
      "lotNumber": "LOT-20260507-745",
      "qualitySpecId": "87c52d69-6f0a-49cc-a33f-1519fa576d49",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Перекисное число",
      "resultValue": 1.467425,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-08T22:34:31.235Z"
    },
    {
      "id": "06ce7568-ae02-4c0e-926d-33f2d838a9aa",
      "lotNumber": "LOT-20260507-893",
      "qualitySpecId": "bff3e3d1-811d-4fbc-a5e4-ab46a96ae83f",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Кислотное число",
      "resultValue": 0.708761,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-08T21:04:31.850Z"
    },
    {
      "id": "2d08bc83-9d0d-44c2-bc7c-a1a6d05905a6",
      "lotNumber": "LOT-20260508-027",
      "qualitySpecId": "c22e5c84-0580-4e0a-a68c-64cf4e8f576a",
      "productId": "bfd01152-1bc4-4f8b-b7dd-30213f50ac3f",
      "parameterName": "Содержание жира",
      "resultValue": 76.558469,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-08T19:02:27.761Z"
    },
    {
      "id": "3b683c64-ac8f-4611-9be4-d35f1e9aebd8",
      "lotNumber": "LOT-20260507-124",
      "qualitySpecId": "e87d9acb-6d87-4119-b768-1dc43e73d053",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "parameterName": "Влажность",
      "resultValue": 10.164187,
      "qualityStatus": "REJECTED",
      "testDate": "2026-05-08T18:24:26.997Z"
    },
    {
      "id": "ea83cfea-9230-40ea-9e64-ab0337dd5fee",
      "lotNumber": "LOT-20260507-101",
      "qualitySpecId": "0f2552d8-559b-44a9-bb95-a2e7bf0f83aa",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "parameterName": "Влажность",
      "resultValue": 0.083222,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-08T17:22:42.816Z"
    },
    {
      "id": "87f1305a-8264-412a-8c3b-53aa0b6a7e4a",
      "lotNumber": "LOT-20260507-101",
      "qualitySpecId": "bb757455-a8be-4d9d-b796-ad549ec686ee",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "parameterName": "Кислотное число",
      "resultValue": 0.082907,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-08T17:22:42.816Z"
    },
    {
      "id": "685481e6-6a2d-4406-9d4f-cdc3428b3130",
      "lotNumber": "LOT-20260507-100",
      "qualitySpecId": "a427b0c0-cba3-4222-a3c9-43d7dbca3756",
      "productId": "b0bcc1ed-c4c7-4c25-9d30-c6766ba51dca",
      "parameterName": "Вес упаковки",
      "resultValue": 1125.222347,
      "qualityStatus": "REJECTED",
      "testDate": "2026-05-08T17:22:42.816Z"
    },
    {
      "id": "de4e81b8-5a7c-4692-b53b-00db305cee3a",
      "lotNumber": "LOT-20260507-669",
      "qualitySpecId": "17cbbf1c-42e4-4a80-95fc-f5fc3a42b8f8",
      "productId": "ee23eb53-c31e-4b45-a60e-c2c5856a5e38",
      "parameterName": "Содержание жира",
      "resultValue": 75.108811,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-08T16:54:08.394Z"
    },
    {
      "id": "7617e832-a5a7-40f6-b7fa-31ea745726ae",
      "lotNumber": "LOT-20260507-669",
      "qualitySpecId": "56664415-9245-4f52-814a-4a2893ef6d8f",
      "productId": "ee23eb53-c31e-4b45-a60e-c2c5856a5e38",
      "parameterName": "Перекисное число",
      "resultValue": 1.565964,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-08T16:54:08.394Z"
    },
    {
      "id": "ed2c7f4e-8da8-4953-94a2-320c7e75be71",
      "lotNumber": "LOT-20260507-668",
      "qualitySpecId": "f22b7507-3190-4b36-a4b4-06ea3efaa007",
      "productId": "23a4979c-cec8-4e0a-8f1a-bda18baaf7af",
      "parameterName": "Влажность",
      "resultValue": 0.119525,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-08T16:54:08.394Z"
    },
    {
      "id": "62fab898-dedc-46c0-aa72-1f69adfcfb8f",
      "lotNumber": "LOT-20260508-670",
      "qualitySpecId": "6357c808-d15c-4f99-8aeb-1525ea2e2fa5",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Влажность",
      "resultValue": 9.189236,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-08T16:54:08.394Z"
    },
    {
      "id": "dfe8501b-bf13-462f-aaf7-413e98960cbc",
      "lotNumber": "LOT-20260507-274",
      "qualitySpecId": "b2f2f571-7163-4776-9228-048b4657a51f",
      "productId": "fd2079d6-6e13-4bb9-a0a9-07dea22cdefa",
      "parameterName": "Влажность",
      "resultValue": 5.225927,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-08T12:33:05.187Z"
    },
    {
      "id": "61db545b-9c79-4878-bfe6-b13225afdc07",
      "lotNumber": "LOT-20260507-906",
      "qualitySpecId": "264e69cf-8acc-42f1-8121-3812f1662ea5",
      "productId": "a5af789d-a3d5-4e30-9386-accf43e7b736",
      "parameterName": "Вес упаковки",
      "resultValue": 709.668953,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-08T12:01:03.466Z"
    },
    {
      "id": "561011e2-03ca-4925-8134-099e24c03fd8",
      "lotNumber": "LOT-20260507-923",
      "qualitySpecId": "63e69c0e-164b-466a-90b2-a7a15fe82ca2",
      "productId": "23a4979c-cec8-4e0a-8f1a-bda18baaf7af",
      "parameterName": "Перекисное число",
      "resultValue": 3.526422,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-08T10:01:27.835Z"
    },
    {
      "id": "6f816c50-9b22-4ae8-ad4f-c461a938fc16",
      "lotNumber": "LOT-20260507-744",
      "qualitySpecId": "0c5c72fc-dbf8-4054-b3d7-2177113bcad6",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Кислотное число",
      "resultValue": 0.483695,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-07T22:34:31.235Z"
    },
    {
      "id": "c2b2706e-dd40-4094-96b8-2a87514144e5",
      "lotNumber": "LOT-20260506-743",
      "qualitySpecId": "febf814a-9318-43fe-ae56-deabbfe036a7",
      "productId": "c963b8f4-aded-4bea-8c4f-559fc3934946",
      "parameterName": "Влажность",
      "resultValue": 0.065751,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T22:34:31.235Z"
    },
    {
      "id": "01c8c125-2f61-4db1-b8de-5c26bcec47ba",
      "lotNumber": "LOT-20260507-742",
      "qualitySpecId": "264e69cf-8acc-42f1-8121-3812f1662ea5",
      "productId": "a5af789d-a3d5-4e30-9386-accf43e7b736",
      "parameterName": "Вес упаковки",
      "resultValue": 711.888785,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-07T22:34:31.235Z"
    },
    {
      "id": "b5314d6e-5afa-4b0d-925f-b54fd7b6cc69",
      "lotNumber": "LOT-20260507-745",
      "qualitySpecId": "8358638a-e0b8-4629-9dfb-da9621c35816",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Влажность",
      "resultValue": 0.056416,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T22:34:31.235Z"
    },
    {
      "id": "98831ae7-44c1-4280-a284-7a4f597c3ca3",
      "lotNumber": "LOT-20260507-745",
      "qualitySpecId": "5b342adc-1a40-43c0-b962-ae70775e3c70",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Кислотное число",
      "resultValue": 0.184866,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T22:34:31.235Z"
    },
    {
      "id": "1463d884-4a53-4a51-916f-40442b912f46",
      "lotNumber": "LOT-20260507-697",
      "qualitySpecId": "d5c39654-a2f2-460f-8a30-a105fd561f16",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "parameterName": "Перекисное число",
      "resultValue": 5.095326,
      "qualityStatus": "REJECTED",
      "testDate": "2026-05-07T21:36:30.135Z"
    },
    {
      "id": "f8f318b9-6542-41f8-9933-5b8f6ae661ce",
      "lotNumber": "LOT-20260507-697",
      "qualitySpecId": "4401a5cb-ba9f-44b8-8620-ce79cde1e7b8",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "parameterName": "Кислотное число",
      "resultValue": 0.15183,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T21:36:30.135Z"
    },
    {
      "id": "60ef2081-1a59-4498-8b4e-d6607b7a8b94",
      "lotNumber": "LOT-20260507-701",
      "qualitySpecId": "b91a4672-cc56-43dc-a7a5-d0ba1c694c3e",
      "productId": "39ba0136-fa55-4218-aa12-5966fcedaa27",
      "parameterName": "Кислотное число",
      "resultValue": 0.657637,
      "qualityStatus": "REJECTED",
      "testDate": "2026-05-07T21:36:30.135Z"
    },
    {
      "id": "3b73aee5-a1c9-461c-bc5f-6f5955c9af35",
      "lotNumber": "LOT-20260506-698",
      "qualitySpecId": "bb757455-a8be-4d9d-b796-ad549ec686ee",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "parameterName": "Кислотное число",
      "resultValue": 0.0655,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-07T21:36:30.135Z"
    },
    {
      "id": "bdab4235-5681-4a2d-b845-fd421d504dba",
      "lotNumber": "LOT-20260507-916",
      "qualitySpecId": "b91a4672-cc56-43dc-a7a5-d0ba1c694c3e",
      "productId": "39ba0136-fa55-4218-aa12-5966fcedaa27",
      "parameterName": "Кислотное число",
      "resultValue": 0.618541,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-07T21:13:20.033Z"
    },
    {
      "id": "722d52e1-5378-4814-a581-8f7a749ba3a5",
      "lotNumber": "LOT-20260506-917",
      "qualitySpecId": "bff3e3d1-811d-4fbc-a5e4-ab46a96ae83f",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Кислотное число",
      "resultValue": 1.57317,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T21:13:20.033Z"
    },
    {
      "id": "64a5470e-132f-4b99-9de7-50047d913317",
      "lotNumber": "LOT-20260507-894",
      "qualitySpecId": "264e69cf-8acc-42f1-8121-3812f1662ea5",
      "productId": "a5af789d-a3d5-4e30-9386-accf43e7b736",
      "parameterName": "Вес упаковки",
      "resultValue": 732.359141,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T21:04:31.850Z"
    },
    {
      "id": "db4ccafc-d174-4a05-bfb2-258fd197a82e",
      "lotNumber": "LOT-20260506-896",
      "qualitySpecId": "264e69cf-8acc-42f1-8121-3812f1662ea5",
      "productId": "a5af789d-a3d5-4e30-9386-accf43e7b736",
      "parameterName": "Вес упаковки",
      "resultValue": 1131.177881,
      "qualityStatus": "REJECTED",
      "testDate": "2026-05-07T21:04:31.850Z"
    },
    {
      "id": "7a24c19f-6bcb-4167-8393-df78551efade",
      "lotNumber": "LOT-20260506-654",
      "qualitySpecId": "bff3e3d1-811d-4fbc-a5e4-ab46a96ae83f",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Кислотное число",
      "resultValue": 0.270174,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-07T18:40:10.171Z"
    },
    {
      "id": "49fd3d36-38b3-40f8-87a8-f893eb22ef53",
      "lotNumber": "LOT-20260507-655",
      "qualitySpecId": "aab22c16-f242-4f75-b8dc-be248b30630a",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Влажность",
      "resultValue": 0.136411,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T18:40:10.171Z"
    },
    {
      "id": "6f65f06b-2fac-4cee-a908-b3ba7764310a",
      "lotNumber": "LOT-20260506-680",
      "qualitySpecId": "ced5884b-7e64-4e09-a041-f6ac90f9e59d",
      "productId": "39ba0136-fa55-4218-aa12-5966fcedaa27",
      "parameterName": "Содержание жира",
      "resultValue": 67.594128,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T18:30:57.746Z"
    },
    {
      "id": "96691c3d-33e8-4444-bfec-b7a63d4e6a11",
      "lotNumber": "LOT-20260506-680",
      "qualitySpecId": "01f2e7a8-077b-4609-805d-03d91dde1c63",
      "productId": "39ba0136-fa55-4218-aa12-5966fcedaa27",
      "parameterName": "Перекисное число",
      "resultValue": 3.096444,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T18:30:57.746Z"
    },
    {
      "id": "1ae68d85-08cb-4dc2-b390-4c5fb550195e",
      "lotNumber": "LOT-20260506-128",
      "qualitySpecId": "8358638a-e0b8-4629-9dfb-da9621c35816",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Влажность",
      "resultValue": 0.049255,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T18:24:26.997Z"
    },
    {
      "id": "3e435f42-ed35-4671-8fde-003a4e0b6894",
      "lotNumber": "LOT-20260506-127",
      "qualitySpecId": "8358638a-e0b8-4629-9dfb-da9621c35816",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Влажность",
      "resultValue": 0.113823,
      "qualityStatus": "REJECTED",
      "testDate": "2026-05-07T18:24:26.997Z"
    },
    {
      "id": "6f855d82-966c-4398-bfff-9466a5903cdb",
      "lotNumber": "LOT-20260506-127",
      "qualitySpecId": "87c52d69-6f0a-49cc-a33f-1519fa576d49",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Перекисное число",
      "resultValue": 1.128242,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T18:24:26.997Z"
    },
    {
      "id": "b21e77bb-3ad1-45ed-9462-181b9a2357d3",
      "lotNumber": "LOT-20260507-101",
      "qualitySpecId": "06a960b6-5ae5-4a65-9d88-c8210f86e36c",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "parameterName": "Перекисное число",
      "resultValue": 1.601935,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T17:22:42.816Z"
    },
    {
      "id": "00e0b5f4-f957-4943-b066-c2c7c29ef149",
      "lotNumber": "LOT-20260507-671",
      "qualitySpecId": "264e69cf-8acc-42f1-8121-3812f1662ea5",
      "productId": "a5af789d-a3d5-4e30-9386-accf43e7b736",
      "parameterName": "Вес упаковки",
      "resultValue": 698.372524,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T16:54:08.394Z"
    },
    {
      "id": "354eb180-46ca-4e5c-bb2c-8c6cf0587403",
      "lotNumber": "LOT-20260507-669",
      "qualitySpecId": "4ff87a92-793e-43d3-a4fc-6b711652adbf",
      "productId": "ee23eb53-c31e-4b45-a60e-c2c5856a5e38",
      "parameterName": "Влажность",
      "resultValue": 0.08236,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T16:54:08.394Z"
    },
    {
      "id": "f10e2bb0-ec0b-4052-9157-392b352faf7f",
      "lotNumber": "LOT-20260507-668",
      "qualitySpecId": "8f797d1a-55cd-49af-8335-c44b5e1175bf",
      "productId": "23a4979c-cec8-4e0a-8f1a-bda18baaf7af",
      "parameterName": "Содержание жира",
      "resultValue": 70.712617,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T16:54:08.394Z"
    },
    {
      "id": "62636884-14b4-433b-b2ff-cc7b29458b75",
      "lotNumber": "LOT-20260506-064",
      "qualitySpecId": "bff3e3d1-811d-4fbc-a5e4-ab46a96ae83f",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Кислотное число",
      "resultValue": 1.260778,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T15:17:43.799Z"
    },
    {
      "id": "d1c68ac3-152c-4220-9f2d-cc6cf00b5ba8",
      "lotNumber": "LOT-20260506-064",
      "qualitySpecId": "6357c808-d15c-4f99-8aeb-1525ea2e2fa5",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Влажность",
      "resultValue": 5.94897,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T15:17:43.799Z"
    },
    {
      "id": "856af413-78e7-4db2-afa7-d81d21fd93c6",
      "lotNumber": "LOT-20260506-066",
      "qualitySpecId": "87c52d69-6f0a-49cc-a33f-1519fa576d49",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Перекисное число",
      "resultValue": 1.047044,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T15:17:43.799Z"
    },
    {
      "id": "f1c8555c-ad5e-4b1d-b012-656b763deee6",
      "lotNumber": "LOT-20260507-274",
      "qualitySpecId": "fd7adeac-0bcc-4838-8484-e4e753c913dc",
      "productId": "fd2079d6-6e13-4bb9-a0a9-07dea22cdefa",
      "parameterName": "Кислотное число",
      "resultValue": 0.448744,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T12:33:05.187Z"
    },
    {
      "id": "37797797-9933-4d23-aa71-51c525b00482",
      "lotNumber": "LOT-20260506-273",
      "qualitySpecId": "6357c808-d15c-4f99-8aeb-1525ea2e2fa5",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Влажность",
      "resultValue": 9.662637,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-07T12:33:05.187Z"
    },
    {
      "id": "2534cd6a-8348-42e0-a921-6b927f8f8c83",
      "lotNumber": "LOT-20260506-273",
      "qualitySpecId": "bff3e3d1-811d-4fbc-a5e4-ab46a96ae83f",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Кислотное число",
      "resultValue": 2.344975,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T12:33:05.187Z"
    },
    {
      "id": "fbcc5657-2962-43b5-9dd6-515cb6a876e6",
      "lotNumber": "LOT-20260507-907",
      "qualitySpecId": "6208ee98-cf43-4747-b8d6-46e225f7d9db",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "parameterName": "Кислотное число",
      "resultValue": 1.258246,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T12:01:03.466Z"
    },
    {
      "id": "666a99e7-177d-4495-842b-214a3b6fd467",
      "lotNumber": "LOT-20260507-907",
      "qualitySpecId": "e87d9acb-6d87-4119-b768-1dc43e73d053",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "parameterName": "Влажность",
      "resultValue": 10.296652,
      "qualityStatus": "REJECTED",
      "testDate": "2026-05-07T12:01:03.466Z"
    },
    {
      "id": "bfd9cac3-3870-4c56-a7b3-47f457445168",
      "lotNumber": "LOT-20260506-887",
      "qualitySpecId": "e4e88f42-7e5c-469a-9d7a-b593474bf065",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "parameterName": "Содержание жира",
      "resultValue": 74.752063,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T11:36:05.709Z"
    },
    {
      "id": "4c02eaeb-121d-4e20-ba6d-fca7b5a51792",
      "lotNumber": "LOT-20260506-889",
      "qualitySpecId": "d64fb42e-5526-4c3b-84fb-e88814d11909",
      "productId": "74bce996-1536-4968-be02-667b4dd71a5e",
      "parameterName": "Кислотное число",
      "resultValue": 0.102696,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T11:36:05.709Z"
    },
    {
      "id": "85799d66-fb8d-4fca-86c8-403b9d124aa5",
      "lotNumber": "LOT-20260506-818",
      "qualitySpecId": "edb7bff4-44d5-4e19-b211-a2c605d41be2",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "parameterName": "Влажность",
      "resultValue": 0.117541,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-07T11:30:08.925Z"
    },
    {
      "id": "d5752d05-4873-45d1-a3a0-ff6ef5c83d36",
      "lotNumber": "LOT-20260506-922",
      "qualitySpecId": "b91a4672-cc56-43dc-a7a5-d0ba1c694c3e",
      "productId": "39ba0136-fa55-4218-aa12-5966fcedaa27",
      "parameterName": "Кислотное число",
      "resultValue": 0.174671,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T10:01:27.835Z"
    },
    {
      "id": "382aeb91-51ae-4ae3-a553-f3b08eec66f5",
      "lotNumber": "LOT-20260506-921",
      "qualitySpecId": "bff3e3d1-811d-4fbc-a5e4-ab46a96ae83f",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Кислотное число",
      "resultValue": 0.570294,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-07T10:01:27.835Z"
    },
    {
      "id": "b97f500f-4e9a-4e3d-869e-c81d1523dca0",
      "lotNumber": "LOT-20260506-920",
      "qualitySpecId": "fd7adeac-0bcc-4838-8484-e4e753c913dc",
      "productId": "fd2079d6-6e13-4bb9-a0a9-07dea22cdefa",
      "parameterName": "Кислотное число",
      "resultValue": 2.284223,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T10:01:27.835Z"
    },
    {
      "id": "18689ba7-0b9d-478c-9eb9-f6f1aba9048b",
      "lotNumber": "LOT-20260506-028",
      "qualitySpecId": "4c737e25-803e-49d6-b776-b2ca8f0445b4",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Содержание жира",
      "resultValue": 77.059779,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T07:57:31.290Z"
    },
    {
      "id": "eafce38e-c539-4610-8ff8-b7c0a4912396",
      "lotNumber": "LOT-20260506-121",
      "qualitySpecId": "aab22c16-f242-4f75-b8dc-be248b30630a",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Влажность",
      "resultValue": 0.051158,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T07:19:10.143Z"
    },
    {
      "id": "7015985b-5225-482c-8c1d-40def654bf18",
      "lotNumber": "LOT-20260506-953",
      "qualitySpecId": "17cbbf1c-42e4-4a80-95fc-f5fc3a42b8f8",
      "productId": "ee23eb53-c31e-4b45-a60e-c2c5856a5e38",
      "parameterName": "Содержание жира",
      "resultValue": 76.389385,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-07T05:01:01.278Z"
    },
    {
      "id": "d136b37e-361d-4ada-9a63-8aef1d6e76f3",
      "lotNumber": "LOT-20260505-741",
      "qualitySpecId": "06a960b6-5ae5-4a65-9d88-c8210f86e36c",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "parameterName": "Перекисное число",
      "resultValue": 2.139997,
      "qualityStatus": "REJECTED",
      "testDate": "2026-05-06T22:34:31.235Z"
    },
    {
      "id": "8e78e884-9f5f-498d-95c6-dc51673dccd7",
      "lotNumber": "LOT-20260505-741",
      "qualitySpecId": "0f2552d8-559b-44a9-bb95-a2e7bf0f83aa",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "parameterName": "Влажность",
      "resultValue": 0.038786,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T22:34:31.235Z"
    },
    {
      "id": "2e474f2d-9050-4d5b-bdee-8c9b953da79e",
      "lotNumber": "LOT-20260506-698",
      "qualitySpecId": "06a960b6-5ae5-4a65-9d88-c8210f86e36c",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "parameterName": "Перекисное число",
      "resultValue": 0.898003,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T21:36:30.135Z"
    },
    {
      "id": "4f44eedf-eee8-4a4b-a6db-e8d5dcbd1570",
      "lotNumber": "LOT-20260506-698",
      "qualitySpecId": "0f2552d8-559b-44a9-bb95-a2e7bf0f83aa",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "parameterName": "Влажность",
      "resultValue": 0.041359,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T21:36:30.135Z"
    },
    {
      "id": "fa2d975e-e5bd-434c-8d64-99053668f85e",
      "lotNumber": "LOT-20260505-025",
      "qualitySpecId": "3d74ea83-0538-4190-9d75-a8b1738f8714",
      "productId": "74bce996-1536-4968-be02-667b4dd71a5e",
      "parameterName": "Содержание жира",
      "resultValue": 70.702862,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T19:02:27.761Z"
    },
    {
      "id": "25adb81c-5817-4632-ac8a-52e1304bed32",
      "lotNumber": "LOT-20260506-125",
      "qualitySpecId": "e87d9acb-6d87-4119-b768-1dc43e73d053",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "parameterName": "Влажность",
      "resultValue": 3.268735,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T18:24:26.997Z"
    },
    {
      "id": "b95ef319-8169-4b4c-985c-d2c9d196c257",
      "lotNumber": "LOT-20260505-126",
      "qualitySpecId": "3d74ea83-0538-4190-9d75-a8b1738f8714",
      "productId": "74bce996-1536-4968-be02-667b4dd71a5e",
      "parameterName": "Содержание жира",
      "resultValue": 74.235399,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T18:24:26.997Z"
    },
    {
      "id": "1513ee1c-0dee-4a82-bbbb-2b87f17b29a7",
      "lotNumber": "LOT-20260506-128",
      "qualitySpecId": "87c52d69-6f0a-49cc-a33f-1519fa576d49",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Перекисное число",
      "resultValue": 1.774805,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T18:24:26.997Z"
    },
    {
      "id": "9cf120cd-5214-4ca0-9cb0-0d7f40b30e93",
      "lotNumber": "LOT-20260505-123",
      "qualitySpecId": "6208ee98-cf43-4747-b8d6-46e225f7d9db",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "parameterName": "Кислотное число",
      "resultValue": 2.344075,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-06T18:24:26.997Z"
    },
    {
      "id": "f7fd9eac-dd29-4a0d-b661-22acb86f5838",
      "lotNumber": "LOT-20260505-104",
      "qualitySpecId": "6208ee98-cf43-4747-b8d6-46e225f7d9db",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "parameterName": "Кислотное число",
      "resultValue": 0.994684,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-06T17:22:42.816Z"
    },
    {
      "id": "6f28c02f-c6d8-41cc-a183-495bc1e892e2",
      "lotNumber": "LOT-20260505-102",
      "qualitySpecId": "bff3e3d1-811d-4fbc-a5e4-ab46a96ae83f",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Кислотное число",
      "resultValue": 0.878058,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-06T17:22:42.816Z"
    },
    {
      "id": "fb420450-f4f2-4882-8c43-4585727ae701",
      "lotNumber": "LOT-20260505-672",
      "qualitySpecId": "aab22c16-f242-4f75-b8dc-be248b30630a",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Влажность",
      "resultValue": 0.047314,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T16:54:08.394Z"
    },
    {
      "id": "5b3d7058-829b-4743-8c95-cd92c93e298b",
      "lotNumber": "LOT-20260505-673",
      "qualitySpecId": "264e69cf-8acc-42f1-8121-3812f1662ea5",
      "productId": "a5af789d-a3d5-4e30-9386-accf43e7b736",
      "parameterName": "Вес упаковки",
      "resultValue": 85.284265,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T16:54:08.394Z"
    },
    {
      "id": "6eac9a2e-7746-44e1-baa1-bb61e5716972",
      "lotNumber": "LOT-20260505-062",
      "qualitySpecId": "fd7adeac-0bcc-4838-8484-e4e753c913dc",
      "productId": "fd2079d6-6e13-4bb9-a0a9-07dea22cdefa",
      "parameterName": "Кислотное число",
      "resultValue": 2.502195,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T15:17:43.799Z"
    },
    {
      "id": "2d5263cc-6283-49b1-a16e-57f661b327a3",
      "lotNumber": "LOT-20260506-066",
      "qualitySpecId": "8358638a-e0b8-4629-9dfb-da9621c35816",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Влажность",
      "resultValue": 0.079316,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-06T15:17:43.799Z"
    },
    {
      "id": "e4b42a5f-eb74-4fa6-9c9e-98a3ea26303b",
      "lotNumber": "LOT-20260505-061",
      "qualitySpecId": "a427b0c0-cba3-4222-a3c9-43d7dbca3756",
      "productId": "b0bcc1ed-c4c7-4c25-9d30-c6766ba51dca",
      "parameterName": "Вес упаковки",
      "resultValue": 380.501428,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T15:17:43.799Z"
    },
    {
      "id": "00e19e36-67ff-4c2a-95ee-dd79d7dc8212",
      "lotNumber": "LOT-20260505-152",
      "qualitySpecId": "a427b0c0-cba3-4222-a3c9-43d7dbca3756",
      "productId": "b0bcc1ed-c4c7-4c25-9d30-c6766ba51dca",
      "parameterName": "Вес упаковки",
      "resultValue": 786.794791,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T13:08:54.059Z"
    },
    {
      "id": "9bb18db4-f5ef-4cb6-817c-6be2b41b4b0b",
      "lotNumber": "LOT-20260505-151",
      "qualitySpecId": "d64fb42e-5526-4c3b-84fb-e88814d11909",
      "productId": "74bce996-1536-4968-be02-667b4dd71a5e",
      "parameterName": "Кислотное число",
      "resultValue": 0.158183,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T13:08:54.059Z"
    },
    {
      "id": "8b75bfd9-cb4b-411a-ace4-ef9df6519244",
      "lotNumber": "LOT-20260506-887",
      "qualitySpecId": "d5c39654-a2f2-460f-8a30-a105fd561f16",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "parameterName": "Перекисное число",
      "resultValue": 3.226797,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T11:36:05.709Z"
    },
    {
      "id": "2d881502-7ca0-4dcd-8766-2509412e15e0",
      "lotNumber": "LOT-20260506-887",
      "qualitySpecId": "edb7bff4-44d5-4e19-b211-a2c605d41be2",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "parameterName": "Влажность",
      "resultValue": 0.086601,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T11:36:05.709Z"
    },
    {
      "id": "9bc2a942-8439-4aae-b49f-e6267c615037",
      "lotNumber": "LOT-20260506-815",
      "qualitySpecId": "0f2552d8-559b-44a9-bb95-a2e7bf0f83aa",
      "productId": "46848456-c09e-470c-8d74-2ae422b5ee8a",
      "parameterName": "Влажность",
      "resultValue": 0.06382,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T11:30:08.925Z"
    },
    {
      "id": "d1de6230-acdf-49ca-a9bc-242d03e95a36",
      "lotNumber": "LOT-20260506-818",
      "qualitySpecId": "d5c39654-a2f2-460f-8a30-a105fd561f16",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "parameterName": "Перекисное число",
      "resultValue": 2.932926,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T11:30:08.925Z"
    },
    {
      "id": "6fcca2e1-2559-4b37-aded-b0888356fba4",
      "lotNumber": "LOT-20260506-818",
      "qualitySpecId": "4401a5cb-ba9f-44b8-8620-ce79cde1e7b8",
      "productId": "9fddd328-a163-4935-95dc-da66484a5a35",
      "parameterName": "Кислотное число",
      "resultValue": 0.364753,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-06T11:30:08.925Z"
    },
    {
      "id": "9e98b302-2eb2-4ce4-9e3d-cc1c8fbd9c7f",
      "lotNumber": "LOT-20260505-816",
      "qualitySpecId": "0c5c72fc-dbf8-4054-b3d7-2177113bcad6",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Кислотное число",
      "resultValue": 0.503435,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T11:30:08.925Z"
    },
    {
      "id": "8372d49f-4181-4c8e-a24e-c6dc14dbc866",
      "lotNumber": "LOT-20260505-801",
      "qualitySpecId": "2c02a196-5615-4b2e-b141-7591688592e0",
      "productId": "74bce996-1536-4968-be02-667b4dd71a5e",
      "parameterName": "Влажность",
      "resultValue": 0.081625,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T10:59:37.669Z"
    },
    {
      "id": "eb5f7f6c-8258-4f04-a21a-fb19ea94d568",
      "lotNumber": "LOT-20260505-803",
      "qualitySpecId": "0c5c72fc-dbf8-4054-b3d7-2177113bcad6",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Кислотное число",
      "resultValue": 0.61247,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-06T10:59:37.669Z"
    },
    {
      "id": "6c71334e-3ade-4f61-b4cc-bf0768c0bc5f",
      "lotNumber": "LOT-20260505-803",
      "qualitySpecId": "e4b66e1d-1a36-4107-8787-5551afb75e8d",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Перекисное число",
      "resultValue": 3.330823,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T10:59:37.669Z"
    },
    {
      "id": "6c95d9cf-5cd7-4e91-9c95-b09a452db314",
      "lotNumber": "LOT-20260505-803",
      "qualitySpecId": "4c737e25-803e-49d6-b776-b2ca8f0445b4",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Содержание жира",
      "resultValue": 66.974134,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T10:59:37.669Z"
    },
    {
      "id": "04f3c63e-774b-4b2e-a773-1e2670ab843e",
      "lotNumber": "LOT-20260505-260",
      "qualitySpecId": "a427b0c0-cba3-4222-a3c9-43d7dbca3756",
      "productId": "b0bcc1ed-c4c7-4c25-9d30-c6766ba51dca",
      "parameterName": "Вес упаковки",
      "resultValue": 587.915001,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T10:37:10.933Z"
    },
    {
      "id": "04e8b671-7f3d-48d6-ad90-4f76fbd89e5f",
      "lotNumber": "LOT-20260506-922",
      "qualitySpecId": "ced5884b-7e64-4e09-a041-f6ac90f9e59d",
      "productId": "39ba0136-fa55-4218-aa12-5966fcedaa27",
      "parameterName": "Содержание жира",
      "resultValue": 76.724349,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T10:01:27.835Z"
    },
    {
      "id": "09b404c2-6bff-49d2-99f6-9816e78beb30",
      "lotNumber": "LOT-20260506-921",
      "qualitySpecId": "6357c808-d15c-4f99-8aeb-1525ea2e2fa5",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Влажность",
      "resultValue": 4.911149,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T10:01:27.835Z"
    },
    {
      "id": "b8a2c9c8-f323-43dd-9769-8f013f725606",
      "lotNumber": "LOT-20260505-919",
      "qualitySpecId": "0c5c72fc-dbf8-4054-b3d7-2177113bcad6",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Кислотное число",
      "resultValue": 0.086329,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T10:01:27.835Z"
    },
    {
      "id": "ca0c5945-4216-4ea1-9db3-2df4979583c3",
      "lotNumber": "LOT-20260506-920",
      "qualitySpecId": "b2f2f571-7163-4776-9228-048b4657a51f",
      "productId": "fd2079d6-6e13-4bb9-a0a9-07dea22cdefa",
      "parameterName": "Влажность",
      "resultValue": 2.367404,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T10:01:27.835Z"
    },
    {
      "id": "be0a7fa4-81e1-4b63-997b-43c3b20b7da4",
      "lotNumber": "LOT-20260506-166",
      "qualitySpecId": "fdffa686-49b5-4035-8872-205032f838e8",
      "productId": "dc3f8ec0-47be-48b4-b4ea-724759d99848",
      "parameterName": "Вес упаковки",
      "resultValue": 1048.093554,
      "qualityStatus": "REJECTED",
      "testDate": "2026-05-06T08:16:48.060Z"
    },
    {
      "id": "617b3238-8141-44e8-92e1-33e03caf08df",
      "lotNumber": "LOT-20260505-163",
      "qualitySpecId": "5b342adc-1a40-43c0-b962-ae70775e3c70",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Кислотное число",
      "resultValue": 0.212244,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T08:16:48.060Z"
    },
    {
      "id": "c29c9ae9-cbe5-4e08-b67e-fe2ee5dc7c25",
      "lotNumber": "LOT-20260505-163",
      "qualitySpecId": "8358638a-e0b8-4629-9dfb-da9621c35816",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Влажность",
      "resultValue": 0.0807,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T08:16:48.060Z"
    },
    {
      "id": "6073605a-e337-414e-85d9-25737132a05c",
      "lotNumber": "LOT-20260506-165",
      "qualitySpecId": "264e69cf-8acc-42f1-8121-3812f1662ea5",
      "productId": "a5af789d-a3d5-4e30-9386-accf43e7b736",
      "parameterName": "Вес упаковки",
      "resultValue": 563.594696,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-06T08:16:48.060Z"
    },
    {
      "id": "90e5816d-14ad-4d7c-9211-1a4eb0035997",
      "lotNumber": "LOT-20260506-028",
      "qualitySpecId": "0c5c72fc-dbf8-4054-b3d7-2177113bcad6",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Кислотное число",
      "resultValue": 0.486947,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-06T07:57:31.290Z"
    },
    {
      "id": "8f3ea051-4dfc-4b3e-a249-99931b4a863e",
      "lotNumber": "LOT-20260506-028",
      "qualitySpecId": "e4b66e1d-1a36-4107-8787-5551afb75e8d",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Перекисное число",
      "resultValue": 5.068034,
      "qualityStatus": "PENDING",
      "testDate": "2026-05-06T07:57:31.290Z"
    },
    {
      "id": "a0c3c8e7-0c10-4c3a-bb01-4eda3200040d",
      "lotNumber": "LOT-20260506-121",
      "qualitySpecId": "e4b66e1d-1a36-4107-8787-5551afb75e8d",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "parameterName": "Перекисное число",
      "resultValue": 5.533155,
      "qualityStatus": "REJECTED",
      "testDate": "2026-05-06T07:19:10.143Z"
    },
    {
      "id": "bc078565-c2ad-4104-8d1c-17592fc04928",
      "lotNumber": "LOT-20260506-952",
      "qualitySpecId": "679596d6-9f40-4c7d-90c0-bab89069f3a2",
      "productId": "39ba0136-fa55-4218-aa12-5966fcedaa27",
      "parameterName": "Влажность",
      "resultValue": 0.009455,
      "qualityStatus": "APPROVED",
      "testDate": "2026-05-06T05:01:01.278Z"
    },
    {
      "id": "1864a370-b780-4b31-8dd0-1f9cda6ad83b",
      "lotNumber": "LOT-20260506-951",
      "qualitySpecId": "e87d9acb-6d87-4119-b768-1dc43e73d053",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "parameterName": "Влажность",
      "resultValue": 9.211216,
      "qualityStatus": "REJECTED",
      "testDate": "2026-05-06T05:01:01.278Z"
    }
  ],
  "total": 5156
}
```

### Quality Specs

**Endpoint:** `GET /production/quality-specs`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "qualitySpecs": [
    {
      "id": "8358638a-e0b8-4629-9dfb-da9621c35816",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Влажность",
      "lowerLimit": 0,
      "upperLimit": 0.1,
      "isActive": true
    },
    {
      "id": "5b342adc-1a40-43c0-b962-ae70775e3c70",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Кислотное число",
      "lowerLimit": 0,
      "upperLimit": 0.4,
      "isActive": true
    },
    {
      "id": "87c52d69-6f0a-49cc-a33f-1519fa576d49",
      "productId": "0559a3fa-f01e-42b3-9fe5-c13a4ab8aaed",
      "parameterName": "Перекисное число",
      "lowerLimit": 0,
      "upperLimit": 2,
      "isActive": true
    },
    {
      "id": "e87d9acb-6d87-4119-b768-1dc43e73d053",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "parameterName": "Влажность",
      "lowerLimit": 0,
      "upperLimit": 9,
      "isActive": true
    },
    {
      "id": "6208ee98-cf43-4747-b8d6-46e225f7d9db",
      "productId": "180f0ebe-d23f-40f5-a20e-c171bf4cf5af",
      "parameterName": "Кислотное число",
      "lowerLimit": 0,
      "upperLimit": 3.5,
      "isActive": true
    },
    {
      "id": "6357c808-d15c-4f99-8aeb-1525ea2e2fa5",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Влажность",
      "lowerLimit": 0,
      "upperLimit": 9,
      "isActive": true
    },
    {
      "id": "bff3e3d1-811d-4fbc-a5e4-ab46a96ae83f",
      "productId": "1cc81652-ae01-44ff-9425-dcfab30aab24",
      "parameterName": "Кислотное число",
      "lowerLimit": 0,
      "upperLimit": 3.5,
      "isActive": true
    },
    {
      "id": "f22b7507-3190-4b36-a4b4-06ea3efaa007",
      "productId": "23a4979c-cec8-4e0a-8f1a-bda18baaf7af",
      "parameterName": "Влажность",
      "lowerLimit": 0,
      "upperLimit": 0.15,
      "isActive": true
    },
    {
      "id": "30b90867-5370-4a99-98f8-728fc5d843a5",
      "productId": "23a4979c-cec8-4e0a-8f1a-bda18baaf7af",
      "parameterName": "Кислотное число",
      "lowerLimit": 0,
      "upperLimit": 0.6,
      "isActive": true
    },
    {
      "id": "63e69c0e-164b-466a-90b2-a7a15fe82ca2",
      "productId": "23a4979c-cec8-4e0a-8f1a-bda18baaf7af",
      "parameterName": "Перекисное число",
      "lowerLimit": 0,
      "upperLimit": 5,
      "isActive": true
    }
  ],
  "total": 47
}
```

### Sales

**Endpoint:** `GET /production/sales`

**Parameters:** `{"from": "2026-04-14", "to": "2026-05-14", "limit": 10}`

**Status:** 200

**Response:**

```json
{
  "sales": [
    {
      "id": "da1f76cc-9ccd-4a4b-883c-4c2db0ee00db",
      "externalId": "SALE-0049830",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "customerId": "f5f0b374-f5e3-4852-8501-bd5eac95a199",
      "quantity": 7793.326,
      "amount": 2774980.71,
      "cost": 2023329.56,
      "saleDate": "2026-05-04T00:00:00.000Z",
      "region": "СЗФО",
      "channel": "RETAIL"
    },
    {
      "id": "95ca07c8-cdeb-45b1-a39b-4e196c941bf8",
      "externalId": "SALE-0049638",
      "productId": "bfd01152-1bc4-4f8b-b7dd-30213f50ac3f",
      "customerId": "904682fa-385b-4b05-8574-fad654bd95c9",
      "quantity": 6399.112,
      "amount": 986420.59,
      "cost": 724356.75,
      "saleDate": "2026-05-04T00:00:00.000Z",
      "region": "ЮФО",
      "channel": "RETAIL"
    },
    {
      "id": "7828d06d-4a16-4f4e-bb5f-ad34395bbb9f",
      "externalId": "SALE-0049620",
      "productId": "c963b8f4-aded-4bea-8c4f-559fc3934946",
      "customerId": "5b092ae7-094a-4b0d-b38b-8cb7843aa1f4",
      "quantity": 5659.558,
      "amount": 968215.51,
      "cost": 720885.22,
      "saleDate": "2026-05-04T00:00:00.000Z",
      "region": "СЗФО",
      "channel": "RETAIL"
    },
    {
      "id": "e26d0822-0178-4720-92c1-ac7dbf97e3b4",
      "externalId": "SALE-0049502",
      "productId": "39ba0136-fa55-4218-aa12-5966fcedaa27",
      "customerId": "5d9014fd-4439-4332-95e2-a2e41faaa735",
      "quantity": 6414.681,
      "amount": 1528046.7,
      "cost": 1048478.05,
      "saleDate": "2026-05-04T00:00:00.000Z",
      "region": "СЗФО",
      "channel": "RETAIL"
    },
    {
      "id": "a8321fb8-b76d-4032-a081-ac0d8e17acd4",
      "externalId": "SALE-0049421",
      "productId": "ee23eb53-c31e-4b45-a60e-c2c5856a5e38",
      "customerId": "5d9014fd-4439-4332-95e2-a2e41faaa735",
      "quantity": 4684.041,
      "amount": 680482.83,
      "cost": 492227.3,
      "saleDate": "2026-05-04T00:00:00.000Z",
      "region": "ПФО",
      "channel": "RETAIL"
    },
    {
      "id": "6ac655f7-cda9-486c-b990-37fe67b36c9f",
      "externalId": "SALE-0049400",
      "productId": "ae63332d-1dd2-4576-aa17-f6963fb52e5b",
      "customerId": "84e3670d-ac58-4824-8656-fb5c5ce9cad2",
      "quantity": 7816.387,
      "amount": 36187.41,
      "cost": 26314.9,
      "saleDate": "2026-05-04T00:00:00.000Z",
      "region": "ЦФО",
      "channel": "RETAIL"
    },
    {
      "id": "2870014d-e332-4953-92f3-42a679d60857",
      "externalId": "SALE-0049386",
      "productId": "c963b8f4-aded-4bea-8c4f-559fc3934946",
      "customerId": "de219684-ecaa-4945-a8d5-b4982e9c3d0d",
      "quantity": 3324.333,
      "amount": 2700573.77,
      "cost": 1895552.23,
      "saleDate": "2026-05-04T00:00:00.000Z",
      "region": "ЦФО",
      "channel": "RETAIL"
    },
    {
      "id": "4fe6c5ad-96a2-410a-8f78-2c4bb8baf77e",
      "externalId": "SALE-0049336",
      "productId": "bfd01152-1bc4-4f8b-b7dd-30213f50ac3f",
      "customerId": "84e3670d-ac58-4824-8656-fb5c5ce9cad2",
      "quantity": 1095.261,
      "amount": 589310.49,
      "cost": 455196.29,
      "saleDate": "2026-05-04T00:00:00.000Z",
      "region": "ЦФО",
      "channel": "RETAIL"
    },
    {
      "id": "b61aacac-e831-48b6-bcfe-17a585840364",
      "externalId": "SALE-0049300",
      "productId": "c963b8f4-aded-4bea-8c4f-559fc3934946",
      "customerId": "93706a78-9986-4351-8f1d-387600dfa589",
      "quantity": 1757.594,
      "amount": 113589.39,
      "cost": 86956.09,
      "saleDate": "2026-05-04T00:00:00.000Z",
      "region": "СФО",
      "channel": "RETAIL"
    },
    {
      "id": "d9b4cf7e-4892-44a4-bd14-7280dd4d2a6c",
      "externalId": "SALE-0049247",
      "productId": "74bce996-1536-4968-be02-667b4dd71a5e",
      "customerId": "5b092ae7-094a-4b0d-b38b-8cb7843aa1f4",
      "quantity": 4986.89,
      "amount": 2564509.37,
      "cost": 1980586.31,
      "saleDate": "2026-05-04T00:00:00.000Z",
      "region": "ЦФО",
      "channel": "RETAIL"
    }
  ],
  "total": 8915
}
```

### Sales Summary

**Endpoint:** `GET /production/sales/summary`

**Parameters:** `{"from": "2026-04-14", "to": "2026-05-14"}`

**Status:** 200

**Response:**

```json
{
  "summary": [
    {
      "groupKey": "СФО",
      "totalQuantity": 3476327.989,
      "totalAmount": 1499337616.44,
      "salesCount": 964
    },
    {
      "groupKey": "ЮФО",
      "totalQuantity": 5703304.438,
      "totalAmount": 2281794702.34,
      "salesCount": 1498
    },
    {
      "groupKey": "СЗФО",
      "totalQuantity": 4625546.376,
      "totalAmount": 1840055858.72,
      "salesCount": 1226
    },
    {
      "groupKey": "ЦФО",
      "totalQuantity": 19795487.629,
      "totalAmount": 6894117355.85,
      "salesCount": 3943
    },
    {
      "groupKey": "ПФО",
      "totalQuantity": 4880136.627,
      "totalAmount": 1931091573.18,
      "salesCount": 1284
    }
  ],
  "totalAmount": 14446397106.53,
  "totalQuantity": 38480803.059,
  "total": 5
}
```

### Sensor Parameters

**Endpoint:** `GET /production/sensor-parameters`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "sensorParameters": [
    {
      "id": "4c1ac2c5-2279-4588-ab90-475b2d820849",
      "name": "Влажность",
      "unit": "%ОВ",
      "createdAt": "2026-05-08T15:02:39.750Z"
    },
    {
      "id": "17dd513e-5fbf-481c-872c-6154f532faeb",
      "name": "Расход жидкости",
      "unit": "л/ч",
      "createdAt": "2026-05-08T15:02:39.747Z"
    },
    {
      "id": "cf2009c6-05db-4dbd-ac40-2a49867a98e9",
      "name": "Давление",
      "unit": "бар",
      "createdAt": "2026-05-08T15:02:39.744Z"
    },
    {
      "id": "42bef157-cd92-481e-b1aa-5dbcde1c9fcb",
      "name": "Температура",
      "unit": "°C",
      "createdAt": "2026-05-08T15:02:39.741Z"
    }
  ],
  "total": 4
}
```

### Sensors

**Endpoint:** `GET /production/sensors`

**Parameters:** `{"from": "2026-04-14", "to": "2026-05-14", "limit": 10}`

**Status:** 200

**Response:**

```json
{
  "readings": [
    {
      "id": "9f2fa327-0176-4190-b8cd-b545002af929",
      "sensorId": "7c8ff0d9-c542-4a0b-9add-9e0854be6127",
      "deviceId": "SENSOR-HOH_LINE_A-T03-РАСХ",
      "productionLineId": "49a5ba6f-3838-3d85-6310-cf1ec432864d",
      "sensorParameterId": "17dd513e-5fbf-481c-872c-6154f532faeb",
      "value": 2878.5683,
      "quality": "BAD",
      "recordedAt": "2026-05-05T12:59:00.000Z"
    },
    {
      "id": "ecc92ccc-1967-442d-b981-bb58a1dbf0f8",
      "sensorId": "0af26850-0ce1-447c-8bff-429e368b652b",
      "deviceId": "SENSOR-TAM_LINE_B-T01-РАСХ",
      "productionLineId": "1aebc8ae-4374-f95a-8ec9-b80f1375d3c6",
      "sensorParameterId": "17dd513e-5fbf-481c-872c-6154f532faeb",
      "value": 1794.8377,
      "quality": "BAD",
      "recordedAt": "2026-05-05T12:59:00.000Z"
    },
    {
      "id": "4643b3eb-aacc-44b2-a101-e8e4f6845aa1",
      "sensorId": "9c7a63f9-8ad8-4601-a272-2e72c780ead1",
      "deviceId": "SENSOR-TAM_LINE_B-T01-ВЛАЖ",
      "productionLineId": "1aebc8ae-4374-f95a-8ec9-b80f1375d3c6",
      "sensorParameterId": "4c1ac2c5-2279-4588-ab90-475b2d820849",
      "value": 60.4925,
      "quality": "GOOD",
      "recordedAt": "2026-05-05T12:59:00.000Z"
    },
    {
      "id": "6bb7ca44-43c5-47ad-83c8-6b8dcee0c0c1",
      "sensorId": "df8caa0c-62fb-496b-82fb-5c53644d581a",
      "deviceId": "SENSOR-NOG_LINE_A-T03-ТЕМП",
      "productionLineId": "a0a65c5f-bb95-e4a8-e1be-3b6dff660b2d",
      "sensorParameterId": "42bef157-cd92-481e-b1aa-5dbcde1c9fcb",
      "value": 92.0281,
      "quality": "DEGRADED",
      "recordedAt": "2026-05-05T12:58:00.000Z"
    },
    {
      "id": "56a4eecd-b404-48f8-a2b1-9cafca4da63c",
      "sensorId": "750dfc9d-1ac9-42b9-a5ad-f923b8dea5f7",
      "deviceId": "SENSOR-HOH_LINE_A-T01-ВЛАЖ",
      "productionLineId": "49a5ba6f-3838-3d85-6310-cf1ec432864d",
      "sensorParameterId": "4c1ac2c5-2279-4588-ab90-475b2d820849",
      "value": 68.1576,
      "quality": "GOOD",
      "recordedAt": "2026-05-05T12:56:00.000Z"
    },
    {
      "id": "7ea3776c-0aa2-4010-a128-84546c70f3e4",
      "sensorId": "8d86a184-fe3b-495b-b031-c408457b3c56",
      "deviceId": "SENSOR-HOH_LINE_A-T01-ДАВЛ",
      "productionLineId": "49a5ba6f-3838-3d85-6310-cf1ec432864d",
      "sensorParameterId": "cf2009c6-05db-4dbd-ac40-2a49867a98e9",
      "value": 3.4445,
      "quality": "GOOD",
      "recordedAt": "2026-05-05T12:55:00.000Z"
    },
    {
      "id": "fbd8d3b3-d10a-440c-8cdb-4903f22c37c8",
      "sensorId": "b1759c9c-f338-4b70-b156-7312255d1508",
      "deviceId": "SENSOR-TAM_LINE_B-T01-ТЕМП",
      "productionLineId": "1aebc8ae-4374-f95a-8ec9-b80f1375d3c6",
      "sensorParameterId": "42bef157-cd92-481e-b1aa-5dbcde1c9fcb",
      "value": 66.3199,
      "quality": "GOOD",
      "recordedAt": "2026-05-05T12:55:00.000Z"
    },
    {
      "id": "9f3cc7f2-3221-4fcf-8eac-0f27fe8a89ab",
      "sensorId": "c9a23a36-6d59-4863-b52d-884905c09a7b",
      "deviceId": "SENSOR-EKB_LINE_A-T01-ДАВЛ",
      "productionLineId": "596c3638-89d3-1d32-8529-8207984638e7",
      "sensorParameterId": "cf2009c6-05db-4dbd-ac40-2a49867a98e9",
      "value": 3.3991,
      "quality": "GOOD",
      "recordedAt": "2026-05-05T12:54:00.000Z"
    },
    {
      "id": "3b0a67b6-3c9f-4990-996e-425beccb2c7c",
      "sensorId": "f3137fec-ff4f-4409-877a-0e489f64c7cb",
      "deviceId": "SENSOR-TAM_LINE_B-T01-ДАВЛ",
      "productionLineId": "1aebc8ae-4374-f95a-8ec9-b80f1375d3c6",
      "sensorParameterId": "cf2009c6-05db-4dbd-ac40-2a49867a98e9",
      "value": 2.0003,
      "quality": "GOOD",
      "recordedAt": "2026-05-05T12:53:00.000Z"
    },
    {
      "id": "b94f7439-34c0-4655-b980-8bc6c18f3cc2",
      "sensorId": "5874a75a-fe33-4dd4-a3ff-d0c48c14c6a0",
      "deviceId": "SENSOR-TAM_LINE_B-T02-РАСХ",
      "productionLineId": "1aebc8ae-4374-f95a-8ec9-b80f1375d3c6",
      "sensorParameterId": "17dd513e-5fbf-481c-872c-6154f532faeb",
      "value": 5799.7263,
      "quality": "BAD",
      "recordedAt": "2026-05-05T12:53:00.000Z"
    }
  ],
  "total": 4224
}
```

### Shift Templates

**Endpoint:** `GET /personnel/shift-templates`

**Status:** 200

**Response:**

```json
{
  "templates": [
    {
      "id": "718a5af1-391d-47fd-adc2-db18ad55ab5f",
      "name": "Административный график 5/2",
      "shiftType": "day_shift",
      "startTime": "08:00",
      "endTime": "17:00",
      "workDaysPattern": "1111100"
    },
    {
      "id": "c8b6bbb8-1585-4ea7-b82c-288a95e89001",
      "name": "Вечерняя смена (14–22)",
      "shiftType": "day_shift",
      "startTime": "14:00",
      "endTime": "22:00",
      "workDaysPattern": "1111100"
    },
    {
      "id": "799b6991-1e13-49d8-b15e-17303183d752",
      "name": "Дневная смена (8–20)",
      "shiftType": "day_shift",
      "startTime": "08:00",
      "endTime": "20:00",
      "workDaysPattern": "1111100"
    },
    {
      "id": "16b0a164-aeb4-4e02-8168-0cdd03a793a9",
      "name": "Ночная смена (20–8)",
      "shiftType": "night_shift",
      "startTime": "20:00",
      "endTime": "08:00",
      "workDaysPattern": "1111100"
    },
    {
      "id": "0b5f0a92-9673-453a-9011-86800876d66e",
      "name": "Скользящий 2/2 (12ч)",
      "shiftType": "rotating",
      "startTime": "07:00",
      "endTime": "19:00",
      "workDaysPattern": "1100"
    },
    {
      "id": "85524ddf-b463-4944-b4b0-d8bac15a6837",
      "name": "Утренняя смена (6–14)",
      "shiftType": "day_shift",
      "startTime": "06:00",
      "endTime": "14:00",
      "workDaysPattern": "1111100"
    }
  ],
  "total": 6
}
```

### Units of Measure

**Endpoint:** `GET /production/units-of-measure`

**Status:** 200

**Response:**

```json
{
  "unitsOfMeasure": [
    {
      "id": "8a764a79-7604-4bab-bfd3-071558d8dd52",
      "code": "кг",
      "name": "кг",
      "createdAt": "2026-05-08T15:02:39.639Z"
    },
    {
      "id": "6f5741b4-57a4-46c8-a87e-abb29947aff6",
      "code": "л",
      "name": "л",
      "createdAt": "2026-05-08T15:02:39.652Z"
    },
    {
      "id": "4a76a6bb-10d1-45ba-9784-7580bbc624e4",
      "code": "шт",
      "name": "шт",
      "createdAt": "2026-05-08T15:02:39.649Z"
    }
  ],
  "total": 3
}
```

### Warehouses

**Endpoint:** `GET /production/warehouses`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "warehouses": [
    {
      "id": "20abf47f-3703-4ca2-ac58-6a6f4632a595",
      "name": "Архивный склад",
      "code": "WH-ARCH-01",
      "createdAt": "2026-05-08T15:02:39.775Z"
    },
    {
      "id": "9207ca29-caef-46a2-997f-5779ee8290f5",
      "name": "Экспортный склад",
      "code": "WH-EXP-01",
      "createdAt": "2026-05-08T15:02:39.772Z"
    },
    {
      "id": "4dec6b4e-33ea-436b-9208-08753da7d04c",
      "name": "Склад полуфабрикатов",
      "code": "WH-SF-01",
      "createdAt": "2026-05-08T15:02:39.769Z"
    },
    {
      "id": "fcc1e611-83b4-406f-aed0-c56075f0d689",
      "name": "Склад готовой продукции № 4",
      "code": "WH-FP-04",
      "createdAt": "2026-05-08T15:02:39.766Z"
    },
    {
      "id": "2624b3d0-d5f4-4c63-a520-0b65cf7a6803",
      "name": "Склад готовой продукции № 3",
      "code": "WH-FP-03",
      "createdAt": "2026-05-08T15:02:39.763Z"
    },
    {
      "id": "0d2acc44-bc74-4d84-9285-18fb9662810e",
      "name": "Склад готовой продукции № 2",
      "code": "WH-FP-02",
      "createdAt": "2026-05-08T15:02:39.760Z"
    },
    {
      "id": "3b14e92f-284a-4564-8e0c-b0004bff271a",
      "name": "Склад готовой продукции № 1",
      "code": "WH-FP-01",
      "createdAt": "2026-05-08T15:02:39.757Z"
    },
    {
      "id": "7d3695f2-6d9f-4300-8c69-f0bbe4ad40e4",
      "name": "Склад сырья № 1",
      "code": "WH-RAW-01",
      "createdAt": "2026-05-08T15:02:39.754Z"
    }
  ],
  "total": 8
}
```

### Workstations

**Endpoint:** `GET /personnel/workstations`

**Parameters:** `{"limit": 10}`

**Status:** 200

**Response:**

```json
{
  "workstations": [
    {
      "id": "13ee1dbf-4062-4729-b710-2378ee59eda7",
      "name": "Контрольный пост - Завод ТЗПМ",
      "code": "TAM_CTRL1",
      "locationId": "da976122-c6a5-4c18-8f06-a69085d5742f",
      "productionLineId": "4d1b5527-2315-0129-4000-409c8f901120",
      "workstationType": "control_point",
      "sourceSystemId": null
    },
    {
      "id": "80a06199-ae90-4bcd-aad1-6bb9875fe054",
      "name": "Лабораторный пост - Алматы",
      "code": "ALM_A_LAB1",
      "locationId": "3c79f1a0-0740-4a7b-a64d-2ddd9a0eb2a2",
      "productionLineId": "3d57ea5f-fcd5-3a77-24cb-7996f830f190",
      "workstationType": "lab_station",
      "sourceSystemId": null
    },
    {
      "id": "62a716c8-fa86-40cb-b5a0-d36336a701b7",
      "name": "Лабораторный пост - ЕЖК",
      "code": "EKB_A_LAB1",
      "locationId": "7a348077-d55b-4d5b-b1e3-9df6c2363b58",
      "productionLineId": "596c3638-89d3-1d32-8529-8207984638e7",
      "workstationType": "lab_station",
      "sourceSystemId": null
    },
    {
      "id": "aa843495-e952-4025-80c4-d6ecdc2edddc",
      "name": "Лабораторный пост - Линия А",
      "code": "TAM_A_LAB1",
      "locationId": "da976122-c6a5-4c18-8f06-a69085d5742f",
      "productionLineId": "4d1b5527-2315-0129-4000-409c8f901120",
      "workstationType": "lab_station",
      "sourceSystemId": null
    },
    {
      "id": "68edfe0a-2006-4c60-9059-e3188a0f591d",
      "name": "Пост оператора - Алматы",
      "code": "ALM_A_OP1",
      "locationId": "3c79f1a0-0740-4a7b-a64d-2ddd9a0eb2a2",
      "productionLineId": "3d57ea5f-fcd5-3a77-24cb-7996f830f190",
      "workstationType": "operator_post",
      "sourceSystemId": null
    },
    {
      "id": "339de44c-3245-41a0-adc7-80d2d68ea8d0",
      "name": "Пост оператора - Линия кетчуп/горчица",
      "code": "EKB_B_OP1",
      "locationId": "7a348077-d55b-4d5b-b1e3-9df6c2363b58",
      "productionLineId": "a25e7bc7-221e-1376-0bc0-f30299a83ff1",
      "workstationType": "operator_post",
      "sourceSystemId": null
    },
    {
      "id": "d8322012-94ed-4b2b-86e1-14980a584084",
      "name": "Пост оператора - Линия майонеза",
      "code": "NOG_A_OP1",
      "locationId": "76c4fc37-72b2-4b43-9360-a8ffd7267d06",
      "productionLineId": "a0a65c5f-bb95-e4a8-e1be-3b6dff660b2d",
      "workstationType": "operator_post",
      "sourceSystemId": null
    },
    {
      "id": "8e17ce4c-8362-49ec-8d61-96eb80099426",
      "name": "Пост оператора - Линия маргарина",
      "code": "HOH_A_OP1",
      "locationId": "011ec8c6-ff11-44ec-9d02-ce4610efb6f4",
      "productionLineId": "49a5ba6f-3838-3d85-6310-cf1ec432864d",
      "workstationType": "operator_post",
      "sourceSystemId": null
    },
    {
      "id": "704c3e6a-5847-4053-a332-cd746ab6dc39",
      "name": "Пост оператора - Линия мыла",
      "code": "HOH_B_OP1",
      "locationId": "011ec8c6-ff11-44ec-9d02-ce4610efb6f4",
      "productionLineId": "9330f683-f62b-5e4a-7877-6d2f13d19384",
      "workstationType": "operator_post",
      "sourceSystemId": null
    },
    {
      "id": "a6597edd-a1e5-4abd-a0ad-34496463e65f",
      "name": "Пост оператора 1 - Линия А (Рафинация)",
      "code": "TAM_A_OP1",
      "locationId": "da976122-c6a5-4c18-8f06-a69085d5742f",
      "productionLineId": "4d1b5527-2315-0129-4000-409c8f901120",
      "workstationType": "operator_post",
      "sourceSystemId": null
    }
  ],
  "total": 16
}
```

