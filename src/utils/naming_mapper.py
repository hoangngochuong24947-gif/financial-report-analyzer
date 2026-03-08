"""
====================================================================
模块名称：naming_mapper.py
模块功能：中英文字段名映射器

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ map_columns()                │ df: pd.DataFrame,           │ pd.DataFrame             │
│                              │ mapping: Dict[str, str]     │                          │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ fuzzy_match_column()         │ column: str,                │ Optional[str]            │
│                              │ mapping: Dict[str, str]     │                          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 processor/data_transformer.py 调用
→ 将 AKShare 返回的中文列名转换为英文变量名
====================================================================
"""

from typing import Dict, Optional, List
import pandas as pd
from difflib import get_close_matches


# 资产负债表字段映射
BALANCE_SHEET_MAPPING = {
    "代码": "stock_code",
    "股票代码": "stock_code",
    "证券代码": "stock_code",
    "日期": "report_date",
    "报告期": "report_date",
    "报表日期": "report_date",
    "流动资产合计": "total_current_assets",
    "流动资产总额": "total_current_assets",
    "非流动资产合计": "total_non_current_assets",
    "长期资产合计": "total_non_current_assets",
    "资产总计": "total_assets",
    "总资产": "total_assets",
    "资产合计": "total_assets",
    "流动负债合计": "total_current_liabilities",
    "短期负债合计": "total_current_liabilities",
    "非流动负债合计": "total_non_current_liabilities",
    "长期负债合计": "total_non_current_liabilities",
    "负债合计": "total_liabilities",
    "总负债": "total_liabilities",
    "负债总额": "total_liabilities",
    "所有者权益合计": "total_equity",
    "股东权益": "total_equity",
    "净资产": "total_equity",
}

# 利润表字段映射
INCOME_STATEMENT_MAPPING = {
    "代码": "stock_code",
    "股票代码": "stock_code",
    "日期": "report_date",
    "报告期": "report_date",
    "营业总收入": "total_revenue",
    "营收": "total_revenue",
    "总收入": "total_revenue",
    "营业总成本": "operating_cost",
    "总成本": "operating_cost",
    "营业利润": "operating_profit",
    "经营利润": "operating_profit",
    "利润总额": "total_profit",
    "税前利润": "total_profit",
    "净利润": "net_income",
    "纯利润": "net_income",
    "纯利": "net_income",
}

# 现金流量表字段映射
CASHFLOW_STATEMENT_MAPPING = {
    "代码": "stock_code",
    "股票代码": "stock_code",
    "日期": "report_date",
    "报告期": "report_date",
    "经营活动产生的现金流量净额": "operating_cashflow",
    "经营活动现金流量净额": "operating_cashflow",
    "经营现金流": "operating_cashflow",
    "投资活动产生的现金流量净额": "investing_cashflow",
    "投资活动现金流量净额": "investing_cashflow",
    "投资现金流": "investing_cashflow",
    "筹资活动产生的现金流量净额": "financing_cashflow",
    "筹资活动现金流量净额": "financing_cashflow",
    "融资现金流": "financing_cashflow",
    "现金及现金等价物净增加额": "net_cashflow",
    "现金净增加额": "net_cashflow",
}

# 财务指标字段映射
FINANCIAL_METRICS_MAPPING = {
    "净资产收益率": "roe",
    "净资产收益率(%)": "roe",
    "ROE": "roe",
    "资产负债率": "debt_to_asset_ratio",
    "资产负债率(%)": "debt_to_asset_ratio",
    "负债率": "debt_to_asset_ratio",
    "流动比率": "current_ratio",
    "市盈率": "pe_ratio",
    "市盈率-动态": "pe_ratio",
    "PE": "pe_ratio",
    "市净率": "pb_ratio",
    "PB": "pb_ratio",
    "销售净利率": "net_profit_margin",
    "销售净利率(%)": "net_profit_margin",
    "净利润率": "net_profit_margin",
}


def map_columns(df: pd.DataFrame, mapping: Dict[str, str], fuzzy: bool = True) -> pd.DataFrame:
    """
    将 DataFrame 的中文列名映射为英文列名

    Args:
        df: 原始 DataFrame（中文列名）
        mapping: 中英文映射字典
        fuzzy: 是否启用模糊匹配（处理列名变体）

    Returns:
        pd.DataFrame: 英文列名的 DataFrame

    Examples:
        >>> df = pd.DataFrame({"股票代码": ["600519"], "净利润": [100000]})
        >>> mapped_df = map_columns(df, INCOME_STATEMENT_MAPPING)
        >>> mapped_df.columns
        Index(['stock_code', 'net_income'], dtype='object')
    """
    df_copy = df.copy()
    rename_dict = {}

    for col in df_copy.columns:
        # 精确匹配
        if col in mapping:
            rename_dict[col] = mapping[col]
        # 模糊匹配
        elif fuzzy:
            matched = fuzzy_match_column(col, mapping)
            if matched:
                rename_dict[col] = matched

    return df_copy.rename(columns=rename_dict)


def fuzzy_match_column(column: str, mapping: Dict[str, str], cutoff: float = 0.8) -> Optional[str]:
    """
    模糊匹配列名（处理空格、括号等变体）

    Args:
        column: 待匹配的列名
        mapping: 映射字典
        cutoff: 相似度阈值（0-1）

    Returns:
        Optional[str]: 匹配到的英文列名，未匹配返回 None

    Examples:
        >>> fuzzy_match_column("净利润 ", INCOME_STATEMENT_MAPPING)
        'net_income'
        >>> fuzzy_match_column("净利润（万元）", INCOME_STATEMENT_MAPPING)
        'net_income'
    """
    # 清理列名（去空格、括号内容）
    cleaned = column.strip().split("(")[0].split("（")[0].strip()

    # 在映射字典的键中查找最接近的匹配
    matches = get_close_matches(cleaned, mapping.keys(), n=1, cutoff=cutoff)

    if matches:
        return mapping[matches[0]]

    return None


def get_all_mappings() -> Dict[str, str]:
    """
    获取所有字段映射的合并字典

    Returns:
        Dict[str, str]: 合并后的映射字典
    """
    all_mappings = {}
    all_mappings.update(BALANCE_SHEET_MAPPING)
    all_mappings.update(INCOME_STATEMENT_MAPPING)
    all_mappings.update(CASHFLOW_STATEMENT_MAPPING)
    all_mappings.update(FINANCIAL_METRICS_MAPPING)
    return all_mappings


"""
====================================================================
【使用示例】

from src.utils.naming_mapper import map_columns, BALANCE_SHEET_MAPPING

# 1. 映射资产负债表列名
raw_df = akshare.stock_financial_report_sina("600519", "资产负债表")
mapped_df = map_columns(raw_df, BALANCE_SHEET_MAPPING)

# 2. 模糊匹配（自动处理列名变体）
# "净利润（万元）" → "net_income"
# "净利润 " → "net_income"

====================================================================
"""
