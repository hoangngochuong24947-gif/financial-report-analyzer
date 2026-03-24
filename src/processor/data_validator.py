"""
====================================================================
模块名称：data_validator.py
模块功能：数据验证（金额精度、逻辑一致性）

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ validate_balance_sheet()     │ bs: BalanceSheet            │ ValidationResult         │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ validate_amounts()           │ data: BaseModel             │ ValidationResult         │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被所有层调用（确保数据质量）
====================================================================
"""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field

from src.models.financial_statements import BalanceSheet, IncomeStatement, CashFlowStatement
from src.utils.logger import logger


class ValidationResult(BaseModel):
    """
    验证结果
    """
    is_valid: bool = Field(..., description="是否通过验证")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    warnings: List[str] = Field(default_factory=list, description="警告信息列表")


def validate_balance_sheet(bs: BalanceSheet) -> ValidationResult:
    """
    验证资产负债表的逻辑一致性

    验证规则：
    1. 资产总计 = 流动资产 + 非流动资产
    2. 负债合计 = 流动负债 + 非流动负债
    3. 资产总计 = 负债合计 + 所有者权益

    Args:
        bs: 资产负债表

    Returns:
        ValidationResult: 验证结果
    """
    errors = []
    warnings = []

    # 允许的误差范围（考虑四舍五入）
    tolerance = Decimal("0.01")

    # 验证 1: 资产总计 = 流动资产 + 非流动资产
    calculated_assets = bs.total_current_assets + bs.total_non_current_assets
    if abs(bs.total_assets - calculated_assets) > tolerance:
        errors.append(
            f"资产总计不匹配: {bs.total_assets} ≠ {bs.total_current_assets} + {bs.total_non_current_assets} = {calculated_assets}"
        )

    # 验证 2: 负债合计 = 流动负债 + 非流动负债
    calculated_liabilities = bs.total_current_liabilities + bs.total_non_current_liabilities
    if abs(bs.total_liabilities - calculated_liabilities) > tolerance:
        errors.append(
            f"负债合计不匹配: {bs.total_liabilities} ≠ {bs.total_current_liabilities} + {bs.total_non_current_liabilities} = {calculated_liabilities}"
        )

    # 验证 3: 资产总计 = 负债合计 + 所有者权益
    calculated_total = bs.total_liabilities + bs.total_equity
    if abs(bs.total_assets - calculated_total) > tolerance:
        errors.append(
            f"会计恒等式不成立: {bs.total_assets} ≠ {bs.total_liabilities} + {bs.total_equity} = {calculated_total}"
        )

    # 警告：负值检查
    if bs.total_equity < 0:
        warnings.append(f"所有者权益为负: {bs.total_equity}")

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(f"Balance sheet validation failed for {bs.stock_code} on {bs.report_date}: {errors}")

    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_income_statement(is_: IncomeStatement) -> ValidationResult:
    """
    验证利润表的逻辑一致性

    Args:
        is_: 利润表

    Returns:
        ValidationResult: 验证结果
    """
    errors = []
    warnings = []

    # 警告：收入为负
    if is_.total_revenue < 0:
        warnings.append(f"营业总收入为负: {is_.total_revenue}")

    # 警告：净利润 > 利润总额（不合理）
    if is_.net_income > is_.total_profit:
        warnings.append(f"净利润 ({is_.net_income}) 大于利润总额 ({is_.total_profit})")

    return ValidationResult(is_valid=True, errors=errors, warnings=warnings)


def validate_cashflow_statement(cf: CashFlowStatement) -> ValidationResult:
    """
    验证现金流量表的逻辑一致性

    Args:
        cf: 现金流量表

    Returns:
        ValidationResult: 验证结果
    """
    errors = []
    warnings = []

    tolerance = Decimal("0.01")

    # 验证：现金净增加额 = 三大活动现金流之和
    calculated_net = cf.operating_cashflow + cf.investing_cashflow + cf.financing_cashflow
    if abs(cf.net_cashflow - calculated_net) > tolerance:
        warnings.append(
            f"现金净增加额不匹配: {cf.net_cashflow} ≠ {calculated_net}"
        )

    return ValidationResult(is_valid=True, errors=errors, warnings=warnings)


def validate_amounts(data: BaseModel) -> ValidationResult:
    """
    验证 pydantic 模型中的所有金额字段是否为 Decimal 类型

    Args:
        data: pydantic 模型实例

    Returns:
        ValidationResult: 验证结果
    """
    errors = []

    for field_name, field_value in data.model_dump().items():
        if isinstance(field_value, float):
            errors.append(f"字段 {field_name} 使用了 float 类型，应使用 Decimal")

    is_valid = len(errors) == 0

    return ValidationResult(is_valid=is_valid, errors=errors, warnings=[])


"""
====================================================================
【使用示例】

from src.processor.data_validator import validate_balance_sheet

# 验证资产负债表
result = validate_balance_sheet(balance_sheet)

if not result.is_valid:
    print("验证失败:")
    for error in result.errors:
        print(f"  - {error}")

if result.warnings:
    print("警告:")
    for warning in result.warnings:
        print(f"  - {warning}")

====================================================================
"""
