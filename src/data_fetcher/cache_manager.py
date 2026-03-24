"""Redis-backed cache manager with graceful fallback when Redis is unavailable."""

from __future__ import annotations

import json
from typing import Any, Optional

from src.config.settings import settings
from src.utils.logger import logger

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency fallback
    redis = None


class CacheManager:
    """Cache facade used by data fetchers and analyzers."""

    def __init__(self) -> None:
        if redis is None:
            logger.warning("redis package is not installed. Cache disabled.")
            self.client = None
            return

        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            self.client.ping()
            logger.info(f"Redis connected: {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Cache disabled.")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None

        try:
            value = self.client.get(key)
            if value is None:
                logger.debug(f"Cache miss: {key}")
                return None
            logger.debug(f"Cache hit: {key}")
            return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self.client:
            return

        try:
            ttl_value = ttl or settings.cache_ttl
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            self.client.setex(key, ttl_value, serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl_value}s)")
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")

    def delete(self, key: str) -> None:
        if not self.client:
            return

        try:
            self.client.delete(key)
            logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")

    def exists(self, key: str) -> bool:
        if not self.client:
            return False

        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        if not self.client:
            return 0

        try:
            keys = self.client.keys(pattern)
            if not keys:
                return 0

            deleted = self.client.delete(*keys)
            logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
            return int(deleted)
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0


cache_manager = CacheManager()
