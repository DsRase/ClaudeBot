from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message()
async def echo(message: Message):
    await message.answer(message.text + f"\nYour id is {message.from_user.id}")
