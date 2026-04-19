from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.config import get_settings

from src.bot.markups import build_back_btn


def build_models_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Inline-клавиатура для смены используемой модели."""
    settings = get_settings()
    models = settings.available_models

    keyboard = []

    for model in models:
        keyboard.append([InlineKeyboardButton(text=model, callback_data=f"model:{user_id}:{model}")])

    keyboard.append(build_back_btn())

    return InlineKeyboardMarkup(inline_keyboard=keyboard)