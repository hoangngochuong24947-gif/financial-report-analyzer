"""
====================================================================
模块名称：analysis_result.py
模块功能：综合分析结果数据模型

【数据模型】
- AnalysisReport: AI 生成的综合分析报告
- ComparisonResult: 同行业对比结果

【数据流向】
→ 被 llm_engine/report_generator.py 返回
→ 被 analyzer/peer_comparator.py 返回
→ 被 api/ 路由使用
====================================================================
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AnalysisReport(BaseModel):
    """
    AI 生成的综合分析报告 / AI-Generated Analysis Report
    """
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    report_date: str = Field(..., description="报告日期")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")

    # 分析内容
    executive_summary: str = Field(..., description="执行摘要 / Executive Summary")
    profitability_analysis: str = Field(..., description="盈利能力分析")
    solvency_analysis: str = Field(..., description="偿债能力分析")
    efficiency_analysis: str = Field(..., description="运营效率分析")
    cashflow_analysis: str = Field(..., description="现金流分析")
    trend_analysis: str = Field(..., description="趋势分析")

    # 结论与建议
    strengths: List[str] = Field(default_factory=list, description="优势 / Strengths")
    weaknesses: List[str] = Field(default_factory=list, description="劣势 / Weaknesses")
    recommendations: List[str] = Field(default_factory=list, description="建议 / Recommendations")

    # 风险提示
    risk_warnings: List[str] = Field(default_factory=list, description="风险提示 / Risk Warnings")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "report_date": "2023-12-31",
                "executive_summary": "该公司财务状况良好...",
                "strengths": ["盈利能力强", "现金流充沛"],
                "weaknesses": ["资产周转率偏低"],
                "recommendations": ["关注市场份额变化"]
            }
        }


class ComparisonResult(BaseModel):
    """
    同行业对比结果 / Peer Comparison Result
    """
    target_stock_code: str = Field(..., description="目标股票代码")
    target_stock_name: str = Field(..., description="目标股票名称")
    peer_stocks: List[str] = Field(..., description="对比股票代码列表")

    # 对比指标
    metrics_comparison: Dict[str, Any] = Field(
        default_factory=dict,
        description="指标对比数据 / Metrics Comparison Data"
    )

    # 排名
    ranking: Optional[Dict[str, int]] = Field(
        None,
        description="各指标排名 / Rankings"
    )

    # 分析结论
    summary: Optional[str] = Field(None, description="对比分析总结")

    class Config:
        json_schema_extra = {
            "example": {
                "target_stock_code": "600519",
                "target_stock_name": "贵州茅台",
                "peer_stocks": ["000858", "600809"],
                "metrics_comparison": {
                    "roe": {
                        "600519": 0.25,
                        "000858": 0.18,
                        "600809": 0.15
                    }
                },
                "ranking": {
                    "roe": 1,
                    "roa": 1
                }
            }
        }


"""
====================================================================
【使用示例】

# 1. 创建分析报告
report = AnalysisReport(
    stock_code="600519",
    stock_name="贵州茅台",
    report_date="2023-12-31",
    executive_summary="该公司财务状况良好...",
    strengths=["盈利能力强", "现金流充沛"],
    recommendations=["关注市场份额变化"]
)

# 2. 创建对比结果
comparison = ComparisonResult(
    target_stock_code="600519",
    target_stock_name="贵州茅台",
    peer_stocks=["000858", "600809"],
    metrics_comparison={"roe": {"600519": 0.25}}
)

====================================================================
"""
