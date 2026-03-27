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
- `workspace.ts`: typed shim for the upcoming workspace API surface
- `generated/schema.ts`: generated type definitions (do not hand-edit)

## Environment

- `VITE_API_BASE_URL` (optional)
  - default: `http://localhost:8000`
  - example: `VITE_API_BASE_URL=http://127.0.0.1:8000`

## Notes

- `npm run gen:api` refreshes the backend-exported OpenAPI schema and generated types only.
- Workspace snapshot, metric, model, and AI insight helpers are currently handwritten in `workspace.ts` and point at the expected future `/api/workspaces/...` paths.
- Once the backend exports those routes, regenerate `frontend/openapi/openapi.json` and `frontend/src/api/generated/schema.ts`, then migrate the shim to generated types if desired.
