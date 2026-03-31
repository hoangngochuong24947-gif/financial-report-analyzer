"""Workspace routes for archive-first v2 APIs."""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_workspace_service
from src.api.workspace_service import WorkspaceService
from src.models.workspace_metrics import WorkspaceInsightGenerateRequest
from src.utils.logger import logger

router = APIRouter(prefix="/api/v2", tags=["workspace"])


def _handle_workspace_error(exc: Exception, stock_code: str | None = None) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))

    detail = str(exc) or exc.__class__.__name__
    if stock_code:
        logger.error("Workspace API failed for {}: {}", stock_code, detail)
    else:
        logger.error("Workspace API failed: {}", detail)
    return HTTPException(status_code=500, detail=detail)


def _requested_lang(lang: Optional[str], fallback: str = "zh") -> str:
    if not lang:
        return fallback
    lowered = lang.lower()
    return "en" if lowered.startswith("en") else "zh"


def _build_statement_payload(detail: Any, stock_code: str) -> dict[str, Any]:
    statements = {
        tab.key: [
            {
                "field": row.key,
                "label": row.label,
                "value": row.value,
                "display_value": row.display_value,
                "unit": row.unit,
                "source": row.source,
                "is_estimated": row.is_estimated,
            }
            for row in tab.rows
        ]
        for tab in detail.tabs
    }
    return {
        "stock": detail.stock.model_dump(mode="json"),
        "stock_code": stock_code,
        "stock_name": detail.stock.stock_name,
        "available_periods": detail.available_periods,
        "selected_period": detail.selected_period,
        "report_date": detail.selected_period,
        "lang": detail.lang,
        "tabs": [tab.model_dump(mode="json") for tab in detail.tabs],
        "statements": statements,
        "balance_sheet": statements.get("balance_sheet", []),
        "income_statement": statements.get("income_statement", []),
        "cashflow_statement": statements.get("cashflow_statement", []),
        "source": "baidu_archive",
        "updated_at": detail.updated_at,
    }


def _build_legacy_insight_payload(report: Any) -> dict[str, Any]:
    if isinstance(report, dict):
        payload = dict(report)
    else:
        payload = report.model_dump(mode="json")
    payload.update(
        {
            "executive_summary": payload.get("summary", ""),
            "profitability_analysis": payload.get("summary", ""),
            "solvency_analysis": "",
            "efficiency_analysis": "",
            "cashflow_analysis": "",
            "trend_analysis": "",
            "strengths": payload.get("highlights", []),
            "weaknesses": [],
            "recommendations": payload.get("actions", []),
            "risk_warnings": payload.get("risks", []),
        }
    )
    return payload


@router.get("/workspaces")
async def list_workspaces(
    limit: int = Query(20, ge=1, le=200, description="Number of archive-backed workspaces"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return workspace_service.list_workspaces(limit=limit)
    except Exception as exc:
        raise _handle_workspace_error(exc) from exc


@router.get("/workspaces/{code}/metrics")
async def get_workspace_metric_bundle(
    code: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return workspace_service.get_metric_bundle(code).model_dump(mode="json")
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspaces/{code}/context")
async def get_workspace_context(
    code: str,
    profile_key: str = Query("archive_review", description="Prompt profile key"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return workspace_service.get_context(code, profile_key=profile_key).model_dump(mode="json")
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/snapshot")
async def get_workspace_snapshot(
    code: str,
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return workspace_service.get_snapshot_response(code, lang=lang or "zh-CN").model_dump(mode="json")
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/metrics/catalog")
async def get_workspace_metric_catalog(
    code: str,
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return workspace_service.get_metric_catalog_response(code, lang=lang or "zh-CN").model_dump(mode="json")
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/metrics")
async def get_workspace_metric_values(
    code: str,
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return workspace_service.get_metric_values_response(code, lang=lang or "zh-CN").model_dump(mode="json")
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/models")
async def get_workspace_models(
    code: str,
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return workspace_service.get_model_response(code, lang=lang or "zh-CN").model_dump(mode="json")
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/insights/context")
async def get_workspace_insight_context(
    code: str,
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return workspace_service.get_insight_context_response(code, lang=lang or "zh-CN").model_dump(mode="json")
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/statements")
async def get_workspace_statements(
    code: str,
    period: Optional[str] = Query(None, description="Reporting period"),
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        detail = workspace_service.get_statement_detail_response(code, period=period, lang=lang or "zh-CN")
        payload = _build_statement_payload(detail, code)
        payload["lang"] = _requested_lang(lang, fallback=payload["lang"])
        return payload
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.post("/workspace/{code}/insights/generate")
async def generate_workspace_insights(
    code: str,
    request: Optional[WorkspaceInsightGenerateRequest] = None,
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    requested_lang = request.lang if request and request.lang else lang
    requested_period = request.period if request else None
    try:
        report = workspace_service.generate_insight_report(
            code,
            lang=requested_lang or "zh-CN",
            period=requested_period,
        )
    except RuntimeError as exc:
        logger.warning("Insight generation fell back to archive summary for {}: {}", code, exc)
        try:
            locale = "en-US" if _requested_lang(requested_lang) == "en" else "zh-CN"
            bundle = workspace_service.get_metric_bundle(code)
            model_response = workspace_service.get_model_response(code, locale)
            summary = (
                f"Archive-only fallback insight for {bundle.stock_name or bundle.stock_code}. "
                f"ROE={next((item.value for item in bundle.values if item.key == 'roe'), 'N/A')}, "
                f"Debt/Asset={next((item.value for item in bundle.values if item.key == 'debt_to_asset_ratio'), 'N/A')}."
                if locale == "en-US"
                else f"{bundle.stock_name or bundle.stock_code} 当前返回的是归档数据降级洞察。"
                f"ROE={next((item.value for item in bundle.values if item.key == 'roe'), 'N/A')}，"
                f"资产负债率={next((item.value for item in bundle.values if item.key == 'debt_to_asset_ratio'), 'N/A')}。"
            )
            report_payload = {
                "stock_code": bundle.stock_code,
                "stock_name": bundle.stock_name,
                "report_date": requested_period or bundle.report_date,
                "lang": _requested_lang(requested_lang),
                "summary": summary,
                "highlights": [item.summary for item in model_response.items[:2] if item.summary],
                "risks": [item.summary for item in model_response.items[2:4] if item.summary],
                "open_questions": [],
                "actions": [
                    "Configure DEEPSEEK_API_KEY to enable full AI-generated narrative."
                    if locale == "en-US"
                    else "配置 DEEPSEEK_API_KEY 后可启用完整 AI 叙事分析。"
                ],
                "evidence": [item.key for item in bundle.values[:5]],
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "model_version": "workspace-insights-v1",
            }
            return _build_legacy_insight_payload(report_payload)
        except Exception as inner_exc:
            raise _handle_workspace_error(inner_exc, code) from inner_exc
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc

    payload = _build_legacy_insight_payload(report)
    payload["lang"] = _requested_lang(requested_lang, fallback=payload.get("lang", "zh"))
    return payload
