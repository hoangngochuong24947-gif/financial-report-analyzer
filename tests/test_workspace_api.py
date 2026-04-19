from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.api.dependencies import get_crawler_service, get_workspace_service
from src.main import app


client = TestClient(app)


def _seed_minimal_workspace(tmp_path):
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
                            "一、营业总收入": "5000",
                            "营业成本": "3000",
                            "四、营业利润": "1500",
                            "五、利润总额": "1600",
                            "六、合并净利润": "1200",
                        },
                    )
                ]
            }
        },
        csv_rows=[{"report_date": "2025-09-30", "一、营业总收入": "5000"}],
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

    return WorkspaceService(WorkspaceRepository(archive_root=str(tmp_path)))


def test_v2_stock_list_returns_full_stock_universe_not_just_archived_subset():
    response = client.get("/api/v2/stocks")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert len(payload) > 1000
    assert any(item["stock_code"] == "601012" for item in payload)
    assert any(item["stock_code"] == "300750" for item in payload)


def test_v2_stock_list_falls_back_to_workspace_data_when_crawler_unavailable():
    class FailingCrawlerService:
        def fetch_stock_list(self, market=None, refresh=False):
            raise RuntimeError("crawler unavailable")

    class WorkspaceOnlyService:
        def list_workspaces(self, limit=20):
            return [
                SimpleNamespace(
                    stock_code="601012",
                    stock_name="隆基绿能",
                    market="主板",
                ),
                SimpleNamespace(
                    stock_code="300750",
                    stock_name="宁德时代",
                    market="创业板",
                ),
            ]

    app.dependency_overrides[get_crawler_service] = lambda: FailingCrawlerService()
    app.dependency_overrides[get_workspace_service] = lambda: WorkspaceOnlyService()

    try:
        response = client.get("/api/v2/stocks")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload == [
        {
            "stock_code": "601012",
            "stock_name": "隆基绿能",
            "industry": None,
            "market": "主板",
            "list_date": None,
        },
        {
            "stock_code": "300750",
            "stock_name": "宁德时代",
            "industry": None,
            "market": "创业板",
            "list_date": None,
        },
    ]


def test_workspace_snapshot_endpoint_uses_archive_data():
    response = client.get("/api/v2/workspace/601012/snapshot")

    assert response.status_code == 200
    payload = response.json()
    assert payload["stock"]["stock_code"] == "601012"
    assert payload["stock"]["stock_name"]
    assert len(payload["available_periods"]) >= 1
    assert "balance_sheet" in payload["statements"]
    assert "income_statement" in payload["statements"]


def test_workspace_metric_catalog_endpoint_exposes_core_catalog():
    response = client.get("/api/v2/workspace/601012/metrics/catalog")

    assert response.status_code == 200
    payload = response.json()
    assert payload["stock_code"] == "601012"
    assert payload["total"] >= 20
    keys = {item["key"] for item in payload["items"]}
    assert "roe" in keys
    assert "debt_to_asset_ratio" in keys
    assert "operating_cashflow_margin" in keys


