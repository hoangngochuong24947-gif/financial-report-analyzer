"""FastAPI dependency providers."""

from functools import lru_cache

from src.api.analysis_facade import AnalysisFacade
from src.crawler.service import CrawlerService
from src.api.workspace_service import WorkspaceService


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


@lru_cache(maxsize=1)
def get_workspace_service() -> WorkspaceService:
    return WorkspaceService()


@lru_cache(maxsize=1)
def get_analysis_facade() -> AnalysisFacade:
    return AnalysisFacade(
        workspace_service=get_workspace_service(),
        crawler_service=get_crawler_service(),
    )

