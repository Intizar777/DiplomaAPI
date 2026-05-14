# OpenAPI Client Generation

This document describes how to generate typed frontend clients from the OpenAPI specification.

## Overview

The API contract is defined in OpenAPI format. Frontend applications should generate TypeScript/JavaScript clients from this contract rather than manually defining types.

## Prerequisites

```bash
pip install openapi-typescript-codegen httpx
# or
npm install -g openapi-typescript-codegen
```

## Export OpenAPI Spec

First, ensure the API is running, then export the spec:

```bash
# Option 1: Using the script
python scripts/export_openapi.py export --output docs/openapi.json

# Option 2: Direct curl
curl http://localhost:8000/openapi.json -o docs/openapi.json
```

## Generate TypeScript Client

### Using openapi-typescript-codegen

```bash
npx openapi-typescript-codegen \
  --input docs/openapi.json \
  --output src/api/client \
  --client axios
```

This generates:
- TypeScript types for all schemas
- Request/response types
- API client with typed methods

### Using orval (recommended for React Query/SWR)

```bash
npx orval \
  --input docs/openapi.json \
  --output src/api/orval.ts \
  --client axios
```

## Generated Client Usage

```typescript
import { DashboardApi } from '@/api/client';

// All types are auto-generated
const api = new DashboardApi();

const response = await api.getInventoryTrends({
  productId: 'uuid-here',
  from: '2026-01-01',
  to: '2026-05-13',
});

// response.data is fully typed
console.log(response.data.items);
```

## Contract Validation

Before generating client, validate the contract:

```bash
# Check contract has all required elements
python scripts/export_openapi.py check

# Detect breaking changes vs baseline
python scripts/export_openapi.py diff --baseline docs/openapi_baseline.json
```

## CI Integration

Add to your CI pipeline to catch contract drift:

```yaml
# .github/workflows/api-contract.yml
- name: Validate OpenAPI Contract
  run: |
    python scripts/export_openapi.py check
```

## Updating the Contract

When adding new endpoints:

1. Ensure `response_model` is defined on the route
2. Add example metadata to the schema
3. Run `python scripts/export_openapi.py check`
4. Regenerate client: `npx openapi-typescript-codegen ...`
5. Update baseline: `cp docs/openapi.json docs/openapi_baseline.json`

## Troubleshooting

**Missing response_model**: Ensure the route decorator has `response_model=YourSchema`

**No examples in generated client**: Add `json_schema_extra` with `example` to your Pydantic schemas

**Enum not generated**: Use Pydantic `Literal` or `Enum` types
