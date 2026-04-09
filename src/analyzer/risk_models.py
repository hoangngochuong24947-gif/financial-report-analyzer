from __future__ import annotations

from decimal import Decimal
from typing import Dict

from src.models.workspace_metrics import AnalysisModelItem


def build_liquidity_risk(metrics: Dict[str, Decimal]) -> AnalysisModelItem:
    current_ratio = metrics.get("current_ratio", Decimal("0"))
    liability_to_ocf = metrics.get("liability_to_ocf", Decimal("0"))
    verdict = "low" if current_ratio >= Decimal("1.5") and liability_to_ocf <= Decimal("3") else "medium" if current_ratio >= Decimal("1") else "high"
    summary = (
        f"Current ratio is {current_ratio.quantize(Decimal('0.0001'))} and "
        f"liability/OCF is {liability_to_ocf.quantize(Decimal('0.0001'))}, "
        f"suggesting {'ample short-term liquidity.' if verdict == 'low' else 'watch-list liquidity pressure.' if verdict == 'medium' else 'tight liquidity coverage.'}"
    )
    return AnalysisModelItem(
        key="liquidity_risk",
        label="Liquidity Risk",
        verdict=verdict,
        summary=summary,
        score=f"{liability_to_ocf.quantize(Decimal('0.0001'))}",
        evidence_keys=["current_ratio", "quick_ratio", "liability_to_ocf", "working_capital"],
    )


def build_leverage_risk(metrics: Dict[str, Decimal]) -> AnalysisModelItem:
    debt_ratio = metrics.get("debt_to_asset_ratio", Decimal("0"))
    fcf_to_debt = metrics.get("fcf_to_debt", Decimal("0"))
    verdict = "low" if debt_ratio <= Decimal("0.4") and fcf_to_debt >= Decimal("0.2") else "medium" if debt_ratio <= Decimal("0.6") else "high"
    summary = (
        f"Debt/asset is {debt_ratio.quantize(Decimal('0.0001'))} and "
        f"FCF/debt is {fcf_to_debt.quantize(Decimal('0.0001'))}, "
        f"pointing to {'balanced leverage.' if verdict == 'low' else 'moderate leverage sensitivity.' if verdict == 'medium' else 'elevated leverage strain.'}"
    )
    return AnalysisModelItem(
        key="leverage_risk",
        label="Leverage Risk",
        verdict=verdict,
        summary=summary,
        score=f"{debt_ratio.quantize(Decimal('0.0001'))}",
        evidence_keys=["debt_to_asset_ratio", "debt_to_equity_ratio", "fcf_to_debt", "total_liabilities"],
    )


def build_cashflow_risk(metrics: Dict[str, Decimal]) -> AnalysisModelItem:
    accrual_ratio = metrics.get("accrual_ratio", Decimal("0"))
    cash_to_profit = metrics.get("cash_to_profit_ratio", Decimal("0"))
    verdict = "low" if accrual_ratio <= Decimal("0.05") and cash_to_profit >= Decimal("1") else "medium" if cash_to_profit >= Decimal("0.7") else "high"
    summary = (
        f"Accrual ratio is {accrual_ratio.quantize(Decimal('0.0001'))} and "
        f"cash/profit ratio is {cash_to_profit.quantize(Decimal('0.0001'))}, "
        f"which implies {'earnings are cash-backed.' if verdict == 'low' else 'cash conversion needs monitoring.' if verdict == 'medium' else 'material earnings quality pressure.'}"
    )
    return AnalysisModelItem(
        key="cashflow_risk",
        label="Cashflow Risk",
        verdict=verdict,
        summary=summary,
        score=f"{accrual_ratio.quantize(Decimal('0.0001'))}",
        evidence_keys=["accrual_ratio", "cash_to_profit_ratio", "operating_cashflow_margin", "free_cash_flow"],
    )


def build_debt_service_capacity(metrics: Dict[str, Decimal]) -> AnalysisModelItem:
    ocf_to_liabilities = metrics.get("ocf_to_liabilities", Decimal("0"))
    fcf_to_debt = metrics.get("fcf_to_debt", Decimal("0"))
    current_ratio = metrics.get("current_ratio", Decimal("0"))
    verdict = (
        "strong"
        if ocf_to_liabilities >= Decimal("0.20") and fcf_to_debt >= Decimal("0.10") and current_ratio >= Decimal("1.50")
        else "mixed"
        if ocf_to_liabilities >= Decimal("0.10") and current_ratio >= Decimal("1.00")
        else "weak"
    )
    summary = (
        f"OCF/liabilities is {ocf_to_liabilities.quantize(Decimal('0.0001'))}, "
        f"FCF/debt is {fcf_to_debt.quantize(Decimal('0.0001'))}, and "
        f"current ratio is {current_ratio.quantize(Decimal('0.0001'))}, "
        f"indicating {'solid debt-servicing capacity.' if verdict == 'strong' else 'adequate but monitorable debt coverage.' if verdict == 'mixed' else 'fragile debt-servicing capacity.'}"
    )
    return AnalysisModelItem(
        key="debt_service_capacity",
        label="Debt Service Capacity",
        verdict=verdict,
        summary=summary,
        score=f"{ocf_to_liabilities.quantize(Decimal('0.0001'))}",
        evidence_keys=["ocf_to_liabilities", "fcf_to_debt", "current_ratio", "liability_to_ocf"],
    )


def build_capital_structure_resilience(metrics: Dict[str, Decimal]) -> AnalysisModelItem:
    equity_to_liabilities = metrics.get("equity_to_liabilities", Decimal("0"))
    debt_ratio = metrics.get("debt_to_asset_ratio", Decimal("0"))
    long_term_capital_ratio = metrics.get("long_term_capital_ratio", Decimal("0"))
    verdict = (
        "strong"
        if equity_to_liabilities >= Decimal("1.00") and debt_ratio <= Decimal("0.50") and long_term_capital_ratio >= Decimal("1.00")
        else "mixed"
        if equity_to_liabilities >= Decimal("0.50") and long_term_capital_ratio >= Decimal("0.80")
        else "weak"
    )
    summary = (
        f"Equity/liabilities is {equity_to_liabilities.quantize(Decimal('0.0001'))}, "
        f"debt/asset is {debt_ratio.quantize(Decimal('0.0001'))}, and "
        f"long-term capital ratio is {long_term_capital_ratio.quantize(Decimal('0.0001'))}, "
        f"showing {'a resilient capital structure.' if verdict == 'strong' else 'a serviceable but not fully comfortable capital structure.' if verdict == 'mixed' else 'a stretched capital structure.'}"
    )
    return AnalysisModelItem(
        key="capital_structure_resilience",
        label="Capital Structure Resilience",
        verdict=verdict,
        summary=summary,
        score=f"{equity_to_liabilities.quantize(Decimal('0.0001'))}",
        evidence_keys=["equity_to_liabilities", "debt_to_asset_ratio", "long_term_capital_ratio", "total_equity"],
    )
