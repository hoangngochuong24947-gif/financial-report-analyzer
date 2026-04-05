"""Stock list fetcher."""

from __future__ import annotations

from typing import List, Optional

import akshare as ak
import pandas as pd
import requests

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
    if code.startswith(("300", "301")):
        return "创业板"
    if code.startswith(("4", "8", "9")):
        return "北交所"
    if code.startswith(("600", "601", "603", "000", "001", "002")):
        return "主板"
    return "其他"


def _fallback_stock_list(market: Optional[str]) -> List[StockInfo]:
    data = [stock for stock in FALLBACK_STOCKS if market is None or stock.market == market]
    logger.warning(f"Using built-in fallback stock list ({len(data)} records)")
    return data


def _normalize_stock_df(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    if df.empty:
        return None

    if {"stock_code", "stock_name"}.issubset(set(df.columns)):
        return df[["stock_code", "stock_name"]].copy()

    if {"代码", "名称"}.issubset(set(df.columns)):
        normalized = df[["代码", "名称"]].copy()
        normalized.columns = ["stock_code", "stock_name"]
        return normalized

    if {"code", "name"}.issubset(set(df.columns)):
        normalized = df[["code", "name"]].copy()
        normalized.columns = ["stock_code", "stock_name"]
        return normalized

    return None


def _fetch_stock_list_from_eastmoney() -> Optional[pd.DataFrame]:
    url = "https://82.push2.eastmoney.com/api/qt/clist/get"
    base_params = {
        "pz": 1000,
        "po": 1,
        "np": 1,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "fid": "f12",
        "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048",
        "fields": "f12,f14",
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://quote.eastmoney.com/",
    }

    try:
        logger.info("Fetching stock list from Eastmoney direct endpoint")
        rows: list[dict[str, str]] = []
        page = 1

        while True:
            params = {**base_params, "pn": page}
            response = requests.get(url, params=params, headers=headers, timeout=20)
            response.raise_for_status()
            payload = response.json()
            diff = payload.get("data", {}).get("diff", [])
            if not diff:
                break

            rows.extend(
                {
                    "stock_code": str(item.get("f12", "")).strip(),
                    "stock_name": str(item.get("f14", "")).strip(),
                }
                for item in diff
                if item.get("f12") and item.get("f14")
            )

            total = int(payload.get("data", {}).get("total", 0) or 0)
            if len(rows) >= total:
                break
            page += 1

        if not rows:
            logger.warning("Eastmoney stock list payload is empty")
            return None

        normalized = pd.DataFrame(rows).drop_duplicates(subset=["stock_code"]).reset_index(drop=True)
        if normalized.empty:
            logger.warning("Eastmoney stock list normalization produced no records")
            return None
        return normalized
    except Exception as e:
        logger.warning(f"Eastmoney direct stock list failed: {e}")
        return None


def _fetch_stock_list_from_exchange_endpoints() -> Optional[pd.DataFrame]:
    frames: list[pd.DataFrame] = []

    try:
        logger.info("Fetching stock list from AKShare exchange endpoints")

        sh_df = ak.stock_info_sh_name_code()
        if not sh_df.empty:
            normalized = sh_df[["证券代码", "证券简称"]].copy()
            normalized.columns = ["stock_code", "stock_name"]
            frames.append(normalized)

        sz_df = ak.stock_info_sz_name_code()
        if not sz_df.empty:
            normalized = sz_df[["A股代码", "A股简称"]].copy()
            normalized.columns = ["stock_code", "stock_name"]
            frames.append(normalized)

        bj_df = ak.stock_info_bj_name_code()
        if not bj_df.empty:
            normalized = bj_df[["证券代码", "证券简称"]].copy()
            normalized.columns = ["stock_code", "stock_name"]
            frames.append(normalized)

        if not frames:
            logger.warning("Exchange endpoint stock list returned no frames")
            return None

        return pd.concat(frames, ignore_index=True).drop_duplicates(subset=["stock_code"]).reset_index(drop=True)
    except Exception as e:
        logger.warning(f"Exchange endpoint stock list failed: {e}")
        return None


def _fetch_stock_list_from_secondary() -> Optional[pd.DataFrame]:
    # Fallback chain:
    # 1) stock_zh_a_spot (works in environments where *_em endpoint may be blocked)
    # 2) stock_info_a_code_name
    try:
        logger.info("Fetching stock list from AKShare secondary endpoint: stock_zh_a_spot")
        df = ak.stock_zh_a_spot()
        normalized = _normalize_stock_df(df)
        if normalized is not None:
            return normalized
    except Exception as e:
        logger.warning(f"Secondary endpoint stock_zh_a_spot failed: {e}")

    try:
        logger.info("Fetching stock list from AKShare tertiary endpoint: stock_info_a_code_name")
        df = ak.stock_info_a_code_name()
        normalized = _normalize_stock_df(df)
        if normalized is not None:
            return normalized
    except Exception as e:
        logger.warning(f"Tertiary endpoint stock_info_a_code_name failed: {e}")

    return None


def fetch_stock_list(market: Optional[str] = None, refresh: bool = False) -> List[StockInfo]:
    cache_key = f"stock_list:{market or 'all'}"

    if refresh:
        cache_manager.delete(cache_key)
    else:
        cached = cache_manager.get(cache_key)
        if cached:
            logger.info(f"Stock list loaded from cache: {len(cached)} stocks")
            return [StockInfo(**item) for item in cached]

    try:
        df = _fetch_stock_list_from_exchange_endpoints()
        if df is None:
            df = _fetch_stock_list_from_eastmoney()
        if df is None:
            logger.info("Fetching stock list from AKShare...")
            df = ak.stock_zh_a_spot_em()
        normalized = _normalize_stock_df(df)
        if normalized is None:
            logger.warning("Primary stock list payload is empty or missing required columns")
            normalized = _fetch_stock_list_from_secondary()
            if normalized is None:
                fallback = _fallback_stock_list(market)
                cache_manager.set(
                    cache_key,
                    [stock.model_dump(mode="json") for stock in fallback],
                    ttl=300,
                )
                return fallback
        df = normalized

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
        df2 = _fetch_stock_list_from_secondary()
        if df2 is not None:
            df2["market"] = df2["stock_code"].apply(_get_market_from_code)
            if market:
                df2 = df2[df2["market"] == market]

            stock_list = [
                StockInfo(
                    stock_code=row["stock_code"],
                    stock_name=row["stock_name"],
                    market=row["market"],
                )
                for _, row in df2.iterrows()
            ]
            if stock_list:
                cache_manager.set(
                    cache_key,
                    [stock.model_dump(mode="json") for stock in stock_list],
                    ttl=3600,
                )
                logger.info(f"Fetched {len(stock_list)} stocks via secondary chain")
                return stock_list

        fallback = _fallback_stock_list(market)
        cache_manager.set(
            cache_key,
            [stock.model_dump(mode="json") for stock in fallback],
            ttl=300,
        )
        return fallback
