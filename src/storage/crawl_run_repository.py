from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config.settings import settings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CrawlRunRepository:
    """Persist resumable crawl run state on the filesystem."""

    def __init__(self, root: str | None = None) -> None:
        base_root = Path(root or settings.archive_root)
        self._root = base_root / "runs" / "baidu_finance"
        self._root.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id: str) -> Path:
        return self._root / run_id

    def state_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "state.json"

    def log_dir(self, run_id: str) -> Path:
        path = self.run_dir(run_id) / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def create_run(self, run_id: str, config: dict[str, Any], stocks: list[dict[str, Any]]) -> dict[str, Any]:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "run_id": run_id,
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "status": "created",
            "config": config,
            "summary": {
                "total": len(stocks),
                "pending": len(stocks),
                "running": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
            },
            "stocks": {
                item["stock_code"]: {
                    "stock_code": item["stock_code"],
                    "stock_name": item.get("stock_name"),
                    "market": item.get("market"),
                    "status": "pending",
                    "attempts": 0,
                    "started_at": None,
                    "finished_at": None,
                    "last_error": None,
                    "artifacts": {},
                }
                for item in stocks
            },
        }
        self.save_run(run_id, payload)
        return payload

    def load_run(self, run_id: str) -> dict[str, Any]:
        path = self.state_path(run_id)
        if not path.exists():
            raise FileNotFoundError(f"Run state not found: {run_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def save_run(self, run_id: str, payload: dict[str, Any]) -> None:
        payload["updated_at"] = utc_now()
        payload["summary"] = self._build_summary(payload.get("stocks", {}))
        path = self.state_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def update_stock(self, run_id: str, stock_code: str, patch: dict[str, Any]) -> dict[str, Any]:
        payload = self.load_run(run_id)
        stocks = payload.setdefault("stocks", {})
        if stock_code not in stocks:
            raise KeyError(f"Stock {stock_code} does not exist in run {run_id}")
        stocks[stock_code].update(patch)
        self.save_run(run_id, payload)
        return payload

    def _build_summary(self, stocks: dict[str, dict[str, Any]]) -> dict[str, int]:
        summary = {
            "total": len(stocks),
            "pending": 0,
            "running": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }
        for item in stocks.values():
            status = item.get("status", "pending")
            if status in summary:
                summary[status] += 1
            else:
                summary["pending"] += 1
        return summary
