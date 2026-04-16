from langchain_anthropic import ChatAnthropic

from src.config.settings import get_settings
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


async def ask(message: str) -> str:
    """Отправляет одно сообщение LLM без контекста и возвращает ответ."""
    settings = get_settings()
    logger.debug(f"Запрос к модели {settings.premium_model}, длина сообщения: {len(message)}")

    llm = ChatAnthropic(
        model=settings.premium_model,
        anthropic_api_key=settings.anthropic_api_key,
    )
    response = await llm.ainvoke(message)

    logger.debug(f"Получен ответ от модели, длина: {len(response.content)}")
    return response.content
