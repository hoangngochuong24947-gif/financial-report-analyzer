"""AKShare data access client."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

import akshare as ak
import pandas as pd

from src.data_fetcher.cache_manager import cache_manager
from src.models.financial_statements import BalanceSheet, CashFlowStatement, IncomeStatement
from src.utils.logger import logger
from src.utils.naming_mapper import (
    BALANCE_SHEET_MAPPING,
    CASHFLOW_STATEMENT_MAPPING,
    INCOME_STATEMENT_MAPPING,
    map_columns,
)
from src.utils.precision import to_amount


class AKShareClient:
    """Wrapper around AKShare financial endpoints with cache support."""

    @staticmethod
    def _to_scalar(value: Any, default: Any = 0) -> Any:
        if isinstance(value, pd.Series):
            non_null_values = [v for v in value.tolist() if not pd.isna(v)]
            return non_null_values[0] if non_null_values else default
        return value if value is not None else default

    @staticmethod
    def _parse_report_date(row: pd.Series) -> Optional[date]:
        for key in ("report_date", "日期", "报告日期", "报告期", "公告日期", "date"):
            value = AKShareClient._to_scalar(row.get(key), default=None)
            if value is None:
                continue

            parsed = pd.to_datetime(value, errors="coerce")
            if isinstance(parsed, pd.Series):
                parsed = parsed.dropna()
                if parsed.empty:
                    continue
                parsed = parsed.iloc[0]

            if pd.isna(parsed):
                continue

            if hasattr(parsed, "date"):
                return parsed.date()

        return None

    @staticmethod
    def _build_fallback_indicators(stock_code: str) -> Dict[str, Any]:
        balance_sheets = AKShareClient.fetch_balance_sheet(stock_code)
        income_statements = AKShareClient.fetch_income_statement(stock_code)

        if not balance_sheets or not income_statements:
            return {}

        bs = balance_sheets[0]
        is_ = income_statements[0]

        total_assets = float(bs.total_assets)
        total_equity = float(bs.total_equity)
        total_liabilities = float(bs.total_liabilities)
        net_income = float(is_.net_income)

        return {
            "report_date": str(bs.report_date),
            "roe": (net_income / total_equity) if total_equity else None,
            "roa": (net_income / total_assets) if total_assets else None,
            "debt_to_asset_ratio": (total_liabilities / total_assets) if total_assets else None,
            "net_income": net_income,
            "total_assets": total_assets,
            "total_equity": total_equity,
        }

    @staticmethod
    def fetch_balance_sheet(
        stock_code: str,
        raise_on_error: bool = False,
    ) -> List[BalanceSheet]:
        cache_key = f"stock:{stock_code}:balance_sheet"

        cached = cache_manager.get(cache_key)
        if cached:
            logger.info(f"Balance sheet loaded from cache: {stock_code}")
            return [BalanceSheet(**item) for item in cached]

        try:
            logger.info(f"Fetching balance sheet from AKShare: {stock_code}")
            df = ak.stock_financial_report_sina(stock=stock_code, symbol="资产负债表")

            if df.empty:
                logger.warning(f"No balance sheet data for {stock_code}")
                return []

            df = map_columns(df, BALANCE_SHEET_MAPPING)

            balance_sheets: List[BalanceSheet] = []
            for _, row in df.iterrows():
                report_date = AKShareClient._parse_report_date(row)
                if report_date is None:
                    logger.debug("Skip balance sheet row without valid report_date")
                    continue

                try:
                    sheet = BalanceSheet(
                        stock_code=stock_code,
                        report_date=report_date,
                        total_current_assets=to_amount(AKShareClient._to_scalar(row.get("total_current_assets", 0))),
                        total_non_current_assets=to_amount(
                            AKShareClient._to_scalar(row.get("total_non_current_assets", 0))
                        ),
                        total_assets=to_amount(AKShareClient._to_scalar(row.get("total_assets", 0))),
                        total_current_liabilities=to_amount(
                            AKShareClient._to_scalar(row.get("total_current_liabilities", 0))
                        ),
                        total_non_current_liabilities=to_amount(
                            AKShareClient._to_scalar(row.get("total_non_current_liabilities", 0))
                        ),
                        total_liabilities=to_amount(AKShareClient._to_scalar(row.get("total_liabilities", 0))),
                        total_equity=to_amount(AKShareClient._to_scalar(row.get("total_equity", 0))),
                    )
                    balance_sheets.append(sheet)
                except Exception as e:
                    logger.warning(f"Failed to parse balance sheet row: {e}")

            logger.info(f"Fetched {len(balance_sheets)} balance sheet records for {stock_code}")

            cache_manager.set(
                cache_key,
                [sheet.model_dump(mode="json") for sheet in balance_sheets],
                ttl=3600,
            )
            return balance_sheets

        except Exception as e:
            logger.error(f"Failed to fetch balance sheet for {stock_code}: {e}")
            if raise_on_error:
                raise
            return []

    @staticmethod
    def fetch_income_statement(
        stock_code: str,
        raise_on_error: bool = False,
    ) -> List[IncomeStatement]:
        cache_key = f"stock:{stock_code}:income_statement"

        cached = cache_manager.get(cache_key)
        if cached:
            logger.info(f"Income statement loaded from cache: {stock_code}")
            return [IncomeStatement(**item) for item in cached]

        try:
            logger.info(f"Fetching income statement from AKShare: {stock_code}")
            df = ak.stock_financial_report_sina(stock=stock_code, symbol="利润表")

            if df.empty:
                logger.warning(f"No income statement data for {stock_code}")
                return []

            df = map_columns(df, INCOME_STATEMENT_MAPPING)

            income_statements: List[IncomeStatement] = []
            for _, row in df.iterrows():
                report_date = AKShareClient._parse_report_date(row)
                if report_date is None:
                    logger.debug("Skip income statement row without valid report_date")
                    continue

                try:
                    statement = IncomeStatement(
                        stock_code=stock_code,
                        report_date=report_date,
                        total_revenue=to_amount(AKShareClient._to_scalar(row.get("total_revenue", 0))),
                        operating_cost=to_amount(AKShareClient._to_scalar(row.get("operating_cost", 0))),
                        operating_profit=to_amount(AKShareClient._to_scalar(row.get("operating_profit", 0))),
                        total_profit=to_amount(AKShareClient._to_scalar(row.get("total_profit", 0))),
                        net_income=to_amount(AKShareClient._to_scalar(row.get("net_income", 0))),
                    )
                    income_statements.append(statement)
                except Exception as e:
                    logger.warning(f"Failed to parse income statement row: {e}")

            logger.info(f"Fetched {len(income_statements)} income statement records for {stock_code}")

            cache_manager.set(
                cache_key,
                [stmt.model_dump(mode="json") for stmt in income_statements],
                ttl=3600,
            )
            return income_statements

        except Exception as e:
            logger.error(f"Failed to fetch income statement for {stock_code}: {e}")
            if raise_on_error:
                raise
            return []

    @staticmethod
    def fetch_cashflow_statement(
        stock_code: str,
        raise_on_error: bool = False,
    ) -> List[CashFlowStatement]:
        cache_key = f"stock:{stock_code}:cashflow_statement"

        cached = cache_manager.get(cache_key)
        if cached:
            logger.info(f"Cash flow statement loaded from cache: {stock_code}")
            return [CashFlowStatement(**item) for item in cached]

        try:
            logger.info(f"Fetching cash flow statement from AKShare: {stock_code}")
            df = ak.stock_financial_report_sina(stock=stock_code, symbol="现金流量表")

            if df.empty:
                logger.warning(f"No cash flow statement data for {stock_code}")
                return []

            df = map_columns(df, CASHFLOW_STATEMENT_MAPPING)

            cashflow_statements: List[CashFlowStatement] = []
            for _, row in df.iterrows():
                report_date = AKShareClient._parse_report_date(row)
                if report_date is None:
                    logger.debug("Skip cashflow statement row without valid report_date")
                    continue

                try:
                    statement = CashFlowStatement(
                        stock_code=stock_code,
                        report_date=report_date,
                        operating_cashflow=to_amount(AKShareClient._to_scalar(row.get("operating_cashflow", 0))),
                        investing_cashflow=to_amount(AKShareClient._to_scalar(row.get("investing_cashflow", 0))),
                        financing_cashflow=to_amount(AKShareClient._to_scalar(row.get("financing_cashflow", 0))),
                        net_cashflow=to_amount(AKShareClient._to_scalar(row.get("net_cashflow", 0))),
                    )
                    cashflow_statements.append(statement)
                except Exception as e:
                    logger.warning(f"Failed to parse cash flow statement row: {e}")

            logger.info(f"Fetched {len(cashflow_statements)} cash flow statement records for {stock_code}")

            cache_manager.set(
                cache_key,
                [stmt.model_dump(mode="json") for stmt in cashflow_statements],
                ttl=3600,
            )
            return cashflow_statements

        except Exception as e:
            logger.error(f"Failed to fetch cash flow statement for {stock_code}: {e}")
            if raise_on_error:
                raise
            return []

    @staticmethod
    def fetch_financial_indicators(
        stock_code: str,
        raise_on_error: bool = False,
    ) -> Dict[str, Any]:
        cache_key = f"stock:{stock_code}:financial_indicators"

        cached = cache_manager.get(cache_key)
        if cached:
            logger.info(f"Financial indicators loaded from cache: {stock_code}")
            return cached

        try:
            logger.info(f"Fetching financial indicators from AKShare: {stock_code}")
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)

            if df.empty:
                fallback = AKShareClient._build_fallback_indicators(stock_code)
                if fallback:
                    logger.warning(
                        f"No financial indicators from endpoint for {stock_code}; "
                        "using statement-derived fallback"
                    )
                    cache_manager.set(cache_key, fallback, ttl=3600)
                    return fallback

                logger.warning(f"No financial indicators for {stock_code}")
                return {}

            latest = df.iloc[0].to_dict()
            cache_manager.set(cache_key, latest, ttl=3600)
            return latest

        except Exception as e:
            logger.error(f"Failed to fetch financial indicators for {stock_code}: {e}")
            if raise_on_error:
                raise
            fallback = AKShareClient._build_fallback_indicators(stock_code)
            if fallback:
                logger.warning(f"Using fallback financial indicators for {stock_code}")
                return fallback
            return {}
