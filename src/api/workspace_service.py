from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.analyzer.metric_engine import WorkspaceMetricEngine
from src.analyzer.model_engine import WorkspaceModelEngine
from src.llm_engine.context_builder import PromptContextBuilder
from src.llm_engine.llm_client import get_llm_client
from src.models.workspace_metrics import (
    AiContextResponse,
    AnalysisModelItem,
    AnalysisModelResponse,
    ApiPromptProfile,
    InsightContextResponse,
    InsightReportHistoryItem,
    InsightReportResponse,
    MetricCatalogItem,
    MetricCatalogResponse,
    MetricValueItem,
    MetricValuesResponse,
    PromptInjectionBundle,
    SnapshotResponse,
    StatementDetailResponse,
    StatementDetailRow,
    StatementDetailTab,
    WorkspaceMetricBundle,
    WorkspaceStockInfo,
    WorkspaceSummary,
)
from src.storage.workspace_repository import ArchiveWorkspace, WorkspaceRepository
from src.storage.report_repository import ReportRepository


class WorkspaceService:
    """Archive-first workspace orchestration."""

    _STATEMENT_TAB_TITLES = {
        "zh-CN": {
            "balance_sheet": "资产负债表",
            "income_statement": "利润表",
            "cashflow_statement": "现金流量表",
        },
        "en-US": {
            "balance_sheet": "Balance Sheet",
            "income_statement": "Income Statement",
            "cashflow_statement": "Cash Flow Statement",
        },
    }

    _STATEMENT_LABELS = {
        "zh-CN": {
            "report_date": "报告期",
            "total_current_assets": "流动资产合计",
            "total_non_current_assets": "非流动资产合计",
            "total_assets": "总资产",
            "total_current_liabilities": "流动负债合计",
            "total_non_current_liabilities": "非流动负债合计",
            "total_liabilities": "总负债",
            "total_equity": "所有者权益合计",
            "total_revenue": "营业总收入",
            "operating_cost": "营业成本",
            "operating_profit": "营业利润",
            "total_profit": "利润总额",
            "net_income": "净利润",
            "operating_cashflow": "经营活动现金流量净额",
            "investing_cashflow": "投资活动现金流量净额",
            "financing_cashflow": "筹资活动现金流量净额",
            "net_cashflow": "现金及现金等价物净增加额",
        },
        "en-US": {
            "report_date": "Report Date",
            "total_current_assets": "Total Current Assets",
            "total_non_current_assets": "Total Non-current Assets",
            "total_assets": "Total Assets",
            "total_current_liabilities": "Total Current Liabilities",
            "total_non_current_liabilities": "Total Non-current Liabilities",
            "total_liabilities": "Total Liabilities",
            "total_equity": "Total Equity",
            "total_revenue": "Total Revenue",
            "operating_cost": "Operating Cost",
            "operating_profit": "Operating Profit",
            "total_profit": "Total Profit",
            "net_income": "Net Income",
            "operating_cashflow": "Operating Cash Flow",
            "investing_cashflow": "Investing Cash Flow",
            "financing_cashflow": "Financing Cash Flow",
            "net_cashflow": "Net Cash Flow",
        },
    }

    _METRIC_LABELS_ZH = {
        "Return on Equity": "净资产收益率",
        "Return on Assets": "总资产收益率",
        "Net Profit Margin": "净利率",
        "Gross Profit Margin": "毛利率",
        "Operating Margin": "营业利润率",
        "Pretax Margin": "税前利润率",
        "Current Ratio": "流动比率",
        "Quick Ratio": "速动比率",
        "Debt to Asset Ratio": "资产负债率",
        "Debt to Equity Ratio": "产权比率",
        "Equity Ratio": "权益比率",
        "Working Capital": "营运资本",
        "Asset Turnover": "总资产周转率",
        "Equity Multiplier": "权益乘数",
        "Revenue to Equity": "营收权益比",
        "Current Asset Turnover": "流动资产周转率",
        "Operating Cash Flow": "经营现金流",
        "Free Cash Flow": "自由现金流",
        "Cash to Profit Ratio": "现金利润比",
        "Operating Cash Flow Margin": "经营现金流率",
        "Net Cash Flow": "净现金流",
        "Investing Cash Flow": "投资现金流",
        "Financing Cash Flow": "筹资现金流",
        "Net Income YoY": "净利润同比",
        "Revenue YoY": "营收同比",
        "Operating Profit YoY": "营业利润同比",
        "Operating Cash Flow YoY": "经营现金流同比",
        "Total Assets": "总资产",
        "Total Liabilities": "总负债",
        "Total Equity": "总权益",
    }

    _MODEL_LABELS_ZH = {
        "DuPont Analysis": "杜邦分析",
        "Cashflow Quality": "现金流质量",
        "Growth Quality": "成长质量",
        "Solvency Pressure": "偿债压力",
        "Operating Efficiency": "经营效率",
    }

    def __init__(
        self,
        repository: WorkspaceRepository | None = None,
        report_repository: ReportRepository | None = None,
        metric_engine: WorkspaceMetricEngine | None = None,
        model_engine: WorkspaceModelEngine | None = None,
        context_builder: PromptContextBuilder | None = None,
    ) -> None:
        self._repository = repository or WorkspaceRepository()
        self._report_repository = report_repository or ReportRepository(
            root=str(getattr(self._repository, "_archive_root", "data"))
        )
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

    def get_snapshot_response(self, stock_code: str, lang: str = "zh-CN") -> SnapshotResponse:
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

    def get_statement_detail_response(
        self,
        stock_code: str,
        period: str | None = None,
        lang: str = "zh-CN",
    ) -> StatementDetailResponse:
        workspace = self.get_workspace(stock_code)
        locale = self._normalize_lang(lang)
        available_periods = self._collect_periods(workspace)
        if not available_periods:
            raise FileNotFoundError(f"No statement periods found for {stock_code}")

        selected_period = period or available_periods[0]
        if selected_period not in available_periods:
            raise FileNotFoundError(f"No statement data found for period {selected_period}")

        tabs = [
            StatementDetailTab(
                key=tab_key,
                title=self._STATEMENT_TAB_TITLES[locale][tab_key],
                rows=self._statement_rows(workspace, tab_key, selected_period, locale),
            )
            for tab_key in ("balance_sheet", "income_statement", "cashflow_statement")
        ]

        return StatementDetailResponse(
            stock=WorkspaceStockInfo(
                stock_code=workspace.stock_code,
                stock_name=workspace.stock_name,
                market=workspace.market,
            ),
            lang=locale,
            available_periods=available_periods,
            selected_period=selected_period,
            tabs=tabs,
            updated_at=workspace.archives[0].fetched_at if workspace.archives else None,
        )

    def get_metric_catalog_response(self, stock_code: str, lang: str = "zh-CN") -> MetricCatalogResponse:
        bundle = self._localized_bundle(self.get_metric_bundle(stock_code), lang)
        return MetricCatalogResponse(
            stock_code=bundle.stock_code,
            stock_name=bundle.stock_name,
            report_date=bundle.report_date,
            total=len(bundle.catalog),
            items=bundle.catalog,
        )

    def get_metric_values_response(self, stock_code: str, lang: str = "zh-CN") -> MetricValuesResponse:
        bundle = self._localized_bundle(self.get_metric_bundle(stock_code), lang)
        return MetricValuesResponse(
            stock_code=bundle.stock_code,
            stock_name=bundle.stock_name,
            report_date=bundle.report_date,
            categories=self._metric_engine.grouped_values(bundle),
            summary=bundle.summary,
        )

    def get_model_response(self, stock_code: str, lang: str = "zh-CN") -> AnalysisModelResponse:
        locale = self._normalize_lang(lang)
        bundle = self.get_metric_bundle(stock_code)
        metric_values = self._metric_engine.value_map(bundle)
        items = self._localized_models(self._model_engine.build_items(metric_values), locale)
        return AnalysisModelResponse(
            stock_code=bundle.stock_code,
            stock_name=bundle.stock_name,
            report_date=bundle.report_date,
            items=items,
        )

    def get_insight_context_response(self, stock_code: str, lang: str = "zh-CN") -> InsightContextResponse:
        locale = self._normalize_lang(lang)
        workspace = self.get_workspace(stock_code)
        bundle = self._localized_bundle(self.get_metric_bundle(stock_code), locale)
        model_response = self.get_model_response(stock_code, locale)

        profile = ApiPromptProfile(
            key="default",
            name="Default Archive Insight" if locale == "en-US" else "默认归档洞察",
            output_contract=(
                ["Core Conclusion", "Highlights", "Risks", "Open Questions", "Actions"]
                if locale == "en-US"
                else ["核心结论", "亮点", "风险", "待验证点", "行动建议"]
            ),
        )
        injection_bundle = PromptInjectionBundle(
            system_prompt=(
                "You are an archive-first A-share financial analyst. Use Baidu archive evidence as the primary source of truth."
                if locale == "en-US"
                else "你是一名以归档优先为原则的 A 股财报分析师，请以百度归档数据为主要事实来源。"
            ),
            company_context=(
                f"{workspace.stock_code} {workspace.stock_name} latest report date {bundle.report_date}."
                if locale == "en-US"
                else f"{workspace.stock_code} {workspace.stock_name} 最新报告期为 {bundle.report_date}。"
            ),
            risk_overlay=self._build_risk_overlay(bundle, locale),
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

    def generate_insight_report(
        self,
        stock_code: str,
        lang: str = "zh-CN",
        period: str | None = None,
    ) -> InsightReportResponse:
        locale = self._normalize_lang(lang)
        context = self.get_insight_context_response(stock_code, locale)
        model_response = self.get_model_response(stock_code, locale)
        selected_period = period or context.report_date
        prompt = self._build_insight_prompt(context, model_response, locale)
        raw_output = get_llm_client().analyze(prompt=prompt, system_prompt=context.injection_bundle.system_prompt)
        parsed = self._parse_generated_report(raw_output, locale)
        evidence = parsed["evidence"] if parsed["evidence"] else self._default_evidence_keys(stock_code)
        return InsightReportResponse(
            stock_code=context.stock_code,
            stock_name=context.stock_name,
            report_date=selected_period,
            lang=locale,
            summary=parsed["summary"],
            highlights=parsed["highlights"],
            risks=parsed["risks"],
            open_questions=parsed["open_questions"],
            actions=parsed["actions"],
            evidence=evidence,
            generated_at=datetime.now(timezone.utc).isoformat(),
            model_version="workspace-insights-v1",
        )

    def generate_and_save_insight_report(
        self,
        stock_code: str,
        lang: str = "zh-CN",
        period: str | None = None,
    ) -> InsightReportResponse:
        report = self.generate_insight_report(stock_code=stock_code, lang=lang, period=period)
        self._report_repository.save_report(report)
        return report

    def save_insight_report(self, report: InsightReportResponse) -> InsightReportHistoryItem:
        return self._report_repository.save_report(report)

    def get_saved_insight_report(
        self,
        stock_code: str,
        lang: str = "zh-CN",
        period: str | None = None,
    ) -> InsightReportResponse:
        locale = self._normalize_lang(lang)
        return self._report_repository.load_report(stock_code=stock_code, period=period, lang=locale)

    def list_saved_insight_reports(self, stock_code: str, limit: int = 20) -> list[InsightReportHistoryItem]:
        return self._report_repository.list_reports(stock_code=stock_code, limit=limit)

    def export_statement_rows(
        self,
        stock_code: str,
        statement_key: str,
        period: str | None = None,
        lang: str = "zh-CN",
    ) -> tuple[str, str, list[StatementDetailRow]]:
        detail = self.get_statement_detail_response(stock_code=stock_code, period=period, lang=lang)
        tab = next((item for item in detail.tabs if item.key == statement_key), None)
        if tab is None:
            raise FileNotFoundError(f"No statement tab found for {stock_code} {statement_key}")
        return detail.stock.stock_name, detail.selected_period, tab.rows

    def export_all_statement_rows(
        self,
        stock_code: str,
        lang: str = "zh-CN",
    ) -> tuple[str, dict[str, list[dict[str, object]]]]:
        workspace = self.get_workspace(stock_code)
        locale = self._normalize_lang(lang)
        sheets: dict[str, list[dict[str, object]]] = {}
        for statement_key in ("balance_sheet", "income_statement", "cashflow_statement"):
            rows: list[dict[str, object]] = []
            for period in self._collect_periods(workspace):
                for row in self._statement_rows(workspace, statement_key, period, locale):
                    rows.append(
                        {
                            "report_date": period,
                            "section": row.section or "",
                            "label": row.label,
                            "display_value": row.display_value,
                            "value": row.value,
                            "unit": row.unit,
                            "source": row.source,
                            "is_estimated": row.is_estimated,
                        }
                    )
            sheets[statement_key] = rows
        return workspace.stock_name, sheets

    @staticmethod
    def _collect_periods(workspace: ArchiveWorkspace) -> List[str]:
        periods = {
            str(item.report_date)
            for item in workspace.snapshot.balance_sheets + workspace.snapshot.income_statements + workspace.snapshot.cashflow_statements
        }
        return sorted(periods, reverse=True)

    def _localized_bundle(self, bundle: WorkspaceMetricBundle, lang: str) -> WorkspaceMetricBundle:
        locale = self._normalize_lang(lang)
        if locale == "en-US":
            return bundle

        localized_catalog = [
            MetricCatalogItem(
                key=item.key,
                label=self._METRIC_LABELS_ZH.get(item.label, item.label),
                group=item.group,
                description=item.description,
                unit=item.unit,
                source=item.source,
            )
            for item in bundle.catalog
        ]
        catalog_lookup = {item.key: item for item in localized_catalog}
        localized_values = [
            MetricValueItem(
                key=item.key,
                label=catalog_lookup.get(item.key, item).label,
                group=item.group,
                value=item.value,
                period=item.period,
                source=item.source,
                note=item.note,
            )
            for item in bundle.values
        ]
        summary = (
            f"{bundle.stock_name or bundle.stock_code} 归档指标摘要："
            f"ROE={self._metric_value_from_key(bundle, 'roe')}，"
            f"资产负债率={self._metric_value_from_key(bundle, 'debt_to_asset_ratio')}，"
            f"经营现金流率={self._metric_value_from_key(bundle, 'operating_cashflow_margin')}，"
            f"自由现金流={self._metric_value_from_key(bundle, 'free_cash_flow')}"
        )
        return WorkspaceMetricBundle(
            stock_code=bundle.stock_code,
            stock_name=bundle.stock_name,
            report_date=bundle.report_date,
            catalog=localized_catalog,
            values=localized_values,
            summary=summary,
        )

    def _localized_models(self, items: list[AnalysisModelItem], lang: str) -> list[AnalysisModelItem]:
        if lang == "en-US":
            return items
        return [
            AnalysisModelItem(
                key=item.key,
                label=self._MODEL_LABELS_ZH.get(item.label, item.label),
                verdict=item.verdict,
                summary=item.summary,
                score=item.score,
                evidence_keys=item.evidence_keys,
            )
            for item in items
        ]

    def _statement_rows(
        self,
        workspace: ArchiveWorkspace,
        statement_key: str,
        period: str,
        lang: str,
    ) -> list[StatementDetailRow]:
        detailed_rows = workspace.statement_details.get(statement_key, {}).get(period, [])
        if detailed_rows:
            return [
                StatementDetailRow(
                    key=str(row.get("key", "")),
                    label=str(row.get("label", "")),
                    section=str(row.get("section")) if row.get("section") else None,
                    value=row.get("value"),
                    display_value=str(row.get("display_value", "")),
                    unit=str(row.get("unit", "")),
                    source=str(row.get("source", "baidu_archive")),
                    is_estimated=bool(row.get("is_estimated", False)),
                )
                for row in detailed_rows
                if row.get("label")
            ]

        statement_items = {
            "balance_sheet": workspace.snapshot.balance_sheets,
            "income_statement": workspace.snapshot.income_statements,
            "cashflow_statement": workspace.snapshot.cashflow_statements,
        }[statement_key]

        match = next((item for item in statement_items if str(item.report_date) == period), None)
        if match is None:
            return []

        payload = match.model_dump(mode="json")
        rows: list[StatementDetailRow] = []
        for key, value in payload.items():
            if key == "stock_code":
                continue
            rows.append(
                StatementDetailRow(
                    key=key,
                    label=self._STATEMENT_LABELS[lang].get(key, key),
                    section=None,
                    value=value,
                    display_value=str(value),
                    unit="",
                    source="baidu_archive",
                    is_estimated=False,
                )
            )
        return rows

    @staticmethod
    def _metric_value_from_key(bundle: WorkspaceMetricBundle, key: str) -> str:
        match = next((item for item in bundle.values if item.key == key), None)
        return match.value if match else "0"

    @staticmethod
    def _build_metric_digest(bundle: WorkspaceMetricBundle) -> str:
        priority_keys = {"roe", "debt_to_asset_ratio", "operating_cashflow_margin", "free_cash_flow", "net_income_yoy"}
        parts = [f"{item.label}: {item.value}" for item in bundle.values if item.key in priority_keys]
        return " | ".join(parts)

    def _default_evidence_keys(self, stock_code: str) -> list[str]:
        bundle = self.get_metric_bundle(stock_code)
        return [item.key for item in bundle.values[:5]]

    @staticmethod
    def _build_model_summary(items: List[AnalysisModelItem]) -> str:
        return " | ".join(f"{item.label}: {item.verdict}" for item in items)

    @staticmethod
    def _build_risk_overlay(bundle: WorkspaceMetricBundle, lang: str) -> str:
        values: Dict[str, str] = {item.key: item.value for item in bundle.values}
        if lang == "en-US":
            return (
                f"Leverage={values.get('debt_to_asset_ratio', '0.0000')}, "
                f"Liquidity={values.get('current_ratio', '0.0000')}, "
                f"Growth={values.get('net_income_yoy', '0.0000')}"
            )
        return (
            f"杠杆={values.get('debt_to_asset_ratio', '0.0000')}，"
            f"流动性={values.get('current_ratio', '0.0000')}，"
            f"成长={values.get('net_income_yoy', '0.0000')}"
        )

    @staticmethod
    def _normalize_lang(lang: str | None) -> str:
        if not lang:
            return "zh-CN"
        lowered = lang.lower()
        if lowered.startswith("en"):
            return "en-US"
        return "zh-CN"

    @staticmethod
    def _build_insight_prompt(
        context: InsightContextResponse,
        models: AnalysisModelResponse,
        lang: str,
    ) -> str:
        response_instruction = (
            "Return valid JSON with keys summary, highlights, risks, open_questions, actions, evidence."
            if lang == "en-US"
            else "请只返回合法 JSON，包含 summary、highlights、risks、open_questions、actions、evidence 这些字段。"
        )
        model_lines = "\n".join(f"- {item.label}: {item.summary}" for item in models.items)
        return (
            f"{response_instruction}\n\n"
            f"Company:\n{context.injection_bundle.company_context}\n\n"
            f"Risk overlay:\n{context.injection_bundle.risk_overlay}\n\n"
            f"Metric digest:\n{context.injection_bundle.metric_digest}\n\n"
            f"Model summary:\n{context.injection_bundle.model_summary}\n\n"
            f"Detailed model cards:\n{model_lines}"
        )

    @staticmethod
    def _parse_generated_report(raw_output: str, lang: str) -> dict[str, list[str] | str]:
        parsed = WorkspaceService._try_parse_json(raw_output)
        if parsed is None:
            parsed = {
                "summary": raw_output.strip() or (
                    "No summary generated."
                    if lang == "en-US"
                    else "暂未生成总结。"
                ),
                "highlights": [],
                "risks": [],
                "open_questions": [],
                "actions": [],
                "evidence": [],
            }

        defaults = {
            "summary": "No summary generated." if lang == "en-US" else "暂未生成总结。",
            "highlights": [],
            "risks": [],
            "open_questions": [],
            "actions": [],
            "evidence": [],
        }
        normalized: dict[str, list[str] | str] = {}
        for key, default in defaults.items():
            value = parsed.get(key, default)
            if isinstance(default, list):
                normalized[key] = [str(item).strip() for item in value] if isinstance(value, list) else []
            else:
                normalized[key] = str(value).strip() if value else default
        return normalized

    @staticmethod
    def _try_parse_json(raw_output: str) -> dict[str, Any] | None:
        text = raw_output.strip()
        if not text:
            return None
        candidates = [text]
        block_match = re.search(r"\{.*\}", text, re.S)
        if block_match:
            candidates.insert(0, block_match.group(0))

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None
