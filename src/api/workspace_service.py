from __future__ import annotations

from typing import Dict, List

from src.analyzer.metric_engine import WorkspaceMetricEngine
from src.analyzer.model_engine import WorkspaceModelEngine
from src.llm_engine.context_builder import PromptContextBuilder
from src.models.workspace_metrics import (
    AiContextResponse,
    AnalysisModelResponse,
    ApiPromptProfile,
    InsightContextResponse,
    MetricCatalogResponse,
    MetricValuesResponse,
    PromptInjectionBundle,
    SnapshotResponse,
    WorkspaceMetricBundle,
    WorkspaceStockInfo,
    WorkspaceSummary,
)
from src.storage.workspace_repository import ArchiveWorkspace, WorkspaceRepository


class WorkspaceService:
    """Archive-first workspace orchestration."""

    def __init__(
        self,
        repository: WorkspaceRepository | None = None,
        metric_engine: WorkspaceMetricEngine | None = None,
        model_engine: WorkspaceModelEngine | None = None,
        context_builder: PromptContextBuilder | None = None,
    ) -> None:
        self._repository = repository or WorkspaceRepository()
        self._metric_engine = metric_engine or WorkspaceMetricEngine()
        self._model_engine = model_engine or WorkspaceModelEngine()
        self._context_builder = context_builder or PromptContextBuilder()

    def list_workspaces(self, limit: int = 20) -> list[WorkspaceSummary]:
        return self._repository.list_workspaces(limit=limit)

    def get_workspace(self, stock_code: str) -> ArchiveWorkspace:
        return self._repository.load_workspace(stock_code)

    def get_metric_bundle(self, stock_code: str) -> WorkspaceMetricBundle:
        workspace = self.get_workspace(stock_code)
        return self._metric_engine.build_bundle(
            snapshot=workspace.snapshot,
            stock_name=workspace.stock_name,
            indicator_snapshot=workspace.indicator_snapshot,
        )

    def get_context(self, stock_code: str, profile_key: str = "archive_review") -> AiContextResponse:
        workspace = self.get_workspace(stock_code)
        bundle = self._metric_engine.build_bundle(
            snapshot=workspace.snapshot,
            stock_name=workspace.stock_name,
            indicator_snapshot=workspace.indicator_snapshot,
        )
        return self._context_builder.build(workspace=workspace, metric_bundle=bundle, profile_key=profile_key)

    def get_snapshot_response(self, stock_code: str) -> SnapshotResponse:
        workspace = self.get_workspace(stock_code)
        available_periods = self._collect_periods(workspace)
        statements = {
            "balance_sheet": [item.model_dump(mode="json") for item in workspace.snapshot.balance_sheets],
            "income_statement": [item.model_dump(mode="json") for item in workspace.snapshot.income_statements],
            "cashflow_statement": [item.model_dump(mode="json") for item in workspace.snapshot.cashflow_statements],
        }
        return SnapshotResponse(
            stock=WorkspaceStockInfo(
                stock_code=workspace.stock_code,
                stock_name=workspace.stock_name,
                market=workspace.market,
            ),
            available_periods=available_periods,
            statements=statements,
            updated_at=workspace.archives[0].fetched_at if workspace.archives else None,
        )

    def get_metric_catalog_response(self, stock_code: str) -> MetricCatalogResponse:
        bundle = self.get_metric_bundle(stock_code)
        return MetricCatalogResponse(
            stock_code=bundle.stock_code,
            stock_name=bundle.stock_name,
            report_date=bundle.report_date,
            total=len(bundle.catalog),
            items=bundle.catalog,
        )

    def get_metric_values_response(self, stock_code: str) -> MetricValuesResponse:
        bundle = self.get_metric_bundle(stock_code)
        return MetricValuesResponse(
            stock_code=bundle.stock_code,
            stock_name=bundle.stock_name,
            report_date=bundle.report_date,
            categories=self._metric_engine.grouped_values(bundle),
            summary=bundle.summary,
        )

    def get_model_response(self, stock_code: str) -> AnalysisModelResponse:
        bundle = self.get_metric_bundle(stock_code)
        metric_values = self._metric_engine.value_map(bundle)
        return AnalysisModelResponse(
            stock_code=bundle.stock_code,
            stock_name=bundle.stock_name,
            report_date=bundle.report_date,
            items=self._model_engine.build_items(metric_values),
        )

    def get_insight_context_response(self, stock_code: str) -> InsightContextResponse:
        workspace = self.get_workspace(stock_code)
        bundle = self.get_metric_bundle(stock_code)
        model_response = self.get_model_response(stock_code)

        profile = ApiPromptProfile(
            key="default",
            name="Default Archive Insight",
            output_contract=["核心结论", "亮点", "风险", "待验证点", "行动建议"],
        )
        injection_bundle = PromptInjectionBundle(
            system_prompt=(
                "You are an archive-first A-share financial analyst. "
                "Use Baidu archive evidence as the primary source of truth."
            ),
            company_context=f"{workspace.stock_code} {workspace.stock_name} latest report date {bundle.report_date}.",
            risk_overlay=self._build_risk_overlay(bundle),
            model_summary=self._build_model_summary(model_response.items),
            metric_digest=self._build_metric_digest(bundle),
        )
        return InsightContextResponse(
            stock_code=workspace.stock_code,
            stock_name=workspace.stock_name,
            report_date=bundle.report_date,
            profile=profile,
            injection_bundle=injection_bundle,
        )

    @staticmethod
    def _collect_periods(workspace: ArchiveWorkspace) -> List[str]:
        periods = {
            str(item.report_date)
            for item in workspace.snapshot.balance_sheets + workspace.snapshot.income_statements + workspace.snapshot.cashflow_statements
        }
        return sorted(periods, reverse=True)

    @staticmethod
    def _build_metric_digest(bundle: WorkspaceMetricBundle) -> str:
        priority_keys = {"roe", "debt_to_asset_ratio", "operating_cashflow_margin", "free_cash_flow", "net_income_yoy"}
        parts = [f"{item.label}: {item.value}" for item in bundle.values if item.key in priority_keys]
        return " | ".join(parts)

    @staticmethod
    def _build_model_summary(items: List) -> str:
        return " | ".join(f"{item.label}: {item.verdict}" for item in items)

    @staticmethod
    def _build_risk_overlay(bundle: WorkspaceMetricBundle) -> str:
        values: Dict[str, str] = {item.key: item.value for item in bundle.values}
        return (
            f"Leverage={values.get('debt_to_asset_ratio', '0.0000')}, "
            f"Liquidity={values.get('current_ratio', '0.0000')}, "
            f"Growth={values.get('net_income_yoy', '0.0000')}"
        )
