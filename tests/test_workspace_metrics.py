from decimal import Decimal
from datetime import date

from src.crawler.interfaces import FinancialSnapshot
from src.models.financial_statements import BalanceSheet, CashFlowStatement, IncomeStatement


def test_workspace_metric_engine_builds_catalog_and_values_from_archive_snapshot():
    from src.analyzer.metric_engine import WorkspaceMetricEngine

    snapshot = FinancialSnapshot(
        stock_code="000001",
        balance_sheets=[
            BalanceSheet(
                stock_code="000001",
                report_date=date(2025, 9, 30),
                total_current_assets=Decimal("1000"),
                total_non_current_assets=Decimal("2000"),
                total_assets=Decimal("3000"),
                total_current_liabilities=Decimal("500"),
                total_non_current_liabilities=Decimal("500"),
                total_liabilities=Decimal("1000"),
                total_equity=Decimal("2000"),
            )
        ],
        income_statements=[
            IncomeStatement(
                stock_code="000001",
                report_date=date(2025, 9, 30),
                total_revenue=Decimal("5000"),
                operating_cost=Decimal("3000"),
                operating_profit=Decimal("1500"),
                total_profit=Decimal("1600"),
                net_income=Decimal("1200"),
            ),
            IncomeStatement(
                stock_code="000001",
                report_date=date(2025, 6, 30),
                total_revenue=Decimal("4500"),
                operating_cost=Decimal("2800"),
                operating_profit=Decimal("1300"),
                total_profit=Decimal("1350"),
                net_income=Decimal("1000"),
            ),
        ],
        cashflow_statements=[
            CashFlowStatement(
                stock_code="000001",
                report_date=date(2025, 9, 30),
                operating_cashflow=Decimal("1500"),
                investing_cashflow=Decimal("-700"),
                financing_cashflow=Decimal("200"),
                net_cashflow=Decimal("1000"),
            )
        ],
    )

    engine = WorkspaceMetricEngine()
    bundle = engine.build_bundle(snapshot=snapshot, stock_name="测试公司")

    assert bundle.stock_code == "000001"
    assert bundle.stock_name == "测试公司"

    catalog_keys = {item.key for item in bundle.catalog}
    assert {"roe", "current_ratio", "free_cash_flow", "net_income_yoy"}.issubset(catalog_keys)

    values = {item.key: item.value for item in bundle.values}
    assert values["roe"] == "0.6000"
    assert values["current_ratio"] == "2.0000"
    assert values["free_cash_flow"] == "800.00"
    assert values["net_income_yoy"] == "0.2000"
