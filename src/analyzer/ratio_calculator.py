"""
====================================================================
模块名称：ratio_calculator.py
模块功能：计算各类财务比率（盈利能力、偿债能力、运营效率）

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ calc_profitability()         │ bs: BalanceSheet,           │ ProfitabilityMetrics     │
│                              │ is_: IncomeStatement        │                          │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ calc_solvency()              │ bs: BalanceSheet            │ SolvencyMetrics          │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ calc_efficiency()            │ bs: BalanceSheet,           │ EfficiencyMetrics        │
│                              │ is_: IncomeStatement        │                          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 api/routes_analysis.py 调用（提供 REST API）
→ 被 llm_engine/report_generator.py 调用（AI报告生成）
→ 被 export/excel_exporter.py 调用（Excel导出）
====================================================================
"""

from decimal import Decimal
from src.models.financial_statements import BalanceSheet, IncomeStatement
from src.models.financial_metrics import ProfitabilityMetrics, SolvencyMetrics, EfficiencyMetrics
from src.utils.precision import safe_divide, to_ratio
from src.utils.logger import logger


def calc_profitability(bs: BalanceSheet, is_: IncomeStatement) -> ProfitabilityMetrics:
    """
    计算盈利能力指标

    Args:
        bs: 资产负债表
        is_: 利润表

    Returns:
        ProfitabilityMetrics: 盈利能力指标

    Examples:
        >>> metrics = calc_profitability(balance_sheet, income_statement)
        >>> metrics.roe  # 净资产收益率
    """
    # ROE = 净利润 / 所有者权益
    roe = safe_divide(is_.net_income, bs.total_equity)

    # ROA = 净利润 / 总资产
    roa = safe_divide(is_.net_income, bs.total_assets)

    # 销售净利率 = 净利润 / 营业总收入
    net_profit_margin = safe_divide(is_.net_income, is_.total_revenue)

    # 毛利率 = (营业收入 - 营业成本) / 营业收入
    gross_profit = is_.total_revenue - is_.operating_cost
    gross_profit_margin = safe_divide(gross_profit, is_.total_revenue)

    logger.debug(f"Profitability calculated: ROE={roe}, ROA={roa}")

    return ProfitabilityMetrics(
        roe=roe,
        roa=roa,
        net_profit_margin=net_profit_margin,
        gross_profit_margin=gross_profit_margin
    )


def calc_solvency(bs: BalanceSheet) -> SolvencyMetrics:
    """
    计算偿债能力指标

    Args:
        bs: 资产负债表

    Returns:
        SolvencyMetrics: 偿债能力指标

    Examples:
        >>> metrics = calc_solvency(balance_sheet)
        >>> metrics.current_ratio  # 流动比率
    """
    # 流动比率 = 流动资产 / 流动负债
    current_ratio = safe_divide(bs.total_current_assets, bs.total_current_liabilities)

    # 速动比率 = (流动资产 - 存货) / 流动负债
    # 注：简化版，假设存货为流动资产的30%（实际应从详细报表获取）
    quick_assets = bs.total_current_assets * Decimal("0.7")
    quick_ratio = safe_divide(quick_assets, bs.total_current_liabilities)

    # 资产负债率 = 负债合计 / 资产总计
    debt_to_asset_ratio = safe_divide(bs.total_liabilities, bs.total_assets)

    # 产权比率 = 负债合计 / 所有者权益
    debt_to_equity_ratio = safe_divide(bs.total_liabilities, bs.total_equity)

    logger.debug(f"Solvency calculated: Current Ratio={current_ratio}, Debt/Asset={debt_to_asset_ratio}")

    return SolvencyMetrics(
        current_ratio=current_ratio,
        quick_ratio=quick_ratio,
        debt_to_asset_ratio=debt_to_asset_ratio,
        debt_to_equity_ratio=debt_to_equity_ratio
    )


def calc_efficiency(bs: BalanceSheet, is_: IncomeStatement) -> EfficiencyMetrics:
    """
    计算运营效率指标

    Args:
        bs: 资产负债表
        is_: 利润表

    Returns:
        EfficiencyMetrics: 运营效率指标

    Examples:
        >>> metrics = calc_efficiency(balance_sheet, income_statement)
        >>> metrics.asset_turnover  # 总资产周转率
    """
    # 总资产周转率 = 营业收入 / 总资产
    asset_turnover = safe_divide(is_.total_revenue, bs.total_assets)

    # 权益乘数 = 总资产 / 所有者权益
    equity_turnover = safe_divide(bs.total_assets, bs.total_equity)

    logger.debug(f"Efficiency calculated: Asset Turnover={asset_turnover}, Equity Multiplier={equity_turnover}")

    return EfficiencyMetrics(
        asset_turnover=asset_turnover,
        equity_turnover=equity_turnover,
        inventory_turnover=None,  # 需要详细数据
        receivables_turnover=None  # 需要详细数据
    )


"""
====================================================================
【使用示例】

from src.analyzer.ratio_calculator import calc_profitability, calc_solvency, calc_efficiency

# 1. 计算盈利能力
profitability = calc_profitability(balance_sheet, income_statement)
print(f"ROE: {profitability.roe}")

# 2. 计算偿债能力
solvency = calc_solvency(balance_sheet)
print(f"流动比率: {solvency.current_ratio}")

# 3. 计算运营效率
efficiency = calc_efficiency(balance_sheet, income_statement)
print(f"总资产周转率: {efficiency.asset_turnover}")

====================================================================
"""
