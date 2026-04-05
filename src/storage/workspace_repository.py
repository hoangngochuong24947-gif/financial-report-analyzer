from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from src.crawler.interfaces import Dataset, FinancialSnapshot
from src.crawler.providers.baidu_finance.extractors import parse_report_date
from src.crawler.providers.baidu_finance.parsers import (
    parse_balance_sheets,
    parse_cashflow_statements,
    parse_income_statements,
)
from src.models.workspace_metrics import WorkspaceArchiveItem, WorkspaceSummary
from src.storage.archive_repository import ArchiveRepository


@dataclass(frozen=True)
class ArchiveWorkspace:
    stock_code: str
    stock_name: str
    market: str
    snapshot: FinancialSnapshot
    statement_details: Dict[str, Dict[str, List[Dict[str, object]]]]
    indicator_snapshot: Dict[str, object]
    archives: List[WorkspaceArchiveItem]
    latest_report_date: str | None


class WorkspaceRepository:
    """Read archive-first workspaces from the Baidu finance archive."""

    def __init__(self, archive_root: str | None = None) -> None:
        self._archive_repository = ArchiveRepository(archive_root=archive_root)
        self._archive_root = Path(archive_root or self._archive_repository._root)

    def load_workspace(self, stock_code: str) -> ArchiveWorkspace:
        archive_items = self._load_archive_items(stock_code)
        if not archive_items:
            raise FileNotFoundError(f"No archived workspace found for {stock_code}")

        stock_name = archive_items[0].stock_name
        market = archive_items[0].market
        dataset_payloads = self._load_dataset_payloads(archive_items)
        stock_snapshot = self._load_snapshot(stock_code, dataset_payloads)
        latest_report_date = None
        if stock_snapshot.balance_sheets:
            latest_report_date = str(stock_snapshot.balance_sheets[0].report_date)
        elif stock_snapshot.income_statements:
            latest_report_date = str(stock_snapshot.income_statements[0].report_date)

        return ArchiveWorkspace(
            stock_code=stock_code,
            stock_name=stock_name,
            market=market,
            snapshot=stock_snapshot,
            statement_details=self._load_statement_details(dataset_payloads),
            indicator_snapshot=self._load_indicator_snapshot(archive_items, dataset_payloads),
            archives=archive_items,
            latest_report_date=latest_report_date,
        )

    def list_workspaces(self, limit: int = 20) -> List[WorkspaceSummary]:
        manifests = self._archive_repository.list_archives(limit=1000)
        stock_codes: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        for manifest in manifests:
            stock_codes[manifest["stock_code"]].append(manifest)

        summaries: List[WorkspaceSummary] = []
        for stock_code in stock_codes:
            workspace = self.load_workspace(stock_code)
            summaries.append(
                WorkspaceSummary(
                    stock_code=workspace.stock_code,
                    stock_name=workspace.stock_name,
                    market=workspace.market,
                    latest_report_date=workspace.latest_report_date,
                    dataset_count=len({item.dataset for item in workspace.archives}),
                    archives=workspace.archives,
                )
            )

        summaries.sort(key=lambda item: item.latest_report_date or "", reverse=True)
        return summaries[:limit]

    def _load_archive_items(self, stock_code: str) -> List[WorkspaceArchiveItem]:
        manifests = self._archive_repository.list_archives(stock_code=stock_code, limit=1000)
        archive_items: List[WorkspaceArchiveItem] = []
        for manifest in manifests:
            archive_items.append(
                WorkspaceArchiveItem(
                    stock_code=manifest["stock_code"],
                    stock_name=manifest.get("stock_name", manifest["stock_code"]),
                    market=manifest.get("market", "ab"),
                    dataset=manifest["dataset"],
                    fetched_at=manifest["fetched_at"],
                    raw_path=manifest["raw_path"],
                    csv_path=manifest["csv_path"],
                    manifest_path=manifest["manifest_path"],
                    row_count=manifest.get("row_count", 0),
                    status=manifest.get("status", "success"),
                    report_date=self._extract_report_date(manifest),
                )
            )
        archive_items.sort(key=lambda item: item.fetched_at, reverse=True)
        return archive_items

    def _load_dataset_payloads(self, archive_items: List[WorkspaceArchiveItem]) -> Dict[str, Dict[str, object]]:
        payloads: Dict[str, Dict[str, object]] = {}
        for item in archive_items:
            if item.dataset not in payloads:
                payloads[item.dataset] = self._read_raw_payload(item.raw_path)
        return payloads

    def _load_snapshot(self, stock_code: str, payloads: Dict[str, Dict[str, object]]) -> FinancialSnapshot:
        income_statements = parse_income_statements(
            stock_code,
            payloads.get(Dataset.INCOME_STATEMENT.value, {}).get("Result", {}),
        )
        balance_sheets = parse_balance_sheets(
            stock_code,
            payloads.get(Dataset.BALANCE_SHEET.value, {}).get("Result", {}),
        )
        cashflow_statements = parse_cashflow_statements(
            stock_code,
            payloads.get(Dataset.CASHFLOW_STATEMENT.value, {}).get("Result", {}),
        )

        balance_sheets.sort(key=lambda item: item.report_date, reverse=True)
        income_statements.sort(key=lambda item: item.report_date, reverse=True)
        cashflow_statements.sort(key=lambda item: item.report_date, reverse=True)

        return FinancialSnapshot(
            stock_code=stock_code,
            balance_sheets=balance_sheets,
            income_statements=income_statements,
            cashflow_statements=cashflow_statements,
        )

    def _load_statement_details(
        self,
        payloads: Dict[str, Dict[str, object]],
    ) -> Dict[str, Dict[str, List[Dict[str, object]]]]:
        return {
            Dataset.BALANCE_SHEET.value: self._extract_statement_details(
                payloads.get(Dataset.BALANCE_SHEET.value, {}).get("Result", {})
            ),
            Dataset.INCOME_STATEMENT.value: self._extract_statement_details(
                payloads.get(Dataset.INCOME_STATEMENT.value, {}).get("Result", {})
            ),
            Dataset.CASHFLOW_STATEMENT.value: self._extract_statement_details(
                payloads.get(Dataset.CASHFLOW_STATEMENT.value, {}).get("Result", {})
            ),
        }

    def _load_indicator_snapshot(
        self,
        archive_items: List[WorkspaceArchiveItem],
        payloads: Dict[str, Dict[str, object]],
    ) -> Dict[str, object]:
        for item in archive_items:
            if item.dataset != Dataset.FINANCIAL_INDICATORS.value:
                continue

            payload = payloads.get(item.dataset) or self._read_raw_payload(item.raw_path)
            latest = payload.get("latest")
            if isinstance(latest, dict):
                return latest

            rows = payload.get("rows")
            if isinstance(rows, list):
                indicator_snapshot: Dict[str, object] = {}
                for row in rows:
                    if isinstance(row, dict) and row.get("metric"):
                        indicator_snapshot[str(row["metric"])] = row.get("latest_value")
                if indicator_snapshot:
                    return indicator_snapshot

        return {}

    @staticmethod
    def _extract_statement_details(result: Dict[str, Any]) -> Dict[str, List[Dict[str, object]]]:
        details: Dict[str, List[Dict[str, object]]] = {}
        for block in result.get("data", []):
            report_label = str(block.get("text", "")).strip()
            report_date = parse_report_date(report_label)
            if report_date is None:
                continue

            rows: List[Dict[str, object]] = []
            row_index = 0
            for content in block.get("content", []):
                section_name = str(content.get("name", "")).strip() or None
                for item in content.get("data", []):
                    header = item.get("header") or []
                    if header:
                        extracted = WorkspaceRepository._build_statement_row(
                            row_index=row_index,
                            section_name=section_name,
                            raw_item=header,
                        )
                        if extracted is not None:
                            rows.append(extracted)
                            row_index += 1

                    for body in item.get("body", []):
                        extracted = WorkspaceRepository._build_statement_row(
                            row_index=row_index,
                            section_name=section_name,
                            raw_item=body,
                        )
                        if extracted is not None:
                            rows.append(extracted)
                            row_index += 1

            details[report_date.isoformat()] = rows
        return details

    @staticmethod
    def _build_statement_row(
        row_index: int,
        section_name: str | None,
        raw_item: List[object],
    ) -> Dict[str, object] | None:
        if not raw_item:
            return None

        label = str(raw_item[0]).strip() if raw_item[0] is not None else ""
        if not label:
            return None

        value = raw_item[2] if len(raw_item) > 2 else None
        display_value = "" if value is None else str(value).strip()
        row_key_prefix = section_name or "statement"
        return {
            "key": f"{row_key_prefix}:{label}:{row_index}",
            "label": label,
            "section": section_name,
            "value": value,
            "display_value": display_value,
            "unit": "",
            "source": "baidu_archive",
            "is_estimated": False,
        }

    def _read_raw_payload(self, raw_path: str) -> Dict[str, object]:
        path = Path(raw_path)
        if not path.exists():
            raw_path_str = str(raw_path)
            root_name = self._archive_root.name
            if raw_path_str.startswith(f"{root_name}\\") or raw_path_str.startswith(f"{root_name}/"):
                path = Path(raw_path_str[len(root_name) + 1 :])
            path = self._archive_root / path
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _extract_report_date(manifest: Dict[str, object]) -> str | None:
        csv_path = manifest.get("csv_path")
        if isinstance(csv_path, str):
            path = Path(csv_path)
            stem_parts = path.stem.split("_")
            if len(stem_parts) >= 4:
                return stem_parts[-1]
        return None
