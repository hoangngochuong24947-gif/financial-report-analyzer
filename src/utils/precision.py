"""
====================================================================
模块名称：precision.py
模块功能：金额和比率精度控制工具

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ to_amount()                  │ value: Any                  │ Decimal                  │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ to_ratio()                   │ value: Any                  │ Decimal                  │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ safe_divide()                │ numerator: Decimal,         │ Decimal                  │
│                              │ denominator: Decimal        │                          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被所有层调用（data_fetcher, processor, analyzer）
→ 确保金额精度不丢失（避免 float 精度问题）
====================================================================
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Any, Optional

# 金额精度：保留2位小数（单位：元）
AMOUNT_PRECISION = Decimal("0.01")

# 比率精度：保留4位小数（如 0.1234 = 12.34%）
RATIO_PRECISION = Decimal("0.0001")

# 百分比精度：保留2位小数（如 12.34%）
PERCENTAGE_PRECISION = Decimal("0.01")


def to_amount(value: Any) -> Decimal:
    """
    安全转换为金额精度（保留2位小数）

    Args:
        value: 任意类型的数值（int, float, str, Decimal）

    Returns:
        Decimal: 保留2位小数的金额

    Examples:
        >>> to_amount(123.456)
        Decimal('123.46')
        >>> to_amount("1000.999")
        Decimal('1001.00')
    """
    if value is None or value == "":
        return Decimal("0.00")

    try:
        # 先转为字符串再转 Decimal，避免 float 精度问题
        decimal_value = Decimal(str(value))
        return decimal_value.quantize(AMOUNT_PRECISION, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def to_ratio(value: Any) -> Decimal:
    """
    安全转换为比率精度（保留4位小数）

    Args:
        value: 任意类型的数值

    Returns:
        Decimal: 保留4位小数的比率

    Examples:
        >>> to_ratio(0.123456)
        Decimal('0.1235')
        >>> to_ratio("0.5")
        Decimal('0.5000')
    """
    if value is None or value == "":
        return Decimal("0.0000")

    try:
        decimal_value = Decimal(str(value))
        return decimal_value.quantize(RATIO_PRECISION, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return Decimal("0.0000")


def to_percentage(value: Any) -> Decimal:
    """
    安全转换为百分比精度（保留2位小数）

    Args:
        value: 任意类型的数值（如 0.1234 表示 12.34%）

    Returns:
        Decimal: 保留2位小数的百分比值

    Examples:
        >>> to_percentage(0.1234)
        Decimal('12.34')
    """
    if value is None or value == "":
        return Decimal("0.00")

    try:
        decimal_value = Decimal(str(value)) * Decimal("100")
        return decimal_value.quantize(PERCENTAGE_PRECISION, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def safe_divide(numerator: Decimal, denominator: Decimal, precision: Decimal = RATIO_PRECISION) -> Decimal:
    """
    安全除法，避免除零错误

    Args:
        numerator: 分子
        denominator: 分母
        precision: 精度（默认为比率精度）

    Returns:
        Decimal: 计算结果，分母为0时返回0

    Examples:
        >>> safe_divide(Decimal("100"), Decimal("50"))
        Decimal('2.0000')
        >>> safe_divide(Decimal("100"), Decimal("0"))
        Decimal('0.0000')
    """
    if denominator == 0 or denominator is None:
        return Decimal("0").quantize(precision)

    try:
        result = numerator / denominator
        return result.quantize(precision, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ZeroDivisionError):
        return Decimal("0").quantize(precision)


def validate_precision(value: Decimal, expected_precision: Decimal) -> bool:
    """
    验证 Decimal 值是否符合预期精度

    Args:
        value: 待验证的 Decimal 值
        expected_precision: 预期精度（如 Decimal("0.01")）

    Returns:
        bool: 是否符合精度要求
    """
    quantized = value.quantize(expected_precision, rounding=ROUND_HALF_UP)
    return value == quantized


"""
====================================================================
【使用示例】

# 1. 金额转换
amount = to_amount(123456.789)  # Decimal('123456.79')

# 2. 比率转换
ratio = to_ratio(0.123456)  # Decimal('0.1235')

# 3. 安全除法
roe = safe_divide(net_income, total_equity)  # 避免除零

# 4. 百分比转换
percentage = to_percentage(0.1234)  # Decimal('12.34')

====================================================================
"""
