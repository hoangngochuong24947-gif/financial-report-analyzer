from __future__ import annotations

from decimal import Decimal
from typing import Dict, List

from src.models.workspace_metrics import AnalysisModelItem


class WorkspaceModelEngine:
    """Build fixed financial analysis model cards from metric evidence."""

    def build_items(self, metric_values: Dict[str, Decimal]) -> List[AnalysisModelItem]:
        return [
            self._dupont(metric_values),
            self._cashflow_quality(metric_values),
            self._growth_quality(metric_values),
            self._solvency_pressure(metric_values),
            self._operating_efficiency(metric_values),
        ]

    def _dupont(self, metrics: Dict[str, Decimal]) -> AnalysisModelItem:
        roe = metrics.get("roe", Decimal("0"))
        verdict = "strong" if roe >= Decimal("0.1500") else "mixed" if roe >= Decimal("0.0800") else "weak"
        summary = (
            f"ROE {roe.quantize(Decimal('0.0001'))} is driven by "
            f"net margin {metrics.get('net_profit_margin', Decimal('0')).quantize(Decimal('0.0001'))}, "
            f"asset turnover {metrics.get('asset_turnover', Decimal('0')).quantize(Decimal('0.0001'))}, "
            f"and equity multiplier {metrics.get('equity_multiplier', Decimal('0')).quantize(Decimal('0.0001'))}."
        )
        return AnalysisModelItem(
            key="dupont",
            label="DuPont Analysis",
            verdict=verdict,
            summary=summary,
            score=f"{roe.quantize(Decimal('0.0001'))}",
            evidence_keys=["roe", "net_profit_margin", "asset_turnover", "equity_multiplier"],
        )

    def _cashflow_quality(self, metrics: Dict[str, Decimal]) -> AnalysisModelItem:
        ratio = metrics.get("cash_to_profit_ratio", Decimal("0"))
        fcf = metrics.get("free_cash_flow", Decimal("0"))
        verdict = "strong" if ratio >= Decimal("1.0000") and fcf > 0 else "mixed" if fcf >= 0 else "weak"
        summary = (
            f"Cash/profit ratio is {ratio.quantize(Decimal('0.0001'))} and "
            f"free cash flow is {fcf.quantize(Decimal('0.01'))}, indicating "
            f"{'solid earnings cash conversion.' if verdict == 'strong' else 'a partially supported earnings profile.' if verdict == 'mixed' else 'cash generation pressure.'}"
        )
        return AnalysisModelItem(
            key="cashflow_quality",
            label="Cashflow Quality",
            verdict=verdict,
            summary=summary,
            score=f"{ratio.quantize(Decimal('0.0001'))}",
            evidence_keys=["cash_to_profit_ratio", "free_cash_flow", "operating_cashflow_margin"],
        )

    def _growth_quality(self, metrics: Dict[str, Decimal]) -> AnalysisModelItem:
        revenue_yoy = metrics.get("revenue_yoy", Decimal("0"))
        income_yoy = metrics.get("net_income_yoy", Decimal("0"))
        verdict = "strong" if revenue_yoy > 0 and income_yoy > 0 else "mixed" if revenue_yoy > 0 or income_yoy > 0 else "weak"
        summary = (
            f"Revenue YoY is {revenue_yoy.quantize(Decimal('0.0001'))} and "
            f"net income YoY is {income_yoy.quantize(Decimal('0.0001'))}, "
            f"suggesting {'broad-based growth.' if verdict == 'strong' else 'uneven growth quality.' if verdict == 'mixed' else 'growth deterioration.'}"
        )
        return AnalysisModelItem(
            key="growth_quality",
            label="Growth Quality",
            verdict=verdict,
            summary=summary,
            score=f"{income_yoy.quantize(Decimal('0.0001'))}",
            evidence_keys=["revenue_yoy", "net_income_yoy", "operating_profit_yoy"],
        )

    def _solvency_pressure(self, metrics: Dict[str, Decimal]) -> AnalysisModelItem:
        current_ratio = metrics.get("current_ratio", Decimal("0"))
        debt_ratio = metrics.get("debt_to_asset_ratio", Decimal("0"))
        verdict = "low" if current_ratio >= Decimal("1.5000") and debt_ratio <= Decimal("0.5000") else "medium" if current_ratio >= Decimal("1.0000") else "high"
        summary = (
            f"Current ratio is {current_ratio.quantize(Decimal('0.0001'))} and "
            f"debt-to-asset ratio is {debt_ratio.quantize(Decimal('0.0001'))}, indicating "
            f"{'contained balance-sheet pressure.' if verdict == 'low' else 'manageable solvency pressure.' if verdict == 'medium' else 'elevated solvency pressure.'}"
        )
        return AnalysisModelItem(
            key="solvency_pressure",
            label="Solvency Pressure",
            verdict=verdict,
            summary=summary,
            score=f"{debt_ratio.quantize(Decimal('0.0001'))}",
            evidence_keys=["current_ratio", "debt_to_asset_ratio", "debt_to_equity_ratio", "working_capital"],
        )

    def _operating_efficiency(self, metrics: Dict[str, Decimal]) -> AnalysisModelItem:
        asset_turnover = metrics.get("asset_turnover", Decimal("0"))
        ocf_margin = metrics.get("operating_cashflow_margin", Decimal("0"))
        verdict = "strong" if asset_turnover >= Decimal("0.5000") and ocf_margin > 0 else "mixed" if ocf_margin > 0 else "weak"
        summary = (
            f"Asset turnover is {asset_turnover.quantize(Decimal('0.0001'))} and "
            f"operating cashflow margin is {ocf_margin.quantize(Decimal('0.0001'))}, "
            f"showing {'healthy operating efficiency.' if verdict == 'strong' else 'acceptable but improvable efficiency.' if verdict == 'mixed' else 'weak operating efficiency.'}"
        )
        return AnalysisModelItem(
            key="operating_efficiency",
            label="Operating Efficiency",
            verdict=verdict,
            summary=summary,
            score=f"{asset_turnover.quantize(Decimal('0.0001'))}",
            evidence_keys=["asset_turnover", "operating_cashflow_margin", "operating_margin"],
        )
