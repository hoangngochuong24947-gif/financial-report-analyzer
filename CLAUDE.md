# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an A-Share (A股) financial report analyzer for Chinese listed companies. It fetches financial statements (balance sheet, income statement, cash flow), calculates financial ratios, performs DuPont analysis, and generates AI-powered reports.

## Tech Stack

- **Backend**: FastAPI + Python 3.10+
- **Data Source**: AKShare (free, no API key required)
- **Data Processing**: pandas + NumPy
- **Validation**: pydantic v2 with Decimal precision
- **Cache**: Redis (optional, auto-disables if unavailable)
- **Database**: MySQL (SQLAlchemy)
- **LLM**: DeepSeek API
- **Logging**: Loguru
- **Testing**: pytest

## Common Commands

```bash
# Install dependencies
poetry install

# Run development server
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run all tests
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_precision.py -v

# Run specific test
poetry run pytest tests/test_precision.py::TestPrecision::test_safe_divide_zero -v
```

## Architecture

### Layer Structure

```
src/
├── config/        # pydantic Settings for env vars
├── models/        # pydantic models (BalanceSheet, IncomeStatement, etc.)
├── utils/         # precision.py (Decimal utils), logger.py, naming_mapper.py
├── data_fetcher/  # AKShareClient - fetches data from AKShare API with Redis cache
├── processor/     # Data cleaning, transformation, validation
├── analyzer/      # Financial ratio calculation, DuPont, trend analysis
├── api/           # FastAPI routes (routes_stock.py, routes_analysis.py)
├── llm_engine/    # DeepSeek integration for AI reports
├── export/        # Excel and chart generation
└── storage/       # Database models and operations
```

### Key Patterns

1. **Decimal Precision**: All monetary values use `Decimal`, never `float`. Use `to_amount()`, `to_ratio()`, and `safe_divide()` from `src/utils/precision.py`.

2. **Data Flow**: AKShare API → cache_manager → data_cleaner → data_validator → analyzer → API response

3. **Pydantic Models**: All financial data is validated through pydantic models in `src/models/`.

4. **Caching**: Redis caches AKShare responses with 1-hour TTL. Cache auto-disables if Redis is unavailable.

5. **Configuration**: Use `src/config/settings.py` singleton for all config. Environment variables loaded from `.env`.

## API Endpoints

```
GET /api/stocks                    # List all stocks
GET /api/stocks/{code}/statements  # Three financial statements
GET /api/stocks/{code}/ratios      # Financial ratios
GET /api/stocks/{code}/dupont      # DuPont analysis
GET /api/stocks/{code}/cashflow    # Cash flow analysis
GET /api/stocks/{code}/trend       # Trend analysis (YoY, QoQ)
GET /api/stocks/{code}/report      # AI-generated analysis report
```

## Testing

- Tests are in `tests/` directory
- No conftest.py - fixtures are in test files
- Use `pytest tests/test_precision.py -v` for quick validation of core math
- Test stock: 600519 (Kweichow Moutai / 贵州茅台)

## Environment Setup

Copy `.env.example` to `.env` and configure:
- MySQL connection (optional for Phase 1)
- Redis connection (optional, caching)
- DeepSeek API key (for LLM reports)

## Development Notes

- All modules have Chinese headers documenting function interfaces and data flow
- Use `from src.X import Y` for imports (not relative imports)
- Loguru logger is initialized in `src/utils/logger.py`
- AKShare data is in Chinese - `naming_mapper.py` maps Chinese columns to English field names
