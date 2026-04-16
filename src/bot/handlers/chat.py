from aiogram import Router
from aiogram.types import Message

from src.agent.agent import ask
from src.config.messages import BotMessages
from src.config.settings import get_settings
from src.utils.logger.LoggerFactory import LoggerFactory

router = Router()
logger = LoggerFactory.get_logger(__name__)


@router.message()
async def chat(message: Message):
    """Перенаправляет сообщение пользователя в LLM и возвращает ответ. Делается только в случае если пользовать в списке premium."""
    user_id = message.from_user.id
    settings = get_settings()

    logger.info(f"Получено сообщение от user_id={user_id}")

    if user_id not in settings.premium_user_ids:
        logger.warning(f"Доступ отклонён для user_id={user_id} (не в premium-списке)")
        await message.answer(BotMessages.NOT_PREMIUM)
        return

    logger.debug(f"User {user_id} в premium-списке, отправляем запрос в агент")
    answer = await ask(message.text)
    await message.answer(answer)
    logger.info(f"Ответ отправлен user_id={user_id}")
