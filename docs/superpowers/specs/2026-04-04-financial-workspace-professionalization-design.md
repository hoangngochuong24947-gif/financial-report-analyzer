# Financial Workspace Professionalization Design

## Summary

This design upgrades the current archive-first A-share financial workspace from a polished demo into a publishable financial analysis system. The implementation keeps the existing React + FastAPI + archive-first backbone, preserves the current `metrics / models / insights` route model, and focuses on four targeted upgrades:

- promote the metrics page into a real single-company financial overview
- upgrade statement detail into a professional report-reading surface
- strengthen bilingual and async feedback across the core workflow
- automate archive acquisition so the workspace can be filled with Baidu Finance statement data continuously

The goal is not a visual redesign for its own sake. The goal is to make the system feel credible for real financial statement reading, metric review, model interpretation, and ongoing data preparation.

## Product Direction

### Primary Release Shape

The publishable product should prioritize a single-company analysis workflow while preserving extension points for a future multi-company research platform.

### Information Hierarchy

The primary user journey becomes:

1. select a company
2. inspect statement and reporting-period context
3. review statement previews and key metrics
4. drill into full financial statement detail
5. review model conclusions and sensitivity-oriented interpretation
6. generate or read AI-supported narrative

### Architectural Principle

Do not replace the current frontend shell or backend workspace contracts unless necessary. Reuse the current routes, typed API layer, and archive-first repository model, then reorganize page composition and detail rendering around a more professional financial-analysis flow.

## Frontend Design

### Reuse Strategy

Keep and extend:

- existing workspace pages under `frontend/src/pages`
- existing `workspace.ts` API wrappers
- existing lightweight route state in `frontend/src/lib/routing.ts`
- existing React Query usage

Refactor incrementally:

- add a real `App.tsx` shell assembly layer
- separate reusable table and feedback components from generic card helpers
- reduce over-reliance on decorative glass-card presentation
- promote statement and metric detail into first-class analytical surfaces

### Page Architecture

#### Overview Page

The current metrics page becomes the financial overview page. It should include:

- company identity and reporting context
- archive freshness and source status
- statement preview blocks for balance sheet, income statement, and cash flow
- key metric matrix grouped by analysis category
- expandable metric detail area
- links into full statement detail and model interpretation

#### Statement Detail Page

The statement detail page becomes a large-format financial report page with:

- reporting-period selector
- statement tab selector
- professional table rendering with grouping
- wider, scroll-safe layout
- side analysis notes and source metadata

This page should no longer feel like a simple key-value card dump.

#### Models Page

Keep the existing models page, but present it as a structured analysis layer rather than a parallel demo page. It remains the home for DuPont, trend, and sensitivity-adjacent interpretation.

#### Insights Page

Keep the insights page as an evidence-backed narrative page. It should expose:

- input context readiness
- generation status
- generated report sections
- highlights, risks, and actions

### Bilingual Strategy

Keep a lightweight in-repo translation system. Do not introduce a full external i18n framework in this phase.

Refactor copy into modular dictionaries for:

- navigation
- overview
- statements
- metrics
- models
- insights
- shared status text

Financial field labels should be handled separately from UI copy so statement rows and metric labels can remain consistent and maintainable.

### Async Feedback Strategy

Use the current React Query foundation and formalize four user-facing states:

- loading financial data
- analysis in progress
- report generation in progress
- crawl/archive refresh in progress

The interaction language should emphasize professional status feedback instead of decorative loading effects.

## Backend and Data Design

### Reuse Strategy

Keep the current workspace API model and archive-first repository flow. Add only what is necessary for:

- better statement detail rendering
- clearer task status exposure
- automated archive filling

### Statement Data

Continue using `/api/v2/workspace/{code}/statements` as the primary detail source. The frontend will transform this response into grouped analytical tables without requiring a backend rewrite.

### Async Report Generation

The current report generation endpoint remains valid for this phase. The frontend should treat it as a long-running action with status feedback rather than as a static page load.

### Auto-Crawl and Archive Fill

Single-stock crawl jobs should continue to exist, but the system also needs a batch-oriented archive preparation workflow for Baidu Finance data.

The implementation should add:

- a batch crawl runner
- resumable run-state persistence
- low-concurrency execution suitable for multi-day runs
- logging and per-stock status recording

## Crawler Automation Design

### Scope

Automate archive preparation for A-share financial statement data from Baidu Finance over multiple days. Reuse the existing Baidu crawler and archive repository rather than replacing it.

### Required Capabilities

- fetch or freeze the A-share stock universe
- process stocks in bounded batches
- store per-run and per-stock progress state
- retry failures without blocking the whole run
- support resume after interruption
- allow optional indicator scraping modes

### Recommended Execution Shape

Add a new batch script as the operational entry point. The script should:

1. collect the stock universe
2. create a run manifest
3. iterate through pending stocks
4. invoke the existing Baidu archive crawler per stock
5. persist status after every stock
6. allow later resume using the recorded run state

This keeps the automation practical without forcing a new distributed architecture.

## Publishability

### Frontend Release Readiness

The frontend release should include:

- a stable shell entrypoint
- clear route hierarchy
- modular copy and styles
- deterministic build output
- no dependence on hand-wired missing files

### Repository Hygiene

Clarify the difference between:

- source code
- generated API schema
- runtime logs
- build artifacts
- archive data

### Data Preparation

The release story must explicitly include archive preparation. A financial analysis frontend without prepared archives will not look or behave like a usable product.

## Risks

- Existing bilingual strings contain encoding issues.
  - Mitigation: rewrite frontend-facing copy and avoid depending on broken UI strings.
- The current frontend entrypoint is incomplete.
  - Mitigation: add a proper `App.tsx` and central shell composition.
- Batch crawling may be long-running and fragile.
  - Mitigation: keep concurrency low, persist state after each stock, and support resume.

## Deliverables for This Phase

- professionalized frontend shell and page composition
- stronger statement detail rendering
- bilingual cleanup for core UI
- async task feedback for data and report generation
- resumable Baidu Finance batch crawl automation
- design, plan, and progress documentation for continued development
