"""
====================================================================
模块名称：akshare_client.py
模块功能：AKShare API 封装，获取三大财务报表

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ fetch_balance_sheet()        │ stock_code: str             │ List[BalanceSheet]       │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ fetch_income_statement()     │ stock_code: str             │ List[IncomeStatement]    │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ fetch_cashflow_statement()   │ stock_code: str             │ List[CashFlowStatement]  │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ fetch_financial_indicators() │ stock_code: str             │ Dict[str, Any]           │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 processor/ 调用（数据清洗）
→ 被 analyzer/ 调用（财务分析）
→ 被 api/ 调用（API 路由）
====================================================================
"""

import akshare as ak
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal

from src.models.financial_statements import BalanceSheet, IncomeStatement, CashFlowStatement
from src.data_fetcher.cache_manager import cache_manager
from src.utils.logger import logger
from src.utils.naming_mapper import map_columns, BALANCE_SHEET_MAPPING, INCOME_STATEMENT_MAPPING, CASHFLOW_STATEMENT_MAPPING
from src.utils.precision import to_amount


class AKShareClient:
    """
    AKShare API 客户端，封装财务数据获取
    """

    @staticmethod
    def fetch_balance_sheet(stock_code: str) -> List[BalanceSheet]:
        """
        获取资产负债表

        Args:
            stock_code: 股票代码（如 "600519"）

        Returns:
            List[BalanceSheet]: 资产负债表列表（多个报告期）

        Examples:
            >>> client = AKShareClient()
            >>> sheets = client.fetch_balance_sheet("600519")
            >>> len(sheets) > 0
            True
        """
        cache_key = f"stock:{stock_code}:balance_sheet"

        # 尝试从缓存获取
        cached = cache_manager.get(cache_key)
        if cached:
            logger.info(f"Balance sheet loaded from cache: {stock_code}")
            return [BalanceSheet(**item) for item in cached]

        try:
            logger.info(f"Fetching balance sheet from AKShare: {stock_code}")

            # 调用 AKShare API
            df = ak.stock_financial_report_sina(stock=stock_code, symbol="资产负债表")

            if df.empty:
                logger.warning(f"No balance sheet data for {stock_code}")
                return []

            # 映射列名（中文 → 英文）
            df = map_columns(df, BALANCE_SHEET_MAPPING)

            # 转换为 pydantic 模型
            balance_sheets = []
            for _, row in df.iterrows():
                try:
                    sheet = BalanceSheet(
                        stock_code=stock_code,
                        report_date=pd.to_datetime(row.get("report_date", row.get("日期"))).date(),
                        total_current_assets=to_amount(row.get("total_current_assets", 0)),
                        total_non_current_assets=to_amount(row.get("total_non_current_assets", 0)),
                        total_assets=to_amount(row.get("total_assets", 0)),
                        total_current_liabilities=to_amount(row.get("total_current_liabilities", 0)),
                        total_non_current_liabilities=to_amount(row.get("total_non_current_liabilities", 0)),
                        total_liabilities=to_amount(row.get("total_liabilities", 0)),
                        total_equity=to_amount(row.get("total_equity", 0)),
                    )
                    balance_sheets.append(sheet)
                except Exception as e:
                    logger.warning(f"Failed to parse balance sheet row: {e}")
                    continue

            logger.info(f"Fetched {len(balance_sheets)} balance sheet records for {stock_code}")

            # 缓存结果
            cache_manager.set(
                cache_key,
                [sheet.model_dump(mode='json') for sheet in balance_sheets],
                ttl=3600
            )

            return balance_sheets

        except Exception as e:
            logger.error(f"Failed to fetch balance sheet for {stock_code}: {e}")
            return []

    @staticmethod
    def fetch_income_statement(stock_code: str) -> List[IncomeStatement]:
        """
        获取利润表

        Args:
            stock_code: 股票代码

        Returns:
            List[IncomeStatement]: 利润表列表
        """
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

            income_statements = []
            for _, row in df.iterrows():
                try:
                    statement = IncomeStatement(
                        stock_code=stock_code,
                        report_date=pd.to_datetime(row.get("report_date", row.get("日期"))).date(),
                        total_revenue=to_amount(row.get("total_revenue", 0)),
                        operating_cost=to_amount(row.get("operating_cost", 0)),
                        operating_profit=to_amount(row.get("operating_profit", 0)),
                        total_profit=to_amount(row.get("total_profit", 0)),
                        net_income=to_amount(row.get("net_income", 0)),
                    )
                    income_statements.append(statement)
                except Exception as e:
                    logger.warning(f"Failed to parse income statement row: {e}")
                    continue

            logger.info(f"Fetched {len(income_statements)} income statement records for {stock_code}")

            cache_manager.set(
                cache_key,
                [stmt.model_dump(mode='json') for stmt in income_statements],
                ttl=3600
            )

            return income_statements

        except Exception as e:
            logger.error(f"Failed to fetch income statement for {stock_code}: {e}")
            return []

    @staticmethod
    def fetch_cashflow_statement(stock_code: str) -> List[CashFlowStatement]:
        """
        获取现金流量表

        Args:
            stock_code: 股票代码

        Returns:
            List[CashFlowStatement]: 现金流量表列表
        """
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

            cashflow_statements = []
            for _, row in df.iterrows():
                try:
                    statement = CashFlowStatement(
                        stock_code=stock_code,
                        report_date=pd.to_datetime(row.get("report_date", row.get("日期"))).date(),
                        operating_cashflow=to_amount(row.get("operating_cashflow", 0)),
                        investing_cashflow=to_amount(row.get("investing_cashflow", 0)),
                        financing_cashflow=to_amount(row.get("financing_cashflow", 0)),
                        net_cashflow=to_amount(row.get("net_cashflow", 0)),
                    )
                    cashflow_statements.append(statement)
                except Exception as e:
                    logger.warning(f"Failed to parse cash flow statement row: {e}")
                    continue

            logger.info(f"Fetched {len(cashflow_statements)} cash flow statement records for {stock_code}")

            cache_manager.set(
                cache_key,
                [stmt.model_dump(mode='json') for stmt in cashflow_statements],
                ttl=3600
            )

            return cashflow_statements

        except Exception as e:
            logger.error(f"Failed to fetch cash flow statement for {stock_code}: {e}")
            return []

    @staticmethod
    def fetch_financial_indicators(stock_code: str) -> Dict[str, Any]:
        """
        获取财务指标（如 ROE、资产负债率等）

        Args:
            stock_code: 股票代码

        Returns:
            Dict[str, Any]: 财务指标字典
        """
        cache_key = f"stock:{stock_code}:financial_indicators"

        cached = cache_manager.get(cache_key)
        if cached:
            logger.info(f"Financial indicators loaded from cache: {stock_code}")
            return cached

        try:
            logger.info(f"Fetching financial indicators from AKShare: {stock_code}")

            df = ak.stock_financial_analysis_indicator(symbol=stock_code)

            if df.empty:
                logger.warning(f"No financial indicators for {stock_code}")
                return {}

            # 取最新一期数据
            latest = df.iloc[0].to_dict()

            cache_manager.set(cache_key, latest, ttl=3600)

            return latest

        except Exception as e:
            logger.error(f"Failed to fetch financial indicators for {stock_code}: {e}")
            return {}


"""
====================================================================
【使用示例】

from src.data_fetcher.akshare_client import AKShareClient

client = AKShareClient()

# 1. 获取资产负债表
balance_sheets = client.fetch_balance_sheet("600519")
for sheet in balance_sheets:
    print(f"{sheet.report_date}: 总资产 = {sheet.total_assets}")

# 2. 获取利润表
income_statements = client.fetch_income_statement("600519")

# 3. 获取现金流量表
cashflow_statements = client.fetch_cashflow_statement("600519")

# 4. 获取财务指标
indicators = client.fetch_financial_indicators("600519")

====================================================================
"""