def test_workspace_metric_values_endpoint_returns_grouped_values():
    response = client.get("/api/v2/workspace/601012/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["stock_code"] == "601012"
    assert payload["report_date"]
    assert payload["categories"]
    assert "profitability" in payload["categories"]
    assert any(item["key"] == "roe" for item in payload["categories"]["profitability"])


def test_workspace_models_endpoint_returns_analysis_cards():
    response = client.get("/api/v2/workspace/601012/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["stock_code"] == "601012"
    assert len(payload["items"]) >= 16
    keys = {item["key"] for item in payload["items"]}
    assert "dupont" in keys
    assert "cashflow_quality" in keys
    assert "earnings_quality" in keys
    assert "capital_intensity" in keys
    assert "solvency_pressure" in keys
    assert "liquidity_risk" in keys
    assert "debt_service_capacity" in keys
    assert "capital_structure_resilience" in keys
    assert "valuation_snapshot" in keys
    assert "shareholder_return_quality" in keys
    assert "valuation_compression_risk" in keys


def test_workspace_insight_context_endpoint_returns_prompt_injection_bundle():
    response = client.get("/api/v2/workspace/601012/insights/context")

    assert response.status_code == 200
    payload = response.json()
    assert payload["stock_code"] == "601012"
    assert payload["profile"]["key"] == "default"
    assert payload["injection_bundle"]["system_prompt"]
    assert payload["injection_bundle"]["metric_digest"]
    assert payload["injection_bundle"]["model_summary"]


def test_workspace_statements_endpoint_returns_tabbed_period_view_and_lang():
    response = client.get("/api/v2/workspace/601012/statements?lang=en")

    assert response.status_code == 200
    payload = response.json()
    assert payload["lang"] == "en"
    assert payload["available_periods"]
    assert payload["selected_period"] == payload["available_periods"][0]
    assert payload["selected_period"] in payload["available_periods"]
    assert [tab["key"] for tab in payload["tabs"]] == [
        "balance_sheet",
        "income_statement",
        "cashflow_statement",
    ]
    assert all(isinstance(tab["rows"], list) for tab in payload["tabs"])

    missing_period_response = client.get("/api/v2/workspace/601012/statements?period=1900-01-01")
    assert missing_period_response.status_code == 404


def test_workspace_statements_endpoint_returns_empty_rows_for_missing_tabs(tmp_path):
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
                            "一、营业总收入": "5000",
                            "营业成本": "3000",
                            "四、营业利润": "1500",
                            "五、利润总额": "1600",
                            "六、合并净利润": "1200",
                        },
                    )
                ]
            }
        },
        csv_rows=[{"report_date": "2025-09-30", "一、营业总收入": "5000"}],
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

    service = WorkspaceService(WorkspaceRepository(archive_root=str(tmp_path)))
    app.dependency_overrides[get_workspace_service] = lambda: service

    try:
        response = client.get("/api/v2/workspace/000001/statements?period=2025-09-30")
        assert response.status_code == 200
        payload = response.json()
        tabs = {tab["key"]: tab for tab in payload["tabs"]}
        assert tabs["balance_sheet"]["rows"]
        assert tabs["income_statement"]["rows"]
        assert tabs["cashflow_statement"]["rows"] == []
    finally:
        app.dependency_overrides.clear()


