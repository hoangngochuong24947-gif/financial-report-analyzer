from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.crawler.interfaces import FinancialDataGateway
from src.data_fetcher.akshare_client import AKShareClient
from src.data_fetcher.cache_manager import cache_manager
from src.data_fetcher.stock_list import fetch_stock_list
from src.models.financial_statements import (
    BalanceSheet,
    CashFlowStatement,
    IncomeStatement,
)
from src.models.stock_info import StockInfo
from src.utils.logger import logger

try:
    from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
except Exception:  # pragma: no cover - optional dependency fallback
    def retry(*args, **kwargs):  # type: ignore
        def decorator(func):
            return func

        return decorator

    def stop_after_attempt(*args, **kwargs):  # type: ignore
        return None

    def wait_exponential(*args, **kwargs):  # type: ignore
        return None

    def retry_if_exception_type(*args, **kwargs):  # type: ignore
        return None


class AKShareProvider(FinancialDataGateway):
    """
    Adapter around existing AKShare fetchers.

    This keeps source-specific logic behind a provider contract so API and
    business logic don't depend on concrete crawler implementation details.
    """

    @staticmethod
    def _invalidate_stock_cache(stock_code: str) -> None:
        cache_manager.clear_pattern(f"stock:{stock_code}:*")

    @staticmethod
    def _invalidate_stock_list_cache(market: Optional[str]) -> None:
        cache_manager.delete(f"stock_list:{market or 'all'}")

    def fetch_stock_list(self, market: Optional[str] = None) -> List[StockInfo]:
        return fetch_stock_list(market=market)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def fetch_balance_sheet(self, stock_code: str, refresh: bool = False) -> List[BalanceSheet]:
        if refresh:
            self._invalidate_stock_cache(stock_code)
        return AKShareClient.fetch_balance_sheet(stock_code, raise_on_error=True)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def fetch_income_statement(self, stock_code: str, refresh: bool = False) -> List[IncomeStatement]:
        if refresh:
            self._invalidate_stock_cache(stock_code)
        return AKShareClient.fetch_income_statement(stock_code, raise_on_error=True)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def fetch_cashflow_statement(self, stock_code: str, refresh: bool = False) -> List[CashFlowStatement]:
        if refresh:
            self._invalidate_stock_cache(stock_code)
        return AKShareClient.fetch_cashflow_statement(stock_code, raise_on_error=True)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def fetch_financial_indicators(
        self,
        stock_code: str,
        refresh: bool = False,
    ) -> Dict[str, Any]:
        if refresh:
            self._invalidate_stock_cache(stock_code)
        return AKShareClient.fetch_financial_indicators(stock_code, raise_on_error=True)

