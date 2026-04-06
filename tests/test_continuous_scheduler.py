from src.crawler.continuous_scheduler import select_stocks_for_cycle


def test_select_stocks_for_cycle_skips_successful_today_and_respects_batch_size():
    stock_pool = [
        {"stock_code": "000001", "stock_name": "A"},
        {"stock_code": "000002", "stock_name": "B"},
        {"stock_code": "000003", "stock_name": "C"},
        {"stock_code": "000004", "stock_name": "D"},
    ]

    selected = select_stocks_for_cycle(
        stock_pool=stock_pool,
        successful_codes={"000001", "000003"},
        batch_size=2,
    )

    assert [item["stock_code"] for item in selected] == ["000002", "000004"]
