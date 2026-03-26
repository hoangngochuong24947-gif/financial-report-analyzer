from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from src.crawler.interfaces import Dataset


@dataclass(frozen=True)
class DatasetEndpointSpec:
    dataset: Dataset
    tab_text: str
    group: Optional[str] = None
    query: Optional[str] = None


DATASET_ENDPOINT_SPECS: Dict[Dataset, DatasetEndpointSpec] = {
    Dataset.INCOME_STATEMENT: DatasetEndpointSpec(
        dataset=Dataset.INCOME_STATEMENT,
        tab_text="\u5229\u6da6\u5206\u914d\u8868",
        group="income_detail",
    ),
    Dataset.BALANCE_SHEET: DatasetEndpointSpec(
        dataset=Dataset.BALANCE_SHEET,
        tab_text="\u8d44\u4ea7\u8d1f\u503a\u8868",
        group="balance_detail",
    ),
    Dataset.CASHFLOW_STATEMENT: DatasetEndpointSpec(
        dataset=Dataset.CASHFLOW_STATEMENT,
        tab_text="\u73b0\u91d1\u6d41\u91cf\u8868",
        group="cash_flow_detail",
    ),
    Dataset.FINANCIAL_INDICATORS: DatasetEndpointSpec(
        dataset=Dataset.FINANCIAL_INDICATORS,
        tab_text="\u5173\u952e\u6307\u6807",
        query="ROE",
    ),
}
