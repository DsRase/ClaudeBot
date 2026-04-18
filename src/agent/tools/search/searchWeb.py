import asyncio

from ddgs import DDGS

from src.config import get_settings
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def _sync_search(query: str, max_results: int) -> list[dict]:
    """Sync вызов DDGS — выносится в отдельный поток через asyncio.to_thread."""
    raw = DDGS().text(query, max_results=max_results)
    return [
        {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
        for r in raw
    ]


async def search_web(query: str, max_results: int | None = None) -> list[dict]:
    """Ищет в DuckDuckGo и возвращает список результатов с title/url/snippet."""
    if max_results is None:
        max_results = get_settings().search_default_max_results
    logger.info(f"search_web: query={query!r}, max_results={max_results}")
    results = await asyncio.to_thread(_sync_search, query, max_results)
    logger.debug(f"search_web: получено {len(results)} результатов")
    return results
