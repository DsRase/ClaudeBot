from aiogram import Router
from aiogram.types import Message

from src.agent.agent import ask
from src.config.messages import BotMessages
from src.config.settings import get_settings
from src.utils.logger.LoggerFactory import LoggerFactory
from src.utils.messager import get_random_message

router = Router()
logger = LoggerFactory.get_logger(__name__)


@router.message()
async def chat(message: Message):
    """Перенаправляет сообщение пользователя в LLM и возвращает ответ. Делается только в случае если пользовать в списке premium."""
    user_id = message.from_user.id
    settings = get_settings()

    logger.info(f"Получено сообщение от user_id={user_id}")

    is_premium = False

    # Если пользователь в списке премиума: ставим is_premium true
    # Если пользователь не в премиум списке и не в обычном списке, то реджектим сообщение
    if user_id in settings.premium_user_ids:
        is_premium = True
    elif user_id not in settings.base_user_ids:
        logger.warning(f"Доступ отклонён для user_id={user_id} (не в premium-списке)")
        await message.answer(get_random_message(BotMessages.NOT_PREMIUM))
        return

    logger.debug(f"User {user_id} в premium-списке, отправляем запрос в агент")
    think_msg_id = await message.answer(get_random_message(BotMessages.WAIT_FOR_RESPONSE))

    answer = await ask(message.text, is_premium)

    chunk_size = 4096  # ограничение телеграма на длину сообщения
    chunks = [answer[i:i + chunk_size] for i in range(0, len(answer), chunk_size)]
    for chunk in chunks:
        await message.answer(chunk)

    await think_msg_id.delete()
    logger.info(f"Ответ отправлен user_id={user_id}")
