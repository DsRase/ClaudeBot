import telegramify_markdown
from aiogram.types import Message, MessageEntity

from src.bot.utils import split_text_with_entities
from src.config import BotMessages
from src.utils.logger.LoggerFactory import LoggerFactory
from src.utils.messager import get_random_message

logger = LoggerFactory.get_logger(__name__)

_TG_CHUNK_SIZE = 4096

_ERROR_TEXTS = {
    "no_access": BotMessages.NO_ACCESS,
    "llm_failed": BotMessages.LLM_ERROR,
}


class TelegramResponseChannel:
    """Telegram-реализация ResponseChannel: markdown→entities, разбивка на чанки, reply/answer."""

    def __init__(self, message: Message):
        self._message = message
        self._is_private = message.chat.type == "private"

    async def send_response(self, text: str) -> int | None:
        rendered, entities = telegramify_markdown.convert(text)
        entities = [MessageEntity(**e.to_dict()) for e in entities]
        chunks = split_text_with_entities(rendered, entities, _TG_CHUNK_SIZE)

        first_id: int | None = None
        for i, (chunk_text, chunk_entities) in enumerate(chunks):
            send = self._message.reply if (i == 0 and not self._is_private) else self._message.answer
            try:
                sent = await send(chunk_text, entities=chunk_entities)
            except Exception:
                logger.exception(f"chat_id={self._message.chat.id}: не удалось отправить ответ юзеру")
                raise
            if i == 0:
                first_id = sent.message_id
        return first_id

    async def send_error(self, reason: str) -> None:
        texts = _ERROR_TEXTS.get(reason)
        if texts is None:
            logger.warning(f"неизвестный код ошибки: {reason!r}")
            return
        respond = self._message.answer if self._is_private else self._message.reply
        await respond(get_random_message(texts))
