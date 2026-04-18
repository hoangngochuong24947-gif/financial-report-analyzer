"""Workspace routes for archive-first v2 APIs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from src.api.dependencies import get_workspace_service
from src.api.workspace_service import WorkspaceService
from src.models.workspace_metrics import InsightReportResponse, WorkspaceInsightGenerateRequest
from src.storage.report_repository import ReportRepository
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
    return "en" if lang.lower().startswith("en") else "zh"


def _service_lang(lang: Optional[str]) -> str:
    if not lang:
        return "zh-CN"
    return "en-US" if lang.lower().startswith("en") else "zh-CN"


def _build_statement_payload(detail: Any, stock_code: str) -> dict[str, Any]:
    statements = {
        tab.key: [
            {
                "field": row.key,
                "label": row.label,
                "section": row.section,
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
    payload = dict(report) if isinstance(report, dict) else report.model_dump(mode="json")
    summary = payload.get("summary", "")
    payload.update(
        {
            "executive_summary": payload.get("executive_summary", summary),
            "profitability_analysis": payload.get("profitability_analysis", summary),
            "solvency_analysis": payload.get("solvency_analysis", ""),
            "efficiency_analysis": payload.get("efficiency_analysis", ""),
            "cashflow_analysis": payload.get("cashflow_analysis", ""),
            "trend_analysis": payload.get("trend_analysis", ""),
            "strengths": payload.get("strengths", payload.get("highlights", [])),
            "weaknesses": payload.get("weaknesses", []),
            "recommendations": payload.get("recommendations", payload.get("actions", [])),
            "risk_warnings": payload.get("risk_warnings", payload.get("risks", [])),
        }
    )
    return payload


def _statement_export_filename(stock_code: str, statement_key: str, period: str, file_ext: str) -> str:
    return f"{stock_code}_{statement_key}_{period}.{file_ext}"


def _history_export_filename(stock_code: str, file_ext: str) -> str:
    return f"{stock_code}_statement_history.{file_ext}"


@router.get("/workspaces")
async def list_workspaces(
    limit: int = Query(20, ge=1, le=5000, description="Number of archive-backed workspaces"),
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
        return workspace_service.get_snapshot_response(code, lang=_service_lang(lang)).model_dump(mode="json")
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/metrics/catalog")
async def get_workspace_metric_catalog(
    code: str,
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return workspace_service.get_metric_catalog_response(code, lang=_service_lang(lang)).model_dump(mode="json")
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/metrics")
async def get_workspace_metric_values(
    code: str,
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return workspace_service.get_metric_values_response(code, lang=_service_lang(lang)).model_dump(mode="json")
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/models")
async def get_workspace_models(
    code: str,
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return workspace_service.get_model_response(code, lang=_service_lang(lang)).model_dump(mode="json")
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/insights/context")
async def get_workspace_insight_context(
    code: str,
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return workspace_service.get_insight_context_response(code, lang=_service_lang(lang)).model_dump(mode="json")
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/insights/report")
async def get_workspace_saved_insight_report(
    code: str,
    period: Optional[str] = Query(None, description="Reporting period"),
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        report = workspace_service.get_saved_insight_report(code, lang=_service_lang(lang), period=period)
        payload = _build_legacy_insight_payload(report)
        payload["lang"] = _requested_lang(lang, fallback=payload.get("lang", "zh"))
        return payload
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/insights/history")
async def list_workspace_saved_insight_reports(
    code: str,
    limit: int = Query(20, ge=1, le=100, description="Stored report history size"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return [item.model_dump(mode="json") for item in workspace_service.list_saved_insight_reports(code, limit=limit)]
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
        detail = workspace_service.get_statement_detail_response(code, period=period, lang=_service_lang(lang))
        payload = _build_statement_payload(detail, code)
        payload["lang"] = _requested_lang(lang, fallback=payload["lang"])
        return payload
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/statements/export")
async def export_workspace_statement(
    code: str,
    statement_key: str = Query(..., description="Statement key"),
    period: Optional[str] = Query(None, description="Reporting period"),
    format: str = Query("csv", pattern="^(csv|xlsx)$", description="Export format"),
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        _, selected_period, rows = workspace_service.export_statement_rows(
            code,
            statement_key=statement_key,
            period=period,
            lang=_service_lang(lang),
        )
        if format == "xlsx":
            body = ReportRepository.rows_to_excel_bytes(
                {
                    statement_key: [
                        {
                            "label": row.label,
                            "section": row.section or "",
                            "display_value": row.display_value,
                            "value": row.value,
                            "unit": row.unit,
                            "source": row.source,
                            "is_estimated": row.is_estimated,
                        }
                        for row in rows
                    ]
                }
            )
            filename = _statement_export_filename(code, statement_key, selected_period, "xlsx")
            return Response(
                content=body,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        body = ReportRepository.rows_to_csv_bytes(rows)
        filename = _statement_export_filename(code, statement_key, selected_period, "csv")
        return Response(
            content=body,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc


@router.get("/workspace/{code}/statements/export/all")
async def export_workspace_statement_history(
    code: str,
    format: str = Query("xlsx", pattern="^(csv|xlsx)$", description="Export format"),
    lang: Optional[str] = Query(None, description="Response language"),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        _, sheets = workspace_service.export_all_statement_rows(code, lang=_service_lang(lang))
        if format == "csv":
            csv_parts: list[str] = []
            for sheet_name, rows in sheets.items():
                csv_parts.append(f"# {sheet_name}")
                csv_parts.append(ReportRepository.rows_to_csv_bytes(rows).decode("utf-8-sig"))
            filename = _history_export_filename(code, "csv")
            return Response(
                content="\n".join(csv_parts).encode("utf-8-sig"),
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        filename = _history_export_filename(code, "xlsx")
        return Response(
            content=ReportRepository.rows_to_excel_bytes(sheets),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
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
    service_lang = _service_lang(requested_lang)

    latest_period = workspace_service.get_metric_bundle(code).report_date
    if requested_period and requested_period != latest_period:
        raise HTTPException(
            status_code=400,
            detail=f"Historical-period insight generation is not supported yet. Latest available period is {latest_period}.",
        )

    try:
        report = workspace_service.generate_and_save_insight_report(
            code,
            lang=service_lang,
            period=requested_period,
        )
    except RuntimeError as exc:
        logger.warning("Insight generation fell back to archive summary for {}: {}", code, exc)
        try:
            bundle = workspace_service.get_metric_bundle(code)
            model_response = workspace_service.get_model_response(code, service_lang)
            if service_lang == "en-US":
                summary = (
                    f"Archive-only fallback insight for {bundle.stock_name or bundle.stock_code}. "
                    f"ROE={next((item.value for item in bundle.values if item.key == 'roe'), 'N/A')}, "
                    f"Debt/Asset={next((item.value for item in bundle.values if item.key == 'debt_to_asset_ratio'), 'N/A')}."
                )
                actions = ["Configure DEEPSEEK_API_KEY to enable full AI-generated narrative."]
            else:
                summary = (
                    f"{bundle.stock_name or bundle.stock_code} 当前返回的是归档数据降级洞察。"
                    f"ROE={next((item.value for item in bundle.values if item.key == 'roe'), 'N/A')}，"
                    f"资产负债率={next((item.value for item in bundle.values if item.key == 'debt_to_asset_ratio'), 'N/A')}。"
                )
                actions = ["配置 DEEPSEEK_API_KEY 后可启用完整 AI 叙事分析。"]

            fallback_report = InsightReportResponse(
                stock_code=bundle.stock_code,
                stock_name=bundle.stock_name,
                report_date=requested_period or bundle.report_date,
                lang=service_lang,
                summary=summary,
                highlights=[item.summary for item in model_response.items[:2] if item.summary],
                risks=[item.summary for item in model_response.items[2:4] if item.summary],
                open_questions=[],
                actions=actions,
                evidence=[item.key for item in bundle.values[:5]],
                generated_at=datetime.now(timezone.utc).isoformat(),
                model_version="workspace-insights-v1",
            )
            workspace_service.save_insight_report(fallback_report)
            payload = _build_legacy_insight_payload(fallback_report)
            payload["lang"] = _requested_lang(requested_lang, fallback=payload.get("lang", "zh"))
            return payload
        except Exception as inner_exc:
            raise _handle_workspace_error(inner_exc, code) from inner_exc
    except Exception as exc:
        raise _handle_workspace_error(exc, code) from exc

    payload = _build_legacy_insight_payload(report)
    payload["lang"] = _requested_lang(requested_lang, fallback=payload.get("lang", "zh"))
    return payload
