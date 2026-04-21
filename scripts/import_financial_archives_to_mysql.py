from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import mysql.connector
from mysql.connector import MySQLConnection

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import settings
from src.crawler.interfaces import Dataset
from src.crawler.providers.baidu_finance.extractors import parse_report_date
from src.storage.archive_repository import ArchiveRepository
from src.storage.workspace_repository import WorkspaceRepository
from src.utils.precision import to_amount


SCHEMA_PATH = PROJECT_ROOT / "sql" / "financial_reports_schema.sql"

STATEMENT_DATASET_MAP = {
    Dataset.BALANCE_SHEET.value: "balance_sheet",
    Dataset.INCOME_STATEMENT.value: "income_statement",
    Dataset.CASHFLOW_STATEMENT.value: "cashflow_statement",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import archived Baidu finance statements into MySQL.",
    )
    parser.add_argument("--stock-code", help="Only import one stock code, e.g. 600519")
    parser.add_argument("--archive-root", default=settings.archive_root, help="Archive root directory")
    parser.add_argument("--host", default=settings.mysql_host, help="MySQL host")
    parser.add_argument("--port", type=int, default=settings.mysql_port, help="MySQL port")
    parser.add_argument("--user", default=settings.mysql_user, help="MySQL user")
    parser.add_argument("--password", default=settings.mysql_password, help="MySQL password")
    parser.add_argument("--database", default=settings.mysql_database, help="MySQL database")
    parser.add_argument(
        "--init-schema",
        action="store_true",
        help="Create tables from sql/financial_reports_schema.sql before importing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write database rows, only print import summary",
    )
    return parser.parse_args()


def connect_mysql(args: argparse.Namespace) -> MySQLConnection:
    return mysql.connector.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        autocommit=False,
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
    )


def run_schema(connection: MySQLConnection) -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    cursor = connection.cursor()
    try:
        for statement in split_sql_statements(schema_sql):
            if statement.strip():
                cursor.execute(statement)
        connection.commit()
    finally:
        cursor.close()


def split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buffer.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(buffer))
            buffer = []
    if buffer:
        statements.append("\n".join(buffer))
    return statements


def upsert_stock(cursor: Any, workspace: Any) -> None:
    cursor.execute(
        """
        INSERT INTO stocks (stock_code, stock_name, market, latest_report_date)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          stock_name = VALUES(stock_name),
          market = VALUES(market),
          latest_report_date = VALUES(latest_report_date)
        """,
        (
            workspace.stock_code,
            workspace.stock_name,
            workspace.market,
            workspace.latest_report_date,
        ),
    )


def upsert_archive_manifests(cursor: Any, archive_repository: ArchiveRepository, stock_code: str) -> int:
    manifests = archive_repository.list_archives(stock_code=stock_code, limit=1000)
    for manifest in manifests:
        cursor.execute(
            """
            INSERT INTO archive_manifests (
              stock_code, stock_name, market, dataset, fetched_at, report_date,
              raw_path, csv_path, manifest_path, row_count, status, request_url,
              request_params, error_message
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              stock_name = VALUES(stock_name),
              market = VALUES(market),
              dataset = VALUES(dataset),
              fetched_at = VALUES(fetched_at),
              report_date = VALUES(report_date),
              raw_path = VALUES(raw_path),
              csv_path = VALUES(csv_path),
              row_count = VALUES(row_count),
              status = VALUES(status),
              request_url = VALUES(request_url),
              request_params = VALUES(request_params),
              error_message = VALUES(error_message)
            """,
            (
                manifest["stock_code"],
                manifest.get("stock_name", stock_code),
                manifest.get("market", "ab"),
                manifest["dataset"],
                manifest["fetched_at"],
                extract_manifest_report_date(manifest),
                manifest["raw_path"],
                manifest["csv_path"],
                manifest["manifest_path"],
                manifest.get("row_count", 0),
                manifest.get("status", "success"),
                manifest.get("request_url"),
                json.dumps(manifest.get("request_params", {}), ensure_ascii=False),
                manifest.get("error"),
            ),
        )
    return len(manifests)


def extract_manifest_report_date(manifest: dict[str, Any]) -> date | None:
    csv_path = Path(str(manifest.get("csv_path", "")))
    stem_parts = csv_path.stem.split("_")
    if len(stem_parts) >= 4:
        try:
            return date.fromisoformat(stem_parts[-1])
        except ValueError:
            return None
    return None


