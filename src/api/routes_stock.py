"""
====================================================================
模块名称：routes_stock.py
模块功能：股票查询相关路由

【API 接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 路由                         │ 方法                        │ 说明                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ GET /api/stocks              │ 获取股票列表                │ 支持市场筛选             │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ GET /api/stocks/{code}/      │ 获取三大财务报表            │ 返回最新报表数据         │
│     statements               │                             │                          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 前端调用这些 API 获取数据
====================================================================
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional

from src.api.dependencies import get_akshare_client
from src.data_fetcher.akshare_client import AKShareClient
from src.data_fetcher.stock_list import fetch_stock_list
from src.models.stock_info import StockInfo
from src.models.financial_statements import BalanceSheet, IncomeStatement, CashFlowStatement
from src.utils.logger import logger

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/", response_model=List[StockInfo])
async def get_stock_list(
    market: Optional[str] = Query(None, description="市场类型（主板/创业板/科创板）")
):
    """
    获取股票列表

    Args:
        market: 市场类型筛选

    Returns:
        List[StockInfo]: 股票信息列表
    """
    try:
        stocks = fetch_stock_list(market=market)
        return stocks
    except Exception as e:
        logger.error(f"Failed to fetch stock list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/statements")
async def get_financial_statements(
    code: str,
    client: AKShareClient = Depends(get_akshare_client)
):
    """
    获取三大财务报表

    Args:
        code: 股票代码

    Returns:
        dict: 包含三大报表的字典
    """
    try:
        balance_sheets = client.fetch_balance_sheet(code)
        income_statements = client.fetch_income_statement(code)
        cashflow_statements = client.fetch_cashflow_statement(code)

        if not balance_sheets or not income_statements or not cashflow_statements:
            raise HTTPException(status_code=404, detail=f"No financial data found for {code}")

        return {
            "stock_code": code,
            "balance_sheet": balance_sheets[0].model_dump(mode='json'),
            "income_statement": income_statements[0].model_dump(mode='json'),
            "cashflow_statement": cashflow_statements[0].model_dump(mode='json')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch statements for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


"""
====================================================================
【使用示例】

# 1. 获取所有股票
GET /api/stocks

# 2. 获取主板股票
GET /api/stocks?market=主板

# 3. 获取某股票的财务报表
GET /api/stocks/600519/statements

====================================================================
"""
