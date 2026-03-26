import json

from src.crawler.interfaces import Dataset
from src.storage.archive_repository import ArchiveRepository


def test_archive_repository_saves_raw_csv_and_manifest(tmp_path):
    repository = ArchiveRepository(archive_root=str(tmp_path))

    result = repository.save_dataset(
        stock_code="300059",
        stock_name="东方财富",
        market="ab",
        dataset=Dataset.INCOME_STATEMENT,
        request_url="https://finance.pae.baidu.com/selfselect/openapi",
        request_params={"group": "income_detail", "code": "300059"},
        raw_payload={"Result": {"ok": True}},
        csv_rows=[{"report_date": "2024-12-31", "营业总收入": "100"}],
    )

    assert (tmp_path / "raw").exists()
    assert (tmp_path / "processed").exists()
    assert result.row_count == 1

    raw_payload = json.loads((tmp_path / result.raw_path).read_text(encoding="utf-8"))
    manifest_payload = json.loads((tmp_path / result.manifest_path).read_text(encoding="utf-8"))

    assert raw_payload == {"Result": {"ok": True}}
    assert manifest_payload["stock_code"] == "300059"
    assert manifest_payload["dataset"] == Dataset.INCOME_STATEMENT.value
    assert manifest_payload["request_params"]["group"] == "income_detail"
    assert manifest_payload["raw_path"] == result.raw_path
    assert (tmp_path / result.csv_path).exists()


def test_archive_repository_lists_recent_archives(tmp_path):
    repository = ArchiveRepository(archive_root=str(tmp_path))
    repository.save_dataset(
        stock_code="300059",
        stock_name="东方财富",
        market="ab",
        dataset=Dataset.BALANCE_SHEET,
        request_url="https://finance.pae.baidu.com/selfselect/openapi",
        request_params={"group": "balance_detail", "code": "300059"},
        raw_payload={"Result": {"ok": True}},
        csv_rows=[{"report_date": "2024-12-31", "总资产": "100"}],
    )

    items = repository.list_archives(stock_code="300059", dataset=Dataset.BALANCE_SHEET, limit=10)

    assert len(items) == 1
    assert items[0]["dataset"] == Dataset.BALANCE_SHEET.value
