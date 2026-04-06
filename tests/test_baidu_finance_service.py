import src.crawler.providers.baidu_finance.service as service_module
from src.crawler.providers.baidu_finance.service import BaiduFinanceCrawlerService


def test_indicator_payload_uses_akshare_fallback_when_dom_scrape_disabled(monkeypatch):
    service = BaiduFinanceCrawlerService()

    monkeypatch.setattr(service_module.settings, "baidu_finance_indicator_dom_enabled", False)

    def fail_if_called(_stock_code: str):
        raise AssertionError("DOM scrape should not run when disabled")

    monkeypatch.setattr(service, "_scrape_indicator_table", fail_if_called)
    monkeypatch.setattr(
        "src.crawler.providers.baidu_finance.service.AKShareClient.fetch_financial_indicators",
        lambda stock_code: {
            "report_date": "2025-12-31",
            "roe": 0.1234,
            "debt_to_asset_ratio": 0.4567,
        },
    )

    payload = service._load_indicator_payload("600000")

    assert payload["latest"]["roe"] == 0.1234
    assert payload["rows"][0]["metric"] == "report_date"
    assert payload["rows"][1]["metric"] == "roe"
