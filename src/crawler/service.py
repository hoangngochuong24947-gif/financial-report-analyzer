from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.crawler.interfaces import (
    CrawlerDataNotFoundError,
    FinancialDataGateway,
    FinancialSnapshot,
)
from src.crawler.providers.akshare_provider import AKShareProvider
from src.models.financial_statements import (
    BalanceSheet,
    CashFlowStatement,
    IncomeStatement,
)
from src.models.stock_info import StockInfo
from src.utils.logger import logger


class CrawlerService:
    """
    Application-facing crawler facade.

    API routes and downstream services should consume this service instead of
    touching source-specific crawler implementations directly.
    """

    def __init__(self, provider: Optional[FinancialDataGateway] = None):
        self._provider = provider or AKShareProvider()

    def fetch_stock_list(self, market: Optional[str] = None) -> List[StockInfo]:
        return self._provider.fetch_stock_list(market=market)

    def fetch_balance_sheet(self, stock_code: str, refresh: bool = False) -> List[BalanceSheet]:
        return self._provider.fetch_balance_sheet(stock_code, refresh=refresh)

    def fetch_income_statement(self, stock_code: str, refresh: bool = False) -> List[IncomeStatement]:
        return self._provider.fetch_income_statement(stock_code, refresh=refresh)

    def fetch_cashflow_statement(self, stock_code: str, refresh: bool = False) -> List[CashFlowStatement]:
        return self._provider.fetch_cashflow_statement(stock_code, refresh=refresh)

    def fetch_financial_indicators(
        self,
        stock_code: str,
        refresh: bool = False,
    ) -> Dict[str, Any]:
        return self._provider.fetch_financial_indicators(stock_code, refresh=refresh)

    def get_snapshot(self, stock_code: str, refresh: bool = False) -> FinancialSnapshot:
        balance_sheets = self.fetch_balance_sheet(stock_code, refresh=refresh)
        income_statements = self.fetch_income_statement(stock_code, refresh=refresh)
        cashflow_statements = self.fetch_cashflow_statement(stock_code, refresh=refresh)

        if not balance_sheets or not income_statements:
            raise CrawlerDataNotFoundError(f"No financial statements for {stock_code}")

        return FinancialSnapshot(
            stock_code=stock_code,
            balance_sheets=balance_sheets,
            income_statements=income_statements,
            cashflow_statements=cashflow_statements,
        )

    def refresh_snapshot(self, stock_code: str) -> FinancialSnapshot:
        logger.info(f"Refreshing snapshot for {stock_code}")
        return self.get_snapshot(stock_code, refresh=True)

    @staticmethod
    def to_snapshot_payload(snapshot: FinancialSnapshot, latest_only: bool = True) -> Dict[str, Any]:
        def _pick(data: list):
            return [data[0]] if latest_only and data else data

        return {
            "stock_code": snapshot.stock_code,
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "statements": {
                "balance_sheet": [item.model_dump(mode="json") for item in _pick(snapshot.balance_sheets)],
                "income_statement": [item.model_dump(mode="json") for item in _pick(snapshot.income_statements)],
                "cashflow_statement": [item.model_dump(mode="json") for item in _pick(snapshot.cashflow_statements)],
            },
        }

