"""
====================================================================
模块名称：test_analyzer.py
模块功能：分析引擎测试

【测试目标】
验证财务比率计算正确（使用已知数据对比）
====================================================================
"""

import pytest
from decimal import Decimal
from datetime import date

from src.models.financial_statements import BalanceSheet, IncomeStatement, CashFlowStatement
from src.analyzer.ratio_calculator import calc_profitability, calc_solvency, calc_efficiency
from src.analyzer.dupont_analyzer import analyze as dupont_analyze
from src.analyzer.cashflow_analyzer import analyze as cashflow_analyze
from src.analyzer.trend_analyzer import calc_yoy, calc_qoq


class TestRatioCalculator:
    """财务比率计算测试"""

    @pytest.fixture
    def sample_balance_sheet(self):
        """示例资产负债表"""
        return BalanceSheet(
            stock_code="TEST",
            report_date=date(2023, 12, 31),
            total_current_assets=Decimal("1000.00"),
            total_non_current_assets=Decimal("2000.00"),
            total_assets=Decimal("3000.00"),
            total_current_liabilities=Decimal("500.00"),
            total_non_current_liabilities=Decimal("500.00"),
            total_liabilities=Decimal("1000.00"),
            total_equity=Decimal("2000.00")
        )

    @pytest.fixture
    def sample_income_statement(self):
        """示例利润表"""
        return IncomeStatement(
            stock_code="TEST",
            report_date=date(2023, 12, 31),
            total_revenue=Decimal("5000.00"),
            operating_cost=Decimal("3000.00"),
            operating_profit=Decimal("1500.00"),
            total_profit=Decimal("1600.00"),
            net_income=Decimal("1200.00")
        )

    def test_calc_profitability(self, sample_balance_sheet, sample_income_statement):
        """测试盈利能力计算"""
        metrics = calc_profitability(sample_balance_sheet, sample_income_statement)

        # ROE = 净利润 / 所有者权益 = 1200 / 2000 = 0.6
        assert metrics.roe == Decimal("0.6000")

        # ROA = 净利润 / 总资产 = 1200 / 3000 = 0.4
        assert metrics.roa == Decimal("0.4000")

        # 销售净利率 = 净利润 / 营业收入 = 1200 / 5000 = 0.24
        assert metrics.net_profit_margin == Decimal("0.2400")

    def test_calc_solvency(self, sample_balance_sheet):
        """测试偿债能力计算"""
        metrics = calc_solvency(sample_balance_sheet)

        # 流动比率 = 流动资产 / 流动负债 = 1000 / 500 = 2.0
        assert metrics.current_ratio == Decimal("2.0000")

        # 资产负债率 = 负债合计 / 资产总计 = 1000 / 3000 = 0.3333
        assert abs(metrics.debt_to_asset_ratio - Decimal("0.3333")) < Decimal("0.0001")

    def test_calc_efficiency(self, sample_balance_sheet, sample_income_statement):
        """测试运营效率计算"""
        metrics = calc_efficiency(sample_balance_sheet, sample_income_statement)

        # 总资产周转率 = 营业收入 / 总资产 = 5000 / 3000 = 1.6667
        assert abs(metrics.asset_turnover - Decimal("1.6667")) < Decimal("0.0001")

        # 权益乘数 = 总资产 / 所有者权益 = 3000 / 2000 = 1.5
        assert metrics.equity_turnover == Decimal("1.5000")


class TestDuPontAnalyzer:
    """杜邦分析测试"""

    def test_dupont_analysis(self):
        """测试杜邦分析"""
        bs = BalanceSheet(
            stock_code="TEST",
            report_date=date(2023, 12, 31),
            total_assets=Decimal("3000.00"),
            total_liabilities=Decimal("1000.00"),
            total_equity=Decimal("2000.00")
        )

        is_ = IncomeStatement(
            stock_code="TEST",
            report_date=date(2023, 12, 31),
            total_revenue=Decimal("5000.00"),
            net_income=Decimal("1200.00")
        )

        result = dupont_analyze(bs, is_)

        # 验证杜邦公式：ROE = 销售净利率 × 总资产周转率 × 权益乘数
        calculated_roe = result.net_profit_margin * result.asset_turnover * result.equity_multiplier
        assert abs(result.roe - calculated_roe) < Decimal("0.0001")


class TestTrendAnalyzer:
    """趋势分析测试"""

    def test_calc_yoy(self):
        """测试同比增长率"""
        current = Decimal("120")
        previous = Decimal("100")

        yoy = calc_yoy(current, previous)

        # (120 - 100) / 100 = 0.2 (20% 增长)
        assert yoy == Decimal("0.2000")

    def test_calc_qoq(self):
        """测试环比增长率"""
        current = Decimal("110")
        previous = Decimal("100")

        qoq = calc_qoq(current, previous)

        # (110 - 100) / 100 = 0.1 (10% 增长)
        assert qoq == Decimal("0.1000")


"""
====================================================================
【运行测试】

pytest tests/test_analyzer.py -v

====================================================================
"""
