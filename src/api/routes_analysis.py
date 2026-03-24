"""Financial analysis routes (v1, backward-compatible)."""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.analyzer import cashflow_analyzer, dupont_analyzer, ratio_calculator, trend_analyzer
from src.api.dependencies import get_crawler_service
from src.crawler.interfaces import CrawlerDataNotFoundError
from src.crawler.service import CrawlerService
from src.models.financial_metrics import CashFlowResult, DuPontResult
from src.utils.logger import logger

router = APIRouter(prefix="/api/stocks", tags=["analysis"])


@router.get("/{code}/ratios")
async def get_financial_ratios(
    code: str,
    crawler: CrawlerService = Depends(get_crawler_service),
):
    try:
        snapshot = crawler.get_snapshot(code)
        bs = snapshot.balance_sheets[0]
        is_ = snapshot.income_statements[0]

        profitability = ratio_calculator.calc_profitability(bs, is_)
        solvency = ratio_calculator.calc_solvency(bs)
        efficiency = ratio_calculator.calc_efficiency(bs, is_)

        return {
            "stock_code": code,
            "report_date": str(bs.report_date),
            "profitability": profitability.model_dump(),
            "solvency": solvency.model_dump(),
            "efficiency": efficiency.model_dump(),
        }
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to calculate ratios for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/dupont", response_model=DuPontResult)
async def get_dupont_analysis(
    code: str,
    crawler: CrawlerService = Depends(get_crawler_service),
):
    try:
        snapshot = crawler.get_snapshot(code)
        return dupont_analyzer.analyze(snapshot.balance_sheets[0], snapshot.income_statements[0])
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to perform DuPont analysis for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/cashflow", response_model=CashFlowResult)
async def get_cashflow_analysis(
    code: str,
    crawler: CrawlerService = Depends(get_crawler_service),
):
    try:
        snapshot = crawler.get_snapshot(code)
        if not snapshot.cashflow_statements:
            raise CrawlerDataNotFoundError(f"No cashflow data for {code}")
        return cashflow_analyzer.analyze(snapshot.cashflow_statements[0], snapshot.income_statements[0])
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to perform cash flow analysis for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/trend")
async def get_trend_analysis(
    code: str,
    metric: str = Query("net_income", description="Metric field name on income statements"),
    crawler: CrawlerService = Depends(get_crawler_service),
):
    try:
        income_statements = crawler.fetch_income_statement(code)
        if len(income_statements) < 2:
            raise CrawlerDataNotFoundError(f"Insufficient data for trend analysis: {code}")

        current = income_statements[0]
        previous = income_statements[1]
        current_value = getattr(current, metric, None)
        previous_value = getattr(previous, metric, None)

        if current_value is None or previous_value is None:
            raise HTTPException(status_code=400, detail=f"Invalid metric: {metric}")

        return trend_analyzer.analyze_trend(
            metric_name=metric,
            current=current_value,
            previous=previous_value,
        )
    except HTTPException:
        raise
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to perform trend analysis for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

