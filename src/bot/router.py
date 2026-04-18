from aiogram import Dispatcher
from src.bot.handlers import *
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def include_routers(dp: Dispatcher):
    """Добавляет в диспетчер роутеры со всех хендлеров."""
    logger.debug("Включение роутеров в диспетчер запустилось.")
    dp.include_router(permissionsRouter)
    dp.include_router(commandsRouter)
    dp.include_router(chatRouter)
    logger.debug("Включение роутеров в диспетчер закончилось.")
