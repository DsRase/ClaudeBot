import asyncio
import secrets
from html import escape

from aiogram import Bot

from src.bot.markups import build_permission_keyboard
from src.bot.permissions.state import PendingRequest, get_permission_state
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

DEFAULT_TIMEOUT = 120


def _build_prompt(initiator_username: str | None, tool_name: str, tool_description: str) -> str:
    """Формирует HTML-текст сообщения с описанием запрашиваемого действия."""
    who = f"@{escape(initiator_username)}" if initiator_username else "инициатор"
    return (
        f"{who}, агент хочет вызвать инструмент <code>{escape(tool_name)}</code>.\n"
        f"{escape(tool_description)}\n\n"
        f"Только ты можешь решить."
    )


async def request_permission(
    bot: Bot,
    chat_id: int,
    initiator_user_id: int,
    initiator_username: str | None,
    tool_name: str,
    tool_description: str,
    reply_to_message_id: int | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> bool:
    """Запрашивает у инициатора разрешение на вызов тулы. Возвращает True/False по решению или таймауту."""
    state = get_permission_state()

    if state.is_allowed_in_session(initiator_user_id, tool_name):
        logger.info(
            f"user_id={initiator_user_id}, chat_id={chat_id}: "
            f"'{tool_name}' уже разрешён до конца сессии, пропускаем UI"
        )
        return True

    request_id = secrets.token_urlsafe(8)
    request = PendingRequest(
        initiator_user_id=initiator_user_id,
        initiator_username=initiator_username,
        tool_name=tool_name,
    )
    state.register_request(request_id, request)
    logger.info(
        f"user_id={initiator_user_id}, chat_id={chat_id}: "
        f"запрос '{tool_name}' зарегистрирован, request_id={request_id}"
    )

    prompt = _build_prompt(initiator_username, tool_name, tool_description)
    sent = await bot.send_message(
        chat_id=chat_id,
        text=prompt,
        reply_markup=build_permission_keyboard(request_id),
        reply_to_message_id=reply_to_message_id,
        parse_mode="HTML",
    )

    try:
        await asyncio.wait_for(request.event.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        state.pop_request(request_id)
        logger.warning(
            f"user_id={initiator_user_id}, chat_id={chat_id}: "
            f"таймаут ожидания решения по '{tool_name}' (request_id={request_id})"
        )
        await sent.edit_text(
            f"<s>{prompt}</s>\n\n⏱ Время вышло. Запрос отклонён.",
            parse_mode="HTML",
            reply_markup=None,
        )
        return False

    state.pop_request(request_id)
    if request.result and request.save_for_session:
        state.grant_for_session(initiator_user_id, tool_name)

    decision = "разрешён" if request.result else "запрещён"
    logger.info(
        f"user_id={initiator_user_id}, chat_id={chat_id}: "
        f"'{tool_name}' {decision} (request_id={request_id}, session={request.save_for_session})"
    )
    return request.result
