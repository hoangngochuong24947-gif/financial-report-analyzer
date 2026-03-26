from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from src.config.settings import settings
from src.crawler.interfaces import CrawlerDependencyError
from src.crawler.service import CrawlerService
from src.utils.logger import logger

try:
    import redis
    from rq import Queue
    from rq.job import Job
except Exception:  # pragma: no cover - optional dependency fallback
    redis = None  # type: ignore
    Queue = None  # type: ignore
    Job = None  # type: ignore

LOCAL_JOB_STORE: Dict[str, Dict[str, Any]] = {}


def has_queue_dependencies() -> bool:
    return not (redis is None or Queue is None or Job is None)


def _ensure_queue_dependencies() -> None:
    if not has_queue_dependencies():
        raise CrawlerDependencyError("rq/redis package is not available")


def _get_queue() -> "Queue":
    _ensure_queue_dependencies()
    connection = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return Queue(name="crawler", connection=connection, default_timeout=300)


def run_refresh_snapshot(stock_code: str) -> Dict[str, Any]:
    service = CrawlerService()
    snapshot = service.refresh_snapshot(stock_code)
    return {
        "stock_code": stock_code,
        "balance_count": len(snapshot.balance_sheets),
        "income_count": len(snapshot.income_statements),
        "cashflow_count": len(snapshot.cashflow_statements),
    }


def enqueue_refresh_snapshot(stock_code: str) -> str:
    queue = _get_queue()
    job = queue.enqueue(run_refresh_snapshot, stock_code)
    logger.info(f"Crawler refresh job queued: {job.id} for {stock_code}")
    return str(job.id)


def enqueue_local_refresh_snapshot(stock_code: str) -> str:
    job_id = f"sync-{uuid4().hex[:12]}"
    created_at = datetime.utcnow().isoformat() + "Z"
    try:
        result = run_refresh_snapshot(stock_code)
        payload = {
            "job_id": job_id,
            "status": "finished",
            "result": result,
            "error": None,
            "created_at": created_at,
        }
    except Exception as e:
        payload = {
            "job_id": job_id,
            "status": "failed",
            "result": None,
            "error": str(e),
            "created_at": created_at,
        }
    LOCAL_JOB_STORE[job_id] = payload
    return job_id


def get_job_status(job_id: str) -> Dict[str, Any]:
    if job_id in LOCAL_JOB_STORE:
        return LOCAL_JOB_STORE[job_id]

    _ensure_queue_dependencies()
    queue = _get_queue()
    job = Job.fetch(job_id, connection=queue.connection)
    status = job.get_status(refresh=True)
    return {
        "job_id": job_id,
        "status": status,
        "result": job.result if status == "finished" else None,
        "error": str(job.exc_info) if status == "failed" else None,
    }
