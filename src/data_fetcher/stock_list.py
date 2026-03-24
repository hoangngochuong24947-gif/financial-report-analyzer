"""
====================================================================
模块名称：stock_list.py
模块功能：获取股票列表

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 函数名                       │ 输入                        │ 输出                     │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ fetch_stock_list()           │ market: Optional[str]       │ List[StockInfo]          │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 api/routes_stock.py 调用
====================================================================
"""

import akshare as ak
import pandas as pd
from typing import List, Optional
from src.models.stock_info import StockInfo
from src.data_fetcher.cache_manager import cache_manager
from src.utils.logger import logger


def fetch_stock_list(market: Optional[str] = None) -> List[StockInfo]:
    """
    获取 A 股股票列表

    Args:
        market: 市场类型筛选（"主板", "创业板", "科创板"），None 表示全部

    Returns:
        List[StockInfo]: 股票信息列表

    Examples:
        >>> stocks = fetch_stock_list()
        >>> len(stocks) > 0
        True
        >>> stocks = fetch_stock_list(market="主板")
    """
    cache_key = f"stock_list:{market or 'all'}"

    # 尝试从缓存获取
    cached = cache_manager.get(cache_key)
    if cached:
        logger.info(f"Stock list loaded from cache: {len(cached)} stocks")
        return [StockInfo(**item) for item in cached]

    try:
        logger.info("Fetching stock list from AKShare...")

        # 获取 A 股实时行情（包含所有股票）
        df = ak.stock_zh_a_spot_em()

        # 筛选需要的列
        df = df[["代码", "名称"]].copy()
        df.columns = ["stock_code", "stock_name"]

        # 根据代码判断市场类型
        def get_market(code: str) -> str:
            if code.startswith("688"):
                return "科创板"
            elif code.startswith("300"):
                return "创业板"
            elif code.startswith(("600", "601", "603", "000", "001", "002")):
                return "主板"
            else:
                return "其他"

        df["market"] = df["stock_code"].apply(get_market)

        # 市场筛选
        if market:
            df = df[df["market"] == market]

        # 转换为 StockInfo 列表
        stock_list = [
            StockInfo(
                stock_code=row["stock_code"],
                stock_name=row["stock_name"],
                market=row["market"]
            )
            for _, row in df.iterrows()
        ]

        logger.info(f"Fetched {len(stock_list)} stocks from AKShare")

        # 缓存结果（24小时）
        cache_manager.set(
            cache_key,
            [stock.model_dump() for stock in stock_list],
            ttl=86400
        )

        return stock_list

    except Exception as e:
        logger.error(f"Failed to fetch stock list: {e}")
        return []


"""
====================================================================
【使用示例】

from src.data_fetcher.stock_list import fetch_stock_list

# 1. 获取所有股票
all_stocks = fetch_stock_list()

# 2. 获取主板股票
main_board = fetch_stock_list(market="主板")

# 3. 获取科创板股票
star_market = fetch_stock_list(market="科创板")

====================================================================
"""
