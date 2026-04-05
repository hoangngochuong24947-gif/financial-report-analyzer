# 2026-04-04 Frontend and Crawler Progress

## Goal

Upgrade the project into a more professional financial analysis workspace while starting a resumable Baidu Finance archive-fill workflow.

## Confirmed Direction

- Reuse the existing archive-first backend and workspace APIs
- Reuse the current frontend pages instead of rebuilding the product from scratch
- Make the release feel like a real financial report analysis system
- Prioritize single-company analysis while keeping room for a future research-platform view
- Add batch crawler automation and begin storing Baidu Finance archive data

## Current Findings

- The frontend foundation is usable but incomplete:
  - page components already exist
  - workspace API wrappers already exist
  - route state already exists
  - `frontend/src/main.tsx` references an `App` component that is currently missing
- Core bilingual UI copy exists but includes encoding issues
- Statement detail exists but is still too close to card-style preview rendering
- The backend archive-first model and workspace routes are already suitable for incremental enhancement
- Single-stock Baidu archive crawling already exists
- Full-universe resumable batch crawling does not yet exist

## Implementation Progress

### Documentation

- [x] Design document written
- [x] Implementation plan written
- [x] Progress log initialized

### Frontend

- [x] Add and wire `App.tsx`
- [x] Upgrade overview composition
- [x] Upgrade statement detail rendering
- [x] Clean bilingual copy
- [x] Add crawl/report async feedback

### Crawler Automation

- [x] Add run-state persistence
- [x] Add batch crawl script
- [x] Force archive-refresh jobs onto Baidu archive flow
- [x] Start low-concurrency batch run

## Completed Today

- Added a real frontend entry shell in `frontend/src/App.tsx` and connected stock selection, route tabs, bilingual switching, and crawler state feedback.
- Reworked the overview page into a statement-first financial workspace using the existing archive-first API surface.
- Rebuilt statement detail into a larger report-reading surface with period switching and grouped table rendering.
- Cleaned the core bilingual dictionary and fixed visible mojibake in the main financial workspace UI.
- Added `src/storage/crawl_run_repository.py` for resumable filesystem-backed batch crawl state.
- Added `scripts/crawl_baidu_finance_batch.py` and patched `src/crawler/jobs.py` so refresh jobs use the Baidu archive provider.
- Hardened stock-universe fetching by preferring exchange-specific AKShare code lists instead of falling back to a tiny built-in sample.
- Verified the frontend with `npm run build`.
- Verified crawler-related Python files with `python -m py_compile`.

## Active Run

- Run ID: `full-a-share-20260404T131500Z`
- Run state: `data/runs/baidu_finance/full-a-share-20260404T131500Z/state.json`
- Stdout log: `data/runs/baidu_finance/full-a-share-20260404T131500Z/stdout.log`
- Stderr log: `data/runs/baidu_finance/full-a-share-20260404T131500Z/stderr.log`
- Current snapshot at 2026-04-04 13:26 CST:
  - total stocks: `4891`
  - success: `2`
  - running: `1`
  - pending: `4888`
  - failed: `0`
  - skipped: `0`

## Verification Notes

- `frontend/npm run build`: passed
- `python -m py_compile src/storage/crawl_run_repository.py scripts/crawl_baidu_finance_batch.py src/crawler/jobs.py`: passed
- Smoke batch runner test: passed
- Full-universe run: started successfully and is processing stocks sequentially

## Risks

- Existing backend Chinese display labels may still contain mojibake in non-workspace paths
- Full-universe crawling may take multiple days and must be resumable
- Indicator scraping is the slowest part of the Baidu workflow
- Redis is unavailable locally, so short-lived stock-list caching still relies on in-process execution

## Active Decisions

- Prefer incremental enhancement over large-scale rewrite
- Keep the current route model
- Prefer filesystem-backed crawl run state for this phase
- Start archive fill with low concurrency
- Use exchange-specific stock lists as the primary full-universe source

## Next Actions

1. Continue monitoring `full-a-share-20260404T131500Z` and restart with `--resume` if interrupted
2. Add a small release-facing note in the frontend about archive freshness and crawl status
3. Consider local file caching for the stock universe when Redis is unavailable
4. Add a dedicated metric-detail route when the next frontend iteration starts
