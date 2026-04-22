from aiogram import Bot, Router
from aiogram.types import Message

from src.agent.dto import IncomingMessage
from src.agent.service import record_message, respond
from src.bot.adapters import (
    TelegramPermissionRequester,
    TelegramResponseChannel,
    TelegramThinkingIndicator,
)
from src.utils.logger.LoggerFactory import LoggerFactory
from src.utils.metrics import bot_messages_total

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


def _to_incoming(message: Message) -> IncomingMessage:
    reply_to_msg_id = None
    reply_to_username = None
    if message.reply_to_message:
        reply_to_msg_id = message.reply_to_message.message_id
        if message.reply_to_message.from_user:
            reply_to_username = message.reply_to_message.from_user.username
    return IncomingMessage(
        text=message.text,
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        platform_msg_id=message.message_id,
        ts=int(message.date.timestamp()),
        username=message.from_user.username,
        fname=message.from_user.first_name,
        lname=message.from_user.last_name,
        reply_to_msg_id=reply_to_msg_id,
        reply_to_username=reply_to_username,
    )


@router.message()
async def chat(message: Message, bot: Bot):
    """Сохраняет любое текстовое сообщение в контекст чата и отвечает, если триггер сработал."""
    if not message.text or message.from_user is None or message.from_user.is_bot:
        return

    incoming = _to_incoming(message)
    is_private = message.chat.type == "private"

    logger.info(
        f"user_id={incoming.user_id}, chat_id={incoming.chat_id}, "
        f"type={message.chat.type}: получено сообщение"
    )

    if not await _is_triggered(message, bot):
        await record_message(incoming)
        bot_messages_total.labels(status="ignored").inc()
        return

    response = TelegramResponseChannel(message)
    permissions = TelegramPermissionRequester(
        bot=bot,
        chat_id=incoming.chat_id,
        initiator_user_id=incoming.user_id,
        initiator_username=incoming.username,
        reply_to_message_id=None if is_private else message.message_id,
    )
    thinking = TelegramThinkingIndicator(message)

    await respond(incoming, response, permissions, thinking)
