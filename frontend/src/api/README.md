# Frontend API SDK

## One-command generation

```bash
cd frontend
npm install
npm run gen:api
```

This command chain does:

1. `python ../scripts/export_openapi.py --output ./openapi/openapi.json`
2. `openapi-typescript ./openapi/openapi.json --output ./src/api/generated/schema.ts`

## Files

- `client.ts`: typed API client setup via `openapi-fetch`
- `sdk.ts`: project-level API wrappers for v2 crawler + v1 analysis endpoints
- `generated/schema.ts`: generated type definitions (do not hand-edit)

## Environment

- `VITE_API_BASE_URL` (optional)
  - default: `http://localhost:8000`
  - example: `VITE_API_BASE_URL=http://127.0.0.1:8000`
