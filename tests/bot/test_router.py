from aiogram import Dispatcher

from src.bot.handlers import chat
from src.bot.router import include_routers


class TestIncludeRouters:
    """Сценарии регистрации роутеров в диспетчере."""

    def test_adds_chat_router(self, mocker):
        """Проверяет, что include_routers регистрирует роутер чата в диспетчере."""
        dp = mocker.MagicMock(spec=Dispatcher)

        include_routers(dp)

        dp.include_router.assert_called_once_with(chat.router)
