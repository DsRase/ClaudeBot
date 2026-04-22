import asyncio

import pytest

from src.agent.permissions.state import get_permission_state
from src.bot.adapters.permissionRequester import TelegramPermissionRequester


@pytest.fixture
def fresh_state():
    get_permission_state.cache_clear()
    yield get_permission_state()
    get_permission_state.cache_clear()


@pytest.fixture
def settings_stub(mocker):
    mocker.patch(
        "src.bot.adapters.permissionRequester.get_settings",
    ).return_value.permission_request_timeout = 60
    return None


def _make_bot(mocker):
    bot = mocker.MagicMock()
    sent = mocker.MagicMock()
    sent.edit_text = mocker.AsyncMock()
    bot.send_message = mocker.AsyncMock(return_value=sent)
    return bot, sent


class TestTelegramPermissionRequester:
    """Сценарии TG-реализации PermissionRequester."""

    @pytest.mark.asyncio
    async def test_session_allowed_skips_ui(self, mocker, fresh_state, settings_stub):
        """Если уже разрешено на сессию — UI не показывается, сразу True."""
        fresh_state.grant_for_session(1, "search")
        bot, _ = _make_bot(mocker)

        req = TelegramPermissionRequester(bot=bot, chat_id=10, initiator_user_id=1, initiator_username="u")

        assert await req.request("search", "desc") is True
        bot.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_user_grants_returns_true(self, mocker, fresh_state, settings_stub):
        """Если пользователь нажимает allow (event.set, result=True) — возвращается True."""
        bot, sent = _make_bot(mocker)
        req = TelegramPermissionRequester(bot=bot, chat_id=10, initiator_user_id=1, initiator_username="u")

        async def grant_after_send():
            await asyncio.sleep(0)
            pending = list(fresh_state.pending_requests.values())[0]
            pending.result = True
            pending.event.set()

        async def request_and_grant():
            task = asyncio.create_task(grant_after_send())
            result = await req.request("search", "desc")
            await task
            return result

        result = await request_and_grant()

        assert result is True
        bot.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_user_denies_returns_false(self, mocker, fresh_state, settings_stub):
        """Если пользователь отклонил (result=False) — возвращается False."""
        bot, _ = _make_bot(mocker)
        req = TelegramPermissionRequester(bot=bot, chat_id=10, initiator_user_id=1, initiator_username="u")

        async def deny_after_send():
            await asyncio.sleep(0)
            pending = list(fresh_state.pending_requests.values())[0]
            pending.result = False
            pending.event.set()

        async def run():
            task = asyncio.create_task(deny_after_send())
            result = await req.request("search", "desc")
            await task
            return result

        assert await run() is False

    @pytest.mark.asyncio
    async def test_session_grant_persists(self, mocker, fresh_state, settings_stub):
        """allow + save_for_session=True → следующий запрос той же тулы обходит UI."""
        bot, _ = _make_bot(mocker)
        req = TelegramPermissionRequester(bot=bot, chat_id=10, initiator_user_id=1, initiator_username="u")

        async def grant_session():
            await asyncio.sleep(0)
            pending = list(fresh_state.pending_requests.values())[0]
            pending.result = True
            pending.save_for_session = True
            pending.event.set()

        task = asyncio.create_task(grant_session())
        await req.request("search", "desc")
        await task

        assert fresh_state.is_allowed_in_session(1, "search")

    @pytest.mark.asyncio
    async def test_timeout_returns_false_and_edits_message(self, mocker, fresh_state, settings_stub):
        """По таймауту → False + сообщение редактируется (запись о таймауте)."""
        bot, sent = _make_bot(mocker)
        req = TelegramPermissionRequester(
            bot=bot, chat_id=10, initiator_user_id=1, initiator_username="u", timeout=0
        )

        result = await req.request("search", "desc")

        assert result is False
        sent.edit_text.assert_awaited_once()
