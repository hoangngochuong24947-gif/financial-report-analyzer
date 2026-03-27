"""Workspace routes for archive-first analysis."""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_workspace_service
from src.api.workspace_service import WorkspaceService
from src.models.workspace_metrics import (
    AiContextResponse,
    AnalysisModelResponse,
    InsightContextResponse,
    MetricCatalogResponse,
    MetricValuesResponse,
    SnapshotResponse,
    WorkspaceMetricBundle,
    WorkspaceSummary,
)
from src.utils.logger import logger

router = APIRouter(tags=["workspaces"])


@router.get("/api/v2/workspaces", response_model=list[WorkspaceSummary])
@router.get("/api/v2/workspace", response_model=list[WorkspaceSummary])
async def list_workspaces(
    limit: int = Query(20, ge=1, le=200, description="Number of workspaces to return"),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.list_workspaces(limit=limit)
    except Exception as exc:
        logger.error(f"Failed to list workspaces: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/v2/workspaces/{code}/metrics", response_model=WorkspaceMetricBundle)
async def get_workspace_metrics(
    code: str,
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.get_metric_bundle(code)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to build workspace metrics for {code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/v2/workspaces/{code}/context", response_model=AiContextResponse)
async def get_workspace_context(
    code: str,
    profile_key: str = Query("archive_review", description="Prompt profile key"),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.get_context(code, profile_key=profile_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to build workspace context for {code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/v2/workspace/{code}/snapshot", response_model=SnapshotResponse)
async def get_workspace_snapshot(
    code: str,
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.get_snapshot_response(code)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to build workspace snapshot for {code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/v2/workspace/{code}/metrics/catalog", response_model=MetricCatalogResponse)
async def get_workspace_metric_catalog(
    code: str,
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.get_metric_catalog_response(code)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to build workspace metric catalog for {code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/v2/workspace/{code}/metrics", response_model=MetricValuesResponse)
async def get_workspace_metric_values(
    code: str,
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.get_metric_values_response(code)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to build workspace metric values for {code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/v2/workspace/{code}/models", response_model=AnalysisModelResponse)
async def get_workspace_models(
    code: str,
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.get_model_response(code)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to build workspace models for {code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/v2/workspace/{code}/insights/context", response_model=InsightContextResponse)
async def get_workspace_insight_context(
    code: str,
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.get_insight_context_response(code)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to build workspace insight context for {code}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
