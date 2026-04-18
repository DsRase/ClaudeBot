from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_permission_keyboard(request_id: str) -> InlineKeyboardMarkup:
    """Inline-клавиатура для permission-запроса: разрешить разово / на сессию / запретить."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Разрешить", callback_data=f"perm:{request_id}:allow"),
        InlineKeyboardButton(text="🔁 До конца сессии", callback_data=f"perm:{request_id}:allow_session"),
        InlineKeyboardButton(text="❌ Запретить", callback_data=f"perm:{request_id}:deny"),
    ]])
