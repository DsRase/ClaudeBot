import asyncio

import pytest

from src.bot.permissions.requestPermission import request_permission
from src.bot.permissions.state import PendingRequest, get_permission_state


@pytest.fixture(autouse=True)
def fresh_state():
    """Чистит синглтон permission-стейта между тестами."""
    state = get_permission_state()
    state.session_permissions.clear()
    state.pending_requests.clear()
    yield
    state.session_permissions.clear()
    state.pending_requests.clear()


@pytest.fixture
def bot(mocker):
    sent_msg = mocker.AsyncMock()
    sent_msg.edit_text = mocker.AsyncMock()
    b = mocker.MagicMock()
    b.send_message = mocker.AsyncMock(return_value=sent_msg)
    return b


class TestRequestPermission:
    """Сценарии запроса разрешения у пользователя."""

    @pytest.mark.asyncio
    async def test_session_cached_skips_ui(self, bot):
        """Если тула уже разрешена в сессии, UI не показывается, возвращается True сразу."""
        get_permission_state().grant_for_session(111, "search")

        result = await request_permission(
            bot=bot, chat_id=999, initiator_user_id=111,
            initiator_username="vasya", tool_name="search",
            tool_description="ищет в гугле",
        )

        assert result is True, "session-кеш должен возвращать True"
        bot.send_message.assert_not_awaited(), "UI не должен показываться, если есть session-разрешение"

    @pytest.mark.asyncio
    async def test_allow_resolves_with_true(self, bot, mocker):
        """Если инициатор кликнул allow, функция возвращает True и не сохраняет в session."""
        async def resolve():
            await asyncio.sleep(0)
            req = next(iter(get_permission_state().pending_requests.values()))
            req.result = True
            req.save_for_session = False
            req.event.set()

        asyncio.create_task(resolve())
        result = await request_permission(
            bot=bot, chat_id=999, initiator_user_id=111,
            initiator_username="vasya", tool_name="search",
            tool_description="ищет в гугле",
        )

        assert result is True, "allow должен возвращать True"
        assert not get_permission_state().is_allowed_in_session(111, "search"), \
            "разовое разрешение не должно попадать в session-кеш"

    @pytest.mark.asyncio
    async def test_allow_session_caches(self, bot):
        """Если инициатор выбрал save_for_session, тула попадает в session-кеш."""
        async def resolve():
            await asyncio.sleep(0)
            req = next(iter(get_permission_state().pending_requests.values()))
            req.result = True
            req.save_for_session = True
            req.event.set()

        asyncio.create_task(resolve())
        result = await request_permission(
            bot=bot, chat_id=999, initiator_user_id=111,
            initiator_username="vasya", tool_name="search",
            tool_description="ищет в гугле",
        )

        assert result is True
        assert get_permission_state().is_allowed_in_session(111, "search"), \
            "при save_for_session тула должна попасть в session-кеш"

    @pytest.mark.asyncio
    async def test_deny_resolves_with_false(self, bot):
        """Если инициатор кликнул deny, функция возвращает False."""
        async def resolve():
            await asyncio.sleep(0)
            req = next(iter(get_permission_state().pending_requests.values()))
            req.result = False
            req.event.set()

        asyncio.create_task(resolve())
        result = await request_permission(
            bot=bot, chat_id=999, initiator_user_id=111,
            initiator_username="vasya", tool_name="search",
            tool_description="ищет в гугле",
        )

        assert result is False, "deny должен возвращать False"

    @pytest.mark.asyncio
    async def test_timeout_returns_false_and_strikes_message(self, bot):
        """При таймауте возвращается False, а сообщение редачится с зачёркиванием оригинала."""
        result = await request_permission(
            bot=bot, chat_id=999, initiator_user_id=111,
            initiator_username="vasya", tool_name="search",
            tool_description="ищет в гугле",
            timeout=0,
        )

        assert result is False
        sent = bot.send_message.return_value
        sent.edit_text.assert_awaited_once()
        edited_text = sent.edit_text.await_args.args[0]
        assert "<s>" in edited_text and "</s>" in edited_text, \
            "оригинал должен быть зачёркнут, а не заменён полностью"
        assert "Время вышло" in edited_text, "должна быть пометка о таймауте"

    @pytest.mark.asyncio
    async def test_timeout_clears_pending_request(self, bot):
        """После таймаута запрос удаляется из реестра pending."""
        await request_permission(
            bot=bot, chat_id=999, initiator_user_id=111,
            initiator_username="vasya", tool_name="search",
            tool_description="...",
            timeout=0,
        )

        assert not get_permission_state().pending_requests, \
            "pending-запрос должен быть удалён после таймаута"

    @pytest.mark.asyncio
    async def test_keyboard_carries_request_id(self, bot):
        """Проверяет, что кнопки в клавиатуре содержат сгенерированный request_id."""
        async def resolve():
            await asyncio.sleep(0)
            req_id = next(iter(get_permission_state().pending_requests.keys()))
            req = get_permission_state().get_request(req_id)
            req.event.set()
            return req_id

        task = asyncio.create_task(resolve())
        await request_permission(
            bot=bot, chat_id=999, initiator_user_id=111,
            initiator_username="vasya", tool_name="search",
            tool_description="...",
        )
        req_id = await task

        keyboard = bot.send_message.await_args.kwargs["reply_markup"]
        all_callback_data = [b.callback_data for row in keyboard.inline_keyboard for b in row]
        assert all(req_id in cd for cd in all_callback_data), \
            f"request_id={req_id} не попал во все callback_data: {all_callback_data}"
