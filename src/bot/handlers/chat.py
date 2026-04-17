from datetime import datetime, timezone

import telegramify_markdown
from aiogram import Router
from aiogram.types import Message

from src.agent.agent import ask
from src.config.messages import BotMessages
from src.config.settings import get_settings
from src.storage import ChatMessage, add_message, get_context
from src.utils.logger.LoggerFactory import LoggerFactory
from src.utils.messager import get_random_message

router = Router()
logger = LoggerFactory.get_logger(__name__)


@router.message()
async def chat(message: Message):
    """Перенаправляет сообщение пользователя в LLM и возвращает ответ. Делается только в случае если пользовать в списке premium."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    settings = get_settings()

    logger.info(f"Получено сообщение от user_id={user_id}, chat_id={chat_id}")

    is_premium = False

    # Если пользователь в списке премиума: ставим is_premium true
    # Если пользователь не в премиум списке и не в обычном списке, то реджектим сообщение
    if user_id in settings.premium_user_ids:
        is_premium = True
    elif user_id not in settings.base_user_ids:
        logger.warning(f"Доступ отклонён для user_id={user_id}")
        await message.answer(get_random_message(BotMessages.NOT_PREMIUM))
        return

    user_msg = ChatMessage(
        role="user",
        user_id=user_id,
        content=message.text,
        timestamp=int(message.date.timestamp()),
    )
    await add_message(chat_id, user_msg)
    logger.debug(f"chat_id={chat_id}: сообщение пользователя сохранено в Redis")

    history = await get_context(chat_id)
    logger.debug(f"chat_id={chat_id}: получен контекст ({len(history)} сообщений)")

    think_msg = await message.answer(get_random_message(BotMessages.WAIT_FOR_RESPONSE))

    answer = await ask(history, is_premium)

    assistant_msg = ChatMessage(
        role="assistant",
        user_id=None,
        content=answer,
        timestamp=int(datetime.now(timezone.utc).timestamp()),
    )
    await add_message(chat_id, assistant_msg)
    logger.debug(f"chat_id={chat_id}: ответ ассистента сохранён в Redis")

    text, entities = telegramify_markdown.convert(answer)
    chunk_size = 4096  # ограничение телеграма на длину сообщения
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    for chunk in chunks:
        await message.answer(chunk, entities=entities)

    await think_msg.delete()
    logger.info(f"Ответ отправлен user_id={user_id}, chat_id={chat_id}")
