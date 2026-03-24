"""
====================================================================
模块名称：data_cleaner.py
模块功能：数据清洗（处理空值、异常值）

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ clean_financial_data()       │ df: pd.DataFrame            │ pd.DataFrame             │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ handle_missing_values()      │ df: pd.DataFrame            │ pd.DataFrame             │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ remove_outliers()            │ df: pd.DataFrame            │ pd.DataFrame             │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 analyzer/ 调用（分析前清洗数据）
====================================================================
"""

import pandas as pd
import numpy as np
from typing import List, Optional
from src.utils.logger import logger


def clean_financial_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗财务数据（综合处理）

    Args:
        df: 原始 DataFrame

    Returns:
        pd.DataFrame: 清洗后的 DataFrame

    Examples:
        >>> df = pd.DataFrame({"amount": [100, None, -999, 200]})
        >>> cleaned = clean_financial_data(df)
    """
    if df.empty:
        return df

    df_cleaned = df.copy()

    # 1. 处理缺失值
    df_cleaned = handle_missing_values(df_cleaned)

    # 2. 移除异常值
    df_cleaned = remove_outliers(df_cleaned)

    # 3. 去重（基于日期）
    if "report_date" in df_cleaned.columns:
        df_cleaned = df_cleaned.drop_duplicates(subset=["report_date"], keep="first")

    # 4. 按日期排序
    if "report_date" in df_cleaned.columns:
        df_cleaned = df_cleaned.sort_values("report_date", ascending=False)

    logger.info(f"Data cleaned: {len(df)} → {len(df_cleaned)} rows")

    return df_cleaned


def handle_missing_values(df: pd.DataFrame, fill_value: float = 0.0) -> pd.DataFrame:
    """
    处理缺失值

    Args:
        df: 原始 DataFrame
        fill_value: 填充值（默认 0）

    Returns:
        pd.DataFrame: 处理后的 DataFrame
    """
    df_filled = df.copy()

    # 数值列填充为 0
    numeric_cols = df_filled.select_dtypes(include=[np.number]).columns
    df_filled[numeric_cols] = df_filled[numeric_cols].fillna(fill_value)

    # 字符串列填充为空字符串
    string_cols = df_filled.select_dtypes(include=["object"]).columns
    df_filled[string_cols] = df_filled[string_cols].fillna("")

    return df_filled


def remove_outliers(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    method: str = "iqr",
    threshold: float = 3.0
) -> pd.DataFrame:
    """
    移除异常值

    Args:
        df: 原始 DataFrame
        columns: 需要检测异常值的列（None 表示所有数值列）
        method: 检测方法（"iqr" 或 "zscore"）
        threshold: 阈值（IQR 倍数或 Z-score 标准差倍数）

    Returns:
        pd.DataFrame: 移除异常值后的 DataFrame
    """
    if df.empty:
        return df

    df_cleaned = df.copy()

    # 默认检测所有数值列
    if columns is None:
        columns = df_cleaned.select_dtypes(include=[np.number]).columns.tolist()

    if method == "iqr":
        # IQR 方法（四分位距）
        for col in columns:
            if col not in df_cleaned.columns:
                continue

            Q1 = df_cleaned[col].quantile(0.25)
            Q3 = df_cleaned[col].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR

            # 将异常值替换为边界值（而非删除行）
            df_cleaned[col] = df_cleaned[col].clip(lower=lower_bound, upper=upper_bound)

    elif method == "zscore":
        # Z-score 方法
        for col in columns:
            if col not in df_cleaned.columns:
                continue

            mean = df_cleaned[col].mean()
            std = df_cleaned[col].std()

            if std == 0:
                continue

            z_scores = np.abs((df_cleaned[col] - mean) / std)
            df_cleaned = df_cleaned[z_scores < threshold]

    return df_cleaned


"""
====================================================================
【使用示例】

from src.processor.data_cleaner import clean_financial_data

# 1. 综合清洗
df_cleaned = clean_financial_data(raw_df)

# 2. 单独处理缺失值
df_filled = handle_missing_values(df, fill_value=0)

# 3. 移除异常值
df_no_outliers = remove_outliers(df, method="iqr", threshold=3.0)

====================================================================
"""
