"""
====================================================================
模块名称：cache_manager.py
模块功能：Redis 缓存管理

【函数接口总览】
┌─────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ 类/函数                      │ 方法                        │ 输入/输出                │
├─────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ CacheManager                 │ get(key: str)               │ str → Optional[Any]      │
│                              │ set(key, value, ttl)        │ str, Any, int → None     │
│                              │ delete(key: str)            │ str → None               │
│                              │ exists(key: str)            │ str → bool               │
└─────────────────────────────┴────────────────────────────┴─────────────────────────┘

【数据流向】
→ 被 data_fetcher/akshare_client.py 调用（缓存 API 响应）
→ 被 analyzer/ 调用（缓存计算结果）
====================================================================
"""

import json
import redis
from typing import Any, Optional
from src.config.settings import settings
from src.utils.logger import logger


class CacheManager:
    """
    Redis 缓存管理器
    """

    def __init__(self):
        """初始化 Redis 连接"""
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # 测试连接
            self.client.ping()
            logger.info(f"Redis connected: {settings.redis_host}:{settings.redis_port}")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Cache disabled.")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据

        Args:
            key: 缓存键

        Returns:
            Optional[Any]: 缓存的数据，未命中返回 None
        """
        if not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """
        设置缓存数据

        Args:
            key: 缓存键
            value: 缓存值（会被 JSON 序列化）
            ttl: 过期时间（秒），默认使用配置中的 cache_ttl
        """
        if not self.client:
            return

        try:
            ttl = ttl or settings.cache_ttl
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            self.client.setex(key, ttl, serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")

    def delete(self, key: str) -> None:
        """
        删除缓存数据

        Args:
            key: 缓存键
        """
        if not self.client:
            return

        try:
            self.client.delete(key)
            logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")

    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在

        Args:
            key: 缓存键

        Returns:
            bool: 是否存在
        """
        if not self.client:
            return False

        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有键

        Args:
            pattern: 键模式（如 "stock:600519:*"）

        Returns:
            int: 删除的键数量
        """
        if not self.client:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0


# 全局缓存实例
cache_manager = CacheManager()


"""
====================================================================
【使用示例】

from src.data_fetcher.cache_manager import cache_manager

# 1. 设置缓存
cache_manager.set("stock:600519:balance_sheet", data, ttl=3600)

# 2. 获取缓存
data = cache_manager.get("stock:600519:balance_sheet")
if data is None:
    # 缓存未命中，从 AKShare 获取
    data = fetch_from_akshare()
    cache_manager.set("stock:600519:balance_sheet", data)

# 3. 删除缓存
cache_manager.delete("stock:600519:balance_sheet")

# 4. 清除某股票的所有缓存
cache_manager.clear_pattern("stock:600519:*")

====================================================================
"""
