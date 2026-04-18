from aiogram import Dispatcher

from src.bot.handlers import chat, permissions
from src.bot.router import include_routers


class TestIncludeRouters:
    """Сценарии регистрации роутеров в диспетчере."""

    def test_registers_all_routers(self, mocker):
        """Проверяет, что include_routers регистрирует роутеры permissions и chat."""
        dp = mocker.MagicMock(spec=Dispatcher)

        include_routers(dp)

        registered = [c.args[0] for c in dp.include_router.call_args_list]
        assert chat.router in registered, "роутер chat не зарегистрирован"
        assert permissions.router in registered, "роутер permissions не зарегистрирован"

    def test_permissions_router_first(self, mocker):
        """Проверяет, что permissions-роутер подключается раньше chat — иначе /reset_perms перехватит chat."""
        dp = mocker.MagicMock(spec=Dispatcher)

        include_routers(dp)

        order = [c.args[0] for c in dp.include_router.call_args_list]
        assert order.index(permissions.router) < order.index(chat.router), \
            "permissions должен быть зарегистрирован раньше chat-роутера"
