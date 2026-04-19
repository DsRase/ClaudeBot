import asyncio
from alembic import command
from alembic.config import Config
from aiogram import Bot, Dispatcher
from src.bot.router import include_routers
from src.config.settings import get_settings


def run_migrations() -> None:
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


async def main():
    settings = get_settings()

    run_migrations()

    dp = Dispatcher()
    include_routers(dp)

    async with Bot(token=settings.telegram_token) as bot:
        await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
