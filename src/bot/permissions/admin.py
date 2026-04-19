from functools import wraps

from aiogram.types import Message

from src.config import BotMessages
from src.config.settings import get_settings
from src.utils.messager import get_random_message


def admin_required(handler):
    """Декоратор для админских команд. Если юзер не в admin_user_ids — отшивает с NOT_ADMIN."""
    @wraps(handler)
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user is None or message.from_user.id not in get_settings().admin_user_ids:
            await message.answer(get_random_message(BotMessages.NOT_ADMIN))
            return
        return await handler(message, *args, **kwargs)
    return wrapper
