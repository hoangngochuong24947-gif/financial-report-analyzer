from src.storage.crawl_run_repository import CrawlRunRepository


def test_crawl_run_repository_collects_successful_stocks_for_date(tmp_path):
    repository = CrawlRunRepository(root=str(tmp_path))

    repository.create_run(
        "run-a",
        config={},
        stocks=[
            {"stock_code": "000001"},
            {"stock_code": "000002"},
        ],
    )
    repository.update_stock(
        "run-a",
        "000001",
        {
            "status": "success",
            "finished_at": "2026-04-06T01:00:00+08:00",
        },
    )
    repository.update_stock(
        "run-a",
        "000002",
        {
            "status": "failed",
            "finished_at": "2026-04-06T02:00:00+08:00",
        },
    )

    repository.create_run(
        "run-b",
        config={},
        stocks=[
            {"stock_code": "000003"},
        ],
    )
    repository.update_stock(
        "run-b",
        "000003",
        {
            "status": "success",
            "finished_at": "2026-04-05T23:00:00+08:00",
        },
    )

    assert repository.successful_stocks_for_date("2026-04-06") == {"000001"}

