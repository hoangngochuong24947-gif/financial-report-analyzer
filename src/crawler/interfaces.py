from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from src.models.financial_statements import (
    BalanceSheet,
    CashFlowStatement,
    IncomeStatement,
)
from src.models.stock_info import StockInfo


class CrawlerError(RuntimeError):
    """Base crawler-domain exception."""


class CrawlerDataNotFoundError(CrawlerError):
    """Raised when no usable data can be fetched for a stock."""


class CrawlerDependencyError(CrawlerError):
    """Raised when optional crawler dependencies are unavailable."""


class Dataset(str, Enum):
    """Supported financial datasets."""

    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASHFLOW_STATEMENT = "cashflow_statement"
    FINANCIAL_INDICATORS = "financial_indicators"


class FinancialDataGateway(Protocol):
    """Abstraction for financial data providers."""

    def fetch_stock_list(self, market: Optional[str] = None, refresh: bool = False) -> List[StockInfo]:
        ...

    def fetch_balance_sheet(self, stock_code: str, refresh: bool = False) -> List[BalanceSheet]:
        ...

    def fetch_income_statement(self, stock_code: str, refresh: bool = False) -> List[IncomeStatement]:
        ...

    def fetch_cashflow_statement(self, stock_code: str, refresh: bool = False) -> List[CashFlowStatement]:
        ...

    def fetch_financial_indicators(
        self,
        stock_code: str,
        refresh: bool = False,
    ) -> Dict[str, Any]:
        ...


@dataclass(frozen=True)
class FinancialSnapshot:
    """A normalized data bundle for one stock."""

    stock_code: str
    balance_sheets: List[BalanceSheet]
    income_statements: List[IncomeStatement]
    cashflow_statements: List[CashFlowStatement]
