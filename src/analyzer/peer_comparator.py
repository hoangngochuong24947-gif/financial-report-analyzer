"""
====================================================================
模块名称：peer_comparator.py
模块功能：同行业对比分析

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ compare()                    │ target_code: str,           │ ComparisonResult         │
│                              │ peer_codes: List[str]       │                          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 api/routes_analysis.py 调用
====================================================================
"""

from typing import List, Dict, Any, Optional

from src.models.analysis_result import ComparisonResult
from src.crawler.interfaces import FinancialDataGateway
from src.crawler.service import CrawlerService
from src.analyzer.ratio_calculator import calc_profitability, calc_solvency, calc_efficiency
from src.utils.logger import logger


def compare(
    target_code: str,
    peer_codes: List[str],
    gateway: Optional[FinancialDataGateway] = None,
) -> ComparisonResult:
    """
    同行业对比分析

    Args:
        target_code: 目标股票代码
        peer_codes: 对比股票代码列表

    Returns:
        ComparisonResult: 对比分析结果

    Examples:
        >>> result = compare("600519", ["000858", "600809"])
        >>> result.ranking["roe"]  # ROE 排名
    """
    client = gateway or CrawlerService()

    # 收集所有股票的指标
    all_metrics: Dict[str, Dict[str, Any]] = {}

    # 目标股票
    all_codes = [target_code] + peer_codes

    for code in all_codes:
        try:
            # 获取最新财报
            balance_sheets = client.fetch_balance_sheet(code)
            income_statements = client.fetch_income_statement(code)

            if not balance_sheets or not income_statements:
                logger.warning(f"No data for {code}, skipping")
                continue

            bs = balance_sheets[0]  # 最新一期
            is_ = income_statements[0]

            # 计算指标
            profitability = calc_profitability(bs, is_)
            solvency = calc_solvency(bs)
            efficiency = calc_efficiency(bs, is_)

            all_metrics[code] = {
                "roe": float(profitability.roe),
                "roa": float(profitability.roa),
                "net_profit_margin": float(profitability.net_profit_margin),
                "current_ratio": float(solvency.current_ratio),
                "debt_to_asset_ratio": float(solvency.debt_to_asset_ratio),
                "asset_turnover": float(efficiency.asset_turnover),
            }

        except Exception as e:
            logger.error(f"Failed to analyze {code}: {e}")
            continue

    # 计算排名
    ranking = {}
    for metric in ["roe", "roa", "net_profit_margin", "current_ratio", "asset_turnover"]:
        # 按指标值降序排序
        sorted_codes = sorted(
            all_metrics.keys(),
            key=lambda c: all_metrics[c].get(metric, 0),
            reverse=True
        )
        # 目标股票的排名
        if target_code in sorted_codes:
            ranking[metric] = sorted_codes.index(target_code) + 1

    # 生成总结
    summary = f"在 {len(all_codes)} 只对比股票中，{target_code} 的综合排名："
    for metric, rank in ranking.items():
        summary += f"\n  - {metric}: 第 {rank} 名"

    logger.info(f"Peer comparison completed for {target_code}")

    return ComparisonResult(
        target_stock_code=target_code,
        target_stock_name="",  # 需要从股票列表获取
        peer_stocks=peer_codes,
        metrics_comparison=all_metrics,
        ranking=ranking,
        summary=summary
    )


"""
====================================================================
【使用示例】

from src.analyzer.peer_comparator import compare

# 同行业对比（白酒行业）
result = compare(
    target_code="600519",  # 贵州茅台
    peer_codes=["000858", "600809"]  # 五粮液、山西汾酒
)

print(result.summary)
print(f"ROE 排名: {result.ranking['roe']}")

====================================================================
"""
