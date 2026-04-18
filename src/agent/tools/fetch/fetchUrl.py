import httpx
from bs4 import BeautifulSoup

from src.config import get_settings
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def _extract_text(html: str) -> str:
    """Достаёт читаемый текст из HTML, выкидывая script/style/nav-шумы."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


async def fetch_url(url: str) -> str:
    """Скачивает страницу и возвращает её текст. Обрезает до Settings.fetch_max_content_chars символов."""
    settings = get_settings()
    logger.info(f"fetch_url: url={url}")
    async with httpx.AsyncClient(
        timeout=settings.fetch_request_timeout,
        follow_redirects=True,
        headers={"User-Agent": settings.fetch_user_agent},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    text = _extract_text(response.text)
    if len(text) > settings.fetch_max_content_chars:
        text = text[:settings.fetch_max_content_chars]
    logger.debug(f"fetch_url: вернули {len(text)} символов")
    return text
