# API Contract Style Guide (v1 Compatibility)

## Error Envelope

All non-2xx responses MUST return:

- `error.code`: stable machine-readable code (`validation_error`, `internal_server_error`, `http_<status>`)
- `error.message`: human-readable message
- `error.details`: optional structured details (validation issues, field errors)
- `error.trace_id`: request correlation ID

Compatibility fields kept for `/api/v1` clients:

- `detail`: mirrors previous payload shape
- `trace_id`: top-level trace ID mirror

## Nullable and Optional

- Optional field: omitted only when not available and not needed by client flow.
- Nullable field: explicitly present with `null` when value is known to be missing.
- Do not mix omitted and nullable semantics for the same field across endpoints.

## Date/Time

- Use ISO-8601 only for all date/time values.
- `date` for calendar-only values; timezone-aware datetime where time precision is required.

## Backward Compatibility and Deprecation

- Additive changes are allowed in `/api/v1`.
- Breaking changes must go to `/api/v2`.
- Deprecated fields/params must remain available through agreed compatibility window and be marked deprecated in OpenAPI.

## Include/Expand Policy

- Default responses must stay slim and return only core fields.
- Optional related objects are returned only when client sends `include=...`.
- Supported includes (Phase 3):
  - `GET /api/v1/orders/list` and `GET /api/v1/orders/{order_id}`: `product`, `productionLine`
  - `GET /api/v1/inventory/current`: `product`
  - `GET /api/v1/products` and `GET /api/v1/products/{product_id}`: `inventorySummary`
  - `GET /api/production/kpi/breakdown`: `productionLine`, `product`

Roundtrip reduction reference for frontend screens:
- Orders screen:
  - before: list + product fetch + line fetch (3 requests)
  - after (`include=product,productionLine`): 1 request
- Product/inventory screen:
  - before: products + inventory summary (2 requests)
  - after (`include=inventorySummary`): 1 request
