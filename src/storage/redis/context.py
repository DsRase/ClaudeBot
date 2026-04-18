import json

from src.config.settings import get_settings
from src.storage.redis.redis_client import get_redis
from src.storage.schemas.chatMessage import ChatMessage
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

_KEY_PREFIX = "context"


def _key(chat_id: int) -> str:
    """Возвращает Redis ключ для чата."""
    return f"{_KEY_PREFIX}:{chat_id}"


async def add_message(chat_id: int, message: ChatMessage) -> None:
    """Добавляет сообщение в историю чата и обрезает до context_max_stored."""
    redis = get_redis()
    settings = get_settings()
    key = _key(chat_id)
    await redis.rpush(key, json.dumps(message.model_dump(mode="python"), ensure_ascii=False))
    await redis.ltrim(key, -settings.context_max_stored, -1)
    logger.debug(f"chat_id={chat_id}: добавлено сообщение role={message.role}")


async def get_context(chat_id: int, limit: int | None = None) -> list[ChatMessage]:
    """Возвращает последние `limit` сообщений из истории чата."""
    redis = get_redis()
    settings = get_settings()
    if limit is None:
        limit = settings.context_default_limit
    key = _key(chat_id)
    raw_messages = await redis.lrange(key, -limit, -1)
    messages = [ChatMessage.model_validate(json.loads(m)) for m in raw_messages]
    logger.debug(f"chat_id={chat_id}: получено {len(messages)} сообщений (limit={limit})")
    return messages
