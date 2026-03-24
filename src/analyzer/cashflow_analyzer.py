"""
====================================================================
模块名称：cashflow_analyzer.py
模块功能：现金流分析

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ analyze()                    │ cf: CashFlowStatement,      │ CashFlowResult           │
│                              │ is_: IncomeStatement        │                          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 api/routes_analysis.py 调用
→ 被 llm_engine/report_generator.py 调用
====================================================================
"""

from decimal import Decimal
from src.models.financial_statements import CashFlowStatement, IncomeStatement
from src.models.financial_metrics import CashFlowResult
from src.utils.precision import safe_divide, to_amount
from src.utils.logger import logger


def analyze(cf: CashFlowStatement, is_: IncomeStatement, capex: Decimal = None) -> CashFlowResult:
    """
    现金流分析

    Args:
        cf: 现金流量表
        is_: 利润表
        capex: 资本支出（Capital Expenditure），默认为投资现金流的绝对值

    Returns:
        CashFlowResult: 现金流分析结果

    Examples:
        >>> result = analyze(cashflow_statement, income_statement)
        >>> result.free_cash_flow  # 自由现金流
    """
    # 1. 自由现金流 = 经营活动现金流 - 资本支出
    # 注：资本支出通常为负值，这里取投资现金流的绝对值作为近似
    if capex is None:
        capex = abs(cf.investing_cashflow)

    free_cash_flow = cf.operating_cashflow - capex

    # 2. 现金流量与净利润比率 = 经营活动现金流 / 净利润
    # 该比率 > 1 说明盈利质量高（现金流充沛）
    cash_to_profit_ratio = safe_divide(cf.operating_cashflow, is_.net_income)

    # 3. 经营现金流覆盖率 = 经营活动现金流 / 流动负债
    # 注：需要资产负债表数据，这里简化为 0
    operating_cash_coverage = Decimal("0")

    logger.info(f"Cash Flow Analysis: FCF={free_cash_flow}, Cash/Profit={cash_to_profit_ratio}")

    return CashFlowResult(
        operating_cashflow=cf.operating_cashflow,
        free_cash_flow=free_cash_flow,
        cash_to_profit_ratio=cash_to_profit_ratio,
        operating_cash_coverage=operating_cash_coverage
    )


"""
====================================================================
【使用示例】

from src.analyzer.cashflow_analyzer import analyze

# 现金流分析
result = analyze(cashflow_statement, income_statement)

print(f"经营现金流: {result.operating_cashflow}")
print(f"自由现金流: {result.free_cash_flow}")
print(f"现金流/净利润: {result.cash_to_profit_ratio}")

# 分析结论：
# - 自由现金流 > 0：企业有充足的现金用于分红、扩张
# - 现金流/净利润 > 1：盈利质量高，现金回收能力强
# - 现金流/净利润 < 1：可能存在应收账款过多、盈利质量差

====================================================================
"""
