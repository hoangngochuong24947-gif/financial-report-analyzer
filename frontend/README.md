# Frontend Workspace

## Run app

```bash
cd frontend
npm install
npm run gen:api
npm run dev
```

Default URL: `http://localhost:5173`

## Generate typed SDK from backend OpenAPI

```bash
cd frontend
npm install
npm run gen:api
```

Generated output:

- `openapi/openapi.json`
- `src/api/generated/schema.ts`

Business-level API wrappers:

- `src/api/client.ts`
- `src/api/sdk.ts`

Optional env:

- `VITE_API_BASE_URL` (default: `http://localhost:8000`)
- `VITE_API_BASE_URL` (default: `http://127.0.0.1:8000`)
