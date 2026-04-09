from __future__ import annotations

from decimal import Decimal
from typing import Callable, Dict, List

from src.analyzer.risk_models import (
    build_capital_structure_resilience,
    build_cashflow_risk,
    build_debt_service_capacity,
    build_leverage_risk,
    build_liquidity_risk,
)
from src.analyzer.valuation_models import (
    build_shareholder_return_quality,
    build_valuation_compression_risk,
    build_valuation_snapshot,
    build_value_trap,
)
from src.models.workspace_metrics import AnalysisModelItem


class WorkspaceModelEngine:
    """Build fixed financial analysis model cards from metric evidence."""

    def __init__(self) -> None:
        self._builders: List[Callable[[Dict[str, Decimal]], AnalysisModelItem]] = [
            self._dupont,
            self._cashflow_quality,
            self._growth_quality,
            self._solvency_pressure,
            self._operating_efficiency,
            self._earnings_quality,
            self._capital_intensity,
            build_liquidity_risk,
            build_leverage_risk,
            build_cashflow_risk,
            build_debt_service_capacity,
            build_capital_structure_resilience,
            build_valuation_snapshot,
            build_value_trap,
            build_shareholder_return_quality,
            build_valuation_compression_risk,
        ]

    def build_items(self, metric_values: Dict[str, Decimal]) -> List[AnalysisModelItem]:
        return [builder(metric_values) for builder in self._builders]

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

    def _earnings_quality(self, metrics: Dict[str, Decimal]) -> AnalysisModelItem:
        cash_to_profit = metrics.get("cash_to_profit_ratio", Decimal("0"))
        accrual_ratio = metrics.get("accrual_ratio", Decimal("0"))
        profit_gap = abs(metrics.get("profit_to_ocf_gap", Decimal("0")))
        verdict = (
            "strong"
            if cash_to_profit >= Decimal("1.0000") and accrual_ratio <= Decimal("0.0500")
            else "mixed"
            if cash_to_profit >= Decimal("0.7000")
            else "weak"
        )
        summary = (
            f"Cash/profit ratio is {cash_to_profit.quantize(Decimal('0.0001'))}, "
            f"accrual ratio is {accrual_ratio.quantize(Decimal('0.0001'))}, and "
            f"the profit/OCF gap is {profit_gap.quantize(Decimal('0.01'))}, "
            f"indicating {'high earnings quality.' if verdict == 'strong' else 'acceptable but uneven earnings quality.' if verdict == 'mixed' else 'fragile earnings quality.'}"
        )
        return AnalysisModelItem(
            key="earnings_quality",
            label="Earnings Quality",
            verdict=verdict,
            summary=summary,
            score=f"{cash_to_profit.quantize(Decimal('0.0001'))}",
            evidence_keys=["cash_to_profit_ratio", "accrual_ratio", "profit_to_ocf_gap", "operating_cashflow_margin"],
        )

    def _capital_intensity(self, metrics: Dict[str, Decimal]) -> AnalysisModelItem:
        capex_intensity = metrics.get("capex_intensity", Decimal("0"))
        fcf_margin = metrics.get("fcf_margin", Decimal("0"))
        ocf_to_assets = metrics.get("ocf_to_assets", Decimal("0"))
        verdict = (
            "light"
            if capex_intensity <= Decimal("0.1000") and fcf_margin > 0
            else "balanced"
            if fcf_margin >= Decimal("0")
            else "heavy"
        )
        summary = (
            f"Capex intensity is {capex_intensity.quantize(Decimal('0.0001'))}, "
            f"FCF margin is {fcf_margin.quantize(Decimal('0.0001'))}, and "
            f"OCF/assets is {ocf_to_assets.quantize(Decimal('0.0001'))}, "
            f"suggesting {'a relatively asset-light reinvestment profile.' if verdict == 'light' else 'a manageable reinvestment burden.' if verdict == 'balanced' else 'a heavy capital intensity profile.'}"
        )
        return AnalysisModelItem(
            key="capital_intensity",
            label="Capital Intensity",
            verdict=verdict,
            summary=summary,
            score=f"{capex_intensity.quantize(Decimal('0.0001'))}",
            evidence_keys=["capex_intensity", "fcf_margin", "ocf_to_assets", "capex_proxy"],
        )
