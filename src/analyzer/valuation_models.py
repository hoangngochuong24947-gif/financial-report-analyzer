from __future__ import annotations

from decimal import Decimal
from typing import Dict

from src.models.workspace_metrics import AnalysisModelItem


def build_valuation_snapshot(metrics: Dict[str, Decimal]) -> AnalysisModelItem:
    pe_ttm = metrics.get("pe_ttm", Decimal("0"))
    pb_ratio = metrics.get("pb_ratio", Decimal("0"))
    if pe_ttm <= 0 and pb_ratio <= 0:
        verdict = "insufficient"
        summary = "Valuation multiples are unavailable from the current archive snapshot."
    else:
        verdict = "cheap" if (0 < pe_ttm <= Decimal("15")) or (0 < pb_ratio <= Decimal("1.5")) else "neutral" if (pe_ttm <= Decimal("25") or pb_ratio <= Decimal("3")) else "expensive"
        summary = (
            f"PE TTM is {pe_ttm.quantize(Decimal('0.0001'))} and "
            f"PB is {pb_ratio.quantize(Decimal('0.0001'))}, "
            f"suggesting {'a compressed valuation.' if verdict == 'cheap' else 'a mid-range valuation.' if verdict == 'neutral' else 'a rich valuation level.'}"
        )
    return AnalysisModelItem(
        key="valuation_snapshot",
        label="Valuation Snapshot",
        verdict=verdict,
        summary=summary,
        score=f"{pe_ttm.quantize(Decimal('0.0001'))}",
        evidence_keys=["pe_ttm", "pb_ratio", "ps_ratio"],
    )


def build_value_trap(metrics: Dict[str, Decimal]) -> AnalysisModelItem:
    earnings_yield = metrics.get("earnings_yield", Decimal("0"))
    revenue_yoy = metrics.get("revenue_yoy", Decimal("0"))
    cashflow_risk = metrics.get("cash_to_profit_ratio", Decimal("0"))
    verdict = "low" if earnings_yield >= Decimal("0.06") and revenue_yoy >= 0 and cashflow_risk >= Decimal("1") else "medium" if earnings_yield >= Decimal("0.04") else "high"
    summary = (
        f"Earnings yield is {earnings_yield.quantize(Decimal('0.0001'))}, "
        f"revenue YoY is {revenue_yoy.quantize(Decimal('0.0001'))}, and "
        f"cash/profit ratio is {cashflow_risk.quantize(Decimal('0.0001'))}; "
        f"this points to {'limited value-trap risk.' if verdict == 'low' else 'a mixed valuation-quality profile.' if verdict == 'medium' else 'a potential value trap.'}"
    )
    return AnalysisModelItem(
        key="value_trap",
        label="Value Trap Check",
        verdict=verdict,
        summary=summary,
        score=f"{earnings_yield.quantize(Decimal('0.0001'))}",
        evidence_keys=["earnings_yield", "revenue_yoy", "cash_to_profit_ratio", "accrual_ratio"],
    )
