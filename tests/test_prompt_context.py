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


def test_prompt_context_builder_assembles_profile_and_injection_bundle(tmp_path):
    from src.analyzer.metric_engine import WorkspaceMetricEngine
    from src.llm_engine.context_builder import PromptContextBuilder
    from src.llm_engine.prompt_profiles import PromptProfileRegistry
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
                    )
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

    workspace = WorkspaceRepository(archive_root=str(tmp_path)).load_workspace("000001")
    bundle = WorkspaceMetricEngine().build_bundle(workspace.snapshot, stock_name=workspace.stock_name)

    registry = PromptProfileRegistry.default()
    context = PromptContextBuilder(registry=registry).build(
        workspace=workspace,
        metric_bundle=bundle,
        profile_key="archive_review",
    )

    assert context.profile_key == "archive_review"
    assert context.profile_name == "Archive Review"
    assert context.injection_bundle.stock_code == "000001"
    assert "ROE" in context.context_text
    assert "archive-first" in context.system_prompt
    assert "profitability" in context.injection_bundle.metric_groups
