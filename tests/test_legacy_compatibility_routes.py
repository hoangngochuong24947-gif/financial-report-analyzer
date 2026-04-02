from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_legacy_stock_routes_are_backed_by_workspace_analysis(tmp_path):
    from src.api.dependencies import get_analysis_facade
    from src.api.analysis_facade import AnalysisFacade
    from src.crawler.interfaces import FinancialSnapshot
    from src.models.financial_statements import BalanceSheet, CashFlowStatement, IncomeStatement
    from src.models.workspace_metrics import WorkspaceArchiveItem
    from src.storage.workspace_repository import ArchiveWorkspace

    class StubWorkspaceService:
        def get_workspace(self, stock_code: str) -> ArchiveWorkspace:
            assert stock_code == "000001"
            return ArchiveWorkspace(
                stock_code="000001",
                stock_name="测试公司",
                market="ab",
                snapshot=FinancialSnapshot(
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
                ),
                indicator_snapshot={},
                archives=[
                    WorkspaceArchiveItem(
                        stock_code="000001",
                        stock_name="测试公司",
                        market="ab",
                        dataset="income_statement",
                        fetched_at="2025-10-01T00:00:00Z",
                        raw_path="raw.json",
                        csv_path="data.csv",
                        manifest_path="manifest.json",
                        row_count=1,
                        status="success",
                        report_date="2025-09-30",
                    )
                ],
                latest_report_date="2025-09-30",
            )

    workspace_service = StubWorkspaceService()
    app.dependency_overrides[get_analysis_facade] = lambda: AnalysisFacade(workspace_service=workspace_service)

    try:
        statements = client.get("/api/stocks/000001/statements")
        assert statements.status_code == 200
        statement_payload = statements.json()
        assert statement_payload["stock_code"] == "000001"
        assert statement_payload["balance_sheet"]
        assert statement_payload["income_statement"]

        ratios = client.get("/api/stocks/000001/ratios")
        assert ratios.status_code == 200
        ratio_payload = ratios.json()
        assert ratio_payload["stock_code"] == "000001"
        assert ratio_payload["profitability"]["roe"] == "0.6000"
        assert ratio_payload["solvency"]["current_ratio"] == "2.0000"

        dupont = client.get("/api/stocks/000001/dupont")
        assert dupont.status_code == 200
        assert dupont.json()["roe"] == "0.6000"

        cashflow = client.get("/api/stocks/000001/cashflow")
        assert cashflow.status_code == 200
        assert cashflow.json()["free_cash_flow"] == "800.00"
    finally:
        app.dependency_overrides.clear()
