from functools import lru_cache

from redis.asyncio import Redis

from src.config.settings import get_settings
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


@lru_cache
def get_redis() -> Redis:
    """Возвращает синглтон async Redis клиента."""
    settings = get_settings()
    logger.info(f"Создание Redis клиента: {settings.redis_url}")
    return Redis.from_url(settings.redis_url, decode_responses=True)
