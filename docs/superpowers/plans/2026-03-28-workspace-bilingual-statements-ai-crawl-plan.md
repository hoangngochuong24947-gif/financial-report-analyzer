# Workspace Bilingual, Statement Detail, AI Insight, and Auto-Crawl Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bilingual workspace shell, a tabbed financial statement detail experience, first-pass AI insight generation backed by the configured model, and automatic crawler fallback when a selected stock lacks archive-backed workspace data.

**Architecture:** Extend the current archive-first workspace stack instead of replacing it. Add small, focused backend endpoints for statement detail and insight generation, then wire the frontend shell to locale state, child routes, and auto-crawl orchestration. Keep metrics, models, and insight evidence as the shared substrate so analysis logic does not fork.

**Tech Stack:** FastAPI, pydantic v2, existing workspace service/repository modules, React + TypeScript frontend, TanStack Query, existing crawler job endpoints, existing LLM engine integration.

---

## Chunk 1: Backend Contracts and Tests

### Task 1: Add failing backend tests for localized statement detail

**Files:**
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/tests/test_workspace_api.py`
- Test: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/tests/test_workspace_api.py`

- [ ] **Step 1: Write failing tests for `GET /api/v2/workspace/{code}/statements`**
- [ ] **Step 2: Run `poetry run pytest tests/test_workspace_api.py -q` and verify the new tests fail for missing endpoint or shape mismatch**
- [ ] **Step 3: Implement the minimal response contract in the backend**
- [ ] **Step 4: Run `poetry run pytest tests/test_workspace_api.py -q` and verify the statement endpoint tests pass**

### Task 2: Add failing backend tests for insight generation endpoint

**Files:**
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/tests/test_workspace_api.py`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/tests/test_workspace_metric_fallbacks.py`

- [ ] **Step 1: Write failing tests for `POST /api/v2/workspace/{code}/insights/generate` covering shape, lang propagation, and fallback parsing**
- [ ] **Step 2: Run `poetry run pytest tests/test_workspace_api.py tests/test_workspace_metric_fallbacks.py -q` and confirm the tests fail for the intended reason**
- [ ] **Step 3: Implement the minimal generation flow and parser normalization**
- [ ] **Step 4: Re-run `poetry run pytest tests/test_workspace_api.py tests/test_workspace_metric_fallbacks.py -q` and verify green**

### Task 3: Implement backend statement detail and AI generation support

**Files:**
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/src/api/routes_workspace.py`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/src/api/workspace_service.py`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/src/storage/workspace_repository.py`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/src/llm_engine/` (relevant existing provider integration file)

- [ ] **Step 1: Add service and repository helpers to expose statement rows grouped by statement type and period**
- [ ] **Step 2: Add localized display labels with a simple `lang`-aware mapping layer**
- [ ] **Step 3: Add the new statements route and response models**
- [ ] **Step 4: Add the insight generation route that composes snapshot, metrics, models, and insight context into a provider request**
- [ ] **Step 5: Normalize provider output into fixed report fields and evidence list**
- [ ] **Step 6: Run `poetry run pytest tests/test_workspace_api.py tests/test_workspace_metric_fallbacks.py -q`**

## Chunk 2: Frontend Locale and Routing

### Task 4: Add failing frontend tests or route assertions for locale-aware shell and statement detail route

**Files:**
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/lib/routing.ts`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/App.tsx`
- Test: existing frontend test location if present; otherwise add lightweight route helpers only

- [ ] **Step 1: Add route and translation-key expectations for a statement detail child route under metrics**
- [ ] **Step 2: If automated frontend tests do not exist, at minimum add type-safe route helpers and use compile checks as the red/green loop**
- [ ] **Step 3: Run `npm run build` in `frontend` and confirm failure if route usage is incomplete**
- [ ] **Step 4: Implement the minimal route and locale plumbing to restore a passing build**

### Task 5: Implement global bilingual shell support

**Files:**
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/App.tsx`
- Add: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/i18n/messages.ts`
- Add or Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/lib/locale.ts`

- [ ] **Step 1: Add a small locale store with `zh-CN` and `en-US`**
- [ ] **Step 2: Move shell copy, nav labels, and key workspace labels into translation dictionaries**
- [ ] **Step 3: Add a visible language switch in the app shell**
- [ ] **Step 4: Propagate `lang` to relevant workspace API calls**
- [ ] **Step 5: Run `npm run build` in `frontend`**

### Task 6: Implement statement detail route and tabbed page

**Files:**
- Add: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/pages/StatementDetailPage.tsx`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/pages/MetricsPage.tsx`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/api/workspace.ts`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/lib/routing.ts`

- [ ] **Step 1: Add a typed API client for the new statements endpoint**
- [ ] **Step 2: Add a metrics-page entry point to the statement detail view**
- [ ] **Step 3: Build a single statement detail page with three tabs**
- [ ] **Step 4: Render localized labels and formatted values**
- [ ] **Step 5: Run `npm run build` in `frontend`**

## Chunk 3: Auto-Crawl Selection Flow and Insights UI

### Task 7: Implement automatic crawl orchestration for missing workspaces

**Files:**
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/App.tsx`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/api/workspace.ts`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/api/crawler.ts`

- [ ] **Step 1: Detect missing-workspace state during selection or direct code entry**
- [ ] **Step 2: Automatically create a crawler job instead of waiting for a manual button click**
- [ ] **Step 3: Add visible staged status UI for crawling, processing, success, and failure**
- [ ] **Step 4: On success, invalidate snapshot, metrics, models, statements, and insights queries**
- [ ] **Step 5: Preserve a manual refresh control for re-crawl use cases**
- [ ] **Step 6: Run `npm run build` in `frontend`**

### Task 8: Implement first-pass insight generation UI

**Files:**
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/pages/InsightsPage.tsx`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/api/workspace.ts`

- [ ] **Step 1: Add a typed client for `POST /insights/generate`**
- [ ] **Step 2: Add a generate action and loading/error states to the insights page**
- [ ] **Step 3: Render the structured report sections and evidence references**
- [ ] **Step 4: Make generation language follow the selected locale**
- [ ] **Step 5: Run `npm run build` in `frontend`**

## Chunk 4: Integrated Verification

### Task 9: Backend regression verification

**Files:**
- Verify only

- [ ] **Step 1: Run `poetry run pytest tests/test_precision.py tests/test_workspace_metric_fallbacks.py tests/test_workspace_repository.py tests/test_workspace_api.py -q`**
- [ ] **Step 2: Confirm all targeted backend tests pass and record any warnings**

### Task 10: Frontend verification

**Files:**
- Verify only

- [ ] **Step 1: Run `npm run build` in `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend`**
- [ ] **Step 2: Confirm the production build succeeds**

### Task 11: Playwright end-to-end verification

**Files:**
- Verify only

- [ ] **Step 1: Start local backend and frontend if needed**
- [ ] **Step 2: Use Playwright to verify language switching**
- [ ] **Step 3: Use Playwright to verify statement detail tab navigation**
- [ ] **Step 4: Use Playwright to verify archived selection and auto-crawl fallback behavior**
- [ ] **Step 5: Use Playwright to verify first-pass insight generation UI flow**
- [ ] **Step 6: Record any residual UX or latency issues for follow-up**
