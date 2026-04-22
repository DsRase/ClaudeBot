import asyncio
import secrets
from html import escape

from aiogram import Bot

from src.agent.permissions import PendingRequest, get_permission_state
from src.bot.markups import build_permission_keyboard
from src.config import get_settings
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def _build_prompt(initiator_username: str | None, tool_name: str, tool_description: str) -> str:
    """Формирует HTML-текст сообщения с описанием запрашиваемого действия."""
    who = f"@{escape(initiator_username)}" if initiator_username else "инициатор"
    return (
        f"{who}, агент хочет вызвать инструмент <code>{escape(tool_name)}</code>.\n"
        f"{escape(tool_description)}\n\n"
        f"Только ты можешь решить."
    )


class TelegramPermissionRequester:
    """Telegram-реализация PermissionRequester: inline-клавиатура + ожидание клика инициатора."""

    def __init__(
        self,
        bot: Bot,
        chat_id: int,
        initiator_user_id: int,
        initiator_username: str | None,
        reply_to_message_id: int | None = None,
        timeout: int | None = None,
    ):
        self._bot = bot
        self._chat_id = chat_id
        self._user_id = initiator_user_id
        self._username = initiator_username
        self._reply_to = reply_to_message_id
        self._timeout = timeout if timeout is not None else get_settings().permission_request_timeout

    async def request(self, tool_name: str, description: str) -> bool:
        state = get_permission_state()

        if state.is_allowed_in_session(self._user_id, tool_name):
            logger.info(
                f"user_id={self._user_id}, chat_id={self._chat_id}: "
                f"'{tool_name}' уже разрешён до конца сессии, пропускаем UI"
            )
            return True

        request_id = secrets.token_urlsafe(8)
        pending = PendingRequest(
            initiator_user_id=self._user_id,
            initiator_username=self._username,
            tool_name=tool_name,
        )
        state.register_request(request_id, pending)
        logger.info(
            f"user_id={self._user_id}, chat_id={self._chat_id}: "
            f"запрос '{tool_name}' зарегистрирован, request_id={request_id}"
        )

        prompt = _build_prompt(self._username, tool_name, description)
        sent = await self._bot.send_message(
            chat_id=self._chat_id,
            text=prompt,
            reply_markup=build_permission_keyboard(request_id),
            reply_to_message_id=self._reply_to,
            parse_mode="HTML",
        )

        try:
            await asyncio.wait_for(pending.event.wait(), timeout=self._timeout)
        except asyncio.TimeoutError:
            state.pop_request(request_id)
            logger.warning(
                f"user_id={self._user_id}, chat_id={self._chat_id}: "
                f"таймаут ожидания решения по '{tool_name}' (request_id={request_id})"
            )
            await sent.edit_text(
                f"<s>{prompt}</s>\n\n⏱ Время вышло. Запрос отклонён.",
                parse_mode="HTML",
                reply_markup=None,
            )
            return False

        state.pop_request(request_id)
        if pending.result and pending.save_for_session:
            state.grant_for_session(self._user_id, tool_name)

        decision = "разрешён" if pending.result else "запрещён"
        logger.info(
            f"user_id={self._user_id}, chat_id={self._chat_id}: "
            f"'{tool_name}' {decision} (request_id={request_id}, session={pending.save_for_session})"
        )
        return pending.result
