from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MetricCatalogItem(BaseModel):
    key: str = Field(..., description="Stable metric key")
    label: str = Field(..., description="Human-readable metric label")
    group: str = Field(..., description="Metric group")
    description: str = Field(..., description="Metric description")
    unit: str = Field(default="", description="Display unit")
    source: str = Field(default="archive", description="Primary data source")


class MetricValueItem(BaseModel):
    key: str = Field(..., description="Stable metric key")
    label: str = Field(..., description="Human-readable metric label")
    group: str = Field(..., description="Metric group")
    value: str = Field(..., description="Formatted metric value")
    period: Optional[str] = Field(default=None, description="Reporting period")
    source: str = Field(default="archive", description="Primary data source")
    note: Optional[str] = Field(default=None, description="Extra context")


class WorkspaceMetricBundle(BaseModel):
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    report_date: str = Field(..., description="Latest archive report date")
    catalog: list[MetricCatalogItem] = Field(default_factory=list, description="Metric catalog")
    values: list[MetricValueItem] = Field(default_factory=list, description="Metric values")
    summary: str = Field(default="", description="Short metric summary")


class PromptProfile(BaseModel):
    key: str = Field(..., description="Profile key")
    name: str = Field(..., description="Profile name")
    system_prompt: str = Field(..., description="System prompt instructions")
    context_title: str = Field(..., description="Context title")
    context_guidance: list[str] = Field(default_factory=list, description="Profile-specific context hints")


class InjectionBundle(BaseModel):
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    report_date: str = Field(..., description="Latest report date")
    metric_groups: list[str] = Field(default_factory=list, description="Metric groups included")
    metric_values: list[MetricValueItem] = Field(default_factory=list, description="Metric values")
    archives: list[str] = Field(default_factory=list, description="Archive manifest paths")


class AiContextResponse(BaseModel):
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    report_date: str = Field(..., description="Latest report date")
    profile_key: str = Field(..., description="Prompt profile key")
    profile_name: str = Field(..., description="Prompt profile name")
    system_prompt: str = Field(..., description="System prompt")
    context_text: str = Field(..., description="Rendered prompt context")
    injection_bundle: InjectionBundle = Field(..., description="Structured injection bundle")
    summary: str = Field(default="", description="Short context summary")


class WorkspaceArchiveItem(BaseModel):
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    market: str = Field(..., description="Market code")
    dataset: str = Field(..., description="Dataset name")
    fetched_at: str = Field(..., description="Fetch timestamp")
    raw_path: str = Field(..., description="Raw archive path")
    csv_path: str = Field(..., description="Processed archive path")
    manifest_path: str = Field(..., description="Manifest path")
    row_count: int = Field(..., description="Row count")
    status: str = Field(..., description="Archive status")
    report_date: Optional[str] = Field(default=None, description="Latest report date")


class WorkspaceSummary(BaseModel):
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    market: str = Field(..., description="Market code")
    latest_report_date: Optional[str] = Field(default=None, description="Latest report date")
    dataset_count: int = Field(default=0, description="Number of datasets")
    archives: list[WorkspaceArchiveItem] = Field(default_factory=list, description="Archive items")


class WorkspaceStockInfo(BaseModel):
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    market: str = Field(..., description="Market code")


class SnapshotResponse(BaseModel):
    stock: WorkspaceStockInfo = Field(..., description="Stock identity")
    available_periods: list[str] = Field(default_factory=list, description="Available reporting periods")
    statements: dict[str, list[dict[str, Any]]] = Field(default_factory=dict, description="Normalized statements")
    source: str = Field(default="baidu_archive", description="Primary source")
    updated_at: Optional[str] = Field(default=None, description="Latest archive fetch timestamp")


class WorkspaceStatementRow(BaseModel):
    field: str = Field(..., description="Stable field key")
    label: str = Field(..., description="Display label")
    value: str = Field(..., description="Raw serialized value")
    display_value: str = Field(..., description="Human-friendly display value")
    period: Optional[str] = Field(default=None, description="Reporting period")
    source: str = Field(default="archive", description="Primary data source")


class WorkspaceStatementTab(BaseModel):
    key: str = Field(..., description="Stable statement key")
    label: str = Field(..., description="Display label")
    period: str = Field(..., description="Selected reporting period")
    rows: list[WorkspaceStatementRow] = Field(default_factory=list, description="Normalized statement rows")


class WorkspaceStatementsResponse(BaseModel):
    stock: WorkspaceStockInfo = Field(..., description="Stock identity")
    lang: str = Field(default="zh", description="Response language")
    available_periods: list[str] = Field(default_factory=list, description="Available reporting periods")
    selected_period: str = Field(..., description="Selected reporting period")
    tabs: list[WorkspaceStatementTab] = Field(default_factory=list, description="Statement tabs")
    source: str = Field(default="baidu_archive", description="Primary source")