def test_workspace_insights_generate_endpoint_returns_fixed_structure_and_lang(tmp_path):
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
                            "一、营业总收入": "5000",
                            "营业成本": "3000",
                            "四、营业利润": "1500",
                            "五、利润总额": "1600",
                            "六、合并净利润": "1200",
                        },
                    )
                ]
            }
        },
        csv_rows=[{"report_date": "2025-09-30", "一、营业总收入": "5000"}],
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
        response = client.post("/api/v2/workspace/000001/insights/generate", json={"lang": "en"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["lang"] == "en"
        assert payload["summary"]
        assert payload["highlights"]
        assert payload["risks"]
        assert payload["open_questions"]
        assert payload["actions"]
        assert payload["evidence"]
        assert payload["model_version"] == "workspace-insights-v1"
        assert datetime.fromisoformat(payload["generated_at"])
        assert {"summary", "highlights", "risks", "open_questions", "actions", "evidence", "generated_at", "model_version"}.issubset(
            payload.keys()
        )
    finally:
        app.dependency_overrides.clear()


def test_workspace_statements_endpoint_returns_tabbed_detail_rows():
    response = client.get("/api/v2/workspace/601012/statements", params={"lang": "en-US"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["stock"]["stock_code"] == "601012"
    assert payload["selected_period"]
    assert payload["available_periods"]
    assert len(payload["tabs"]) == 3
    keys = {tab["key"] for tab in payload["tabs"]}
    assert keys == {"balance_sheet", "income_statement", "cashflow_statement"}
    balance_tab = next(tab for tab in payload["tabs"] if tab["key"] == "balance_sheet")
    assert balance_tab["rows"]
    first_row = balance_tab["rows"][0]
    assert first_row["label"]
    assert "value" in first_row
    assert "display_value" in first_row


def test_workspace_statements_endpoint_rejects_unknown_period():
    response = client.get("/api/v2/workspace/601012/statements", params={"period": "1999-12-31"})

    assert response.status_code == 404


def test_workspace_insight_generate_endpoint_returns_structured_report(monkeypatch):
    from src.api import workspace_service as workspace_service_module

    def fake_analyze(prompt: str, system_prompt: str = "") -> str:
        assert prompt
        assert system_prompt
        return """
        {
          "summary": "Cash generation is stable and leverage is manageable.",
          "highlights": ["ROE remains resilient", "Operating cash flow covers profit"],
          "risks": ["Revenue growth slowed year over year"],
          "open_questions": ["Need to verify capex sustainability"],
          "actions": ["Track next report revenue recovery"],
          "evidence": ["roe", "cashflow_quality", "revenue_yoy"]
        }
        """

    monkeypatch.setattr(workspace_service_module, "get_llm_client", lambda: type("FakeClient", (), {"analyze": staticmethod(fake_analyze)})())

    response = client.post(
        "/api/v2/workspace/601012/insights/generate",
        json={"lang": "en-US"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["stock_code"] == "601012"
    assert payload["summary"]
    assert payload["highlights"]
    assert payload["risks"]
    assert payload["open_questions"]
    assert payload["actions"]
    assert payload["evidence"]
    assert payload["model_version"]
    assert payload["generated_at"]


def test_workspace_saved_report_endpoints_round_trip(tmp_path, monkeypatch):
    from src.api import workspace_service as workspace_service_module

    def fake_analyze(prompt: str, system_prompt: str = "") -> str:
        assert prompt
        assert system_prompt
        return """
        {
          "summary": "Archive-backed report persisted successfully.",
          "highlights": ["Operating cash flow remains positive"],
          "risks": ["Revenue growth slowed"],
          "open_questions": ["Need to validate next quarter orders"],
          "actions": ["Review next quarterly statement"],
          "evidence": ["roe", "free_cash_flow"]
        }
        """

    monkeypatch.setattr(workspace_service_module, "get_llm_client", lambda: type("FakeClient", (), {"analyze": staticmethod(fake_analyze)})())

    service = _seed_minimal_workspace(tmp_path)
    app.dependency_overrides[get_workspace_service] = lambda: service

    try:
        generated = client.post("/api/v2/workspace/000001/insights/generate", params={"lang": "en-US"})
        assert generated.status_code == 200
        generated_payload = generated.json()
        assert generated_payload["summary"] == "Archive-backed report persisted successfully."

        latest = client.get("/api/v2/workspace/000001/insights/report", params={"lang": "en-US"})
        assert latest.status_code == 200
        latest_payload = latest.json()
        assert latest_payload["summary"] == generated_payload["summary"]
        assert latest_payload["report_date"] == "2025-09-30"

        history = client.get("/api/v2/workspace/000001/insights/history", params={"limit": 5})
        assert history.status_code == 200
        history_payload = history.json()
        assert len(history_payload) == 1
        assert history_payload[0]["stock_code"] == "000001"
        assert history_payload[0]["markdown_path"].endswith("insight_report.md")
    finally:
        app.dependency_overrides.clear()


def test_workspace_statement_export_endpoints_return_downloadable_files(tmp_path):
    service = _seed_minimal_workspace(tmp_path)
    app.dependency_overrides[get_workspace_service] = lambda: service

    try:
        current_csv = client.get(
            "/api/v2/workspace/000001/statements/export",
            params={"statement_key": "balance_sheet", "period": "2025-09-30", "format": "csv", "lang": "zh-CN"},
        )
        assert current_csv.status_code == 200
        assert current_csv.headers["content-type"].startswith("text/csv")
        assert "attachment;" in current_csv.headers["content-disposition"]
        assert "流动资产合计".encode("utf-8") in current_csv.content

        history_xlsx = client.get(
            "/api/v2/workspace/000001/statements/export/all",
            params={"format": "xlsx", "lang": "zh-CN"},
        )
        assert history_xlsx.status_code == 200
        assert history_xlsx.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert history_xlsx.content[:2] == b"PK"

        history_csv = client.get(
            "/api/v2/workspace/000001/statements/export/all",
            params={"format": "csv", "lang": "zh-CN"},
        )
        assert history_csv.status_code == 200
        assert history_csv.headers["content-type"].startswith("text/csv")
        assert "balance_sheet" in history_csv.content.decode("utf-8-sig")
    finally:
        app.dependency_overrides.clear()


def test_workspace_saved_report_endpoint_returns_404_when_missing(tmp_path):
    service = _seed_minimal_workspace(tmp_path)
    app.dependency_overrides[get_workspace_service] = lambda: service

    try:
        response = client.get("/api/v2/workspace/000001/insights/report", params={"lang": "en-US"})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_workspace_historical_period_insight_generation_is_rejected(tmp_path):
    service = _seed_minimal_workspace(tmp_path)
    app.dependency_overrides[get_workspace_service] = lambda: service

    try:
        response = client.post(
            "/api/v2/workspace/000001/insights/generate",
            params={"lang": "en-US"},
            json={"period": "2024-12-31", "lang": "en-US"},
        )
        assert response.status_code == 400
        assert "Historical-period insight generation is not supported yet" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
