from __future__ import annotations

from typing import List

from src.models.workspace_metrics import AiContextResponse, InjectionBundle, WorkspaceMetricBundle
from src.storage.workspace_repository import ArchiveWorkspace
from src.llm_engine.prompt_profiles import PromptProfileRegistry


class PromptContextBuilder:
    """Render AI context from archive workspace evidence and metric bundles."""

    def __init__(self, registry: PromptProfileRegistry | None = None) -> None:
        self._registry = registry or PromptProfileRegistry.default()

    def build(
        self,
        *,
        workspace: ArchiveWorkspace,
        metric_bundle: WorkspaceMetricBundle,
        profile_key: str = "archive_review",
    ) -> AiContextResponse:
        profile = self._registry.get(profile_key)
        metric_groups = self._collect_metric_groups(metric_bundle)
        archives = [item.manifest_path for item in workspace.archives]
        injection_bundle = InjectionBundle(
            stock_code=workspace.stock_code,
            stock_name=workspace.stock_name,
            report_date=workspace.latest_report_date or metric_bundle.report_date,
            metric_groups=metric_groups,
            metric_values=metric_bundle.values,
            archives=archives,
        )

        context_text = self._render_context(profile.context_title, workspace.stock_code, workspace.stock_name, metric_bundle)
        summary = (
            f"{workspace.stock_name} archive-first context prepared with "
            f"{len(metric_bundle.values)} metrics from {len(workspace.archives)} archives."
        )

        return AiContextResponse(
            stock_code=workspace.stock_code,
            stock_name=workspace.stock_name,
            report_date=injection_bundle.report_date,
            profile_key=profile.key,
            profile_name=profile.name,
            system_prompt=profile.system_prompt,
            context_text=context_text,
            injection_bundle=injection_bundle,
            summary=summary,
        )

    @staticmethod
    def _collect_metric_groups(metric_bundle: WorkspaceMetricBundle) -> List[str]:
        groups = []
        for item in metric_bundle.values:
            if item.group not in groups:
                groups.append(item.group)
        return groups

    @staticmethod
    def _render_context(title: str, stock_code: str, stock_name: str, metric_bundle: WorkspaceMetricBundle) -> str:
        lines = [
            title,
            f"Stock: {stock_code} {stock_name}",
            f"Report date: {metric_bundle.report_date}",
            "Metrics:",
        ]
        for item in metric_bundle.values:
            lines.append(f"- {item.key.upper()}: {item.value}")
        lines.append("Source preference: archive-first")
        return "\n".join(lines)
