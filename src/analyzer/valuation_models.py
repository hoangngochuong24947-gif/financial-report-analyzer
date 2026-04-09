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


def build_shareholder_return_quality(metrics: Dict[str, Decimal]) -> AnalysisModelItem:
    roe = metrics.get("roe", Decimal("0"))
    earnings_yield = metrics.get("earnings_yield", Decimal("0"))
    book_to_price = metrics.get("book_to_price", Decimal("0"))
    verdict = (
        "strong"
        if roe >= Decimal("0.1200") and (earnings_yield + book_to_price) >= Decimal("0.1000")
        else "mixed"
        if roe >= Decimal("0.0800")
        else "weak"
    )
    summary = (
        f"ROE is {roe.quantize(Decimal('0.0001'))}, earnings yield is {earnings_yield.quantize(Decimal('0.0001'))}, "
        f"and book-to-price is {book_to_price.quantize(Decimal('0.0001'))}, "
        f"suggesting {'shareholder returns are supported by a reasonable valuation base.' if verdict == 'strong' else 'returns are acceptable but valuation support is mixed.' if verdict == 'mixed' else 'returns look weak relative to valuation support.'}"
    )
    return AnalysisModelItem(
        key="shareholder_return_quality",
        label="Shareholder Return Quality",
        verdict=verdict,
        summary=summary,
        score=f"{roe.quantize(Decimal('0.0001'))}",
        evidence_keys=["roe", "earnings_yield", "book_to_price", "valuation_buffer"],
    )


def build_valuation_compression_risk(metrics: Dict[str, Decimal]) -> AnalysisModelItem:
    pe_ttm = metrics.get("pe_ttm", Decimal("0"))
    ps_ratio = metrics.get("ps_ratio", Decimal("0"))
    revenue_yoy = metrics.get("revenue_yoy", Decimal("0"))
    net_income_yoy = metrics.get("net_income_yoy", Decimal("0"))
    verdict = (
        "high"
        if ((pe_ttm > Decimal("25") or ps_ratio > Decimal("4")) and (revenue_yoy < 0 or net_income_yoy < 0))
        else "medium"
        if pe_ttm > Decimal("15") or ps_ratio > Decimal("2")
        else "low"
    )
    summary = (
        f"PE TTM is {pe_ttm.quantize(Decimal('0.0001'))}, PS is {ps_ratio.quantize(Decimal('0.0001'))}, "
        f"revenue YoY is {revenue_yoy.quantize(Decimal('0.0001'))}, and net income YoY is {net_income_yoy.quantize(Decimal('0.0001'))}; "
        f"this points to {'elevated valuation compression risk.' if verdict == 'high' else 'moderate multiple compression sensitivity.' if verdict == 'medium' else 'limited valuation compression pressure.'}"
    )
    return AnalysisModelItem(
        key="valuation_compression_risk",
        label="Valuation Compression Risk",
        verdict=verdict,
        summary=summary,
        score=f"{pe_ttm.quantize(Decimal('0.0001'))}",
        evidence_keys=["pe_ttm", "ps_ratio", "revenue_yoy", "net_income_yoy"],
    )
