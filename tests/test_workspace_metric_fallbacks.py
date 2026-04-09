from datetime import date
from decimal import Decimal

from src.crawler.interfaces import FinancialSnapshot
from src.models.financial_statements import BalanceSheet, CashFlowStatement, IncomeStatement


def test_workspace_metric_engine_uses_indicator_fallback_for_sparse_archive_snapshot():
    from src.analyzer.metric_engine import WorkspaceMetricEngine

    snapshot = FinancialSnapshot(
        stock_code="601012",
        balance_sheets=[
            BalanceSheet(
                stock_code="601012",
                report_date=date(2025, 9, 30),
                total_current_assets=Decimal("89144000000"),
                total_non_current_assets=Decimal("0"),
                total_assets=Decimal("0"),
                total_current_liabilities=Decimal("0"),
                total_non_current_liabilities=Decimal("0"),
                total_liabilities=Decimal("0"),
                total_equity=Decimal("0"),
            )
        ],
        income_statements=[
            IncomeStatement(
                stock_code="601012",
                report_date=date(2025, 9, 30),
                total_revenue=Decimal("50915000000"),
                operating_cost=Decimal("0"),
                operating_profit=Decimal("0"),
                total_profit=Decimal("0"),
                net_income=Decimal("0"),
            )
        ],
        cashflow_statements=[
            CashFlowStatement(
                stock_code="601012",
                report_date=date(2025, 9, 30),
                operating_cashflow=Decimal("1819000000"),
                investing_cashflow=Decimal("0"),
                financing_cashflow=Decimal("0"),
                net_cashflow=Decimal("0"),
            )
        ],
    )

    engine = WorkspaceMetricEngine()
    bundle = engine.build_bundle(
        snapshot=snapshot,
        stock_name="隆基绿能",
        indicator_snapshot={
            "roe": -7.438225617470899,
            "roa": -0.022429721293259736,
            "debt_to_asset_ratio": 0.6243104016283303,
            "net_income": -3453559769.08,
            "total_assets": 153971435649.18,
            "total_equity": 57857069570.65,
        },
    )

    values = {item.key: item.value for item in bundle.values}
    expected_liabilities = (
        Decimal("153971435649.18") * Decimal("0.6243")
    ).quantize(Decimal("0.01"))
    assert values["roe"] == "-0.0744"
    assert values["roa"] == "-0.0224"
    assert values["total_assets"] == "153971435649.18"
    assert values["total_equity"] == "57857069570.65"
    assert values["total_liabilities"] == str(expected_liabilities)
    assert values["ocf_to_assets"] == "0.0118"
    assert values["equity_to_liabilities"] == "0.6019"
    assert values["gross_profit_to_assets"] == "0.3307"
