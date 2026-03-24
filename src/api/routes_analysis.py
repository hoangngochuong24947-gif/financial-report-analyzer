"""
====================================================================
模块名称：routes_analysis.py
模块功能：财务分析相关路由

【API 接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 路由                         │ 方法                        │ 说明                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ GET /api/stocks/{code}/      │ 获取财务比率                │ 盈利/偿债/效率指标       │
│     ratios                   │                             │                          │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ GET /api/stocks/{code}/      │ 杜邦分析                    │ ROE 三因素拆解           │
│     dupont                   │                             │                          │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ GET /api/stocks/{code}/      │ 现金流分析                  │ 自由现金流、质量分析     │
│     cashflow                 │                             │                          │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ GET /api/stocks/{code}/      │ 趋势分析                    │ 同比、环比增长           │
│     trend                    │                             │                          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 前端调用这些 API 获取分析结果
====================================================================
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from src.api.dependencies import get_akshare_client
from src.data_fetcher.akshare_client import AKShareClient
from src.analyzer import ratio_calculator, dupont_analyzer, cashflow_analyzer, trend_analyzer
from src.models.financial_metrics import (
    ProfitabilityMetrics,
    SolvencyMetrics,
    EfficiencyMetrics,
    DuPontResult,
    CashFlowResult,
    TrendResult
)
from src.utils.logger import logger

router = APIRouter(prefix="/api/stocks", tags=["analysis"])


@router.get("/{code}/ratios")
async def get_financial_ratios(
    code: str,
    client: AKShareClient = Depends(get_akshare_client)
):
    """
    获取财务比率（盈利能力、偿债能力、运营效率）

    Args:
        code: 股票代码

    Returns:
        dict: 包含所有财务比率的字典
    """
    try:
        # 获取最新财报
        balance_sheets = client.fetch_balance_sheet(code)
        income_statements = client.fetch_income_statement(code)

        if not balance_sheets or not income_statements:
            raise HTTPException(status_code=404, detail=f"No financial data found for {code}")

        bs = balance_sheets[0]
        is_ = income_statements[0]

        # 计算各类比率
        profitability = ratio_calculator.calc_profitability(bs, is_)
        solvency = ratio_calculator.calc_solvency(bs)
        efficiency = ratio_calculator.calc_efficiency(bs, is_)

        return {
            "stock_code": code,
            "report_date": str(bs.report_date),
            "profitability": profitability.model_dump(),
            "solvency": solvency.model_dump(),
            "efficiency": efficiency.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate ratios for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/dupont", response_model=DuPontResult)
async def get_dupont_analysis(
    code: str,
    client: AKShareClient = Depends(get_akshare_client)
):
    """
    杜邦分析

    Args:
        code: 股票代码

    Returns:
        DuPontResult: 杜邦分析结果
    """
    try:
        balance_sheets = client.fetch_balance_sheet(code)
        income_statements = client.fetch_income_statement(code)

        if not balance_sheets or not income_statements:
            raise HTTPException(status_code=404, detail=f"No financial data found for {code}")

        bs = balance_sheets[0]
        is_ = income_statements[0]

        result = dupont_analyzer.analyze(bs, is_)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform DuPont analysis for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/cashflow", response_model=CashFlowResult)
async def get_cashflow_analysis(
    code: str,
    client: AKShareClient = Depends(get_akshare_client)
):
    """
    现金流分析

    Args:
        code: 股票代码

    Returns:
        CashFlowResult: 现金流分析结果
    """
    try:
        cashflow_statements = client.fetch_cashflow_statement(code)
        income_statements = client.fetch_income_statement(code)

        if not cashflow_statements or not income_statements:
            raise HTTPException(status_code=404, detail=f"No financial data found for {code}")

        cf = cashflow_statements[0]
        is_ = income_statements[0]

        result = cashflow_analyzer.analyze(cf, is_)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform cash flow analysis for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/trend")
async def get_trend_analysis(
    code: str,
    metric: str = "net_income",
    client: AKShareClient = Depends(get_akshare_client)
):
    """
    趋势分析（同比、环比）

    Args:
        code: 股票代码
        metric: 指标名称（net_income, total_revenue, etc.）

    Returns:
        TrendResult: 趋势分析结果
    """
    try:
        income_statements = client.fetch_income_statement(code)

        if not income_statements or len(income_statements) < 2:
            raise HTTPException(status_code=404, detail=f"Insufficient data for trend analysis")

        # 取最近两期数据
        current = income_statements[0]
        previous = income_statements[1]

        # 根据指标名称获取值
        current_value = getattr(current, metric, None)
        previous_value = getattr(previous, metric, None)

        if current_value is None or previous_value is None:
            raise HTTPException(status_code=400, detail=f"Invalid metric: {metric}")

        result = trend_analyzer.analyze_trend(
            metric_name=metric,
            current=current_value,
            previous=previous_value
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform trend analysis for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


"""
====================================================================
【使用示例】

# 1. 获取财务比率
GET /api/stocks/600519/ratios

# 2. 杜邦分析
GET /api/stocks/600519/dupont

# 3. 现金流分析
GET /api/stocks/600519/cashflow

# 4. 趋势分析
GET /api/stocks/600519/trend?metric=net_income

====================================================================
"""
