"""
====================================================================
模块名称：test_processor.py
模块功能：数据处理层测试

【测试目标】
验证数据清洗、转换、验证功能正常
====================================================================
"""

import pytest
import pandas as pd
from decimal import Decimal
from datetime import date

from src.processor.data_cleaner import clean_financial_data, handle_missing_values, remove_outliers
from src.processor.data_transformer import chinese_to_english, convert_units
from src.processor.data_validator import validate_balance_sheet, validate_amounts
from src.models.financial_statements import BalanceSheet


class TestDataCleaner:
    """数据清洗测试"""

    def test_handle_missing_values(self):
        """测试缺失值处理"""
        df = pd.DataFrame({
            "amount": [100, None, 200],
            "name": ["A", None, "C"]
        })

        df_filled = handle_missing_values(df)

        assert df_filled["amount"].isna().sum() == 0
        assert df_filled["name"].isna().sum() == 0

    def test_remove_outliers_iqr(self):
        """测试 IQR 异常值移除"""
        df = pd.DataFrame({
            "value": [10, 12, 11, 13, 100, 12, 11]  # 100 是异常值
        })

        df_cleaned = remove_outliers(df, columns=["value"], method="iqr")

        # 异常值应该被裁剪到边界值
        assert df_cleaned["value"].max() < 100


class TestDataTransformer:
    """数据转换测试"""

    def test_chinese_to_english(self):
        """测试中英文列名转换"""
        df = pd.DataFrame({
            "股票代码": ["600519"],
            "净利润": [100000]
        })

        df_en = chinese_to_english(df)

        assert "stock_code" in df_en.columns
        assert "net_income" in df_en.columns

    def test_convert_units(self):
        """测试单位转换"""
        df = pd.DataFrame({
            "amount": [Decimal("100")]  # 100万元
        })

        df_converted = convert_units(df, columns=["amount"], from_unit="万元", to_unit="元")

        assert df_converted["amount"][0] == Decimal("1000000.00")


class TestDataValidator:
    """数据验证测试"""

    def test_validate_balance_sheet_valid(self):
        """测试资产负债表验证（正确数据）"""
        bs = BalanceSheet(
            stock_code="600519",
            report_date=date(2023, 12, 31),
            total_current_assets=Decimal("100.00"),
            total_non_current_assets=Decimal("200.00"),
            total_assets=Decimal("300.00"),
            total_current_liabilities=Decimal("50.00"),
            total_non_current_liabilities=Decimal("50.00"),
            total_liabilities=Decimal("100.00"),
            total_equity=Decimal("200.00")
        )

        result = validate_balance_sheet(bs)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_balance_sheet_invalid(self):
        """测试资产负债表验证（错误数据）"""
        bs = BalanceSheet(
            stock_code="600519",
            report_date=date(2023, 12, 31),
            total_current_assets=Decimal("100.00"),
            total_non_current_assets=Decimal("200.00"),
            total_assets=Decimal("400.00"),  # 错误：应该是 300
            total_current_liabilities=Decimal("50.00"),
            total_non_current_liabilities=Decimal("50.00"),
            total_liabilities=Decimal("100.00"),
            total_equity=Decimal("200.00")
        )

        result = validate_balance_sheet(bs)

        assert result.is_valid is False
        assert len(result.errors) > 0


"""
====================================================================
【运行测试】

pytest tests/test_processor.py -v

====================================================================
"""