class MetricCatalogResponse(BaseModel):
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    report_date: str = Field(..., description="Latest report date")
    total: int = Field(..., description="Catalog size")
    items: list[MetricCatalogItem] = Field(default_factory=list, description="Catalog entries")


class MetricValuesResponse(BaseModel):
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    report_date: str = Field(..., description="Latest report date")
    categories: dict[str, list[MetricValueItem]] = Field(default_factory=dict, description="Metrics grouped by category")
    summary: str = Field(default="", description="Short metric summary")


class AnalysisModelItem(BaseModel):
    key: str = Field(..., description="Stable model key")
    label: str = Field(..., description="Model label")
    verdict: str = Field(..., description="Model verdict")
    summary: str = Field(..., description="Model summary")
    score: Optional[str] = Field(default=None, description="Optional normalized score")
    evidence_keys: list[str] = Field(default_factory=list, description="Metric keys backing the model")


class AnalysisModelResponse(BaseModel):
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    report_date: str = Field(..., description="Latest report date")
    items: list[AnalysisModelItem] = Field(default_factory=list, description="Analysis model cards")


class ApiPromptProfile(BaseModel):
    key: str = Field(..., description="Profile key")
    name: str = Field(..., description="Profile name")
    output_contract: list[str] = Field(default_factory=list, description="Expected output sections")


class PromptInjectionBundle(BaseModel):
    system_prompt: str = Field(..., description="Injected system prompt")
    company_context: str = Field(..., description="Company context block")
    risk_overlay: str = Field(..., description="Risk overlay block")
    model_summary: str = Field(..., description="Model summary block")
    metric_digest: str = Field(..., description="Metric digest block")


class InsightContextResponse(BaseModel):
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    report_date: str = Field(..., description="Latest report date")
    profile: ApiPromptProfile = Field(..., description="Prompt profile")
    injection_bundle: PromptInjectionBundle = Field(..., description="Structured prompt injection bundle")


class WorkspaceInsightGenerateRequest(BaseModel):
    period: Optional[str] = Field(default=None, description="Selected reporting period")
    lang: str = Field(default="zh", description="Response language")


class WorkspaceInsightEvidence(BaseModel):
    key: str = Field(..., description="Evidence key")
    label: str = Field(..., description="Evidence label")
    value: str = Field(..., description="Evidence value")
    period: Optional[str] = Field(default=None, description="Evidence period")
    source: str = Field(default="archive", description="Primary source")


class WorkspaceInsightResponse(BaseModel):
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    report_date: str = Field(..., description="Selected report date")
    lang: str = Field(default="zh", description="Response language")
    summary: str = Field(..., description="Short executive summary")
    highlights: list[str] = Field(default_factory=list, description="Key highlights")
    risks: list[str] = Field(default_factory=list, description="Key risks")
    open_questions: list[str] = Field(default_factory=list, description="Open questions")
    actions: list[str] = Field(default_factory=list, description="Recommended actions")
    evidence: list[WorkspaceInsightEvidence] = Field(default_factory=list, description="Evidence citations")
    generated_at: datetime = Field(..., description="Generation timestamp")
    model_version: str = Field(default="workspace-insights-v1", description="Model version tag")


class StatementDetailRow(BaseModel):
    key: str = Field(..., description="Stable row key")
    label: str = Field(..., description="Localized display label")
    value: Any = Field(default=None, description="Raw value")
    display_value: str = Field(default="", description="Formatted display value")
    unit: str = Field(default="", description="Display unit")
    source: str = Field(default="baidu_archive", description="Primary data source")
    is_estimated: bool = Field(default=False, description="Whether value is estimated")


class StatementDetailTab(BaseModel):
    key: str = Field(..., description="Statement tab key")
    title: str = Field(..., description="Localized tab title")
    rows: list[StatementDetailRow] = Field(default_factory=list, description="Statement rows")


class StatementDetailResponse(BaseModel):
    stock: WorkspaceStockInfo = Field(..., description="Stock identity")
    lang: str = Field(default="zh-CN", description="Display language")
    available_periods: list[str] = Field(default_factory=list, description="Available periods across all statement sets")
    selected_period: str = Field(..., description="Selected reporting period")
    tabs: list[StatementDetailTab] = Field(default_factory=list, description="Statement tabs")
    updated_at: Optional[str] = Field(default=None, description="Latest archive fetch timestamp")


class InsightReportResponse(BaseModel):
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    report_date: str = Field(..., description="Selected report date")
    lang: str = Field(default="zh-CN", description="Output language")
    summary: str = Field(default="", description="Executive summary")
    highlights: list[str] = Field(default_factory=list, description="Positive evidence points")
    risks: list[str] = Field(default_factory=list, description="Risk points")
    open_questions: list[str] = Field(default_factory=list, description="Follow-up questions")
    actions: list[str] = Field(default_factory=list, description="Suggested actions")
    evidence: list[str] = Field(default_factory=list, description="Evidence references")
    generated_at: str = Field(..., description="Generation timestamp")
    model_version: str = Field(default="workspace-insights-v1", description="Workspace insight contract version")
