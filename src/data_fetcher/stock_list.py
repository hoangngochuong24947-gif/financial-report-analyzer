"""Stock list fetcher."""

from __future__ import annotations

from typing import List, Optional

import akshare as ak

from src.data_fetcher.cache_manager import cache_manager
from src.models.stock_info import StockInfo
from src.utils.logger import logger


FALLBACK_STOCKS: List[StockInfo] = [
    StockInfo(stock_code="600519", stock_name="贵州茅台", market="主板"),
    StockInfo(stock_code="000858", stock_name="五粮液", market="主板"),
    StockInfo(stock_code="300750", stock_name="宁德时代", market="创业板"),
]


def _get_market_from_code(code: str) -> str:
    if code.startswith("688"):
        return "科创板"
    if code.startswith("300"):
        return "创业板"
    if code.startswith(("600", "601", "603", "000", "001", "002")):
        return "主板"
    return "其他"


def _fallback_stock_list(market: Optional[str]) -> List[StockInfo]:
    data = [stock for stock in FALLBACK_STOCKS if market is None or stock.market == market]
    logger.warning(f"Using built-in fallback stock list ({len(data)} records)")
    return data


def fetch_stock_list(market: Optional[str] = None) -> List[StockInfo]:
    cache_key = f"stock_list:{market or 'all'}"

    cached = cache_manager.get(cache_key)
    if cached:
        logger.info(f"Stock list loaded from cache: {len(cached)} stocks")
        return [StockInfo(**item) for item in cached]

    try:
        logger.info("Fetching stock list from AKShare...")
        df = ak.stock_zh_a_spot_em()

        required_columns = {"代码", "名称"}
        if df.empty or not required_columns.issubset(set(df.columns)):
            logger.warning("AKShare stock list payload is empty or missing required columns")
            fallback = _fallback_stock_list(market)
            cache_manager.set(cache_key, [stock.model_dump(mode="json") for stock in fallback], ttl=3600)
            return fallback

        df = df[["代码", "名称"]].copy()
        df.columns = ["stock_code", "stock_name"]
        df["market"] = df["stock_code"].apply(_get_market_from_code)

        if market:
            df = df[df["market"] == market]

        stock_list = [
            StockInfo(
                stock_code=row["stock_code"],
                stock_name=row["stock_name"],
                market=row["market"],
            )
            for _, row in df.iterrows()
        ]

        if not stock_list:
            logger.warning("Filtered AKShare stock list is empty; using fallback list")
            stock_list = _fallback_stock_list(market)

        cache_manager.set(
            cache_key,
            [stock.model_dump(mode="json") for stock in stock_list],
            ttl=86400,
        )

        logger.info(f"Fetched {len(stock_list)} stocks")
        return stock_list

    except Exception as e:
        logger.error(f"Failed to fetch stock list: {e}")
        fallback = _fallback_stock_list(market)
        cache_manager.set(cache_key, [stock.model_dump(mode="json") for stock in fallback], ttl=3600)
        return fallback
