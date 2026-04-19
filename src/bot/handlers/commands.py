from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.permissions import admin_required, reset_session_permissions
from src.config import BotMessages
from src.config.settings import reload_settings

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

@router.message(Command("update_conf"))
@admin_required
async def update_conf_command(message: Message):
    """Перечитывает config.yaml и сбрасывает кэш настроек."""
    settings = reload_settings()
    logger.info(f"user_id={message.from_user.id}: конфиг перезагружен")
    await message.answer(f"Конфиг обновлён. Дефолтная модель: {settings.default_model}, доступных юзеров: {len(settings.access_user_ids)}")


@router.message(Command("reset_perms"))
async def on_reset_perms(message: Message):
    """Сбрасывает все session-разрешения у пользователя, выполнившего команду."""
    if message.from_user is None:
        return
    cleared = reset_session_permissions(message.from_user.id)
    if cleared:
        await message.reply(f"Сброшено разрешений: {cleared}")
    else:
        await message.reply("Разрешений на сессию у тебя и не было.")