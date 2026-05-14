# API Contract Modernization Plan

## Goal

Bring the current API to a predictable, frontend-oriented contract model without breaking existing clients.

## Scope

- All public read endpoints in `app/routers/*`
- Shared schemas in `app/schemas/*`
- Error handling in `app/main.py` and route-level HTTP errors
- OpenAPI quality and generated frontend typed client flow

## Principles Mapped to Work

1. Frontend use-case first responses (`include`/`expand`, enriched DTOs)
2. Contract stability (no silent breaking changes)
3. No magic values (enums/codes with explicit meaning)
4. Machine-readable errors
5. Predictable list behavior (filter/sort/pagination consistency)
6. Cursor pagination for event-like feeds
7. Versioning discipline (`/api/v1` compatibility, v2 path for hard breaks)
8. Explicit nullable policy
9. Self-descriptive OpenAPI (examples, enums, errors, required/nullable)
10. ISO-8601 dates only

## Current Gaps (From Code Review)

- Mixed error shapes: `detail` and `trace_id` are inconsistent across handlers/routes.
- Mixed pagination models: `page/limit` and `offset/limit` both used.
- Some endpoints return raw dicts without explicit `response_model`.
- Direct DB query exists in route layer (`/api/production/production-lines`), violating service-only business logic rule.
- `include`/`expand` support is mostly absent.
- Nullable/optional policy is not formalized and can drift endpoint-by-endpoint.

## Phased Plan

### Phase 1: Contract Foundation (No Breaking Changes)

Tasks:
- Define API style guide in `docs/`:
  - naming conventions
  - nullable/optional rules
  - date/time format rules (ISO-8601)
  - deprecation policy and backward compatibility window
- Introduce unified error envelope schema:
  - `error.code`
  - `error.message`
  - `error.details`
  - `error.trace_id`
- Update global exception handlers to emit the same shape for 4xx/5xx.
- Add shared error schema(s) in `app/schemas/common.py` using `ConfigDict`.

Done criteria:
- Every non-2xx response in OpenAPI references the unified error schema.
- Existing clients continue to work (compatibility fields kept where needed).

### Phase 2: Unified List Contract

Tasks:
- Standardize list query params for v1 list endpoints:
  - `page`, `limit`, `sort`, `order`, `filter[...]` (or agreed equivalent)
- Standardize list response shape:
  - `items`
  - `meta` (`total`, `page`, `limit`, `pages`)
- Add/normalize `response_model` for all list endpoints.
- Remove ad-hoc list shapes like `{"items": ..., "count": ...}` where inconsistent.

Done criteria:
- Orders/Sales/Products/Inventory/Quality/Sensors/Output list endpoints share one list contract pattern.
- Frontend can use one adapter for all list screens.

### Phase 3: Frontend Use-Case DTO + Include/Expand

Tasks:
- Add `include` support for high-usage screens:
  - orders list/detail
  - products/inventory views
  - production analytics drilldowns
- Return enriched nested objects where this reduces frontend waterfall:
  - e.g. product summary object instead of only `product_id`
  - production line summary object instead of only line id/code when requested
- Keep default payload slim; add included data only when requested.

Done criteria:
- For target screens, frontend roundtrips are reduced (document before/after count).
- Include behavior is documented and tested.

### Phase 4: Cursor Pagination for Event-Like Data

Tasks:
- Introduce cursor pagination for mutable, append-heavy feeds:
  - downtime events
  - batch inputs
  - sensor history/alerts
  - sync logs/running tasks if applicable
- Response shape:
  - `items`
  - `next_cursor`
  - `has_more`
- Keep offset/page endpoints for compatibility, mark as deprecated where needed.

Done criteria:
- Infinite scroll/event screens can use cursor flow without duplicates/skips caused by offset drift.

### Phase 5: OpenAPI as Source of Truth

Tasks:
- Ensure each endpoint has:
  - accurate `response_model`
  - enum values
  - nullable/required clarity
  - example requests/responses
  - documented error codes
- Add OpenAPI contract checks in CI:
  - detect breaking changes
  - fail build on undocumented response shape drift
- Regenerate typed frontend client from OpenAPI and document usage.

Done criteria:
- Frontend types are generated from spec, not duplicated manually.
- Contract drift is caught in CI before release.

### Phase 6: Architecture Cleanup (Rule Compliance)

Tasks:
- Move route-level SQL from `app/routers/production_analytics.py` into a service.
- Audit routers for business-logic leakage and keep DB access in services only.
- Add unit tests for moved logic and integration tests for unchanged behavior.

Done criteria:
- Router layer is orchestration-only (validation + service call + mapping).
- Service-layer test coverage expanded for moved logic.

## Rollout Strategy (Safe Migration)

1. Add new contract fields/shapes in backward-compatible mode.
2. Mark legacy fields/params as deprecated in OpenAPI docs.
3. Migrate frontend to generated typed client and new contract.
4. Remove deprecated legacy only after agreed compatibility window.

## Suggested Work Packages (PR Sequence)

1. PR-1: Unified error envelope + shared schemas + handler updates + tests
2. PR-2: List contract normalization for Orders/Products/Inventory
3. PR-3: List contract normalization for Sales/Quality/Sensors/Output
4. PR-4: `include` support + enriched DTO for Orders and Inventory
5. PR-5: Cursor pagination for Downtime Events and Sensor History
6. PR-6: OpenAPI enrichment + CI contract checks + typed client pipeline
7. PR-7: Route-to-service cleanup for production lines endpoint

## Testing Requirements Per Phase

- Unit tests for service logic updates
- Integration tests for endpoint contracts
- Snapshot/assertion tests for error payload shape
- OpenAPI schema regression checks
- Frontend smoke test against generated client (at least one key screen per domain)

## Risks and Controls

- Risk: breaking existing frontend contract
  - Control: compatibility-first rollout + deprecation window
- Risk: inconsistent implementation across domains
  - Control: shared schema helpers + review checklist
- Risk: pagination migration complexity
  - Control: cursor introduced first on selected event endpoints, expand after validation

## Definition of Done for This Program

- Unified machine-readable errors across all endpoints
- Standardized list contracts for all read domains
- Include/expand implemented on key frontend use-cases
- Cursor pagination available for event-like data
- OpenAPI fully expressive and used for client generation
- No router-level business queries; service-layer pattern enforced
