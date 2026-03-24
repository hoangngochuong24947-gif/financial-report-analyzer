"""Stock query routes (v1, backward-compatible)."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_crawler_service
from src.crawler.interfaces import CrawlerDataNotFoundError
from src.crawler.service import CrawlerService
from src.models.stock_info import StockInfo
from src.utils.logger import logger

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/", response_model=List[StockInfo])
async def get_stock_list(
    market: Optional[str] = Query(None, description="Market filter"),
    crawler: CrawlerService = Depends(get_crawler_service),
):
    try:
        return crawler.fetch_stock_list(market=market)
    except Exception as e:
        logger.error(f"Failed to fetch stock list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/statements")
async def get_financial_statements(
    code: str,
    crawler: CrawlerService = Depends(get_crawler_service),
):
    try:
        snapshot = crawler.get_snapshot(code)
        return {
            "stock_code": code,
            "balance_sheet": snapshot.balance_sheets[0].model_dump(mode="json"),
            "income_statement": snapshot.income_statements[0].model_dump(mode="json"),
            "cashflow_statement": (
                snapshot.cashflow_statements[0].model_dump(mode="json")
                if snapshot.cashflow_statements
                else None
            ),
        }
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch statements for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

