from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.analyzer.cashflow_analyzer import analyze as analyze_cashflow
from src.analyzer.dupont_analyzer import analyze as analyze_dupont
from src.analyzer.ratio_calculator import calc_efficiency, calc_profitability, calc_solvency
from src.analyzer.trend_analyzer import analyze_trend
from src.api.workspace_service import WorkspaceService
from src.crawler.interfaces import CrawlerDataNotFoundError, FinancialSnapshot
from src.crawler.service import CrawlerService
from src.models.financial_metrics import CashFlowResult, DuPontResult, TrendResult
from src.models.stock_info import StockInfo
from src.storage.workspace_repository import ArchiveWorkspace
from src.utils.logger import logger


@dataclass(frozen=True)
class AnalysisContext:
    stock_code: str
    stock_name: str
    market: str
    snapshot: FinancialSnapshot


class AnalysisFacade:
    """Async-first orchestration layer for compatibility and workspace APIs."""

    def __init__(
        self,
        workspace_service: WorkspaceService | None = None,
        crawler_service: CrawlerService | None = None,
    ) -> None:
        self._workspace_service = workspace_service or WorkspaceService()
        self._crawler_service = crawler_service or CrawlerService()

    async def list_stocks(self, market: Optional[str] = None) -> List[StockInfo]:
        workspaces = await asyncio.to_thread(self._workspace_service.list_workspaces, 200)
        if workspaces:
            items = [
                StockInfo(
                    stock_code=item.stock_code,
                    stock_name=item.stock_name,
                    market=item.market,
                )
                for item in workspaces
                if not market or item.market == market
            ]
            if items:
                return items
        return await asyncio.to_thread(self._crawler_service.fetch_stock_list, market, False)

    async def get_context(self, stock_code: str) -> AnalysisContext:
        try:
            workspace = await asyncio.to_thread(self._workspace_service.get_workspace, stock_code)
            return AnalysisContext(
                stock_code=workspace.stock_code,
                stock_name=workspace.stock_name,
                market=workspace.market,
                snapshot=workspace.snapshot,
            )
        except FileNotFoundError:
            logger.warning("Workspace archive missing for {}, falling back to live provider", stock_code)
            return await self._build_live_context(stock_code)

    async def get_legacy_statements(self, stock_code: str) -> Dict[str, Any]:
        context = await self.get_context(stock_code)
        snapshot = context.snapshot
        return {
            "stock_code": stock_code,
            "balance_sheet": snapshot.balance_sheets[0].model_dump(mode="json"),
            "income_statement": snapshot.income_statements[0].model_dump(mode="json"),
            "cashflow_statement": (
                snapshot.cashflow_statements[0].model_dump(mode="json")
                if snapshot.cashflow_statements
                else None
            ),
        }

    async def get_legacy_ratios(self, stock_code: str) -> Dict[str, Any]:
        context = await self.get_context(stock_code)
        snapshot = context.snapshot
        bs = snapshot.balance_sheets[0]
        is_ = snapshot.income_statements[0]

        profitability, solvency, efficiency = await asyncio.gather(
            asyncio.to_thread(calc_profitability, bs, is_),
            asyncio.to_thread(calc_solvency, bs),
            asyncio.to_thread(calc_efficiency, bs, is_),
        )

        return {
            "stock_code": stock_code,
            "report_date": str(bs.report_date),
            "profitability": profitability.model_dump(mode="json"),
            "solvency": solvency.model_dump(mode="json"),
            "efficiency": efficiency.model_dump(mode="json"),
        }

    async def get_dupont(self, stock_code: str) -> DuPontResult:
        context = await self.get_context(stock_code)
        snapshot = context.snapshot
        return await asyncio.to_thread(analyze_dupont, snapshot.balance_sheets[0], snapshot.income_statements[0])

    async def get_cashflow(self, stock_code: str) -> CashFlowResult:
        context = await self.get_context(stock_code)
        snapshot = context.snapshot
        if not snapshot.cashflow_statements:
            raise CrawlerDataNotFoundError(f"No cashflow data for {stock_code}")
        return await asyncio.to_thread(
            analyze_cashflow,
            snapshot.cashflow_statements[0],
            snapshot.income_statements[0],
        )

    async def get_trend(self, stock_code: str, metric: str) -> TrendResult:
        context = await self.get_context(stock_code)
        income_statements = context.snapshot.income_statements
        if len(income_statements) < 2:
            raise CrawlerDataNotFoundError(f"Insufficient data for trend analysis: {stock_code}")

        current = income_statements[0]
        previous = income_statements[1]
        current_value = getattr(current, metric, None)
        previous_value = getattr(previous, metric, None)
        if current_value is None or previous_value is None:
            raise ValueError(metric)

        return await asyncio.to_thread(
            analyze_trend,
            metric_name=metric,
            current=current_value,
            previous=previous_value,
        )

    async def get_export_payload(self, stock_code: str) -> Dict[str, Any]:
        context = await self.get_context(stock_code)
        snapshot = context.snapshot
        bs = snapshot.balance_sheets[0]
        is_ = snapshot.income_statements[0]

        profitability, solvency, efficiency, dupont = await asyncio.gather(
            asyncio.to_thread(calc_profitability, bs, is_),
            asyncio.to_thread(calc_solvency, bs),
            asyncio.to_thread(calc_efficiency, bs, is_),
            asyncio.to_thread(analyze_dupont, bs, is_),
        )

        return {
            "stock_name": context.stock_name,
            "snapshot": snapshot,
            "profitability": profitability,
            "solvency": solvency,
            "efficiency": efficiency,
            "dupont": dupont,
        }

    async def _build_live_context(self, stock_code: str) -> AnalysisContext:
        balance_sheets, income_statements, cashflow_statements = await asyncio.gather(
            asyncio.to_thread(self._crawler_service.fetch_balance_sheet, stock_code, False),
            asyncio.to_thread(self._crawler_service.fetch_income_statement, stock_code, False),
            asyncio.to_thread(self._crawler_service.fetch_cashflow_statement, stock_code, False),
        )

        if not balance_sheets or not income_statements:
            raise CrawlerDataNotFoundError(f"No financial statements for {stock_code}")

        snapshot = FinancialSnapshot(
            stock_code=stock_code,
            balance_sheets=balance_sheets,
            income_statements=income_statements,
            cashflow_statements=cashflow_statements,
        )

        stock_name = stock_code
        market = "ab"
        try:
            stock_items = await asyncio.to_thread(self._crawler_service.fetch_stock_list, None, False)
            matched = next((item for item in stock_items if item.stock_code == stock_code), None)
            if matched:
                stock_name = matched.stock_name
                market = matched.market
        except Exception:
            logger.debug("Live stock list lookup skipped for {}", stock_code)

        return AnalysisContext(
            stock_code=stock_code,
            stock_name=stock_name,
            market=market,
            snapshot=snapshot,
        )
