"""v2 API routes for decoupled crawler orchestration."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.dependencies import get_crawler_service
from src.crawler.interfaces import CrawlerDataNotFoundError, CrawlerDependencyError
from src.crawler.jobs import enqueue_refresh_snapshot, get_job_status
from src.crawler.service import CrawlerService
from src.models.stock_info import StockInfo
from src.utils.logger import logger

router = APIRouter(prefix="/api/v2", tags=["v2"])


class CrawlJobRequest(BaseModel):
    stock_code: str = Field(..., description="Target stock code")


class CrawlJobResponse(BaseModel):
    job_id: str
    stock_code: str
    status: str
    created_at: str


@router.get("/stocks", response_model=List[StockInfo])
async def list_stocks_v2(
    market: Optional[str] = Query(None, description="Market filter"),
    crawler: CrawlerService = Depends(get_crawler_service),
):
    try:
        return crawler.fetch_stock_list(market=market)
    except Exception as e:
        logger.error(f"v2 list stocks failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{code}/snapshot")
async def get_stock_snapshot_v2(
    code: str,
    latest_only: bool = Query(True, description="Only return latest statement period"),
    refresh: bool = Query(False, description="Force refresh from upstream"),
    crawler: CrawlerService = Depends(get_crawler_service),
):
    try:
        snapshot = crawler.get_snapshot(code, refresh=refresh)
        return crawler.to_snapshot_payload(snapshot, latest_only=latest_only)
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"v2 snapshot failed for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawler/jobs", response_model=CrawlJobResponse)
async def create_crawl_job(payload: CrawlJobRequest):
    try:
        job_id = enqueue_refresh_snapshot(payload.stock_code)
        return CrawlJobResponse(
            job_id=job_id,
            stock_code=payload.stock_code,
            status="queued",
            created_at=datetime.utcnow().isoformat() + "Z",
        )
    except CrawlerDependencyError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create crawl job for {payload.stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crawler/jobs/{job_id}")
async def get_crawl_job(job_id: str) -> Dict[str, Any]:
    try:
        return get_job_status(job_id)
    except CrawlerDependencyError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch crawl job status {job_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))

