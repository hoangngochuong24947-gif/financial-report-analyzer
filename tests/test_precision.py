"""
====================================================================
模块名称：test_precision.py
模块功能：金额精度专项测试

【测试目标】
验证 Decimal 精度不丢失，确保金额计算准确
====================================================================
"""

import pytest
from decimal import Decimal
from src.utils.precision import to_amount, to_ratio, safe_divide, validate_precision, AMOUNT_PRECISION, RATIO_PRECISION


class TestPrecision:
    """精度控制测试"""

    def test_to_amount_basic(self):
        """测试基本金额转换"""
        assert to_amount(123.456) == Decimal("123.46")
        assert to_amount("1000.999") == Decimal("1001.00")
        assert to_amount(100) == Decimal("100.00")

    def test_to_amount_edge_cases(self):
        """测试边界情况"""
        assert to_amount(None) == Decimal("0.00")
        assert to_amount("") == Decimal("0.00")
        assert to_amount(0) == Decimal("0.00")

    def test_to_ratio_basic(self):
        """测试比率转换"""
        assert to_ratio(0.123456) == Decimal("0.1235")
        assert to_ratio("0.5") == Decimal("0.5000")

    def test_safe_divide_normal(self):
        """测试安全除法"""
        result = safe_divide(Decimal("100"), Decimal("50"))
        assert result == Decimal("2.0000")

    def test_safe_divide_zero(self):
        """测试除零保护"""
        result = safe_divide(Decimal("100"), Decimal("0"))
        assert result == Decimal("0.0000")

    def test_no_float_precision_loss(self):
        """测试 Decimal 避免 float 精度丢失"""
        # float 精度问题
        float_result = 0.1 + 0.2
        assert float_result != 0.3  # float 有精度问题

        # Decimal 精度正确
        decimal_result = Decimal("0.1") + Decimal("0.2")
        assert decimal_result == Decimal("0.3")

    def test_financial_calculation_accuracy(self):
        """测试财务计算精度"""
        # 模拟资产负债表等式：资产 = 负债 + 权益
        assets = to_amount("1000000.00")
        liabilities = to_amount("600000.00")
        equity = to_amount("400000.00")

        assert assets == liabilities + equity

    def test_validate_precision(self):
        """测试精度验证"""
        value = Decimal("123.46")
        assert validate_precision(value, AMOUNT_PRECISION) is True

        value_wrong = Decimal("123.456")
        assert validate_precision(value_wrong, AMOUNT_PRECISION) is False


"""
====================================================================
【运行测试】

pytest tests/test_precision.py -v

====================================================================
"""
