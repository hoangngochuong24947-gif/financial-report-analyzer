from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List

from src.analyzer.cashflow_analyzer import analyze as analyze_cashflow
from src.analyzer.dupont_analyzer import analyze as analyze_dupont
from src.analyzer.ratio_calculator import calc_efficiency, calc_profitability, calc_solvency
from src.analyzer.trend_analyzer import calc_yoy
from src.crawler.interfaces import FinancialSnapshot
from src.models.workspace_metrics import MetricCatalogItem, MetricValueItem, WorkspaceMetricBundle
from src.utils.precision import safe_divide, to_amount


class WorkspaceMetricEngine:
    """Build archive-first metric bundles from normalized financial snapshots."""

    _CATALOG: List[MetricCatalogItem] = [
        MetricCatalogItem(key="roe", label="Return on Equity", group="profitability", description="Net income divided by total equity.", unit="ratio"),
        MetricCatalogItem(key="roa", label="Return on Assets", group="profitability", description="Net income divided by total assets.", unit="ratio"),
        MetricCatalogItem(key="net_profit_margin", label="Net Profit Margin", group="profitability", description="Net income divided by revenue.", unit="ratio"),
        MetricCatalogItem(key="gross_profit_margin", label="Gross Profit Margin", group="profitability", description="Gross profit divided by revenue.", unit="ratio"),
        MetricCatalogItem(key="operating_margin", label="Operating Margin", group="profitability", description="Operating profit divided by revenue.", unit="ratio"),
        MetricCatalogItem(key="pretax_margin", label="Pretax Margin", group="profitability", description="Total profit divided by revenue.", unit="ratio"),
        MetricCatalogItem(key="current_ratio", label="Current Ratio", group="solvency", description="Current assets divided by current liabilities.", unit="ratio"),
        MetricCatalogItem(key="quick_ratio", label="Quick Ratio", group="solvency", description="Quick assets divided by current liabilities.", unit="ratio"),
        MetricCatalogItem(key="debt_to_asset_ratio", label="Debt to Asset Ratio", group="solvency", description="Total liabilities divided by total assets.", unit="ratio"),
        MetricCatalogItem(key="debt_to_equity_ratio", label="Debt to Equity Ratio", group="solvency", description="Total liabilities divided by total equity.", unit="ratio"),
        MetricCatalogItem(key="equity_ratio", label="Equity Ratio", group="solvency", description="Total equity divided by total assets.", unit="ratio"),
        MetricCatalogItem(key="working_capital", label="Working Capital", group="solvency", description="Current assets minus current liabilities.", unit="amount"),
        MetricCatalogItem(key="asset_turnover", label="Asset Turnover", group="efficiency", description="Revenue divided by total assets.", unit="ratio"),
        MetricCatalogItem(key="equity_multiplier", label="Equity Multiplier", group="efficiency", description="Total assets divided by total equity.", unit="ratio"),
        MetricCatalogItem(key="revenue_to_equity", label="Revenue to Equity", group="efficiency", description="Revenue divided by total equity.", unit="ratio"),
        MetricCatalogItem(key="current_asset_turnover", label="Current Asset Turnover", group="efficiency", description="Revenue divided by current assets.", unit="ratio"),
        MetricCatalogItem(key="operating_cashflow", label="Operating Cash Flow", group="cashflow", description="Cash generated from operating activities.", unit="amount"),
        MetricCatalogItem(key="free_cash_flow", label="Free Cash Flow", group="cashflow", description="Operating cash flow minus capital expenditure proxy.", unit="amount"),
        MetricCatalogItem(key="cash_to_profit_ratio", label="Cash to Profit Ratio", group="cashflow", description="Operating cash flow divided by net income.", unit="ratio"),
        MetricCatalogItem(key="operating_cashflow_margin", label="Operating Cash Flow Margin", group="cashflow", description="Operating cash flow divided by revenue.", unit="ratio"),
        MetricCatalogItem(key="ocf_to_assets", label="OCF to Assets", group="cashflow", description="Operating cash flow divided by total assets.", unit="ratio"),
        MetricCatalogItem(key="ocf_to_liabilities", label="OCF to Liabilities", group="cashflow", description="Operating cash flow divided by total liabilities.", unit="ratio"),
        MetricCatalogItem(key="fcf_margin", label="FCF Margin", group="cashflow", description="Free cash flow divided by revenue.", unit="ratio"),
        MetricCatalogItem(key="capex_proxy", label="Capex Proxy", group="cashflow", description="Capital expenditure proxy based on investing cash flow outflow.", unit="amount"),
        MetricCatalogItem(key="capex_intensity", label="Capex Intensity", group="cashflow", description="Capital expenditure proxy divided by revenue.", unit="ratio"),
        MetricCatalogItem(key="net_cashflow", label="Net Cash Flow", group="cashflow", description="Net increase in cash.", unit="amount"),
        MetricCatalogItem(key="investing_cashflow", label="Investing Cash Flow", group="cashflow", description="Cash flow from investing activities.", unit="amount"),
        MetricCatalogItem(key="financing_cashflow", label="Financing Cash Flow", group="cashflow", description="Cash flow from financing activities.", unit="amount"),
        MetricCatalogItem(key="net_income_yoy", label="Net Income YoY", group="trend", description="Year-over-year growth in net income.", unit="ratio"),
        MetricCatalogItem(key="revenue_yoy", label="Revenue YoY", group="trend", description="Year-over-year growth in revenue.", unit="ratio"),
        MetricCatalogItem(key="operating_profit_yoy", label="Operating Profit YoY", group="trend", description="Year-over-year growth in operating profit.", unit="ratio"),
        MetricCatalogItem(key="operating_cashflow_yoy", label="Operating Cash Flow YoY", group="trend", description="Year-over-year growth in operating cash flow.", unit="ratio"),
        MetricCatalogItem(key="accrual_ratio", label="Accrual Ratio", group="risk", description="Net income minus operating cash flow divided by total assets.", unit="ratio"),
        MetricCatalogItem(key="profit_to_ocf_gap", label="Profit to OCF Gap", group="risk", description="Absolute gap between net income and operating cash flow.", unit="amount"),
        MetricCatalogItem(key="gross_profit_to_assets", label="Gross Profit to Assets", group="risk", description="Gross profit divided by total assets.", unit="ratio"),
        MetricCatalogItem(key="liability_to_ocf", label="Liability to OCF", group="risk", description="Total liabilities divided by operating cash flow.", unit="ratio"),
        MetricCatalogItem(key="fcf_to_debt", label="FCF to Debt", group="risk", description="Free cash flow divided by total liabilities.", unit="ratio"),
        MetricCatalogItem(key="net_cashflow_to_liabilities", label="Net Cash Flow to Liabilities", group="risk", description="Net cash flow divided by total liabilities.", unit="ratio"),
        MetricCatalogItem(key="equity_to_liabilities", label="Equity to Liabilities", group="risk", description="Total equity divided by total liabilities.", unit="ratio"),
        MetricCatalogItem(key="long_term_capital_ratio", label="Long-term Capital Ratio", group="risk", description="Long-term capital divided by non-current assets.", unit="ratio"),
        MetricCatalogItem(key="pe_ttm", label="PE TTM", group="valuation", description="Trailing twelve month price-to-earnings ratio.", unit="ratio"),
        MetricCatalogItem(key="pb_ratio", label="PB Ratio", group="valuation", description="Price-to-book ratio.", unit="ratio"),
        MetricCatalogItem(key="ps_ratio", label="PS Ratio", group="valuation", description="Price-to-sales ratio.", unit="ratio"),
        MetricCatalogItem(key="earnings_yield", label="Earnings Yield", group="valuation", description="Inverse of PE TTM.", unit="ratio"),
        MetricCatalogItem(key="book_to_price", label="Book to Price", group="valuation", description="Inverse of PB ratio.", unit="ratio"),
        MetricCatalogItem(key="sales_to_price", label="Sales to Price", group="valuation", description="Inverse of price-to-sales ratio.", unit="ratio"),
        MetricCatalogItem(key="valuation_buffer", label="Valuation Buffer", group="valuation", description="Combined earnings yield and book-to-price proxy.", unit="ratio"),
        MetricCatalogItem(key="total_assets", label="Total Assets", group="capital", description="Latest total assets.", unit="amount"),
        MetricCatalogItem(key="total_liabilities", label="Total Liabilities", group="capital", description="Latest total liabilities.", unit="amount"),
        MetricCatalogItem(key="total_equity", label="Total Equity", group="capital", description="Latest total equity.", unit="amount"),
    ]

    _AMOUNT_KEYS = {
        "working_capital",
        "operating_cashflow",
        "free_cash_flow",
        "capex_proxy",
        "net_cashflow",
        "investing_cashflow",
        "financing_cashflow",
        "profit_to_ocf_gap",
        "total_assets",
        "total_liabilities",
        "total_equity",
    }

    def build_bundle(
        self,
        snapshot: FinancialSnapshot,
        stock_name: str = "",
        indicator_snapshot: Dict[str, Any] | None = None,
    ) -> WorkspaceMetricBundle:
        indicator_snapshot = indicator_snapshot or {}
        balance_sheet = snapshot.balance_sheets[0]
        income_statement = snapshot.income_statements[0]
        previous_income = snapshot.income_statements[1] if len(snapshot.income_statements) >= 2 else None
        cashflow_statement = snapshot.cashflow_statements[0] if snapshot.cashflow_statements else None
        previous_cashflow = snapshot.cashflow_statements[1] if len(snapshot.cashflow_statements) >= 2 else None

        profitability = calc_profitability(balance_sheet, income_statement)
        solvency = calc_solvency(balance_sheet)
        efficiency = calc_efficiency(balance_sheet, income_statement)
        dupont = analyze_dupont(balance_sheet, income_statement)
        cashflow = analyze_cashflow(cashflow_statement, income_statement) if cashflow_statement else None

        total_assets = self._fallback_amount(balance_sheet.total_assets, indicator_snapshot.get("total_assets"))
        total_equity = self._fallback_amount(balance_sheet.total_equity, indicator_snapshot.get("total_equity"))
        debt_to_asset_ratio = self._fallback_ratio(
            primary=solvency.debt_to_asset_ratio,
            secondary=indicator_snapshot.get("debt_to_asset_ratio"),
            derived=safe_divide(balance_sheet.total_liabilities, total_assets),
        )
        total_liabilities = self._fallback_amount(
            primary=balance_sheet.total_liabilities,
            secondary=indicator_snapshot.get("total_liabilities"),
            derived=total_assets * debt_to_asset_ratio if total_assets and debt_to_asset_ratio else Decimal("0"),
        )
        net_income = self._fallback_amount(income_statement.net_income, indicator_snapshot.get("net_income"))
        roe = self._fallback_ratio(
            primary=profitability.roe,
            secondary=indicator_snapshot.get("roe"),
            derived=safe_divide(net_income, total_equity),
        )
        roa = self._fallback_ratio(
            primary=profitability.roa,
            secondary=indicator_snapshot.get("roa"),
            derived=safe_divide(net_income, total_assets),
        )
        pe_ttm = self._indicator_ratio(
            indicator_snapshot,
            ("pe_ttm", "pettm", "市盈率ttm", "市盈率", "pe"),
        )
        pb_ratio = self._indicator_ratio(
            indicator_snapshot,
            ("pb_ratio", "pbratio", "市净率", "pb"),
        )
        ps_ratio = self._indicator_ratio(
            indicator_snapshot,
            ("ps_ratio", "psratio", "市销率", "ps"),
        )
        operating_cashflow = cashflow.operating_cashflow if cashflow else Decimal("0")
        free_cash_flow = cashflow.free_cash_flow if cashflow else Decimal("0")
        capex_proxy = abs(cashflow_statement.investing_cashflow) if cashflow_statement else Decimal("0")
        gross_profit = income_statement.total_revenue - income_statement.operating_cost

        raw_values: Dict[str, Decimal] = {
            "roe": roe,
            "roa": roa,
            "net_profit_margin": safe_divide(net_income, income_statement.total_revenue),
            "gross_profit_margin": profitability.gross_profit_margin,
            "operating_margin": safe_divide(income_statement.operating_profit, income_statement.total_revenue),
            "pretax_margin": safe_divide(income_statement.total_profit, income_statement.total_revenue),
            "current_ratio": solvency.current_ratio,
            "quick_ratio": solvency.quick_ratio,
            "debt_to_asset_ratio": debt_to_asset_ratio,
            "debt_to_equity_ratio": safe_divide(total_liabilities, total_equity),
            "equity_ratio": safe_divide(total_equity, total_assets),
            "working_capital": balance_sheet.total_current_assets - balance_sheet.total_current_liabilities,
            "asset_turnover": safe_divide(income_statement.total_revenue, total_assets),
            "equity_multiplier": safe_divide(total_assets, total_equity),
            "revenue_to_equity": safe_divide(income_statement.total_revenue, total_equity),
            "current_asset_turnover": safe_divide(income_statement.total_revenue, balance_sheet.total_current_assets),
            "operating_cashflow": operating_cashflow,
            "free_cash_flow": free_cash_flow,
            "cash_to_profit_ratio": safe_divide(operating_cashflow, net_income) if cashflow else Decimal("0"),
            "operating_cashflow_margin": safe_divide(
                operating_cashflow,
                income_statement.total_revenue,
            ),
            "ocf_to_assets": safe_divide(operating_cashflow, total_assets),
            "ocf_to_liabilities": safe_divide(operating_cashflow, total_liabilities),
            "fcf_margin": safe_divide(free_cash_flow, income_statement.total_revenue),
            "capex_proxy": capex_proxy,
            "capex_intensity": safe_divide(capex_proxy, income_statement.total_revenue),
            "net_cashflow": cashflow_statement.net_cashflow if cashflow_statement else Decimal("0"),
            "investing_cashflow": cashflow_statement.investing_cashflow if cashflow_statement else Decimal("0"),
            "financing_cashflow": cashflow_statement.financing_cashflow if cashflow_statement else Decimal("0"),
            "net_income_yoy": calc_yoy(net_income, previous_income.net_income) if previous_income else Decimal("0"),
            "revenue_yoy": calc_yoy(income_statement.total_revenue, previous_income.total_revenue) if previous_income else Decimal("0"),
            "operating_profit_yoy": calc_yoy(income_statement.operating_profit, previous_income.operating_profit) if previous_income else Decimal("0"),
            "operating_cashflow_yoy": (
                calc_yoy(cashflow_statement.operating_cashflow, previous_cashflow.operating_cashflow)
                if cashflow_statement and previous_cashflow
                else Decimal("0")
            ),
            "accrual_ratio": safe_divide(net_income - operating_cashflow, total_assets),
            "profit_to_ocf_gap": net_income - operating_cashflow,
            "gross_profit_to_assets": safe_divide(gross_profit, total_assets),
            "liability_to_ocf": safe_divide(total_liabilities, operating_cashflow),
            "fcf_to_debt": safe_divide(free_cash_flow, total_liabilities),
            "net_cashflow_to_liabilities": safe_divide(
                cashflow_statement.net_cashflow if cashflow_statement else Decimal("0"),
                total_liabilities,
            ),
            "equity_to_liabilities": safe_divide(total_equity, total_liabilities),
            "long_term_capital_ratio": safe_divide(
                total_equity + balance_sheet.total_non_current_liabilities,
                balance_sheet.total_non_current_assets,
            ),
            "pe_ttm": pe_ttm,
            "pb_ratio": pb_ratio,
            "ps_ratio": ps_ratio,
            "earnings_yield": safe_divide(Decimal("1"), pe_ttm) if pe_ttm > 0 else Decimal("0"),
            "book_to_price": safe_divide(Decimal("1"), pb_ratio) if pb_ratio > 0 else Decimal("0"),
            "sales_to_price": safe_divide(Decimal("1"), ps_ratio) if ps_ratio > 0 else Decimal("0"),
            "valuation_buffer": (
                (safe_divide(Decimal("1"), pe_ttm) if pe_ttm > 0 else Decimal("0"))
                + (safe_divide(Decimal("1"), pb_ratio) if pb_ratio > 0 else Decimal("0"))
            ),
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
        }

        values = [
            self._metric_value(
                key=item.key,
                label=item.label,
                group=item.group,
                value=raw_values.get(item.key, Decimal("0")),
            )
            for item in self._CATALOG
        ]

        summary = self._build_summary(snapshot.stock_code, stock_name, raw_values)

        return WorkspaceMetricBundle(
            stock_code=snapshot.stock_code,
            stock_name=stock_name or snapshot.stock_code,
            report_date=str(balance_sheet.report_date),
            catalog=self._CATALOG,
            values=values,
            summary=summary,
        )

    def grouped_values(self, bundle: WorkspaceMetricBundle) -> Dict[str, List[MetricValueItem]]:
        grouped: Dict[str, List[MetricValueItem]] = {}
        for item in bundle.values:
            grouped.setdefault(item.group, []).append(item)
        return grouped

    def value_map(self, bundle: WorkspaceMetricBundle) -> Dict[str, Decimal]:
        values: Dict[str, Decimal] = {}
        for item in bundle.values:
            values[item.key] = Decimal(item.value)
        return values

    def _metric_value(self, key: str, label: str, group: str, value: Decimal) -> MetricValueItem:
        if key in self._AMOUNT_KEYS:
            formatted = f"{value.quantize(Decimal('0.01'))}"
        else:
            formatted = f"{value.quantize(Decimal('0.0001'))}"

        return MetricValueItem(
            key=key,
            label=label,
            group=group,
            value=formatted,
            period=None,
        )

    @staticmethod
    def _fallback_amount(primary: Decimal, secondary: Any, derived: Decimal | None = None) -> Decimal:
        if primary != 0:
            return primary
        secondary_amount = to_amount(secondary)
        if secondary_amount != 0:
            return secondary_amount
        return derived if derived is not None else Decimal("0")

    @staticmethod
    def _fallback_ratio(primary: Decimal, secondary: Any, derived: Decimal | None = None) -> Decimal:
        if primary != 0:
            return primary.quantize(Decimal("0.0001"))

        if secondary not in (None, ""):
            try:
                secondary_ratio = Decimal(str(secondary))
                if abs(secondary_ratio) > 1:
                    return (secondary_ratio / Decimal("100")).quantize(Decimal("0.0001"))
                return secondary_ratio.quantize(Decimal("0.0001"))
            except Exception:
                pass

        if derived is not None and derived != 0:
            return derived.quantize(Decimal("0.0001"))

        return Decimal("0.0000")

    @classmethod
    def _indicator_ratio(cls, indicator_snapshot: Dict[str, Any], aliases: tuple[str, ...]) -> Decimal:
        normalized_aliases = tuple(cls._normalize_key(alias) for alias in aliases)
        for key, value in indicator_snapshot.items():
            normalized_key = cls._normalize_key(str(key))
            if any(alias in normalized_key for alias in normalized_aliases):
                try:
                    return Decimal(str(value)).quantize(Decimal("0.0001"))
                except Exception:
                    continue
        return Decimal("0.0000")

    @staticmethod
    def _normalize_key(value: str) -> str:
        return "".join(ch for ch in value.lower() if ch.isalnum())

    @staticmethod
    def _build_summary(stock_code: str, stock_name: str, values: Dict[str, Decimal]) -> str:
        return (
            f"{stock_name or stock_code} archive workspace: "
            f"ROE={values['roe'].quantize(Decimal('0.0001'))}, "
            f"Debt/Asset={values['debt_to_asset_ratio'].quantize(Decimal('0.0001'))}, "
            f"OCF Margin={values['operating_cashflow_margin'].quantize(Decimal('0.0001'))}, "
            f"FCF={values['free_cash_flow'].quantize(Decimal('0.01'))}, "
            f"Valuation Buffer={values['valuation_buffer'].quantize(Decimal('0.0001'))}"
        )