def import_balance_sheet_summary(cursor: Any, workspace: Any) -> int:
    count = 0
    for item in workspace.snapshot.balance_sheets:
        cursor.execute(
            """
            INSERT INTO balance_sheet_summary (
              stock_code, report_date, total_current_assets, total_non_current_assets, total_assets,
              total_current_liabilities, total_non_current_liabilities, total_liabilities, total_equity
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              total_current_assets = VALUES(total_current_assets),
              total_non_current_assets = VALUES(total_non_current_assets),
              total_assets = VALUES(total_assets),
              total_current_liabilities = VALUES(total_current_liabilities),
              total_non_current_liabilities = VALUES(total_non_current_liabilities),
              total_liabilities = VALUES(total_liabilities),
              total_equity = VALUES(total_equity)
            """,
            (
                item.stock_code,
                item.report_date,
                str(item.total_current_assets),
                str(item.total_non_current_assets),
                str(item.total_assets),
                str(item.total_current_liabilities),
                str(item.total_non_current_liabilities),
                str(item.total_liabilities),
                str(item.total_equity),
            ),
        )
        count += 1
    return count


def import_income_statement_summary(cursor: Any, workspace: Any) -> int:
    count = 0
    for item in workspace.snapshot.income_statements:
        cursor.execute(
            """
            INSERT INTO income_statement_summary (
              stock_code, report_date, total_revenue, operating_cost, operating_profit, total_profit, net_income
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              total_revenue = VALUES(total_revenue),
              operating_cost = VALUES(operating_cost),
              operating_profit = VALUES(operating_profit),
              total_profit = VALUES(total_profit),
              net_income = VALUES(net_income)
            """,
            (
                item.stock_code,
                item.report_date,
                str(item.total_revenue),
                str(item.operating_cost),
                str(item.operating_profit),
                str(item.total_profit),
                str(item.net_income),
            ),
        )
        count += 1
    return count


def import_cashflow_statement_summary(cursor: Any, workspace: Any) -> int:
    count = 0
    for item in workspace.snapshot.cashflow_statements:
        cursor.execute(
            """
            INSERT INTO cashflow_statement_summary (
              stock_code, report_date, operating_cashflow, investing_cashflow, financing_cashflow, net_cashflow
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              operating_cashflow = VALUES(operating_cashflow),
              investing_cashflow = VALUES(investing_cashflow),
              financing_cashflow = VALUES(financing_cashflow),
              net_cashflow = VALUES(net_cashflow)
            """,
            (
                item.stock_code,
                item.report_date,
                str(item.operating_cashflow),
                str(item.investing_cashflow),
                str(item.financing_cashflow),
                str(item.net_cashflow),
            ),
        )
        count += 1
    return count


def import_statement_line_items(cursor: Any, workspace: Any) -> int:
    count = 0
    for dataset, period_map in workspace.statement_details.items():
        statement_type = STATEMENT_DATASET_MAP.get(dataset, dataset)
        for report_date_text, rows in period_map.items():
            report_date_value = date.fromisoformat(report_date_text)
            for row in rows:
                normalized_value = to_amount(row.get("value"))
                cursor.execute(
                    """
                    INSERT INTO statement_line_items (
                      stock_code, statement_type, report_date, row_key, label, section_name,
                      raw_value, normalized_value, display_value, unit, source, is_estimated
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                      label = VALUES(label),
                      section_name = VALUES(section_name),
                      raw_value = VALUES(raw_value),
                      normalized_value = VALUES(normalized_value),
                      display_value = VALUES(display_value),
                      unit = VALUES(unit),
                      source = VALUES(source),
                      is_estimated = VALUES(is_estimated)
                    """,
                    (
                        workspace.stock_code,
                        statement_type,
                        report_date_value,
                        str(row.get("key", "")),
                        str(row.get("label", "")),
                        row.get("section"),
                        None if row.get("value") is None else str(row.get("value")),
                        str(normalized_value),
                        row.get("display_value"),
                        row.get("unit"),
                        row.get("source"),
                        1 if row.get("is_estimated") else 0,
                    ),
                )
                count += 1
    return count


