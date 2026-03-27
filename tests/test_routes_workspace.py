from src.api.dependencies import get_workspace_service
from src.main import app


def test_workspace_routes_expose_archive_first_summary_metrics_and_context(tmp_path):
    from fastapi.testclient import TestClient

    from src.crawler.interfaces import Dataset
    from src.storage.archive_repository import ArchiveRepository
    from src.storage.workspace_repository import WorkspaceRepository
    from src.api.workspace_service import WorkspaceService

    def _openapi_row(report_label: str, values: dict[str, str]) -> dict:
        return {
            "text": report_label,
            "content": [
                {
                    "data": [
                        {
                            "header": ["report_label", "", report_label],
                            "body": [[key, "", value] for key, value in values.items()],
                        }
                    ]
                }
            ],
        }

    archive_repository = ArchiveRepository(archive_root=str(tmp_path))
    archive_repository.save_dataset(
        stock_code="000001",
        stock_name="测试公司",
        market="ab",
        dataset=Dataset.INCOME_STATEMENT,
        request_url="https://finance.pae.baidu.com/selfselect/openapi",
        request_params={"group": "income_detail", "code": "000001"},
        raw_payload={
            "Result": {
                "data": [
                    _openapi_row(
                        "2025三季报",
                        {
                            "一、总营收": "5000",
                            "营业成本": "3000",
                            "四、营业利润": "1500",
                            "五、利润总额": "1600",
                            "六、合并净利润": "1200",
                        },
                    )
                ]
            }
        },
        csv_rows=[{"report_date": "2025-09-30", "一、总营收": "5000"}],
    )
    archive_repository.save_dataset(
        stock_code="000001",
        stock_name="测试公司",
        market="ab",
        dataset=Dataset.BALANCE_SHEET,
        request_url="https://finance.pae.baidu.com/selfselect/openapi",
        request_params={"group": "balance_detail", "code": "000001"},
        raw_payload={
            "Result": {
                "data": [
                    _openapi_row(
                        "2025三季报",
                        {
                            "流动资产合计": "1000",
                            "非流动资产合计": "2000",
                            "总资产": "3000",
                            "流动负债合计": "500",
                            "非流动负债合计": "500",
                            "总负债": "1000",
                            "所有者权益合计": "2000",
                        },
                    )
                ]
            }
        },
        csv_rows=[{"report_date": "2025-09-30", "总资产": "3000"}],
    )
    archive_repository.save_dataset(
        stock_code="000001",
        stock_name="测试公司",
        market="ab",
        dataset=Dataset.CASHFLOW_STATEMENT,
        request_url="https://finance.pae.baidu.com/selfselect/openapi",
        request_params={"group": "cash_flow_detail", "code": "000001"},
        raw_payload={
            "Result": {
                "data": [
                    _openapi_row(
                        "2025三季报",
                        {
                            "经营活动产生的现金流量净额": "1500",
                            "投资活动产生的现金流量净额": "-700",
                            "筹资活动产生的现金流量净额": "200",
                            "现金及现金等价物净增加额": "1000",
                        },
                    )
                ]
            }
        },
        csv_rows=[{"report_date": "2025-09-30", "经营活动产生的现金流量净额": "1500"}],
    )

    service = WorkspaceService(WorkspaceRepository(archive_root=str(tmp_path)))
    app.dependency_overrides[get_workspace_service] = lambda: service

    try:
        client = TestClient(app)

        response = client.get("/api/v2/workspaces")
        assert response.status_code == 200
        summaries = response.json()
        assert summaries[0]["stock_code"] == "000001"
        assert summaries[0]["dataset_count"] == 3

        metrics_response = client.get("/api/v2/workspaces/000001/metrics")
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        value_map = {item["key"]: item["value"] for item in metrics["values"]}
        assert value_map["roe"] == "0.6000"
        assert value_map["free_cash_flow"] == "800.00"

        context_response = client.get("/api/v2/workspaces/000001/context?profile_key=archive_review")
        assert context_response.status_code == 200
        context = context_response.json()
        assert context["profile_key"] == "archive_review"
        assert "archive-first" in context["system_prompt"]
        assert "ROE" in context["context_text"]
    finally:
        app.dependency_overrides.clear()
