from __future__ import annotations

from typing import Any, Dict, List

from src.crawler.providers.baidu_finance.extractors import flatten_openapi_rows
from src.models.financial_statements import BalanceSheet, CashFlowStatement, IncomeStatement
from src.utils.precision import to_amount


INCOME_FIELD_ALIASES = {
    "total_revenue": ["\u4e00\u3001\u603b\u8425\u6536", "\u8425\u4e1a\u603b\u6536\u5165", "\u603b\u8425\u6536"],
    "operating_cost": ["\u8425\u4e1a\u6210\u672c"],
    "operating_profit": ["\u56db\u3001\u8425\u4e1a\u5229\u6da6", "\u8425\u4e1a\u5229\u6da6"],
    "total_profit": ["\u4e94\u3001\u5229\u6da6\u603b\u989d", "\u5229\u6da6\u603b\u989d"],
    "net_income": [
        "\u516d\u3001\u5408\u5e76\u51c0\u5229\u6da6",
        "\u5f52\u5c5e\u4e8e\u6bcd\u516c\u53f8\u6240\u6709\u8005\u7684\u51c0\u5229\u6da6",
        "\u51c0\u5229\u6da6",
    ],
}

BALANCE_FIELD_ALIASES = {
    "total_current_assets": ["\u6d41\u52a8\u8d44\u4ea7\u5408\u8ba1"],
    "total_non_current_assets": ["\u975e\u6d41\u52a8\u8d44\u4ea7\u5408\u8ba1"],
    "total_assets": ["\u603b\u8d44\u4ea7", "\u8d44\u4ea7\u603b\u8ba1", "\u8d1f\u503a\u548c\u6240\u6709\u8005\u6743\u76ca(\u6216\u80a1\u4e1c\u6743\u76ca)\u603b\u8ba1"],
    "total_current_liabilities": ["\u6d41\u52a8\u8d1f\u503a\u5408\u8ba1"],
    "total_non_current_liabilities": ["\u975e\u6d41\u52a8\u8d1f\u503a\u5408\u8ba1"],
    "total_liabilities": ["\u603b\u8d1f\u503a", "\u8d1f\u503a\u5408\u8ba1"],
    "total_equity": ["\u6240\u6709\u8005\u6743\u76ca(\u6216\u80a1\u4e1c\u6743\u76ca)\u5408\u8ba1", "\u5f52\u5c5e\u6bcd\u516c\u53f8\u80a1\u4e1c\u6743\u76ca\u5408\u8ba1"],
}

CASHFLOW_FIELD_ALIASES = {
    "operating_cashflow": ["\u7ecf\u8425\u6d3b\u52a8\u4ea7\u751f\u7684\u73b0\u91d1\u6d41\u91cf\u51c0\u989d"],
    "investing_cashflow": ["\u6295\u8d44\u6d3b\u52a8\u4ea7\u751f\u7684\u73b0\u91d1\u6d41\u91cf\u51c0\u989d"],
    "financing_cashflow": ["\u7b79\u8d44\u6d3b\u52a8\u4ea7\u751f\u7684\u73b0\u91d1\u6d41\u91cf\u51c0\u989d"],
    "net_cashflow": ["\u73b0\u91d1\u53ca\u73b0\u91d1\u7b49\u4ef7\u7269\u51c0\u589e\u52a0\u989d"],
}


def _pick_value(values: Dict[str, Any], aliases: List[str]) -> Any:
    for alias in aliases:
        if alias in values:
            return values[alias]
    return 0


def parse_income_statements(stock_code: str, result: Dict[str, Any]) -> List[IncomeStatement]:
    statements: List[IncomeStatement] = []
    for row in flatten_openapi_rows(result):
        values = row["values"]
        statements.append(
            IncomeStatement(
                stock_code=stock_code,
                report_date=row["report_date"],
                total_revenue=to_amount(_pick_value(values, INCOME_FIELD_ALIASES["total_revenue"])),
                operating_cost=to_amount(_pick_value(values, INCOME_FIELD_ALIASES["operating_cost"])),
                operating_profit=to_amount(_pick_value(values, INCOME_FIELD_ALIASES["operating_profit"])),
                total_profit=to_amount(_pick_value(values, INCOME_FIELD_ALIASES["total_profit"])),
                net_income=to_amount(_pick_value(values, INCOME_FIELD_ALIASES["net_income"])),
            )
        )
    return statements


def parse_balance_sheets(stock_code: str, result: Dict[str, Any]) -> List[BalanceSheet]:
    sheets: List[BalanceSheet] = []
    for row in flatten_openapi_rows(result):
        values = row["values"]
        sheets.append(
            BalanceSheet(
                stock_code=stock_code,
                report_date=row["report_date"],
                total_current_assets=to_amount(_pick_value(values, BALANCE_FIELD_ALIASES["total_current_assets"])),
                total_non_current_assets=to_amount(_pick_value(values, BALANCE_FIELD_ALIASES["total_non_current_assets"])),
                total_assets=to_amount(_pick_value(values, BALANCE_FIELD_ALIASES["total_assets"])),
                total_current_liabilities=to_amount(
                    _pick_value(values, BALANCE_FIELD_ALIASES["total_current_liabilities"])
                ),
                total_non_current_liabilities=to_amount(
                    _pick_value(values, BALANCE_FIELD_ALIASES["total_non_current_liabilities"])
                ),
                total_liabilities=to_amount(_pick_value(values, BALANCE_FIELD_ALIASES["total_liabilities"])),
                total_equity=to_amount(_pick_value(values, BALANCE_FIELD_ALIASES["total_equity"])),
            )
        )
    return sheets


def parse_cashflow_statements(stock_code: str, result: Dict[str, Any]) -> List[CashFlowStatement]:
    statements: List[CashFlowStatement] = []
    for row in flatten_openapi_rows(result):
        values = row["values"]
        statements.append(
            CashFlowStatement(
                stock_code=stock_code,
                report_date=row["report_date"],
                operating_cashflow=to_amount(_pick_value(values, CASHFLOW_FIELD_ALIASES["operating_cashflow"])),
                investing_cashflow=to_amount(_pick_value(values, CASHFLOW_FIELD_ALIASES["investing_cashflow"])),
                financing_cashflow=to_amount(_pick_value(values, CASHFLOW_FIELD_ALIASES["financing_cashflow"])),
                net_cashflow=to_amount(_pick_value(values, CASHFLOW_FIELD_ALIASES["net_cashflow"])),
            )
        )
    return statements
