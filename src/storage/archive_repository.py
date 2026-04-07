from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.config.settings import settings
from src.crawler.interfaces import Dataset


@dataclass
class ArchiveWriteResult:
    dataset: str
    raw_path: str
    csv_path: str
    manifest_path: str
    row_count: int
    fetched_at: str
    request_url: str
    request_params: Dict[str, Any]
    status: str
    error: Optional[str]


class ArchiveRepository:
    """Persist raw and processed crawl outputs to the filesystem."""

    def __init__(self, archive_root: str | None = None) -> None:
        self._root = Path(archive_root or settings.archive_root)

    def save_dataset(
        self,
        *,
        stock_code: str,
        stock_name: str,
        market: str,
        dataset: Dataset,
        request_url: str,
        request_params: Dict[str, Any],
        raw_payload: Dict[str, Any],
        csv_rows: List[Dict[str, Any]],
        error: str | None = None,
    ) -> ArchiveWriteResult:
        fetch_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        fetch_date = fetch_ts[:8]
        request_group = request_params.get("group") or request_params.get("query") or "dom"

        raw_dir = self._root / "raw" / "baidu_finance" / stock_code / dataset.value / fetch_date
        processed_dir = self._root / "processed" / "baidu_finance" / stock_code / dataset.value
        manifest_dir = self._root / "raw" / "baidu_finance" / stock_code / "manifests"
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        manifest_dir.mkdir(parents=True, exist_ok=True)

        raw_path = raw_dir / f"{stock_code}_{dataset.value}_{request_group}_{fetch_ts}.json"
        raw_path.write_text(
            json.dumps(raw_payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

        period_labels = [row.get("report_date") or row.get("latest_report_label") for row in csv_rows if row]
        valid_periods = [str(item) for item in period_labels if item]
        period_start = min(valid_periods) if valid_periods else "na"
        period_end = max(valid_periods) if valid_periods else "na"
        csv_path = processed_dir / f"{stock_code}_{dataset.value}_{period_start}_{period_end}.csv"
        pd.DataFrame(csv_rows).to_csv(csv_path, index=False, encoding="utf-8-sig")

        result = ArchiveWriteResult(
            dataset=dataset.value,
            raw_path=str(raw_path),
            csv_path=str(csv_path),
            manifest_path="",
            row_count=len(csv_rows),
            fetched_at=fetch_ts,
            request_url=request_url,
            request_params=request_params,
            status="success" if error is None else "failed",
            error=error,
        )
        manifest_path = manifest_dir / f"manifest_{stock_code}_{fetch_ts}_{dataset.value}.json"
        payload = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "market": market,
            "dataset": dataset.value,
            "entry_url": "https://finance.pae.baidu.com/api/stockwidget",
            "entry_params": {
                "code": stock_code,
                "market": market,
                "type": "stock",
                "widgetType": "finance",
                "finClientType": "pc",
            },
            **asdict(result),
        }
        payload["manifest_path"] = str(manifest_path)
        manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        result.manifest_path = str(manifest_path)
        return result

    def list_archives(
        self,
        *,
        stock_code: str | None = None,
        dataset: Dataset | None = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        manifest_root = self._root / "raw" / "baidu_finance"
        if stock_code:
            manifest_root = manifest_root / stock_code / "manifests"
            paths = sorted(manifest_root.glob("manifest_*.json"), reverse=True)
        else:
            paths = sorted(manifest_root.glob("*/manifests/manifest_*.json"), reverse=True)

        items: List[Dict[str, Any]] = []
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if dataset and payload.get("dataset") != dataset.value:
                continue
            items.append(payload)
            if len(items) >= limit:
                break
        return items
