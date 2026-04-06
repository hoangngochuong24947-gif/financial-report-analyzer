from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.crawler.continuous_scheduler import (
    DEFAULT_SCHEDULER_TIMEZONE,
    build_scheduler_run_id,
    next_cycle_time,
    scheduler_day_key,
    scheduler_now,
    select_stocks_for_cycle,
)
from src.data_fetcher.stock_list import fetch_stock_list
from src.storage.crawl_run_repository import CrawlRunRepository
from src.utils.logger import logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run continuous Baidu Finance crawl scheduler")
    parser.add_argument("--interval-minutes", type=int, default=60, help="Minutes between scheduler cycles")
    parser.add_argument("--batch-size", type=int, default=300, help="Maximum stocks per cycle")
    parser.add_argument("--max-attempts", type=int, default=3, help="Maximum attempts per stock inside each batch run")
    parser.add_argument("--sleep-seconds", type=float, default=1.0, help="Sleep between stocks inside each batch run")
    parser.add_argument("--timezone", default=DEFAULT_SCHEDULER_TIMEZONE, help="Scheduler timezone")
    parser.add_argument("--run-once", action="store_true", help="Run one cycle and exit")
    return parser.parse_args()


def _batch_script_path() -> Path:
    return PROJECT_ROOT / "scripts" / "crawl_baidu_finance_batch.py"


def run_scheduler_cycle(args: argparse.Namespace, repository: CrawlRunRepository) -> dict[str, object]:
    current_time = scheduler_now(args.timezone)
    day_key = scheduler_day_key(current_time)
    successful_codes = repository.successful_stocks_for_date(day_key)
    stock_pool = [
        {
            "stock_code": item.stock_code,
            "stock_name": item.stock_name,
            "market": item.market,
        }
        for item in fetch_stock_list()
    ]
    selected = select_stocks_for_cycle(
        stock_pool=stock_pool,
        successful_codes=successful_codes,
        batch_size=args.batch_size,
    )

    summary = {
        "timestamp": current_time.isoformat(),
        "day_key": day_key,
        "total_pool": len(stock_pool),
        "successful_today": len(successful_codes),
        "selected_count": len(selected),
        "selected_codes": [item["stock_code"] for item in selected],
        "run_id": None,
    }

    if not selected:
        logger.info("Scheduler cycle skipped: all stocks already processed for {}", day_key)
        return summary

    run_id = build_scheduler_run_id(current_time)
    summary["run_id"] = run_id
    codes = ",".join(item["stock_code"] for item in selected)
    logger.info(
        "Scheduler cycle starting run {} for {} stocks on {}",
        run_id,
        len(selected),
        day_key,
    )
    subprocess.run(
        [
            sys.executable,
            str(_batch_script_path()),
            "--run-id",
            run_id,
            "--stocks",
            codes,
            "--limit",
            str(len(selected)),
            "--max-attempts",
            str(args.max_attempts),
            "--sleep-seconds",
            str(args.sleep_seconds),
        ],
        check=True,
        cwd=str(PROJECT_ROOT),
    )
    return summary


def main() -> int:
    args = parse_args()
    repository = CrawlRunRepository()

    while True:
        cycle_started_at = scheduler_now(args.timezone)
        summary = run_scheduler_cycle(args, repository)
        print(json.dumps(summary, ensure_ascii=False, indent=2))

        if args.run_once:
            return 0

        wake_up_at = next_cycle_time(cycle_started_at, args.interval_minutes)
        sleep_seconds = max((wake_up_at - scheduler_now(args.timezone)).total_seconds(), 1.0)
        logger.info(
            "Scheduler sleeping until {} ({} seconds)",
            wake_up_at.isoformat(),
            round(sleep_seconds, 2),
        )
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
