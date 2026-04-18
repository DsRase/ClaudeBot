import json

from src.config import get_settings
from src.storage.redis.context import get_context
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


async def read_full_history(chat_id: int) -> str:
    """Возвращает до context_max_stored сообщений чата как JSONL — для глубокого ретроспективного запроса."""
    settings = get_settings()
    history = await get_context(chat_id, limit=settings.context_max_stored)
    logger.info(f"chat_id={chat_id}: read_full_history вернул {len(history)} сообщений")
    return "\n".join(json.dumps(m.model_dump(mode="json"), ensure_ascii=False) for m in history)
