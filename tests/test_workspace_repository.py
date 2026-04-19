from datetime import date
from pathlib import Path
from decimal import Decimal

from src.crawler.interfaces import Dataset
from src.storage.archive_repository import ArchiveRepository


def _openapi_row(report_label: str, values: dict[str, str]) -> dict:
    return {
        "text": report_label,
        "content": [
            {
                "data": [
                    {
                        "header": ["report_label", "", report_label],
                        "body": [[key, "", value] for key, value in values.items()],
                    }
                ]
            }
        ],
    }


def test_workspace_repository_loads_archive_workspace(tmp_path):
    from src.storage.workspace_repository import WorkspaceRepository

    archive_repository = ArchiveRepository(archive_root=str(tmp_path))

    archive_repository.save_dataset(
        stock_code="000001",
        stock_name="测试公司",
        market="ab",
        dataset=Dataset.INCOME_STATEMENT,
        request_url="https://finance.pae.baidu.com/selfselect/openapi",
        request_params={"group": "income_detail", "code": "000001"},
        raw_payload={
            "Result": {
                "data": [
                    _openapi_row(
                        "2025三季报",
                        {
                            "一、总营收": "5000",
                            "营业成本": "3000",
                            "四、营业利润": "1500",
                            "五、利润总额": "1600",
                            "六、合并净利润": "1200",
                        },
                    ),
                    _openapi_row(
                        "2025中报",
                        {
                            "一、总营收": "4500",
                            "营业成本": "2800",
                            "四、营业利润": "1300",
                            "五、利润总额": "1350",
                            "六、合并净利润": "1000",
                        },
                    ),
                ]
            }
        },
        csv_rows=[{"report_date": "2025-09-30", "一、总营收": "5000"}],
    )
    archive_repository.save_dataset(
        stock_code="000001",
        stock_name="测试公司",
        market="ab",
        dataset=Dataset.BALANCE_SHEET,
        request_url="https://finance.pae.baidu.com/selfselect/openapi",
        request_params={"group": "balance_detail", "code": "000001"},
        raw_payload={
            "Result": {
                "data": [
                    _openapi_row(
                        "2025三季报",
                        {
                            "流动资产合计": "1000",
                            "非流动资产合计": "2000",
                            "总资产": "3000",
                            "流动负债合计": "500",
                            "非流动负债合计": "500",
                            "总负债": "1000",
                            "所有者权益合计": "2000",
                        },
                    )
                ]
            }
        },
        csv_rows=[{"report_date": "2025-09-30", "总资产": "3000"}],
    )
    archive_repository.save_dataset(
        stock_code="000001",
        stock_name="测试公司",
        market="ab",
        dataset=Dataset.CASHFLOW_STATEMENT,
        request_url="https://finance.pae.baidu.com/selfselect/openapi",
        request_params={"group": "cash_flow_detail", "code": "000001"},
        raw_payload={
            "Result": {
                "data": [
                    _openapi_row(
                        "2025三季报",
                        {
                            "经营活动产生的现金流量净额": "1500",
                            "投资活动产生的现金流量净额": "-700",
                            "筹资活动产生的现金流量净额": "200",
                            "现金及现金等价物净增加额": "1000",
                        },
                    )
                ]
            }
        },
        csv_rows=[{"report_date": "2025-09-30", "经营活动产生的现金流量净额": "1500"}],
    )

    repository = WorkspaceRepository(archive_root=str(tmp_path))
    workspace = repository.load_workspace("000001")

    assert workspace.stock_code == "000001"
    assert workspace.stock_name == "测试公司"
    assert workspace.snapshot.balance_sheets[0].report_date == date(2025, 9, 30)
    assert workspace.snapshot.income_statements[0].net_income == Decimal("1200.00")
    assert workspace.snapshot.cashflow_statements[0].operating_cashflow == Decimal("1500.00")

    summaries = repository.list_workspaces()
    assert summaries[0].stock_code == "000001"
    assert summaries[0].latest_report_date == "2025-09-30"
    assert summaries[0].dataset_count == 3


def test_workspace_repository_list_workspaces_is_not_capped_by_manifest_count(tmp_path, monkeypatch):
    from src.storage.workspace_repository import WorkspaceRepository

    stock_codes = [f"{600000 + index:06d}" for index in range(251)]
    manifests = [
        {
            "stock_code": code,
            "stock_name": f"Test {code}",
            "market": "ab",
            "dataset": "income_statement",
            "fetched_at": "20260409T000000Z",
            "raw_path": str(Path("data") / "raw" / "baidu_finance" / code / "income.json"),
            "csv_path": str(Path("data") / "processed" / "baidu_finance" / code / "income.csv"),
            "manifest_path": str(Path("data") / "raw" / "baidu_finance" / code / "manifests" / "manifest.json"),
            "row_count": 1,
            "status": "success",
            "request_params": {"report_date": "2025-12-31"},
        }
        for code in stock_codes
    ]

    repository = WorkspaceRepository(archive_root=str(tmp_path))
    monkeypatch.setattr(repository._archive_repository, "list_archives", lambda **kwargs: manifests)
    summaries = repository.list_workspaces(limit=300)

    assert len(summaries) == len(stock_codes)


def test_workspace_repository_list_workspaces_uses_manifest_summary_without_loading_workspace(tmp_path, monkeypatch):
    from src.storage.workspace_repository import WorkspaceRepository

    archive_repository = ArchiveRepository(archive_root=str(tmp_path))
    archive_repository.save_dataset(
        stock_code="600000",
        stock_name="浦发银行",
        market="主板",
        dataset=Dataset.INCOME_STATEMENT,
        request_url="https://finance.pae.baidu.com/selfselect/openapi",
        request_params={"group": "income_detail", "code": "600000"},
        raw_payload={"Result": {"data": [_openapi_row("2025三季报", {"一、营业总收入": "100"})]}},
        csv_rows=[{"report_date": "2025-09-30", "一、营业总收入": "100"}],
    )
    archive_repository.save_dataset(
        stock_code="600000",
        stock_name="浦发银行",
        market="主板",
        dataset=Dataset.BALANCE_SHEET,
        request_url="https://finance.pae.baidu.com/selfselect/openapi",
        request_params={"group": "balance_detail", "code": "600000"},
        raw_payload={"Result": {"data": [_openapi_row("2025三季报", {"总资产": "100"})]}},
        csv_rows=[{"report_date": "2025-09-30", "总资产": "100"}],
    )

    def _fail_load_workspace(self, stock_code: str):
        raise AssertionError(f"load_workspace should not be used for summary listing: {stock_code}")

    monkeypatch.setattr(WorkspaceRepository, "load_workspace", _fail_load_workspace)

    repository = WorkspaceRepository(archive_root=str(tmp_path))
    summaries = repository.list_workspaces(limit=20)

    assert len(summaries) == 1
    assert summaries[0].stock_code == "600000"
    assert summaries[0].stock_name == "浦发银行"
    assert summaries[0].market == "主板"
    assert summaries[0].latest_report_date == "2025-09-30"
    assert summaries[0].dataset_count == 2
    assert len(summaries[0].archives) == 2
