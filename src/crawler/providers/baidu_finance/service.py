from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from playwright.sync_api import sync_playwright

from src.crawler.interfaces import Dataset
from src.crawler.providers.baidu_finance.client import BaiduFinanceHTTPClient
from src.crawler.providers.baidu_finance.discovery import BaiduFinanceDiscovery
from src.crawler.providers.baidu_finance.endpoint_registry import DATASET_ENDPOINT_SPECS
from src.crawler.providers.baidu_finance.extractors import build_dataframe_rows, extract_indicator_snapshot
from src.crawler.providers.baidu_finance.parsers import (
    parse_balance_sheets,
    parse_cashflow_statements,
    parse_income_statements,
)
from src.data_fetcher.akshare_client import AKShareClient
from src.config.settings import settings
from src.models.financial_statements import BalanceSheet, CashFlowStatement, IncomeStatement
from src.storage.archive_repository import ArchiveRepository, ArchiveWriteResult
from src.utils.logger import logger


@dataclass
class BaiduFinanceSnapshotBundle:
    stock_code: str
    stock_name: str
    market: str
    income_statements: List[IncomeStatement]
    balance_sheets: List[BalanceSheet]
    cashflow_statements: List[CashFlowStatement]
    financial_indicators: Dict[str, Any]
    artifacts: Dict[Dataset, ArchiveWriteResult]


