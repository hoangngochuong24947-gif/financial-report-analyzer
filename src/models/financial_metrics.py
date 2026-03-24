"""
====================================================================
模块名称：financial_metrics.py
模块功能：财务指标和比率数据模型

【数据模型】
- ProfitabilityMetrics: 盈利能力指标
- SolvencyMetrics: 偿债能力指标
- EfficiencyMetrics: 运营效率指标
- DuPontResult: 杜邦分析结果
- CashFlowResult: 现金流分析结果

【数据流向】
→ 被 analyzer/ 各模块返回
→ 被 api/ 路由使用
====================================================================
"""

from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from src.utils.precision import to_ratio


class ProfitabilityMetrics(BaseModel):
    """
    盈利能力指标 / Profitability Metrics
    """
    roe: Decimal = Field(default=Decimal("0"), description="净资产收益率 / Return on Equity (ROE)")
    roa: Decimal = Field(default=Decimal("0"), description="总资产收益率 / Return on Assets (ROA)")
    net_profit_margin: Decimal = Field(default=Decimal("0"), description="销售净利率 / Net Profit Margin")
    gross_profit_margin: Decimal = Field(default=Decimal("0"), description="毛利率 / Gross Profit Margin")

    @field_validator('roe', 'roa', 'net_profit_margin', 'gross_profit_margin', mode='before')
    @classmethod
    def validate_ratios(cls, v):
        """确保所有比率字段转换为 Decimal 精度"""
        return to_ratio(v)


class SolvencyMetrics(BaseModel):
    """
    偿债能力指标 / Solvency Metrics
    """
    current_ratio: Decimal = Field(default=Decimal("0"), description="流动比率 / Current Ratio")
    quick_ratio: Decimal = Field(default=Decimal("0"), description="速动比率 / Quick Ratio")
    debt_to_asset_ratio: Decimal = Field(default=Decimal("0"), description="资产负债率 / Debt to Asset Ratio")
    debt_to_equity_ratio: Decimal = Field(default=Decimal("0"), description="产权比率 / Debt to Equity Ratio")

    @field_validator('current_ratio', 'quick_ratio', 'debt_to_asset_ratio', 'debt_to_equity_ratio', mode='before')
    @classmethod
    def validate_ratios(cls, v):
        """确保所有比率字段转换为 Decimal 精度"""
        return to_ratio(v)


class EfficiencyMetrics(BaseModel):
    """
    运营效率指标 / Efficiency Metrics
    """
    asset_turnover: Decimal = Field(default=Decimal("0"), description="总资产周转率 / Asset Turnover")
    equity_turnover: Decimal = Field(default=Decimal("0"), description="权益乘数 / Equity Multiplier")
    inventory_turnover: Optional[Decimal] = Field(None, description="存货周转率 / Inventory Turnover")
    receivables_turnover: Optional[Decimal] = Field(None, description="应收账款周转率 / Receivables Turnover")

    @field_validator('asset_turnover', 'equity_turnover', 'inventory_turnover', 'receivables_turnover', mode='before')
    @classmethod
    def validate_ratios(cls, v):
        """确保所有比率字段转换为 Decimal 精度"""
        if v is None:
            return None
        return to_ratio(v)


class DuPontResult(BaseModel):
    """
    杜邦分析结果 / DuPont Analysis Result

    ROE = 销售净利率 × 总资产周转率 × 权益乘数
    """
    roe: Decimal = Field(..., description="净资产收益率 / ROE")
    net_profit_margin: Decimal = Field(..., description="销售净利率 / Net Profit Margin")
    asset_turnover: Decimal = Field(..., description="总资产周转率 / Asset Turnover")
    equity_multiplier: Decimal = Field(..., description="权益乘数 / Equity Multiplier")

    @field_validator('roe', 'net_profit_margin', 'asset_turnover', 'equity_multiplier', mode='before')
    @classmethod
    def validate_ratios(cls, v):
        """确保所有比率字段转换为 Decimal 精度"""
        return to_ratio(v)

    class Config:
        json_schema_extra = {
            "example": {
                "roe": "0.1500",
                "net_profit_margin": "0.3000",
                "asset_turnover": "0.5000",
                "equity_multiplier": "1.0000"
            }
        }


class CashFlowResult(BaseModel):
    """
    现金流分析结果 / Cash Flow Analysis Result
    """
    operating_cashflow: Decimal = Field(..., description="经营活动现金流量净额")
    free_cash_flow: Decimal = Field(..., description="自由现金流 / Free Cash Flow")
    cash_to_profit_ratio: Decimal = Field(..., description="现金流量与净利润比率")
    operating_cash_coverage: Decimal = Field(..., description="经营现金流覆盖率")

    @field_validator('operating_cashflow', 'free_cash_flow', mode='before')
    @classmethod
    def validate_amounts(cls, v):
        """金额字段使用金额精度"""
        from src.utils.precision import to_amount
        return to_amount(v)

    @field_validator('cash_to_profit_ratio', 'operating_cash_coverage', mode='before')
    @classmethod
    def validate_ratios(cls, v):
        """比率字段使用比率精度"""
        return to_ratio(v)


class TrendResult(BaseModel):
    """
    趋势分析结果 / Trend Analysis Result
    """
    metric_name: str = Field(..., description="指标名称")
    current_value: Decimal = Field(..., description="当期值")
    previous_value: Optional[Decimal] = Field(None, description="上期值")
    yoy_growth: Optional[Decimal] = Field(None, description="同比增长率 / Year-over-Year Growth")
    qoq_growth: Optional[Decimal] = Field(None, description="环比增长率 / Quarter-over-Quarter Growth")

    @field_validator('yoy_growth', 'qoq_growth', mode='before')
    @classmethod
    def validate_ratios(cls, v):
        """确保增长率字段转换为 Decimal 精度"""
        if v is None:
            return None
        return to_ratio(v)


"""
====================================================================
【使用示例】

# 1. 盈利能力指标
profitability = ProfitabilityMetrics(
    roe=Decimal("0.1500"),
    roa=Decimal("0.0800"),
    net_profit_margin=Decimal("0.3000")
)

# 2. 杜邦分析
dupont = DuPontResult(
    roe=Decimal("0.1500"),
    net_profit_margin=Decimal("0.3000"),
    asset_turnover=Decimal("0.5000"),
    equity_multiplier=Decimal("1.0000")
)

# 验证：ROE = 0.3000 × 0.5000 × 1.0000 = 0.1500 ✓

====================================================================
"""
