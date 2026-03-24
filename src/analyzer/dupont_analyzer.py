"""
====================================================================
模块名称：dupont_analyzer.py
模块功能：杜邦分析（ROE 三因素拆解）

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ analyze()                    │ bs: BalanceSheet,           │ DuPontResult             │
│                              │ is_: IncomeStatement        │                          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 api/routes_analysis.py 调用
→ 被 llm_engine/report_generator.py 调用
====================================================================
"""

from decimal import Decimal
from src.models.financial_statements import BalanceSheet, IncomeStatement
from src.models.financial_metrics import DuPontResult
from src.utils.precision import safe_divide, to_ratio
from src.utils.logger import logger


def analyze(bs: BalanceSheet, is_: IncomeStatement) -> DuPontResult:
    """
    杜邦分析：ROE 三因素拆解

    公式：ROE = 销售净利率 × 总资产周转率 × 权益乘数

    Args:
        bs: 资产负债表
        is_: 利润表

    Returns:
        DuPontResult: 杜邦分析结果

    Examples:
        >>> result = analyze(balance_sheet, income_statement)
        >>> result.roe
        Decimal('0.1500')
    """
    # 1. 销售净利率 = 净利润 / 营业收入
    net_profit_margin = safe_divide(is_.net_income, is_.total_revenue)

    # 2. 总资产周转率 = 营业收入 / 总资产
    asset_turnover = safe_divide(is_.total_revenue, bs.total_assets)

    # 3. 权益乘数 = 总资产 / 所有者权益
    equity_multiplier = safe_divide(bs.total_assets, bs.total_equity)

    # 4. ROE = 三因素相乘
    roe = net_profit_margin * asset_turnover * equity_multiplier

    # 验证：ROE 也可以直接计算
    roe_direct = safe_divide(is_.net_income, bs.total_equity)

    # 检查两种计算方式的差异
    diff = abs(roe - roe_direct)
    if diff > Decimal("0.0001"):
        logger.warning(f"DuPont ROE mismatch: {roe} vs {roe_direct} (diff: {diff})")

    logger.info(f"DuPont Analysis: ROE={roe} = {net_profit_margin} × {asset_turnover} × {equity_multiplier}")

    return DuPontResult(
        roe=roe,
        net_profit_margin=net_profit_margin,
        asset_turnover=asset_turnover,
        equity_multiplier=equity_multiplier
    )


"""
====================================================================
【使用示例】

from src.analyzer.dupont_analyzer import analyze

# 杜邦分析
dupont = analyze(balance_sheet, income_statement)

print(f"ROE: {dupont.roe}")
print(f"  = 销售净利率 ({dupont.net_profit_margin})")
print(f"  × 总资产周转率 ({dupont.asset_turnover})")
print(f"  × 权益乘数 ({dupont.equity_multiplier})")

# 分析结论：
# - 如果销售净利率高，说明盈利能力强
# - 如果总资产周转率高，说明资产使用效率高
# - 如果权益乘数高，说明财务杠杆高（负债多）

====================================================================
"""
