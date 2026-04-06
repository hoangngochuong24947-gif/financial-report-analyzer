from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo


DEFAULT_SCHEDULER_TIMEZONE = "Asia/Shanghai"


def scheduler_now(timezone_name: str = DEFAULT_SCHEDULER_TIMEZONE) -> datetime:
    return datetime.now(ZoneInfo(timezone_name))


def scheduler_day_key(now: datetime | None = None) -> str:
    current = now or scheduler_now()
    return current.date().isoformat()


def build_scheduler_run_id(now: datetime | None = None) -> str:
    current = now or scheduler_now()
    return current.strftime("scheduler-%Y%m%dT%H%M%S")


def select_stocks_for_cycle(
    *,
    stock_pool: list[dict[str, Any]],
    successful_codes: set[str],
    batch_size: int,
) -> list[dict[str, Any]]:
    candidates = [item for item in stock_pool if item.get("stock_code") not in successful_codes]
    if batch_size <= 0:
        return candidates
    return candidates[:batch_size]


def next_cycle_time(now: datetime, interval_minutes: int) -> datetime:
    aligned = now.replace(second=0, microsecond=0)
    return aligned + timedelta(minutes=interval_minutes)
