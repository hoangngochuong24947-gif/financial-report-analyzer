"""v2 API routes for decoupled crawler orchestration."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.dependencies import get_crawler_service, get_workspace_service
from src.crawler.interfaces import CrawlerDataNotFoundError, CrawlerDependencyError, Dataset
from src.crawler.jobs import (
    enqueue_local_refresh_snapshot,
    enqueue_refresh_snapshot,
    get_job_status,
    has_queue_dependencies,
)
from src.crawler.service import CrawlerService
from src.models.stock_info import StockInfo
from src.api.workspace_service import WorkspaceService
from src.utils.logger import logger

router = APIRouter(prefix="/api/v2", tags=["v2"])


class CrawlJobRequest(BaseModel):
    stock_code: str = Field(..., description="Target stock code")


class CrawlJobResponse(BaseModel):
    job_id: str
    stock_code: str
    status: str
    created_at: str


class ArchiveListItem(BaseModel):
    stock_code: str
    dataset: str
    fetched_at: str
    raw_path: str
    csv_path: str
    manifest_path: str
    row_count: int
    status: str


@router.get("/stocks", response_model=List[StockInfo])
async def list_stocks_v2(
    market: Optional[str] = Query(None, description="Market filter"),
    refresh: bool = Query(False, description="Force refresh stock list cache"),
    crawler: CrawlerService = Depends(get_crawler_service),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        stock_items = crawler.fetch_stock_list(market=market, refresh=refresh)
        if stock_items:
            return stock_items
    except Exception as e:
        logger.warning(f"v2 stock crawler unavailable, falling back to workspace data: {e}")
    try:
        workspace_items = workspace_service.list_workspaces(limit=5000)
        return [
            StockInfo(
                stock_code=item.stock_code,
                stock_name=item.stock_name,
                market=item.market,
            )
            for item in workspace_items
            if not market or item.market == market
        ]
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


@router.get("/crawler/archives", response_model=List[ArchiveListItem])
async def list_crawler_archives(
    stock_code: Optional[str] = Query(None, description="Filter by stock code"),
    dataset: Optional[str] = Query(None, description="Dataset name"),
    limit: int = Query(20, ge=1, le=200, description="Number of recent archives to return"),
    crawler: CrawlerService = Depends(get_crawler_service),
):
    try:
        dataset_enum = Dataset(dataset) if dataset else None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unsupported dataset: {dataset}") from exc

    try:
        return crawler.list_archives(stock_code=stock_code, dataset=dataset_enum, limit=limit)
    except Exception as e:
        logger.error(f"v2 archive listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawler/jobs", response_model=CrawlJobResponse)
async def create_crawl_job(payload: CrawlJobRequest):
    try:
        if not has_queue_dependencies():
            logger.warning(
                "rq/redis unavailable; falling back to sync refresh for %s",
                payload.stock_code,
            )
            job_id = enqueue_local_refresh_snapshot(payload.stock_code)
            local_status = get_job_status(job_id)
            return CrawlJobResponse(
                job_id=job_id,
                stock_code=payload.stock_code,
                status=local_status["status"],
                created_at=local_status["created_at"],
            )

        job_id = enqueue_refresh_snapshot(payload.stock_code)
        return CrawlJobResponse(
            job_id=job_id,
            stock_code=payload.stock_code,
            status="queued",
            created_at=datetime.utcnow().isoformat() + "Z",
        )
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
