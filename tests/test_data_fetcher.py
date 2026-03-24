"""
====================================================================
模块名称：test_data_fetcher.py
模块功能：数据采集层测试

【测试目标】
验证 AKShare 接口能正常返回数据
====================================================================
"""

import pytest
from src.data_fetcher.akshare_client import AKShareClient
from src.data_fetcher.stock_list import fetch_stock_list
from src.models.financial_statements import BalanceSheet, IncomeStatement, CashFlowStatement


class TestAKShareClient:
    """AKShare 客户端测试"""

    @pytest.fixture
    def client(self):
        """创建客户端实例"""
        return AKShareClient()

    def test_fetch_balance_sheet(self, client):
        """测试获取资产负债表"""
        # 使用贵州茅台作为测试股票
        sheets = client.fetch_balance_sheet("600519")

        assert len(sheets) > 0
        assert isinstance(sheets[0], BalanceSheet)
        assert sheets[0].stock_code == "600519"
        assert sheets[0].total_assets > 0

    def test_fetch_income_statement(self, client):
        """测试获取利润表"""
        statements = client.fetch_income_statement("600519")

        assert len(statements) > 0
        assert isinstance(statements[0], IncomeStatement)
        assert statements[0].stock_code == "600519"

    def test_fetch_cashflow_statement(self, client):
        """测试获取现金流量表"""
        statements = client.fetch_cashflow_statement("600519")

        assert len(statements) > 0
        assert isinstance(statements[0], CashFlowStatement)
        assert statements[0].stock_code == "600519"

    def test_fetch_financial_indicators(self, client):
        """测试获取财务指标"""
        indicators = client.fetch_financial_indicators("600519")

        assert isinstance(indicators, dict)
        assert len(indicators) > 0


class TestStockList:
    """股票列表测试"""

    def test_fetch_stock_list(self):
        """测试获取股票列表"""
        stocks = fetch_stock_list()

        assert len(stocks) > 0
        assert stocks[0].stock_code is not None
        assert stocks[0].stock_name is not None

    def test_fetch_stock_list_with_market_filter(self):
        """测试市场筛选"""
        main_board = fetch_stock_list(market="主板")

        assert len(main_board) > 0
        assert all(stock.market == "主板" for stock in main_board)


"""
====================================================================
【运行测试】

pytest tests/test_data_fetcher.py -v

注意：这些测试需要网络连接，因为会实际调用 AKShare API

====================================================================
"""
