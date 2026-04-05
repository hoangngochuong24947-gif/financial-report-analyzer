# Financial Workspace Professionalization Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the current archive-first financial workspace into a more professional, publishable system without replacing the existing backend and frontend foundations.

**Architecture:** Reuse the current workspace routes, React Query API layer, and archive-first backend contracts. Add a proper frontend shell entrypoint, strengthen overview and statement detail composition, clean up core bilingual copy, and introduce a resumable Baidu Finance batch crawl runner that continuously fills archive data.

**Tech Stack:** FastAPI, existing workspace APIs, React 18, TypeScript, TanStack Query, Vite, filesystem archive storage, Python CLI automation.

---

## Chunk 1: Documentation and Scope Lock

### Task 1: Persist design, plan, and progress records

**Files:**
- Create: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/docs/superpowers/specs/2026-04-04-financial-workspace-professionalization-design.md`
- Create: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/docs/superpowers/plans/2026-04-04-financial-workspace-professionalization-plan.md`
- Create: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/docs/progress/2026-04-04-frontend-crawler-progress.md`

- [x] Write the approved design summary and reuse strategy
- [x] Record the execution plan and phase boundaries
- [x] Start a progress log for implementation and verification

## Chunk 2: Frontend Shell and Overview Upgrade

### Task 2: Add the missing app shell entrypoint

**Files:**
- Create: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/App.tsx`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/main.tsx`

- [x] Build a workspace shell that wires stock selection, route tabs, and page rendering
- [x] Add global language switching and selection state
- [x] Add crawler status awareness for missing archives

### Task 3: Upgrade overview composition without replacing existing page foundations

**Files:**
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/pages/MetricsPage.tsx`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/components/DataBlocks.tsx`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/lib/finance.ts`

- [x] Reorganize the metrics page into statement preview, metric matrix, and metric detail sections
- [x] Add larger professional metric tables rather than summary-only cards
- [x] Preserve current API usage and data contracts

## Chunk 3: Statement Detail Professionalization

### Task 4: Turn statement detail into a report-reading surface

**Files:**
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/pages/StatementDetailPage.tsx`
- Add: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/components/FinancialStatementTable.tsx`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/api/workspace.ts`

- [x] Use the existing statement detail endpoint more directly
- [x] Add period switching, grouped rows, and large-table rendering
- [x] Add source and metadata presentation suitable for analytical use

## Chunk 4: Bilingual and Async Feedback Cleanup

### Task 5: Clean and modularize core UI copy

**Files:**
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/lib/i18n.ts`

- [x] Replace broken or incomplete frontend-facing bilingual strings
- [x] Ensure navigation, page titles, buttons, and status copy are covered

### Task 6: Add explicit async feedback for data, reports, and crawl status

**Files:**
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/App.tsx`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/pages/InsightsPage.tsx`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/frontend/src/styles.css`

- [x] Add crawler task status feedback
- [x] Add report-generation progress and refresh messaging
- [x] Keep motion restrained and professional

## Chunk 5: Baidu Finance Batch Crawl Automation

### Task 7: Add resumable batch crawl execution

**Files:**
- Create: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/scripts/crawl_baidu_finance_batch.py`
- Create: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/src/storage/crawl_run_repository.py`
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/src/crawler/jobs.py`

- [x] Add run-state persistence for multi-day crawl runs
- [x] Add a batch runner that reuses the existing Baidu archive crawler
- [x] Ensure crawl jobs explicitly target Baidu archive refresh behavior

### Task 8: Start the archive fill run

**Files:**
- Verify and execute only

- [x] Launch the batch crawl with low concurrency and persisted logs
- [x] Record the run identifier and log locations in the progress document

## Chunk 6: Verification

### Task 9: Frontend verification

**Files:**
- Verify only

- [x] Run `npm run build` in `frontend`
- [x] Confirm the workspace shell compiles successfully

### Task 10: Backend and crawler verification

**Files:**
- Verify only

- [x] Run targeted Python syntax or lightweight validation for new automation files
- [x] Verify the batch runner can initialize a run and process at least one stock

### Task 11: Progress update

**Files:**
- Modify: `C:/Users/30847/Desktop/antigravity/financial-report-analyzer/docs/progress/2026-04-04-frontend-crawler-progress.md`

- [x] Record completed work
- [x] Record active crawl status
- [x] Record remaining follow-ups
