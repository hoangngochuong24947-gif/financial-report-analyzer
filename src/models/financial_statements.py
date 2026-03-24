"""
====================================================================
模块名称：financial_statements.py
模块功能：三大财务报表数据模型（资产负债表、利润表、现金流量表）

【数据模型】
- BalanceSheet: 资产负债表
- IncomeStatement: 利润表
- CashFlowStatement: 现金流量表

【重要】
所有金额字段使用 Decimal 类型，确保精度不丢失

【数据流向】
→ 被 data_fetcher/akshare_client.py 返回
→ 被 analyzer/ 各模块使用
→ 被 api/ 路由返回
====================================================================
"""

from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional
from src.utils.precision import to_amount


class BalanceSheet(BaseModel):
    """
    资产负债表 / Balance Sheet

    记录企业在特定时点的资产、负债和所有者权益状况
    """
    stock_code: str = Field(..., description="股票代码 / Stock Code")
    report_date: date = Field(..., description="报告期 / Report Date")

    # 资产 / Assets
    total_current_assets: Decimal = Field(default=Decimal("0"), description="流动资产合计 / Total Current Assets")
    total_non_current_assets: Decimal = Field(default=Decimal("0"), description="非流动资产合计 / Total Non-Current Assets")
    total_assets: Decimal = Field(default=Decimal("0"), description="资产总计 / Total Assets")

    # 负债 / Liabilities
    total_current_liabilities: Decimal = Field(default=Decimal("0"), description="流动负债合计 / Total Current Liabilities")
    total_non_current_liabilities: Decimal = Field(default=Decimal("0"), description="非流动负债合计 / Total Non-Current Liabilities")
    total_liabilities: Decimal = Field(default=Decimal("0"), description="负债合计 / Total Liabilities")

    # 所有者权益 / Equity
    total_equity: Decimal = Field(default=Decimal("0"), description="所有者权益合计 / Total Equity")

    @field_validator('total_current_assets', 'total_non_current_assets', 'total_assets',
                     'total_current_liabilities', 'total_non_current_liabilities',
                     'total_liabilities', 'total_equity', mode='before')
    @classmethod
    def validate_amounts(cls, v):
        """确保所有金额字段转换为 Decimal 精度"""
        return to_amount(v)

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "600519",
                "report_date": "2023-12-31",
                "total_current_assets": "123456789.12",
                "total_non_current_assets": "234567890.23",
                "total_assets": "358024679.35",
                "total_current_liabilities": "45678901.23",
                "total_non_current_liabilities": "12345678.90",
                "total_liabilities": "58024580.13",
                "total_equity": "300000099.22"
            }
        }


class IncomeStatement(BaseModel):
    """
    利润表 / Income Statement

    记录企业在一定期间的经营成果
    """
    stock_code: str = Field(..., description="股票代码 / Stock Code")
    report_date: date = Field(..., description="报告期 / Report Date")

    total_revenue: Decimal = Field(default=Decimal("0"), description="营业总收入 / Total Revenue")
    operating_cost: Decimal = Field(default=Decimal("0"), description="营业总成本 / Operating Cost")
    operating_profit: Decimal = Field(default=Decimal("0"), description="营业利润 / Operating Profit")
    total_profit: Decimal = Field(default=Decimal("0"), description="利润总额 / Total Profit")
    net_income: Decimal = Field(default=Decimal("0"), description="净利润 / Net Income")

    @field_validator('total_revenue', 'operating_cost', 'operating_profit',
                     'total_profit', 'net_income', mode='before')
    @classmethod
    def validate_amounts(cls, v):
        """确保所有金额字段转换为 Decimal 精度"""
        return to_amount(v)

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "600519",
                "report_date": "2023-12-31",
                "total_revenue": "150000000.00",
                "operating_cost": "50000000.00",
                "operating_profit": "80000000.00",
                "total_profit": "85000000.00",
                "net_income": "70000000.00"
            }
        }


class CashFlowStatement(BaseModel):
    """
    现金流量表 / Cash Flow Statement

    记录企业在一定期间的现金流入和流出情况
    """
    stock_code: str = Field(..., description="股票代码 / Stock Code")
    report_date: date = Field(..., description="报告期 / Report Date")

    operating_cashflow: Decimal = Field(default=Decimal("0"), description="经营活动现金流量净额 / Operating Cash Flow")
    investing_cashflow: Decimal = Field(default=Decimal("0"), description="投资活动现金流量净额 / Investing Cash Flow")
    financing_cashflow: Decimal = Field(default=Decimal("0"), description="筹资活动现金流量净额 / Financing Cash Flow")
    net_cashflow: Decimal = Field(default=Decimal("0"), description="现金净增加额 / Net Cash Flow")

    @field_validator('operating_cashflow', 'investing_cashflow',
                     'financing_cashflow', 'net_cashflow', mode='before')
    @classmethod
    def validate_amounts(cls, v):
        """确保所有金额字段转换为 Decimal 精度"""
        return to_amount(v)

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "600519",
                "report_date": "2023-12-31",
                "operating_cashflow": "90000000.00",
                "investing_cashflow": "-20000000.00",
                "financing_cashflow": "-10000000.00",
                "net_cashflow": "60000000.00"
            }
        }


"""
====================================================================
【使用示例】

from decimal import Decimal
from datetime import date

# 创建资产负债表
balance_sheet = BalanceSheet(
    stock_code="600519",
    report_date=date(2023, 12, 31),
    total_assets=Decimal("358024679.35"),
    total_liabilities=Decimal("58024580.13"),
    total_equity=Decimal("300000099.22")
)

# 验证精度
assert balance_sheet.total_assets == Decimal("358024679.35")

====================================================================
"""
