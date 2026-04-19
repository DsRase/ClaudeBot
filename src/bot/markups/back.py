from typing import List

from aiogram.types import InlineKeyboardButton

def build_back_btn() -> List[InlineKeyboardButton]:
    return [InlineKeyboardButton(text="Отмена", callback_data=f"back")]