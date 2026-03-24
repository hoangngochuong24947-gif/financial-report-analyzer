"""
====================================================================
模块名称：routes_report.py
模块功能：AI 分析报告和 Excel 导出相关路由

【API 接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 路由                         │ 方法                        │ 说明                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ POST /api/stocks/{code}/     │ AI 分析报告                 │ AnalysisReport          │
│     ai-report                │                             │                          │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ GET /api/stocks/{code}/      │ 导出 Excel 报表             │ .xlsx 文件流            │
│     export/excel             │                             │                          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 调用 llm_engine/report_generator.py 生成 AI 报告
→ 调用 export/excel_exporter.py 导出 Excel
→ 前端调用这些 API
====================================================================
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io

from src.api.dependencies import get_akshare_client
from src.data_fetcher.akshare_client import AKShareClient
from src.llm_engine.report_generator import ReportGenerator
from src.export.excel_exporter import ExcelExporter
from src.analyzer.ratio_calculator import calc_profitability, calc_solvency, calc_efficiency
from src.analyzer.dupont_analyzer import analyze as dupont_analyze
from src.models.analysis_result import AnalysisReport
from src.utils.logger import logger


router = APIRouter(prefix="/api/stocks", tags=["report"])


@router.post("/{code}/ai-report", response_model=AnalysisReport)
async def generate_ai_report(
    code: str,
    stock_name: str = "",
    client: AKShareClient = Depends(get_akshare_client),
):
    """
    生成 AI 智能分析报告

    Args:
        code: 股票代码（如 600519）
        stock_name: 股票名称（可选）

    Returns:
        AnalysisReport: 包含各维度分析、优劣势和建议的完整报告

    Raises:
        HTTPException 500: LLM 调用失败或数据获取异常
    """
    try:
        logger.info(f"API: Generating AI report for {code}")
        generator = ReportGenerator(client=client)
        report = generator.generate_report(stock_code=code, stock_name=stock_name)
        return report

    except RuntimeError as e:
        logger.error(f"AI report generation failed for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in AI report for {code}: {e}")
        raise HTTPException(status_code=500, detail=f"AI 报告生成失败: {e}")


@router.get("/{code}/export/excel")
async def export_excel_report(
    code: str,
    stock_name: str = "",
    client: AKShareClient = Depends(get_akshare_client),
):
    """
    导出 Excel 财务报表

    生成包含多个 Sheet 的专业 Excel 文件：
    - 资产负债表
    - 利润表
    - 现金流量表
    - 财务比率
    - 杜邦分析

    Args:
        code: 股票代码
        stock_name: 股票名称（可选）

    Returns:
        StreamingResponse: .xlsx 文件流（自动触发浏览器下载）
    """
    try:
        logger.info(f"API: Exporting Excel for {code}")

        # 获取三大报表
        balance_sheets = client.fetch_balance_sheet(code)
        income_statements = client.fetch_income_statement(code)
        cashflow_statements = client.fetch_cashflow_statement(code)

        if not balance_sheets or not income_statements:
            raise HTTPException(
                status_code=404,
                detail=f"无法获取 {code} 的财务数据，请检查股票代码是否正确。"
            )

        # 计算最新一期的财务比率
        bs = balance_sheets[0]
        is_ = income_statements[0]

        profitability = calc_profitability(bs, is_)
        solvency = calc_solvency(bs)
        efficiency = calc_efficiency(bs, is_)

        dupont = dupont_analyze(bs, is_)

        # 生成 Excel
        exporter = ExcelExporter()
        excel_bytes = exporter.export_full_report(
            stock_code=code,
            stock_name=stock_name or code,
            balance_sheets=balance_sheets,
            income_statements=income_statements,
            cashflow_statements=cashflow_statements,
            profitability=profitability,
            solvency=solvency,
            efficiency=efficiency,
            dupont=dupont,
        )

        # 返回文件流
        file_name = f"{stock_name or code}_财务分析报表.xlsx"
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel export failed for {code}: {e}")
        raise HTTPException(status_code=500, detail=f"Excel 导出失败: {e}")


"""
====================================================================
【使用示例】

# 1. 生成 AI 报告
POST /api/stocks/600519/ai-report?stock_name=贵州茅台

# 2. 导出 Excel
GET /api/stocks/600519/export/excel?stock_name=贵州茅台

====================================================================
"""
