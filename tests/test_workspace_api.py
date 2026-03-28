from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_v2_stock_list_prefers_archive_workspace_summaries():
    response = client.get("/api/v2/stocks")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert any(item["stock_code"] == "601012" for item in payload)


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
    assert len(payload["items"]) >= 5
    keys = {item["key"] for item in payload["items"]}
    assert "dupont" in keys
    assert "cashflow_quality" in keys
    assert "solvency_pressure" in keys


def test_workspace_insight_context_endpoint_returns_prompt_injection_bundle():
    response = client.get("/api/v2/workspace/601012/insights/context")

    assert response.status_code == 200
    payload = response.json()
    assert payload["stock_code"] == "601012"
    assert payload["profile"]["key"] == "default"
    assert payload["injection_bundle"]["system_prompt"]
    assert payload["injection_bundle"]["metric_digest"]
    assert payload["injection_bundle"]["model_summary"]
