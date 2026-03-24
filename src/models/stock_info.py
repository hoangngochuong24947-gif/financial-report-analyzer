"""
====================================================================
模块名称：stock_info.py
模块功能：股票基础信息数据模型

【数据模型】
- StockInfo: 股票基本信息（代码、名称、行业等）

【数据流向】
→ 被 data_fetcher/stock_list.py 返回
→ 被 api/routes_stock.py 使用
====================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional


class StockInfo(BaseModel):
    """
    股票基础信息模型
    """
    stock_code: str = Field(..., description="股票代码 / Stock Code")
    stock_name: str = Field(..., description="股票名称 / Stock Name")
    industry: Optional[str] = Field(None, description="所属行业 / Industry")
    market: Optional[str] = Field(None, description="市场类型 / Market (主板/创业板/科创板)")
    list_date: Optional[str] = Field(None, description="上市日期 / Listing Date")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "industry": "白酒",
                "market": "主板",
                "list_date": "2001-08-27"
            }
        }


"""
====================================================================
【使用示例】

stock = StockInfo(
    stock_code="600519",
    stock_name="贵州茅台",
    industry="白酒",
    market="主板"
)

====================================================================
"""
