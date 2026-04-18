from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from src.config import BotMessages

from src.utils.logger import LoggerFactory
from src.utils.messager import get_random_message

router = Router()
logger = LoggerFactory.get_logger(__name__)

@router.message(Command("start"))
async def start_command(message: Message):
    """Стартовое сообщение. Полезно в личке."""
    logger.debug(f"chat_id: {message.chat.id}. user_id: {message.from_user.id}. Прожал /start")
    await message.answer(get_random_message(BotMessages.START_MESSAGE))

@router.message(Command("help"))
async def help_command(message: Message):
    """Че за бот че умеет."""
    logger.debug(f"chat_id: {message.chat.id}. user_id: {message.from_user.id}. Прожал /help")
    await message.answer(get_random_message(BotMessages.HELP_MESSAGE))

@router.message(Command("getid"))
async def getid_command(message: Message):
    """Возвращает ID юзера"""
    logger.debug(f"chat_id: {message.chat.id}. user_id: {message.from_user.id}. Прожал /getid")
    await message.answer(f"Твой ID: {message.from_user.id}")