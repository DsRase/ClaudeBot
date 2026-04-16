import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from src.bot.router import include_routers
from src.config.settings import get_settings


async def main():
    settings = get_settings()

    dp = Dispatcher()
    include_routers(dp)

    # TODO: Добавить parse_mode с MARKDOWN_V2. Сейчас проблема в том, что LLM возвращает все значения и не парсит их так, как телеграму надо, из-за чего
    #       сообщение не распарсится а API телеги вернёт ошибку. Поэтому пока без парсинга
    properties = DefaultBotProperties(
        # parse_mode=ParseMode.MARKDOWN_V2,
    )
    async with Bot(token=settings.telegram_token, default=properties) as bot:
        await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
