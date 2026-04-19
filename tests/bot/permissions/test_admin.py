import pytest

from src.bot.permissions.admin import admin_required
from src.config import BotMessages


@pytest.fixture
def message(mocker):
    msg = mocker.MagicMock()
    msg.from_user.id = 111
    msg.answer = mocker.AsyncMock()
    return msg


@pytest.fixture
def admin_settings(mocker):
    mocker.patch(
        "src.bot.permissions.admin.get_settings",
    ).return_value.configure_mock(admin_user_ids=[111])


@pytest.fixture
def non_admin_settings(mocker):
    mocker.patch(
        "src.bot.permissions.admin.get_settings",
    ).return_value.configure_mock(admin_user_ids=[999])


class TestAdminRequired:
    """Сценарии декоратора @admin_required."""

    @pytest.mark.asyncio
    async def test_admin_passes_through(self, message, admin_settings):
        """Юзер из admin_user_ids — оригинальный хендлер вызывается."""
        called = []

        @admin_required
        async def handler(msg):
            called.append(True)

        await handler(message)

        assert called, "хендлер должен быть вызван для админа"
        message.answer.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_admin_rejected(self, message, non_admin_settings):
        """Юзер не из admin_user_ids — хендлер не вызывается, отправляется NOT_ADMIN."""
        called = []

        @admin_required
        async def handler(msg):
            called.append(True)

        await handler(message)

        assert not called, "хендлер не должен вызываться для не-админа"
        message.answer.assert_awaited_once()
        sent_text = message.answer.await_args.args[0]
        assert sent_text in BotMessages.NOT_ADMIN, \
            f"отправлен не текст из NOT_ADMIN: {sent_text!r}"

    @pytest.mark.asyncio
    async def test_no_from_user_rejected(self, message, non_admin_settings):
        """Если from_user is None — хендлер не вызывается."""
        message.from_user = None
        called = []

        @admin_required
        async def handler(msg):
            called.append(True)

        await handler(message)

        assert not called, "хендлер не должен вызываться без from_user"

    @pytest.mark.asyncio
    async def test_handler_return_value_preserved(self, message, admin_settings):
        """Декоратор прозрачно пробрасывает возвращаемое значение хендлера."""
        @admin_required
        async def handler(msg):
            return "результат"

        result = await handler(message)

        assert result == "результат", "декоратор должен возвращать то, что вернул хендлер"

    @pytest.mark.asyncio
    async def test_extra_args_passed_through(self, message, admin_settings):
        """Декоратор пробрасывает дополнительные args и kwargs в хендлер."""
        received = []

        @admin_required
        async def handler(msg, bot, extra=None):
            received.append((bot, extra))

        await handler(message, "bot_obj", extra="kw")

        assert received == [("bot_obj", "kw")], \
            f"args/kwargs не пробросились: {received}"
