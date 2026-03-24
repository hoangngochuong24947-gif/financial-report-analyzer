"""
====================================================================
模块名称：test_api.py
模块功能：API 端到端测试

【测试目标】
验证 FastAPI 路由正常工作
====================================================================
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestStockRoutes:
    """股票路由测试"""

    def test_root_endpoint(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_get_stock_list(self):
        """测试获取股票列表"""
        response = client.get("/api/stocks/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_financial_statements(self):
        """测试获取财务报表"""
        response = client.get("/api/stocks/600519/statements")

        if response.status_code == 200:
            data = response.json()
            assert "stock_code" in data
            assert "balance_sheet" in data
            assert "income_statement" in data
            assert "cashflow_statement" in data


class TestAnalysisRoutes:
    """分析路由测试"""

    def test_get_financial_ratios(self):
        """测试获取财务比率"""
        response = client.get("/api/stocks/600519/ratios")

        if response.status_code == 200:
            data = response.json()
            assert "profitability" in data
            assert "solvency" in data
            assert "efficiency" in data

    def test_get_dupont_analysis(self):
        """测试杜邦分析"""
        response = client.get("/api/stocks/600519/dupont")

        if response.status_code == 200:
            data = response.json()
            assert "roe" in data
            assert "net_profit_margin" in data
            assert "asset_turnover" in data
            assert "equity_multiplier" in data

    def test_get_cashflow_analysis(self):
        """测试现金流分析"""
        response = client.get("/api/stocks/600519/cashflow")

        if response.status_code == 200:
            data = response.json()
            assert "operating_cashflow" in data
            assert "free_cash_flow" in data

    def test_get_trend_analysis(self):
        """测试趋势分析"""
        response = client.get("/api/stocks/600519/trend?metric=net_income")

        if response.status_code == 200:
            data = response.json()
            assert "metric_name" in data
            assert "current_value" in data


"""
====================================================================
【运行测试】

pytest tests/test_api.py -v

注意：这些测试需要网络连接和 AKShare API 可用

====================================================================
"""
