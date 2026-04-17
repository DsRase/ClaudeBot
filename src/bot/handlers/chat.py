from datetime import datetime, timezone

import telegramify_markdown
from aiogram import Bot, Router
from aiogram.types import Message, MessageEntity

from src.agent.agent import ask
from src.config import BotMessages
from src.config.settings import get_settings
from src.storage import ChatMessage, add_message, get_context
from src.utils.logger.LoggerFactory import LoggerFactory
from src.utils.messager import get_random_message, split_text_with_entities

router = Router()
logger = LoggerFactory.get_logger(__name__)


async def _is_triggered(message: Message, bot: Bot) -> bool:
    """В личке всегда триггер; в группе — только при @упоминании или ответе на сообщение бота."""
    if message.chat.type == "private":
        return True
    bot_info = await bot.me()
    mentioned = f"@{bot_info.username}" in message.text
    replied_to_bot = (
        message.reply_to_message is not None
        and message.reply_to_message.from_user is not None
        and message.reply_to_message.from_user.id == bot_info.id
    )
    return mentioned or replied_to_bot


@router.message()
async def chat(message: Message, bot: Bot):
    """Сохраняет любое текстовое сообщение в контекст чата и отвечает, если триггер сработал."""
    # Игнорируем не-текстовые сообщения и сообщения от ботов (включая собственные)
    if not message.text or message.from_user is None or message.from_user.is_bot:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    is_private = message.chat.type == "private"

    logger.info(f"user_id={user_id}, chat_id={chat_id}, type={message.chat.type}: получено сообщение")

    reply_to_username = None
    if message.reply_to_message and message.reply_to_message.from_user:
        reply_to_username = message.reply_to_message.from_user.username

    user_msg = ChatMessage(
        role="user",
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        reply_to_username=reply_to_username,
        content=message.text,
        timestamp=int(message.date.timestamp()),
    )
    await add_message(chat_id, user_msg)
    logger.debug(f"user_id={user_id}, chat_id={chat_id}: сообщение пользователя сохранено в Redis")

    if not await _is_triggered(message, bot):
        logger.debug(f"user_id={user_id}, chat_id={chat_id}: триггер не сработал, пропускаем ответ")
        return

    # В группе отвечаем реплаем на сообщение, в личке - обычным answer
    respond = message.answer if is_private else message.reply

    settings = get_settings()
    is_premium = False
    if user_id in settings.premium_user_ids:
        is_premium = True
    elif user_id not in settings.base_user_ids:
        logger.warning(f"user_id={user_id}, chat_id={chat_id}: доступ отклонён")
        await respond(get_random_message(BotMessages.NOT_PREMIUM))
        return

    history = await get_context(chat_id)
    logger.debug(f"user_id={user_id}, chat_id={chat_id}: получен контекст ({len(history)} сообщений)")

    think_msg = await respond(get_random_message(BotMessages.WAIT_FOR_RESPONSE))

    answer = await ask(history, is_premium)

    assistant_msg = ChatMessage(
        role="assistant",
        user_id=None,
        content=answer,
        timestamp=int(datetime.now(timezone.utc).timestamp()),
    )
    await add_message(chat_id, assistant_msg)
    logger.debug(f"user_id={user_id}, chat_id={chat_id}: ответ ассистента сохранён в Redis")

    text, entities = telegramify_markdown.convert(answer)
    entities = [MessageEntity(**entity.to_dict()) for entity in entities]
    chunk_size = 4096  # ограничение телеграма на длину сообщения

    chunks = split_text_with_entities(text, entities, chunk_size)
    for i, (chunk_text, chunk_entities) in enumerate(chunks):
        # Реплаем отправляем только первый чанк, остальные — обычными сообщениями
        send = respond if i == 0 else message.answer
        await send(chunk_text, entities=chunk_entities)

    await think_msg.delete()
    logger.info(f"user_id={user_id}, chat_id={chat_id}: ответ отправлен")
