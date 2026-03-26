from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.crawler.providers.baidu_finance.service import BaiduFinanceCrawlerService


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/crawl_baidu_finance.py <stock_code>")
        return 1

    stock_code = sys.argv[1]
    service = BaiduFinanceCrawlerService()
    bundle = service.crawl_snapshot(stock_code)

    summary = {
        "stock_code": bundle.stock_code,
        "stock_name": bundle.stock_name,
        "market": bundle.market,
        "statement_counts": {
            "income_statement": len(bundle.income_statements),
            "balance_sheet": len(bundle.balance_sheets),
            "cashflow_statement": len(bundle.cashflow_statements),
            "financial_indicators": len(bundle.financial_indicators),
        },
        "artifacts": {
            dataset.value: {
                "raw_path": result.raw_path,
                "csv_path": result.csv_path,
                "manifest_path": result.manifest_path,
                "row_count": result.row_count,
                "status": result.status,
            }
            for dataset, result in bundle.artifacts.items()
        },
        "latest_indicator_keys": sorted(bundle.financial_indicators.keys()),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
