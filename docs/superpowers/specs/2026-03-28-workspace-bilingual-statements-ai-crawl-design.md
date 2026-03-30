# Workspace Bilingual, Statement Detail, AI Insight, and Auto-Crawl Design

## Summary

This design extends the archive-first workspace experience without changing its overall three-page information architecture. The implementation keeps `/metrics`, `/models`, and `/insights` as the primary routes, adds a statement-detail experience inside the metrics area, introduces a bilingual UI switch, wires the insights page to a real LLM generation endpoint, and upgrades stock selection so a missing archive automatically triggers a crawler job and continues into analysis when the job succeeds.

The goal of this phase is not to perfect the analysis narrative quality. The goal is to make the product operational end to end: a user can switch language, inspect the three financial statements in detail, trigger archive acquisition implicitly through the normal selection flow, and obtain a first-pass AI analysis generated from the unified snapshot, metrics, and model results.

## Product Scope

### In Scope

- Global Chinese and English language switch in the frontend shell
- Locale-aware labels for navigation, page chrome, metric categories, and statement detail labels
- A unified statement detail page under the metrics area with tabs for:
  - balance sheet
  - income statement
  - cash flow statement
- Automatic crawler orchestration when the selected stock does not have an archive-backed workspace yet
- A first-pass LLM-backed insights generation endpoint and frontend flow
- Preservation of the existing archive-first data contract for snapshot, metrics, and models

### Out of Scope

- Replacing the current three-page workspace architecture
- Deep prompt editing UI or profile management UI
- A fully polished multilingual translation system for every historical message or backend error
- Reworking the crawler into a separate product workflow
- Final-quality investment research writing; this phase only guarantees a real model call with stable structure

## Recommended Approach

Use the current workspace shell as the primary integration surface and add the new capabilities as composable extensions:

1. Keep the archive-first backend as the truth source.
2. Add a locale layer instead of duplicating pages.
3. Add a statement detail endpoint tailored for frontend rendering.
4. Treat automatic crawling as a precondition-recovery step in stock selection rather than as a separate user flow.
5. Treat AI generation as a second-stage action on top of snapshot + metrics + models, not as a new analytics pipeline.

This approach minimizes disruption, preserves current fast paths, and keeps the new features aligned with the normalized snapshot architecture.

## Architecture

### Frontend

The frontend remains a single workspace shell with route-driven content. A global locale store will control UI copy, API request language parameters, and insights generation language. The metrics page will expose a statement-detail entry that routes to a child metrics path dedicated to the statement explorer. The statement explorer will render one shared page with three tabs rather than three separate pages.

The selected stock workflow becomes:

1. User enters or selects a code.
2. Frontend checks whether archive-backed workspace data exists.
3. If yes, proceed normally.
4. If no, create crawler job automatically.
5. Poll job status with a bounded retry strategy and visible status UI.
6. On success, invalidate and refetch workspace queries.
7. On failure, show explicit failure state and offer retry.

The insights page becomes a dual-mode page:

- context mode for loading evidence inputs
- generation mode for requesting the model output and rendering the structured report

### Backend

The backend continues to read from the normalized archive-backed workspace repository by default. New endpoints will be additive:

- statement detail endpoint for rendering the three statements
- AI generation endpoint that consumes existing workspace-derived evidence and calls the configured LLM

The crawler endpoints remain available, but frontend orchestration becomes more automatic. No primary analysis endpoint should depend on live crawling to serve already archived data.

## Public Interfaces

### Statement Detail Response

Add a dedicated endpoint:

- `GET /api/v2/workspace/{code}/statements`

Query parameters:

- `period`
- `lang`

Response shape:

- `company`
- `available_periods`
- `selected_period`
- `tabs`
- `updated_at`

Each tab contains:

- `key`
- `title`
- `rows`

Each row contains:

- `key`
- `label`
- `value`
- `display_value`
- `unit`
- `source`
- `is_estimated`

This contract lets the frontend render detail tables without reconstructing statement rows from snapshot fragments.

#### Period Selection Rules

- If `period` is omitted, the backend selects the latest period that exists in any statement set and returns it as `selected_period`.
- If `period` is provided and exists in at least one of the three statement sets, the backend returns that period and allows tabs with missing coverage to render an empty-state row set.
- If `period` is provided and exists in none of the statement sets, the endpoint returns `404`.
- `available_periods` is the union of all statement periods in descending order.
- Each tab is allowed to have different row availability for the same selected period; the frontend must not assume perfect cross-statement symmetry.

### AI Insight Generation

Add a generation endpoint:

- `POST /api/v2/workspace/{code}/insights/generate`

