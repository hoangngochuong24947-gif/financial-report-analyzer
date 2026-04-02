"""Stock query routes (v1, backward-compatible)."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.analysis_facade import AnalysisFacade
from src.api.dependencies import get_analysis_facade
from src.crawler.interfaces import CrawlerDataNotFoundError
from src.models.stock_info import StockInfo
from src.utils.logger import logger

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/", response_model=List[StockInfo])
async def get_stock_list(
    market: Optional[str] = Query(None, description="Market filter"),
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    try:
        return await facade.list_stocks(market=market)
    except Exception as e:
        logger.error(f"Failed to fetch stock list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/statements")
async def get_financial_statements(
    code: str,
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    try:
        return await facade.get_legacy_statements(code)
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch statements for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

