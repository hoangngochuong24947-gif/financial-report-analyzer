"""
====================================================================
模块名称：trend_analyzer.py
模块功能：趋势分析（同比、环比、多年趋势）

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ calc_yoy()                   │ current: Decimal,           │ Decimal                  │
│                              │ previous: Decimal           │                          │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ calc_qoq()                   │ current: Decimal,           │ Decimal                  │
│                              │ previous: Decimal           │                          │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ analyze_trend()              │ metric_name: str,           │ TrendResult              │
│                              │ current: Decimal,           │                          │
│                              │ previous: Decimal           │                          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 api/routes_analysis.py 调用
====================================================================
"""

from decimal import Decimal
from typing import Optional
from src.models.financial_metrics import TrendResult
from src.utils.precision import safe_divide, to_ratio
from src.utils.logger import logger


def calc_yoy(current: Decimal, previous: Decimal) -> Decimal:
    """
    计算同比增长率（Year-over-Year）

    Args:
        current: 当期值
        previous: 去年同期值

    Returns:
        Decimal: 同比增长率（如 0.1500 表示增长 15%）

    Examples:
        >>> calc_yoy(Decimal("120"), Decimal("100"))
        Decimal('0.2000')  # 增长 20%
    """
    if previous == 0:
        return Decimal("0")

    growth = safe_divide(current - previous, previous)

    return growth


def calc_qoq(current: Decimal, previous: Decimal) -> Decimal:
    """
    计算环比增长率（Quarter-over-Quarter）

    Args:
        current: 当期值
        previous: 上期值

    Returns:
        Decimal: 环比增长率

    Examples:
        >>> calc_qoq(Decimal("110"), Decimal("100"))
        Decimal('0.1000')  # 增长 10%
    """
    if previous == 0:
        return Decimal("0")

    growth = safe_divide(current - previous, previous)

    return growth


def analyze_trend(
    metric_name: str,
    current: Decimal,
    previous: Optional[Decimal] = None,
    year_ago: Optional[Decimal] = None
) -> TrendResult:
    """
    综合趋势分析

    Args:
        metric_name: 指标名称（如 "净利润"）
        current: 当期值
        previous: 上期值（用于环比）
        year_ago: 去年同期值（用于同比）

    Returns:
        TrendResult: 趋势分析结果

    Examples:
        >>> result = analyze_trend("净利润", Decimal("120"), Decimal("110"), Decimal("100"))
        >>> result.yoy_growth  # 同比增长 20%
        >>> result.qoq_growth  # 环比增长 9.09%
    """
    yoy_growth = None
    qoq_growth = None

    if year_ago is not None:
        yoy_growth = calc_yoy(current, year_ago)

    if previous is not None:
        qoq_growth = calc_qoq(current, previous)

    logger.debug(f"Trend analysis for {metric_name}: YoY={yoy_growth}, QoQ={qoq_growth}")

    return TrendResult(
        metric_name=metric_name,
        current_value=current,
        previous_value=previous,
        yoy_growth=yoy_growth,
        qoq_growth=qoq_growth
    )


"""
====================================================================
【使用示例】

from src.analyzer.trend_analyzer import analyze_trend, calc_yoy

# 1. 计算同比增长率
yoy = calc_yoy(Decimal("120"), Decimal("100"))  # 20% 增长

# 2. 综合趋势分析
trend = analyze_trend(
    metric_name="净利润",
    current=Decimal("120"),
    previous=Decimal("110"),
    year_ago=Decimal("100")
)

print(f"当期值: {trend.current_value}")
print(f"同比增长: {trend.yoy_growth}")
print(f"环比增长: {trend.qoq_growth}")

====================================================================
"""
