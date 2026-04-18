from datetime import datetime, timezone

import telegramify_markdown
from aiogram import Bot, Router
from aiogram.types import Message, MessageEntity

from src.agent.agent import ask
from src.agent.langTools import make_chat_scoped_tools
from src.bot.permissions import request_permission
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

    to_username = None
    reply_id = None
    if message.reply_to_message:
        reply_id = message.reply_to_message.message_id
        if message.reply_to_message.from_user:
            to_username = message.reply_to_message.from_user.username

    user_msg = ChatMessage(
        role="user",
        id=message.message_id,
        ts=int(message.date.timestamp()),
        from_username=message.from_user.username,
        fname=message.from_user.first_name,
        lname=message.from_user.last_name,
        to_username=to_username,
        reply_id=reply_id,
        text=message.text,
        user_id=user_id,
    )
    await add_message(chat_id, user_msg)
    logger.debug(f"user_id={user_id}, chat_id={chat_id}: сообщение пользователя сохранено в Redis")

    if not await _is_triggered(message, bot):
        logger.debug(f"user_id={user_id}, chat_id={chat_id}: триггер не сработал, пропускаем ответ")
        return

    # В группе отвечаем реплаем на сообщение, в личке - обычным answer
    respond = message.answer if is_private else message.reply

    settings = get_settings()
    if user_id not in settings.access_user_ids:
        logger.warning(f"user_id={user_id}, chat_id={chat_id}: доступ отклонён")
        await respond(get_random_message(BotMessages.NO_ACCESS))
        return

    history = await get_context(chat_id)
    logger.debug(f"user_id={user_id}, chat_id={chat_id}: получен контекст ({len(history)} сообщений)")

    think_msg = await respond(get_random_message(BotMessages.WAIT_FOR_RESPONSE))

    async def permission_requester(tool_name: str, tool_description: str) -> bool:
        return await request_permission(
            bot=bot,
            chat_id=chat_id,
            initiator_user_id=user_id,
            initiator_username=message.from_user.username,
            tool_name=tool_name,
            tool_description=tool_description,
            reply_to_message_id=None if is_private else message.message_id,
        )

    answer = await ask(
        history,
        permission_requester=permission_requester,
        extra_tools=make_chat_scoped_tools(chat_id),
    )

    text, entities = telegramify_markdown.convert(answer)
    entities = [MessageEntity(**entity.to_dict()) for entity in entities]
    chunk_size = 4096  # ограничение телеграма на длину сообщения
    chunks = split_text_with_entities(text, entities, chunk_size)

    first_sent = None
    try:
        for i, (chunk_text, chunk_entities) in enumerate(chunks):
            # Реплаем отправляем только первый чанк, остальные — обычными сообщениями
            send = respond if i == 0 else message.answer
            sent = await send(chunk_text, entities=chunk_entities)
            if i == 0:
                first_sent = sent
    except Exception:
        logger.exception(f"user_id={user_id}, chat_id={chat_id}: не удалось отправить ответ юзеру")
        raise
    finally:
        try:
            await think_msg.delete()
        except Exception:
            logger.warning(f"user_id={user_id}, chat_id={chat_id}: не удалось удалить think_msg")

    assistant_msg = ChatMessage(
        role="assistant",
        id=first_sent.message_id,
        ts=int(datetime.now(timezone.utc).timestamp()),
        from_username="Пипиндр",
        to_username=message.from_user.username,
        reply_id=message.message_id,
        text=answer,
    )
    await add_message(chat_id, assistant_msg)
    logger.debug(f"user_id={user_id}, chat_id={chat_id}: ответ ассистента сохранён в Redis")
    logger.info(f"user_id={user_id}, chat_id={chat_id}: ответ отправлен")
