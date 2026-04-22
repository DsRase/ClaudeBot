from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from src.agent.permissions import reset_session_permissions
from src.bot.permissions import admin_required
from src.bot.markups import build_models_keyboard
from src.config import BotMessages
from src.config.settings import reload_settings

from src.storage.sqlite import get_user_model, set_user_model

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

@router.message(Command("change_model"))
async def change_model(message: Message):
    """Меняет модель для использования для конкретного пользователя"""
    user_id = message.from_user.id
    logger.debug(f"chat_id: {message.chat.id}. user_id: {user_id}. Прожал /change_model")

    user_model = await get_user_model(user_id)
    await message.answer(f"Выбранная модель: {user_model}\n\n"
                         f"Чтобы сменить её, нажми на одну из доступных кнопок ниже."
                         f"\nДля отмены есть отдельная кнопка",
                         reply_markup=build_models_keyboard(user_id))

@router.callback_query(F.data.startswith("model:"))
async def change_model_callback(callback: CallbackQuery):
    """Изменяет модель пользователя на ту, что он выбрал"""
    _, init_user_id, model = callback.data.split(":", 2) # инициатор
    click_user_id = callback.from_user.id

    logger.debug(f"chat_id: {callback.message.chat.id}. user_id: {click_user_id}. Прожал нажал на кнопку для смены модели.")

    if int(init_user_id) != click_user_id:
        logger.debug(
            f"chat_id: {callback.message.chat.id}. user_id: {click_user_id}. Не инициатор, реджектим.")
        await callback.answer(f"Не тебе это решать)", show_alert=True)
        return

    await set_user_model(int(init_user_id), model)

    logger.debug(
        f"chat_id: {callback.message.chat.id}. user_id: {click_user_id}. Модель успешно сменена на: {model}")

    await callback.message.edit_text(f"Теперь выбранная модель: {model}", reply_markup=None)

@router.callback_query(F.data.startswith("back"))
async def cancel_model_callback(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(e)
        await callback.message.answer("Короче, какая-то бага случилась, удалить сообщение не вышло...\nНо ты не парься, я всё отменил)")

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