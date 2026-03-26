from __future__ import annotations

from typing import Any, Dict, List

from src.crawler.interfaces import FinancialDataGateway
from src.crawler.providers.akshare_provider import AKShareProvider
from src.crawler.providers.baidu_finance.service import BaiduFinanceCrawlerService, BaiduFinanceSnapshotBundle
from src.models.financial_statements import BalanceSheet, CashFlowStatement, IncomeStatement


class BaiduFinanceProvider(FinancialDataGateway):
    """Provider backed by Baidu Gushitong finance page discovery."""

    def __init__(self) -> None:
        self._service = BaiduFinanceCrawlerService()
        self._bundle_cache: Dict[str, BaiduFinanceSnapshotBundle] = {}
        self._stock_list_provider = AKShareProvider()

    def _get_bundle(self, stock_code: str, refresh: bool = False) -> BaiduFinanceSnapshotBundle:
        if refresh or stock_code not in self._bundle_cache:
            self._bundle_cache[stock_code] = self._service.crawl_snapshot(stock_code)
        return self._bundle_cache[stock_code]

    def fetch_stock_list(self, market: str | None = None, refresh: bool = False):
        return self._stock_list_provider.fetch_stock_list(market=market, refresh=refresh)

    def fetch_balance_sheet(self, stock_code: str, refresh: bool = False) -> List[BalanceSheet]:
        return self._get_bundle(stock_code, refresh=refresh).balance_sheets

    def fetch_income_statement(self, stock_code: str, refresh: bool = False) -> List[IncomeStatement]:
        return self._get_bundle(stock_code, refresh=refresh).income_statements

    def fetch_cashflow_statement(self, stock_code: str, refresh: bool = False) -> List[CashFlowStatement]:
        return self._get_bundle(stock_code, refresh=refresh).cashflow_statements

    def fetch_financial_indicators(self, stock_code: str, refresh: bool = False) -> Dict[str, Any]:
        return self._get_bundle(stock_code, refresh=refresh).financial_indicators

    def list_archives(self, stock_code: str | None = None, dataset=None, limit: int = 20):
        return self._service.list_archives(stock_code=stock_code, dataset=dataset, limit=limit)
