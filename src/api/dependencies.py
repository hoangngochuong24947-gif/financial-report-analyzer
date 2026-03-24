"""FastAPI dependency providers."""

from functools import lru_cache

from src.crawler.service import CrawlerService


@lru_cache(maxsize=1)
def get_crawler_service() -> CrawlerService:
    """
    Return a singleton crawler facade.

    The API layer depends on this abstraction instead of concrete data-fetcher
    implementations so crawler internals remain decoupled from route logic.
    """

    return CrawlerService()


# Backward-compatible alias for legacy code paths.
def get_akshare_client() -> CrawlerService:
    return get_crawler_service()

