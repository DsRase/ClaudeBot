import asyncio

from aiogram.types import Message

from src.bot.utils import add_think_load
from src.config import BotMessages
from src.utils.logger.LoggerFactory import LoggerFactory
from src.utils.messager import get_random_message

logger = LoggerFactory.get_logger(__name__)


class TelegramThinkingIndicator:
    """Telegram-реализация ThinkingIndicator: отправляет think-msg + анимирует, удаляет на выходе."""

    def __init__(self, message: Message):
        self._message = message
        self._is_private = message.chat.type == "private"
        self._think_msg: Message | None = None
        self._task: asyncio.Task | None = None

    async def __aenter__(self) -> "TelegramThinkingIndicator":
        respond = self._message.answer if self._is_private else self._message.reply
        self._think_msg = await respond(get_random_message(BotMessages.WAIT_FOR_RESPONSE))
        self._task = asyncio.create_task(add_think_load(self._think_msg))
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        if self._think_msg is not None:
            try:
                await self._think_msg.delete()
            except Exception:
                logger.warning(f"chat_id={self._message.chat.id}: не удалось удалить think_msg")