def load_latest_indicator_rows(archive_repository: ArchiveRepository, stock_code: str) -> list[dict[str, Any]]:
    manifests = archive_repository.list_archives(
        stock_code=stock_code,
        dataset=Dataset.FINANCIAL_INDICATORS,
        limit=20,
    )
    for manifest in manifests:
        raw_path = Path(str(manifest["raw_path"]))
        if raw_path.exists():
            payload = json.loads(raw_path.read_text(encoding="utf-8"))
            rows = payload.get("rows")
            if isinstance(rows, list) and rows:
                return [row for row in rows if isinstance(row, dict)]
    return []


def import_financial_indicators(cursor: Any, archive_repository: ArchiveRepository, stock_code: str) -> int:
    rows = load_latest_indicator_rows(archive_repository, stock_code)
    count = 0
    for row in rows:
        latest_report_label = row.get("latest_report_label")
        report_date_value = parse_report_date(str(latest_report_label)) if latest_report_label else None
        latest_value_raw = row.get("latest_value")
        latest_value_num = to_amount(latest_value_raw)
        latest_value_num_param = None
        if isinstance(latest_value_num, Decimal) and latest_value_num.is_finite():
            latest_value_num_param = str(latest_value_num)
        cursor.execute(
            """
            INSERT INTO financial_indicators (
              stock_code, report_date, latest_report_label, metric, latest_value_raw, latest_value_num
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              latest_report_label = VALUES(latest_report_label),
              latest_value_raw = VALUES(latest_value_raw),
              latest_value_num = VALUES(latest_value_num)
            """,
            (
                stock_code,
                report_date_value,
                latest_report_label,
                str(row.get("metric", "")),
                None if latest_value_raw is None else str(latest_value_raw),
                latest_value_num_param,
            ),
        )
        count += 1
    return count


def iter_stock_codes(workspace_repository: WorkspaceRepository, stock_code: str | None) -> Iterable[str]:
    if stock_code:
        yield stock_code
        return
    for summary in workspace_repository.list_workspaces(limit=100000):
        yield summary.stock_code


def main() -> int:
    args = parse_args()
    workspace_repository = WorkspaceRepository(archive_root=args.archive_root)
    archive_repository = ArchiveRepository(archive_root=args.archive_root)

    totals = {
        "stocks": 0,
        "archive_manifests": 0,
        "balance_sheet_summary": 0,
        "income_statement_summary": 0,
        "cashflow_statement_summary": 0,
        "statement_line_items": 0,
        "financial_indicators": 0,
    }

    if args.dry_run:
        for stock_code in iter_stock_codes(workspace_repository, args.stock_code):
            workspace = workspace_repository.load_workspace(stock_code)
            totals["stocks"] += 1
            totals["archive_manifests"] += len(archive_repository.list_archives(stock_code=stock_code, limit=1000))
            totals["balance_sheet_summary"] += len(workspace.snapshot.balance_sheets)
            totals["income_statement_summary"] += len(workspace.snapshot.income_statements)
            totals["cashflow_statement_summary"] += len(workspace.snapshot.cashflow_statements)
            totals["statement_line_items"] += sum(
                len(rows)
                for period_map in workspace.statement_details.values()
                for rows in period_map.values()
            )
            totals["financial_indicators"] += len(load_latest_indicator_rows(archive_repository, stock_code))
        print(json.dumps({"dry_run": True, "totals": totals}, ensure_ascii=False, indent=2))
        return 0

    connection = connect_mysql(args)
    try:
        if args.init_schema:
            run_schema(connection)

        cursor = connection.cursor()
        try:
            for stock_code in iter_stock_codes(workspace_repository, args.stock_code):
                workspace = workspace_repository.load_workspace(stock_code)
                upsert_stock(cursor, workspace)
                totals["stocks"] += 1
                totals["archive_manifests"] += upsert_archive_manifests(cursor, archive_repository, stock_code)
                totals["balance_sheet_summary"] += import_balance_sheet_summary(cursor, workspace)
                totals["income_statement_summary"] += import_income_statement_summary(cursor, workspace)
                totals["cashflow_statement_summary"] += import_cashflow_statement_summary(cursor, workspace)
                totals["statement_line_items"] += import_statement_line_items(cursor, workspace)
                totals["financial_indicators"] += import_financial_indicators(cursor, archive_repository, stock_code)

            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
    finally:
        connection.close()

    print(json.dumps({"dry_run": False, "totals": totals}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
