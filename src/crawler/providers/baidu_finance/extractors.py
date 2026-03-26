from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, List, Optional


REPORT_DATE_SUFFIX_MAP = {
    "\u5e74\u62a5": (12, 31),
    "\u4e09\u5b63\u62a5": (9, 30),
    "\u4e2d\u62a5": (6, 30),
    "\u4e00\u5b63\u62a5": (3, 31),
}


def parse_report_date(label: str) -> Optional[date]:
    normalized = label.replace("(", "").replace(")", "").replace("\uff08", "").replace("\uff09", "")
    if len(normalized) < 4 or not normalized[:4].isdigit():
        return None
    year = int(normalized[:4])
    for suffix, (month, day) in REPORT_DATE_SUFFIX_MAP.items():
        if suffix in normalized:
            return date(year, month, day)
    return None


def flatten_openapi_rows(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for block in result.get("data", []):
        report_label = block.get("text", "")
        report_date = parse_report_date(report_label)
        if report_date is None:
            continue
        values: Dict[str, Any] = {}
        for content in block.get("content", []):
            for item in content.get("data", []):
                header = item.get("header", [])
                if header:
                    values[header[0]] = header[2] if len(header) > 2 else None
                for body in item.get("body", []):
                    if body:
                        values[body[0]] = body[2] if len(body) > 2 else None
        rows.append(
            {
                "report_label": report_label,
                "report_date": report_date,
                "values": values,
            }
        )
    return rows


def build_dataframe_rows(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in flatten_openapi_rows(result):
        row = {
            "report_label": item["report_label"],
            "report_date": item["report_date"].isoformat(),
        }
        row.update(item["values"])
        rows.append(row)
    return rows


def extract_indicator_snapshot(indicator_rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    snapshot = {}
    for row in indicator_rows:
        if row.get("metric"):
            snapshot[row["metric"]] = row.get("latest_value")
    return snapshot
