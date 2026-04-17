import re

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.config import get_settings
from src.config import AgentMessages
from src.storage.schemas import ChatMessage
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

_LANGCHAIN_ROLE_MAP = {
    "system": SystemMessage,
    "user": HumanMessage,
    "assistant": AIMessage,
}


async def ask(history: list[ChatMessage], is_premium: bool = False) -> str:
    """Отправляет историю сообщений в LLM и возвращает ответ."""
    settings = get_settings()
    model = settings.premium_model if is_premium else settings.default_model
    logger.debug(f"Запрос к модели {model}, сообщений в контексте: {len(history)}")

    llm = ChatAnthropic(
        model=model,
        anthropic_api_key=settings.anthropic_api_key,
        timeout=120,
        max_tokens=settings.max_tokens,
    )

    lc_messages = [
        SystemMessage(content=AgentMessages.system_prompt),
        *[_LANGCHAIN_ROLE_MAP[m.role](content=m.content) for m in history]
    ]
    response = await llm.ainvoke(lc_messages)

    content = re.sub(r"<think>.*?</think>", "", response.content, flags=re.DOTALL).strip()
    logger.debug(f"Получен ответ от модели, длина: {len(content)}")
    return content
