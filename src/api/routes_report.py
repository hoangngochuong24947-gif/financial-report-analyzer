"""Report routes (v1, backward-compatible)."""

import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.api.analysis_facade import AnalysisFacade
from src.api.dependencies import get_analysis_facade, get_crawler_service
from src.crawler.interfaces import CrawlerDataNotFoundError
from src.crawler.service import CrawlerService
from src.export.excel_exporter import ExcelExporter
from src.llm_engine.report_generator import ReportGenerator
from src.models.analysis_result import AnalysisReport
from src.utils.logger import logger

router = APIRouter(prefix="/api/stocks", tags=["report"])


@router.post("/{code}/ai-report", response_model=AnalysisReport)
async def generate_ai_report(
    code: str,
    stock_name: str = "",
    crawler: CrawlerService = Depends(get_crawler_service),
):
    try:
        logger.info(f"API: Generating AI report for {code}")
        generator = ReportGenerator(client=crawler)
        return generator.generate_report(stock_code=code, stock_name=stock_name)
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.error(f"AI report generation failed for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in AI report for {code}: {e}")
        raise HTTPException(status_code=500, detail=f"AI report generation failed: {e}")


@router.get("/{code}/export/excel")
async def export_excel_report(
    code: str,
    stock_name: str = "",
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    try:
        logger.info(f"API: Exporting Excel for {code}")
        export_payload = await facade.get_export_payload(code)
        snapshot = export_payload["snapshot"]

        exporter = ExcelExporter()
        excel_bytes = exporter.export_full_report(
            stock_code=code,
            stock_name=stock_name or export_payload["stock_name"] or code,
            balance_sheets=snapshot.balance_sheets,
            income_statements=snapshot.income_statements,
            cashflow_statements=snapshot.cashflow_statements,
            profitability=export_payload["profitability"],
            solvency=export_payload["solvency"],
            efficiency=export_payload["efficiency"],
            dupont=export_payload["dupont"],
        )

        file_name = f"{stock_name or code}_financial_report.xlsx"
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel export failed for {code}: {e}")
        raise HTTPException(status_code=500, detail=f"Excel export failed: {e}")

