from datetime import date

from src.crawler.providers.baidu_finance.extractors import build_dataframe_rows, parse_report_date
from src.crawler.providers.baidu_finance.parsers import parse_income_statements


def test_parse_report_date_supports_quarter_labels():
    assert parse_report_date("2024年报") == date(2024, 12, 31)
    assert parse_report_date("2024中报") == date(2024, 6, 30)
    assert parse_report_date("2024三季报") == date(2024, 9, 30)
    assert parse_report_date("2024一季报") == date(2024, 3, 31)
    assert parse_report_date("未知") is None


def test_parse_income_statements_maps_baidu_rows():
    result = {
        "data": [
            {
                "text": "2024年报",
                "content": [
                    {
                        "data": [
                            {"header": ["一、总营收", "", "100.5"], "body": []},
                            {"header": ["营业成本", "", "30.25"], "body": []},
                            {"header": ["营业利润", "", "20"], "body": []},
                            {"header": ["利润总额", "", "18"], "body": []},
                            {"header": ["净利润", "", "16"], "body": []},
                        ]
                    }
                ],
            }
        ]
    }

    statements = parse_income_statements("300059", result)

    assert len(statements) == 1
    assert statements[0].stock_code == "300059"
    assert statements[0].report_date == date(2024, 12, 31)
    assert str(statements[0].total_revenue) == "100.50"
    assert str(statements[0].net_income) == "16.00"


def test_build_dataframe_rows_flattens_openapi_payload():
    result = {
        "data": [
            {
                "text": "2024年报",
                "content": [
                    {
                        "data": [
                            {"header": ["一、总营收", "", "100.5"], "body": []},
                            {"header": ["营业成本", "", "30.25"], "body": []},
                        ]
                    }
                ],
            }
        ]
    }

    rows = build_dataframe_rows(result)

    assert rows == [
        {
            "report_label": "2024年报",
            "report_date": "2024-12-31",
            "一、总营收": "100.5",
            "营业成本": "30.25",
        }
    ]
