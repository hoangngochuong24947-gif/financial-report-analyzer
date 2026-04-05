from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.crawler.providers.baidu_finance.service import BaiduFinanceCrawlerService
from src.data_fetcher.stock_list import fetch_stock_list
from src.storage.archive_repository import ArchiveRepository
from src.storage.crawl_run_repository import CrawlRunRepository
from src.utils.logger import logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run resumable Baidu Finance batch crawl")
    parser.add_argument("--run-id", help="Existing or desired run id")
    parser.add_argument("--resume", action="store_true", help="Resume an existing run")
    parser.add_argument("--stocks", help="Comma-separated stock codes")
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of stocks to process in this invocation")
    parser.add_argument("--only-missing", action="store_true", help="Skip stocks that already have archives")
    parser.add_argument("--max-attempts", type=int, default=3, help="Maximum attempts per stock")
    parser.add_argument("--sleep-seconds", type=float, default=1.0, help="Sleep between stocks")
    return parser.parse_args()


def default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")


def resolve_stock_pool(stock_codes: str | None) -> list[dict[str, str | None]]:
    if stock_codes:
        return [{"stock_code": code.strip(), "stock_name": None, "market": None} for code in stock_codes.split(",") if code.strip()]

    stocks = fetch_stock_list()
    return [
        {
            "stock_code": item.stock_code,
            "stock_name": item.stock_name,
            "market": item.market,
        }
        for item in stocks
    ]


def should_skip_existing(archive_repository: ArchiveRepository, stock_code: str) -> bool:
    return len(archive_repository.list_archives(stock_code=stock_code, limit=1)) > 0


def main() -> int:
    args = parse_args()
    repository = CrawlRunRepository()
    archive_repository = ArchiveRepository()
    crawler = BaiduFinanceCrawlerService()
    run_id = args.run_id or default_run_id()

    if args.resume:
        run_state = repository.load_run(run_id)
    else:
        stock_pool = resolve_stock_pool(args.stocks)
        if not stock_pool:
            print("No stocks resolved for batch crawl.")
            return 1
        run_state = repository.create_run(
            run_id,
            config={
                "only_missing": args.only_missing,
                "max_attempts": args.max_attempts,
                "sleep_seconds": args.sleep_seconds,
                "limit": args.limit,
            },
            stocks=stock_pool,
        )

    processed = 0
    for stock_code, entry in run_state["stocks"].items():
        if args.limit and processed >= args.limit:
            break

        status = entry.get("status", "pending")
        attempts = int(entry.get("attempts", 0))
        if status in {"success", "skipped"}:
            continue
        if attempts >= args.max_attempts:
            continue

        if args.only_missing and should_skip_existing(archive_repository, stock_code):
            repository.update_stock(
                run_id,
                stock_code,
                {
                    "status": "skipped",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "last_error": None,
                },
            )
            processed += 1
            continue

        repository.update_stock(
            run_id,
            stock_code,
            {
                "status": "running",
                "attempts": attempts + 1,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "last_error": None,
            },
        )
        logger.info("Batch crawl run {} processing {}", run_id, stock_code)

        try:
            bundle = crawler.crawl_snapshot(stock_code)
            artifacts = {
                dataset.value: {
                    "raw_path": result.raw_path,
                    "csv_path": result.csv_path,
                    "manifest_path": result.manifest_path,
                    "row_count": result.row_count,
                    "status": result.status,
                }
                for dataset, result in bundle.artifacts.items()
            }
            repository.update_stock(
                run_id,
                stock_code,
                {
                    "status": "success",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "last_error": None,
                    "stock_name": bundle.stock_name,
                    "market": bundle.market,
                    "artifacts": artifacts,
                },
            )
        except Exception as exc:  # pragma: no cover - operational script
            repository.update_stock(
                run_id,
                stock_code,
                {
                    "status": "failed",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "last_error": str(exc),
                },
            )
            logger.exception("Batch crawl run {} failed for {}", run_id, stock_code)

        processed += 1
        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    final_state = repository.load_run(run_id)
    final_state["status"] = "completed" if final_state["summary"]["pending"] == 0 and final_state["summary"]["running"] == 0 else "running"
    repository.save_run(run_id, final_state)
    print(json.dumps({"run_id": run_id, "summary": final_state["summary"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
