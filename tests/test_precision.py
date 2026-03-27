"""
====================================================================
Module: test_precision.py
Purpose: precision and numeric normalization coverage
====================================================================
"""

from decimal import Decimal

from src.utils.precision import (
    AMOUNT_PRECISION,
    safe_divide,
    to_amount,
    to_ratio,
    validate_precision,
)


class TestPrecision:
    def test_to_amount_basic(self):
        assert to_amount(123.456) == Decimal("123.46")
        assert to_amount("1000.999") == Decimal("1001.00")
        assert to_amount(100) == Decimal("100.00")

    def test_to_amount_edge_cases(self):
        assert to_amount(None) == Decimal("0.00")
        assert to_amount("") == Decimal("0.00")
        assert to_amount(0) == Decimal("0.00")
        assert to_amount("--") == Decimal("0.00")

    def test_to_amount_supports_chinese_units(self):
        assert to_amount("513.66亿") == Decimal("51366000000.00")
        assert to_amount("46.70万") == Decimal("467000.00")
        assert to_amount("-6.24亿") == Decimal("-624000000.00")

    def test_to_ratio_basic(self):
        assert to_ratio(0.123456) == Decimal("0.1235")
        assert to_ratio("0.5") == Decimal("0.5000")

    def test_safe_divide_normal(self):
        result = safe_divide(Decimal("100"), Decimal("50"))
        assert result == Decimal("2.0000")

    def test_safe_divide_zero(self):
        result = safe_divide(Decimal("100"), Decimal("0"))
        assert result == Decimal("0.0000")

    def test_no_float_precision_loss(self):
        float_result = 0.1 + 0.2
        assert float_result != 0.3

        decimal_result = Decimal("0.1") + Decimal("0.2")
        assert decimal_result == Decimal("0.3")

    def test_financial_calculation_accuracy(self):
        assets = to_amount("1000000.00")
        liabilities = to_amount("600000.00")
        equity = to_amount("400000.00")

        assert assets == liabilities + equity

    def test_validate_precision(self):
        value = Decimal("123.46")
        assert validate_precision(value, AMOUNT_PRECISION) is True

        value_wrong = Decimal("123.456")
        assert validate_precision(value_wrong, AMOUNT_PRECISION) is False
