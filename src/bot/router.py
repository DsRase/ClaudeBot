from aiogram import Dispatcher
from src.bot.handlers import chat, permissions
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def include_routers(dp: Dispatcher):
    """Добавляет в диспетчер роутеры со всех хендлеров."""
    logger.debug("Включение роутеров в диспетчер запустилось.")
    dp.include_router(permissions.router)
    dp.include_router(chat.router)
    logger.debug("Включение роутеров в диспетчер закончилось.")
