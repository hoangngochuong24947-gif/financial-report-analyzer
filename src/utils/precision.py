"""
Precision helpers for financial values.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

AMOUNT_PRECISION = Decimal("0.01")
RATIO_PRECISION = Decimal("0.0001")
PERCENTAGE_PRECISION = Decimal("0.01")

_PLACEHOLDER_VALUES = {"", "--", "-", "—", "N/A", "n/a", "null", "None"}
_CHINESE_AMOUNT_UNITS = {
    "亿": Decimal("100000000"),
    "万": Decimal("10000"),
    "千": Decimal("1000"),
}


def _normalize_amount_input(value: Any) -> Decimal | None:
    if isinstance(value, Decimal):
        return value

    text = str(value).strip().replace(",", "")
    if text in _PLACEHOLDER_VALUES:
        return Decimal("0")

    multiplier = Decimal("1")
    for unit, scale in _CHINESE_AMOUNT_UNITS.items():
        if text.endswith(unit):
            text = text[: -len(unit)].strip()
            multiplier = scale
            break

    if text.endswith("%"):
        text = text[:-1].strip()

    if text in _PLACEHOLDER_VALUES:
        return Decimal("0")

    try:
        return Decimal(text) * multiplier
    except (InvalidOperation, ValueError):
        return None


def to_amount(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0.00")

    decimal_value = _normalize_amount_input(value)
    if decimal_value is None:
        return Decimal("0.00")

    try:
        return decimal_value.quantize(AMOUNT_PRECISION, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def to_ratio(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0.0000")

    try:
        decimal_value = Decimal(str(value))
        return decimal_value.quantize(RATIO_PRECISION, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return Decimal("0.0000")


def to_percentage(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0.00")

    try:
        decimal_value = Decimal(str(value)) * Decimal("100")
        return decimal_value.quantize(PERCENTAGE_PRECISION, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def safe_divide(numerator: Decimal, denominator: Decimal, precision: Decimal = RATIO_PRECISION) -> Decimal:
    if denominator == 0 or denominator is None:
        return Decimal("0").quantize(precision)

    try:
        result = numerator / denominator
        return result.quantize(precision, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ZeroDivisionError):
        return Decimal("0").quantize(precision)


def validate_precision(value: Decimal, expected_precision: Decimal) -> bool:
    quantized = value.quantize(expected_precision, rounding=ROUND_HALF_UP)
    return value == quantized
