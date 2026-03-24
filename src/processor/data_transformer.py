"""
====================================================================
模块名称：data_transformer.py
模块功能：数据转换（中英文列名转换、单位转换）

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ chinese_to_english()         │ df: pd.DataFrame            │ pd.DataFrame             │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ convert_units()              │ df: pd.DataFrame            │ pd.DataFrame             │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 data_fetcher/akshare_client.py 调用
====================================================================
"""

import pandas as pd
from decimal import Decimal
from typing import Dict, Optional

from src.utils.naming_mapper import map_columns, get_all_mappings
from src.utils.precision import to_amount
from src.utils.logger import logger


def chinese_to_english(df: pd.DataFrame, mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """
    将 DataFrame 的中文列名转换为英文列名

    Args:
        df: 原始 DataFrame（中文列名）
        mapping: 自定义映射字典（None 则使用默认全量映射）

    Returns:
        pd.DataFrame: 英文列名的 DataFrame

    Examples:
        >>> df = pd.DataFrame({"股票代码": ["600519"], "净利润": [100000]})
        >>> df_en = chinese_to_english(df)
        >>> "stock_code" in df_en.columns
        True
    """
    if mapping is None:
        mapping = get_all_mappings()

    df_transformed = map_columns(df, mapping, fuzzy=True)

    logger.debug(f"Columns transformed: {list(df.columns)} → {list(df_transformed.columns)}")

    return df_transformed


def convert_units(
    df: pd.DataFrame,
    columns: Optional[list] = None,
    from_unit: str = "万元",
    to_unit: str = "元"
) -> pd.DataFrame:
    """
    转换金额单位（如 万元 → 元）

    Args:
        df: 原始 DataFrame
        columns: 需要转换的列（None 表示所有数值列）
        from_unit: 原始单位
        to_unit: 目标单位

    Returns:
        pd.DataFrame: 转换后的 DataFrame

    Examples:
        >>> df = pd.DataFrame({"amount": [100]})  # 100万元
        >>> df_converted = convert_units(df, from_unit="万元", to_unit="元")
        >>> df_converted["amount"][0]
        1000000
    """
    df_converted = df.copy()

    # 单位转换系数
    unit_factors = {
        ("万元", "元"): 10000,
        ("亿元", "元"): 100000000,
        ("亿元", "万元"): 10000,
        ("元", "万元"): 0.0001,
        ("元", "亿元"): 0.00000001,
    }

    factor = unit_factors.get((from_unit, to_unit))
    if factor is None:
        logger.warning(f"Unsupported unit conversion: {from_unit} → {to_unit}")
        return df_converted

    # 默认转换所有数值列
    if columns is None:
        columns = df_converted.select_dtypes(include=["number"]).columns.tolist()

    for col in columns:
        if col in df_converted.columns:
            df_converted[col] = df_converted[col].apply(
                lambda x: to_amount(Decimal(str(x)) * Decimal(str(factor))) if pd.notna(x) else Decimal("0")
            )

    logger.info(f"Units converted: {from_unit} → {to_unit} (factor: {factor})")

    return df_converted


"""
====================================================================
【使用示例】

from src.processor.data_transformer import chinese_to_english, convert_units

# 1. 中英文列名转换
df_en = chinese_to_english(df_cn)

# 2. 单位转换（万元 → 元）
df_yuan = convert_units(df, from_unit="万元", to_unit="元")

====================================================================
"""
