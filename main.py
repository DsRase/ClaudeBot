import asyncio
from aiogram import Bot, Dispatcher
from src.bot.router import include_routers
from src.config.settings import get_settings


async def main():
    settings = get_settings()
    dp = Dispatcher()
    include_routers(dp)
    async with Bot(token=settings.telegram_token) as bot:
        await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
