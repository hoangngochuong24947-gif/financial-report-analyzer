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
