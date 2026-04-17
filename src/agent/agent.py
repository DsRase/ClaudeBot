import re

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import get_settings
from src.config import AgentMessages
from src.storage.schemas import ChatMessage
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def _format_user_line(msg: ChatMessage) -> str:
    """Форматирует строку user-сообщения с метаданными отправителя и адресата."""
    parts = []
    if msg.username:
        parts.append(f"@{msg.username}")
    name = " ".join(p for p in (msg.first_name, msg.last_name) if p)
    if name:
        parts.append(name)
    sender = f"[{' | '.join(parts)}]" if parts else "[unknown]"
    reply = f" ответил @{msg.reply_to_username}" if msg.reply_to_username else ""
    return f"{sender}{reply}: {msg.content}"


def _format_assistant_line(msg: ChatMessage) -> str:
    """Форматирует строку ответа бота с указанием, кому конкретно он ответил."""
    reply = f" ответил @{msg.reply_to_username}" if msg.reply_to_username else ""
    return f"Пипиндр{reply}: {msg.content}"


def _format_line(msg: ChatMessage) -> str:
    return _format_user_line(msg) if msg.role == "user" else _format_assistant_line(msg)


def _render_history(history: list[ChatMessage]) -> str:
    """Сворачивает историю в одну строку: блок контекста + блок триггерного сообщения."""
    if not history:
        return "=== Message to reply to NOW ===\n(no message)"
    *context, trigger = history
    lines = []
    if context:
        lines.append("=== Chat history (context only, do not respond to these) ===")
        lines.extend(_format_line(m) for m in context)
        lines.append("")
    lines.append("=== Message to reply to NOW ===")
    lines.append(_format_line(trigger))
    return "\n".join(lines)


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
        HumanMessage(content=_render_history(history)),
    ]
    response = await llm.ainvoke(lc_messages)

    content = re.sub(r"<think>.*?</think>", "", response.content, flags=re.DOTALL).strip()
    logger.debug(f"Получен ответ от модели, длина: {len(content)}")
    return content