Input:

- `period`
- `lang`
- optional `force_refresh`

Output:

- `summary`
- `highlights`
- `risks`
- `open_questions`
- `actions`
- `evidence`
- `generated_at`
- `model_version`

The endpoint uses:

- snapshot
- metric result set
- model result cards
- prompt profile
- injection bundle

The model output must be normalized into this fixed structure even when the LLM response is imperfect.

#### Legacy AI Route Compatibility

- The existing legacy AI-report route remains untouched in this phase.
- The new workspace-scoped generation endpoint is the only endpoint used by the workspace frontend.
- Shared prompt-building and parsing utilities should be reused where practical, but the new endpoint owns the fixed structured response required by the workspace UI.

### Locale Handling

Existing read endpoints that provide user-facing labels should accept optional `lang`. The first phase only needs to guarantee correct localization for:

- shell text supplied by frontend dictionaries
- metric catalog labels and descriptions
- statement row labels
- grouped metric labels and notes where display text is returned by backend
- model card labels and summaries
- insight context display text used by the insights page
- AI insight output language

To keep implementation bounded, the following workspace endpoints should accept optional `lang` in phase one:

- `GET /api/v2/workspace/{code}/snapshot`
- `GET /api/v2/workspace/{code}/statements`
- `GET /api/v2/workspace/{code}/metrics/catalog`
- `GET /api/v2/workspace/{code}/metrics`
- `GET /api/v2/workspace/{code}/models`
- `GET /api/v2/workspace/{code}/insights/context`
- `POST /api/v2/workspace/{code}/insights/generate`

Localization only applies to backend-supplied display text. Numeric values, keys, and structural identifiers remain locale-neutral.

## Data Flow

### Archive-First Selection Flow

1. Frontend requests workspace presence or tries loading snapshot.
2. Missing workspace state triggers crawler job creation.
3. Frontend polls crawler status.
4. Completed crawler refresh persists raw archive and normalized workspace data.
5. Frontend refetches snapshot, metrics, models, and insight context.

### Insight Generation Flow

1. Frontend loads snapshot, metrics, models, and insight context.
2. Frontend calls insights generation endpoint with selected period and locale.
3. Backend builds prompt inputs from existing workspace evidence.
4. Backend calls the configured LLM provider.
5. Backend normalizes output into fixed report structure.
6. Frontend renders the result with evidence references.

## Error Handling

### Auto-Crawl

- Missing workspace must not silently degrade to zero-filled analysis.
- Polling must time out with a clear error state.
- Failed jobs must preserve a retry path.
- Existing archived data must remain usable even if a refresh attempt fails.

### AI Generation

- If context loads but LLM generation fails, the page should show evidence and an explicit generation error.
- The generation endpoint should return partial diagnostic metadata without exposing raw provider secrets.
- Invalid or malformed model output must be normalized into a safe fallback structure rather than crashing the page.

### Localization

- Unsupported locale falls back to Chinese defaults.
- Missing translations fall back to the base label instead of blank strings.

## Testing Strategy

### Backend

- Statement detail endpoint tests:
  - available periods
  - correct tab grouping
  - localized labels
  - missing-statement degradation behavior
- Insight generation endpoint tests:
  - stable response shape
  - language propagation
  - malformed provider response normalization
  - evidence references present
- Auto-crawl orchestration support tests:
  - workspace-missing detection path
  - crawler success path
  - crawler failure path

### Frontend

- Language switch updates shell text and page-level labels
- Metrics page statement entry opens detail route
- Statement detail tabs switch correctly
- Missing archive selection triggers crawl automatically
- Crawl success refills the workspace views
- Crawl failure shows explicit retry state
- Insights page can request and render generated content

### End-to-End

Use Playwright to validate:

- language switching
- stock selection with archived workspace
- stock selection without workspace that auto-triggers crawl
- statement detail tab navigation
- first-pass AI generation request and render

## Risks and Mitigations

- Risk: localization reaches too deeply into backend schemas.
  - Mitigation: localize only display-facing labels in phase one.
- Risk: auto-crawl polling creates a slow or confusing first-load experience.
  - Mitigation: show explicit staged status and keep archive-first fast path unchanged.
- Risk: LLM output is unstable.
  - Mitigation: use fixed prompt structure, normalized parser, and response fallback.

## Implementation Notes

- Preserve current workspace route and query structure where possible.
- Keep AI generation as an additive endpoint, not a replacement for context retrieval.
- Prefer a small frontend locale dictionary and explicit translation keys over scattered inline conditionals.
- Prefer one statement detail route with tabs over three near-duplicate pages.
