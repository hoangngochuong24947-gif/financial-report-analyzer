"""Financial analysis routes (v1, backward-compatible)."""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.analysis_facade import AnalysisFacade
from src.api.dependencies import get_analysis_facade
from src.crawler.interfaces import CrawlerDataNotFoundError
from src.models.financial_metrics import CashFlowResult, DuPontResult
from src.utils.logger import logger

router = APIRouter(prefix="/api/stocks", tags=["analysis"])


@router.get("/{code}/ratios")
async def get_financial_ratios(
    code: str,
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    try:
        return await facade.get_legacy_ratios(code)
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to calculate ratios for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/dupont", response_model=DuPontResult)
async def get_dupont_analysis(
    code: str,
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    try:
        return await facade.get_dupont(code)
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to perform DuPont analysis for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/cashflow", response_model=CashFlowResult)
async def get_cashflow_analysis(
    code: str,
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    try:
        return await facade.get_cashflow(code)
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to perform cash flow analysis for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/trend")
async def get_trend_analysis(
    code: str,
    metric: str = Query("net_income", description="Metric field name on income statements"),
    facade: AnalysisFacade = Depends(get_analysis_facade),
):
    try:
        return await facade.get_trend(code, metric)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid metric: {metric}")
    except HTTPException:
        raise
    except CrawlerDataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to perform trend analysis for {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