class BaiduFinanceCrawlerService:
    """High-level Baidu finance crawler orchestration."""

    STOCKWIDGET_URL = "https://finance.pae.baidu.com/api/stockwidget"

    def __init__(self, archive_repository: ArchiveRepository | None = None) -> None:
        self._discovery = BaiduFinanceDiscovery()
        self._client = BaiduFinanceHTTPClient()
        self._archive_repository = archive_repository or ArchiveRepository()

    def crawl_snapshot(self, stock_code: str) -> BaiduFinanceSnapshotBundle:
        discovered = self._discovery.discover(stock_code)
        entry_payload = self._client.get_json(
            self.STOCKWIDGET_URL,
            {
                "code": stock_code,
                "market": "ab",
                "type": "stock",
                "widgetType": "finance",
                "finClientType": "pc",
            },
        )

        income_payload = self._client.get_json(
            discovered[Dataset.INCOME_STATEMENT].url,
            discovered[Dataset.INCOME_STATEMENT].params,
        )
        balance_payload = self._client.get_json(
            discovered[Dataset.BALANCE_SHEET].url,
            discovered[Dataset.BALANCE_SHEET].params,
        )
        cashflow_payload = self._client.get_json(
            discovered[Dataset.CASHFLOW_STATEMENT].url,
            discovered[Dataset.CASHFLOW_STATEMENT].params,
        )

        income_result = income_payload.get("Result", {})
        balance_result = balance_payload.get("Result", {})
        cashflow_result = cashflow_payload.get("Result", {})
        entry_result = entry_payload.get("Result", {}) if isinstance(entry_payload, dict) else {}

        stock_name = entry_result.get("stockName") or entry_result.get("name") or stock_code
        market = entry_result.get("market") or income_result.get("info", {}).get("market", "ab")

        income_statements = parse_income_statements(stock_code, income_result)
        balance_sheets = parse_balance_sheets(stock_code, balance_result)
        cashflow_statements = parse_cashflow_statements(stock_code, cashflow_result)

        indicator_payload = self._load_indicator_payload(stock_code)

        artifacts = {
            Dataset.INCOME_STATEMENT: self._archive_repository.save_dataset(
                stock_code=stock_code,
                stock_name=stock_name,
                market=market,
                dataset=Dataset.INCOME_STATEMENT,
                request_url=discovered[Dataset.INCOME_STATEMENT].url,
                request_params=discovered[Dataset.INCOME_STATEMENT].params,
                raw_payload=income_payload,
                csv_rows=build_dataframe_rows(income_result),
            ),
            Dataset.BALANCE_SHEET: self._archive_repository.save_dataset(
                stock_code=stock_code,
                stock_name=stock_name,
                market=market,
                dataset=Dataset.BALANCE_SHEET,
                request_url=discovered[Dataset.BALANCE_SHEET].url,
                request_params=discovered[Dataset.BALANCE_SHEET].params,
                raw_payload=balance_payload,
                csv_rows=build_dataframe_rows(balance_result),
            ),
            Dataset.CASHFLOW_STATEMENT: self._archive_repository.save_dataset(
                stock_code=stock_code,
                stock_name=stock_name,
                market=market,
                dataset=Dataset.CASHFLOW_STATEMENT,
                request_url=discovered[Dataset.CASHFLOW_STATEMENT].url,
                request_params=discovered[Dataset.CASHFLOW_STATEMENT].params,
                raw_payload=cashflow_payload,
                csv_rows=build_dataframe_rows(cashflow_result),
            ),
            Dataset.FINANCIAL_INDICATORS: self._archive_repository.save_dataset(
                stock_code=stock_code,
                stock_name=stock_name,
                market=market,
                dataset=Dataset.FINANCIAL_INDICATORS,
                request_url=discovered.get(Dataset.FINANCIAL_INDICATORS).url
                if discovered.get(Dataset.FINANCIAL_INDICATORS)
                else "https://gushitong.baidu.com/stock",
                request_params=discovered.get(Dataset.FINANCIAL_INDICATORS).params
                if discovered.get(Dataset.FINANCIAL_INDICATORS)
                else {"stock_code": stock_code, "mode": "dom_scrape"},
                raw_payload=indicator_payload,
                csv_rows=indicator_payload.get("rows", []),
            ),
        }

        return BaiduFinanceSnapshotBundle(
            stock_code=stock_code,
            stock_name=stock_name,
            market=market,
            income_statements=income_statements,
            balance_sheets=balance_sheets,
            cashflow_statements=cashflow_statements,
            financial_indicators=indicator_payload.get("latest")
            or extract_indicator_snapshot(indicator_payload.get("rows", [])),
            artifacts=artifacts,
        )

    def list_archives(
        self,
        stock_code: str | None = None,
        dataset: Dataset | None = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        return self._archive_repository.list_archives(stock_code=stock_code, dataset=dataset, limit=limit)

    def _scrape_indicator_table(self, stock_code: str) -> Dict[str, Any]:
        url = f"https://gushitong.baidu.com/stock/ab-{stock_code}?mainTab=%E8%B4%A2%E5%8A%A1"
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_default_timeout(settings.baidu_finance_indicator_dom_timeout_ms)
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(min(settings.baidu_finance_indicator_dom_timeout_ms, 6000))
                indicator_tab = page.get_by_text(
                    DATASET_ENDPOINT_SPECS[Dataset.FINANCIAL_INDICATORS].tab_text,
                    exact=False,
                ).first
                indicator_tab.click()
                page.wait_for_timeout(min(settings.baidu_finance_indicator_dom_timeout_ms, 3000))
                payload = page.evaluate(
                    """
                    () => {
                      const bodyText = document.body.innerText;
                      const lines = bodyText.split('\\n').map(item => item.trim()).filter(Boolean);
                      const start = lines.findIndex(item => item === '指标(人民币)');
                      if (start === -1) {
                        return { rows: [], latest: {} };
                      }

                      const slice = lines.slice(start, start + 220);
                      const reportLabels = [];
                      let idx = 1;
                      while (idx < slice.length && /^20\\d{2}/.test(slice[idx])) {
                        reportLabels.push(slice[idx]);
                        idx += 1;
                      }

                      const rows = [];
                      while (idx < slice.length) {
                        const metric = slice[idx];
                        idx += 1;
                        if (!metric || metric.includes('ROE趋势') || metric.includes('同行业对比')) {
                          continue;
                        }

                        const values = [];
                        for (let i = 0; i < reportLabels.length && idx < slice.length; i += 1) {
                          const value = slice[idx];
                          const change = idx + 1 < slice.length ? slice[idx + 1] : '--';
                          values.push({ report_label: reportLabels[i], value, change });
                          idx += 2;
                        }

                        rows.push({
                          metric,
                          latest_report_label: reportLabels[0] || null,
                          latest_value: values[0] ? values[0].value : null,
                          values,
                        });

                        if (rows.length >= 8) {
                          break;
                        }
                      }

                      const latest = Object.fromEntries(rows.map(row => [row.metric, row.latest_value]));
                      return { rows, latest };
                    }
                    """
                )
                browser.close()
                return payload
        except Exception as exc:
            logger.warning("Failed to scrape Baidu indicator table for {}: {}", stock_code, exc)
            return {"rows": [], "latest": {}}

    def _load_indicator_payload(self, stock_code: str) -> Dict[str, Any]:
        if settings.baidu_finance_indicator_dom_enabled:
            indicator_payload = self._scrape_indicator_table(stock_code)
            if indicator_payload.get("rows"):
                return indicator_payload
            logger.warning("Baidu indicator DOM scrape failed, falling back to AKShare indicators for {}", stock_code)

        latest_indicator_snapshot = AKShareClient.fetch_financial_indicators(stock_code)
        return {
            "rows": [
                {
                    "metric": key,
                    "latest_report_label": latest_indicator_snapshot.get("report_date"),
                    "latest_value": value,
                }
                for key, value in latest_indicator_snapshot.items()
            ],
            "latest": latest_indicator_snapshot,
        }
