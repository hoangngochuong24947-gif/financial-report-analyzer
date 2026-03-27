# Frontend OpenAPI Notes

`openapi.json` is generated from the backend FastAPI app via:

```bash
cd frontend
npm run gen:openapi
```

This snapshot currently reflects the backend-exported routes only. The workspace API helpers in `src/api/workspace.ts` are a temporary typed shim for the expected future `/api/workspaces/...` endpoints until the backend OpenAPI document includes them.
