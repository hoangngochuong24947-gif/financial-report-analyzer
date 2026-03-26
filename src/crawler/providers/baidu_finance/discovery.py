from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright

from src.config.settings import settings
from src.crawler.interfaces import Dataset
from src.crawler.providers.baidu_finance.client import BaiduFinanceHTTPClient
from src.crawler.providers.baidu_finance.endpoint_registry import DATASET_ENDPOINT_SPECS
from src.utils.logger import logger


@dataclass
class DiscoveredRequest:
    dataset: Dataset
    url: str
    params: Dict[str, Any]


class BaiduFinanceDiscovery:
    """Discover dataset request params from stockwidget and browser fallbacks."""

    STOCKWIDGET_URL = "https://finance.pae.baidu.com/api/stockwidget"
    OPENDATA_URL = "https://gushitong.baidu.com/opendata"

    def __init__(self) -> None:
        self._client = BaiduFinanceHTTPClient()

    def discover(self, stock_code: str) -> Dict[Dataset, DiscoveredRequest]:
        discovered = self._discover_from_stockwidget(stock_code)

        missing_statement = any(
            dataset not in discovered
            for dataset in (
                Dataset.INCOME_STATEMENT,
                Dataset.BALANCE_SHEET,
                Dataset.CASHFLOW_STATEMENT,
            )
        )
        if missing_statement:
            logger.warning("Stockwidget discovery incomplete for %s, falling back to browser discovery", stock_code)
            discovered.update(self._discover_from_browser(stock_code))

        for dataset in (
            Dataset.INCOME_STATEMENT,
            Dataset.BALANCE_SHEET,
            Dataset.CASHFLOW_STATEMENT,
        ):
            if dataset not in discovered:
                raise RuntimeError(f"Failed to discover Baidu request params for {stock_code} {dataset.value}")

        if Dataset.FINANCIAL_INDICATORS not in discovered:
            discovered[Dataset.FINANCIAL_INDICATORS] = self._build_indicator_request(stock_code)

        return discovered

    def _discover_from_stockwidget(self, stock_code: str) -> Dict[Dataset, DiscoveredRequest]:
        payload = self._client.get_json(
            self.STOCKWIDGET_URL,
            {
                "code": stock_code,
                "market": "ab",
                "type": "stock",
                "widgetType": "finance",
                "finClientType": "pc",
            },
        )

        result = payload.get("Result", {})
        content = result.get("content", {}) if isinstance(result, dict) else {}

        section_map = {
            Dataset.INCOME_STATEMENT: content.get("profitSheet"),
            Dataset.BALANCE_SHEET: content.get("balanceSheet"),
            Dataset.CASHFLOW_STATEMENT: content.get("cashFlowSheet"),
        }

        discovered: Dict[Dataset, DiscoveredRequest] = {}
        for dataset, section in section_map.items():
            asyn_url = section.get("asynUrl") if isinstance(section, dict) else None
            if not asyn_url:
                continue
            parsed = urlparse(asyn_url)
            params = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
            params["finClientType"] = "pc"
            discovered[dataset] = DiscoveredRequest(
                dataset=dataset,
                url=parsed._replace(query="").geturl(),
                params=params,
            )
        return discovered

    def _discover_from_browser(self, stock_code: str) -> Dict[Dataset, DiscoveredRequest]:
        discovered: Dict[Dataset, DiscoveredRequest] = {}

        def classify(url: str) -> Dataset | None:
            parsed = urlparse(url)
            query = parse_qs(parsed.query)
            if "selfselect/openapi" in url:
                group = query.get("group", [None])[0]
                for dataset, spec in DATASET_ENDPOINT_SPECS.items():
                    if spec.group == group:
                        return dataset
            return None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(settings.baidu_finance_timeout * 1000)

            def handle_request(request) -> None:
                dataset = classify(request.url)
                if dataset is None or dataset in discovered:
                    return
                parsed = urlparse(request.url)
                params = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
                params["finClientType"] = "pc"
                discovered[dataset] = DiscoveredRequest(
                    dataset=dataset,
                    url=parsed._replace(query="").geturl(),
                    params=params,
                )

            page.on("request", handle_request)
            page.goto(
                f"https://gushitong.baidu.com/stock/ab-{stock_code}?mainTab=%E8%B4%A2%E5%8A%A1",
                wait_until="domcontentloaded",
            )
            page.wait_for_timeout(8000)
            browser.close()

        return discovered

    def _build_indicator_request(self, stock_code: str) -> DiscoveredRequest:
        spec = DATASET_ENDPOINT_SPECS[Dataset.FINANCIAL_INDICATORS]
        return DiscoveredRequest(
            dataset=Dataset.FINANCIAL_INDICATORS,
            url=self.OPENDATA_URL,
            params={
                "code": stock_code,
                "market": "ab",
                "query": spec.query,
                "finClientType": "pc",
            },
        )
