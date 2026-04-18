from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import List

import pandas as pd

from src.config.settings import settings
from src.models.workspace_metrics import InsightReportHistoryItem, InsightReportResponse, StatementDetailRow


class ReportRepository:
    """Persist generated workspace insight reports on the filesystem."""

    def __init__(self, root: str | None = None) -> None:
        base_root = Path(root or settings.archive_root)
        self._root = base_root / "reports"
        self._root.mkdir(parents=True, exist_ok=True)

    def save_report(self, report: InsightReportResponse) -> InsightReportHistoryItem:
        report_dir = self._root / report.stock_code / report.report_date / report.lang
        report_dir.mkdir(parents=True, exist_ok=True)

        json_path = report_dir / "insight_report.json"
        markdown_path = report_dir / "insight_report.md"

        json_path.write_text(
            report.model_dump_json(indent=2),
            encoding="utf-8",
        )
        markdown_path.write_text(self._to_markdown(report), encoding="utf-8")

        return InsightReportHistoryItem(
            stock_code=report.stock_code,
            stock_name=report.stock_name,
            report_date=report.report_date,
            lang=report.lang,
            generated_at=report.generated_at,
            model_version=report.model_version,
            json_path=str(json_path),
            markdown_path=str(markdown_path),
        )

    def load_report(
        self,
        stock_code: str,
        period: str | None = None,
        lang: str | None = None,
    ) -> InsightReportResponse:
        report_path = self._resolve_report_path(stock_code=stock_code, period=period, lang=lang)
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        return InsightReportResponse(**payload)

    def list_reports(self, stock_code: str, limit: int = 20) -> List[InsightReportHistoryItem]:
        stock_root = self._root / stock_code
        if not stock_root.exists():
            return []

        items: list[InsightReportHistoryItem] = []
        for report_path in stock_root.glob("*/*/insight_report.json"):
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            markdown_path = report_path.with_name("insight_report.md")
            items.append(
                InsightReportHistoryItem(
                    stock_code=payload["stock_code"],
                    stock_name=payload["stock_name"],
                    report_date=payload["report_date"],
                    lang=payload.get("lang", "zh-CN"),
                    generated_at=payload["generated_at"],
                    model_version=payload.get("model_version", "workspace-insights-v1"),
                    json_path=str(report_path),
                    markdown_path=str(markdown_path),
                )
            )

        items.sort(key=lambda item: item.generated_at, reverse=True)
        return items[:limit]

    @staticmethod
    def rows_to_csv_bytes(rows: list[StatementDetailRow] | list[dict[str, object]]) -> bytes:
        normalized_rows = []
        for row in rows:
            if isinstance(row, dict):
                normalized_rows.append(
                    {
                        "label": str(row.get("label", "")),
                        "section": str(row.get("section", "")),
                        "display_value": str(row.get("display_value", "")),
                        "value": row.get("value"),
                        "unit": str(row.get("unit", "")),
                        "source": str(row.get("source", "")),
                        "is_estimated": bool(row.get("is_estimated", False)),
                    }
                )
                continue

            normalized_rows.append(
                {
                    "label": row.label,
                    "section": row.section or "",
                    "display_value": row.display_value,
                    "value": row.value,
                    "unit": row.unit,
                    "source": row.source,
                    "is_estimated": row.is_estimated,
                }
            )

        frame = pd.DataFrame(normalized_rows)
        return frame.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

    @staticmethod
    def rows_to_excel_bytes(sheets: dict[str, list[dict[str, object]]]) -> bytes:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for sheet_name, rows in sheets.items():
                pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name[:31], index=False)
        buffer.seek(0)
        return buffer.getvalue()

    def _resolve_report_path(
        self,
        *,
        stock_code: str,
        period: str | None,
        lang: str | None,
    ) -> Path:
        stock_root = self._root / stock_code
        if not stock_root.exists():
            raise FileNotFoundError(f"No stored insight report found for {stock_code}")

        if period:
            lang_root = stock_root / period
            if not lang_root.exists():
                raise FileNotFoundError(f"No stored insight report found for {stock_code} {period}")
            target_lang = lang or self._latest_lang(lang_root)
            report_path = lang_root / target_lang / "insight_report.json"
            if not report_path.exists():
                raise FileNotFoundError(f"No stored insight report found for {stock_code} {period} {target_lang}")
            return report_path

        report_candidates = sorted(
            stock_root.glob("*/*/insight_report.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not report_candidates:
            raise FileNotFoundError(f"No stored insight report found for {stock_code}")

        if lang:
            for candidate in report_candidates:
                if candidate.parent.name == lang:
                    return candidate

        return report_candidates[0]

    @staticmethod
    def _latest_lang(period_root: Path) -> str:
        candidates = sorted((path.name for path in period_root.iterdir() if path.is_dir()), reverse=True)
        if not candidates:
            raise FileNotFoundError(f"No stored insight report language variants found under {period_root}")
        return candidates[0]

    @staticmethod
    def _to_markdown(report: InsightReportResponse) -> str:
        sections = [
            f"# {report.stock_name} {report.report_date} Insight Report",
            "",
            f"- Stock Code: {report.stock_code}",
            f"- Language: {report.lang}",
            f"- Generated At: {report.generated_at}",
            "",
            "## Summary",
            report.summary or "",
            "",
            "## Highlights",
        ]
        sections.extend(f"- {item}" for item in report.highlights)
        sections.extend(
            [
                "",
                "## Risks",
            ]
        )
        sections.extend(f"- {item}" for item in report.risks)
        sections.extend(
            [
                "",
                "## Open Questions",
            ]
        )
        sections.extend(f"- {item}" for item in report.open_questions)
        sections.extend(
            [
                "",
                "## Actions",
            ]
        )
        sections.extend(f"- {item}" for item in report.actions)
        sections.extend(
            [
                "",
                "## Evidence",
            ]
        )
        sections.extend(f"- {item}" for item in report.evidence)
        return "\n".join(sections).strip() + "\n"
