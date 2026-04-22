import pytest

from src.agent.permissions.state import PendingRequest, get_permission_state
from src.bot.handlers.permissions import on_permission_click


def _callback(mocker, data, user_id=1):
    cb = mocker.MagicMock()
    cb.data = data
    cb.from_user.id = user_id
    cb.message.html_text = "old"
    cb.message.text = "old"
    cb.message.edit_text = mocker.AsyncMock()
    cb.answer = mocker.AsyncMock()
    return cb


@pytest.fixture
def fresh_state():
    get_permission_state.cache_clear()
    yield get_permission_state()
    get_permission_state.cache_clear()


class TestOnPermissionClick:
    """callback_query хендлер для perm: кнопок."""

    @pytest.mark.asyncio
    async def test_unknown_request_answers_outdated(self, mocker, fresh_state):
        """Если request_id не зарегистрирован — answer + не редактируем сообщение."""
        cb = _callback(mocker, "perm:unknown:allow")

        await on_permission_click(cb)

        cb.answer.assert_awaited_once()
        cb.message.edit_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_initiator_rejected(self, mocker, fresh_state):
        """Не инициатор — alert, event.set не зовётся."""
        req = PendingRequest(initiator_user_id=1, initiator_username="u", tool_name="t")
        fresh_state.register_request("rid", req)
        cb = _callback(mocker, "perm:rid:allow", user_id=999)

        await on_permission_click(cb)

        assert not req.event.is_set()
        cb.answer.assert_awaited_once()
        _, kwargs = cb.answer.await_args
        assert kwargs.get("show_alert") is True

    @pytest.mark.asyncio
    async def test_allow_sets_result_true(self, mocker, fresh_state):
        """Инициатор жмёт allow → result=True, save_for_session=False, event.set."""
        req = PendingRequest(initiator_user_id=1, initiator_username="u", tool_name="t")
        fresh_state.register_request("rid", req)
        cb = _callback(mocker, "perm:rid:allow", user_id=1)

        await on_permission_click(cb)

        assert req.result is True
        assert req.save_for_session is False
        assert req.event.is_set()

    @pytest.mark.asyncio
    async def test_allow_session_sets_save_true(self, mocker, fresh_state):
        """allow_session → save_for_session=True."""
        req = PendingRequest(initiator_user_id=1, initiator_username="u", tool_name="t")
        fresh_state.register_request("rid", req)
        cb = _callback(mocker, "perm:rid:allow_session", user_id=1)

        await on_permission_click(cb)

        assert req.result is True
        assert req.save_for_session is True

    @pytest.mark.asyncio
    async def test_deny_sets_result_false(self, mocker, fresh_state):
        """deny → result=False, event.set."""
        req = PendingRequest(initiator_user_id=1, initiator_username="u", tool_name="t")
        fresh_state.register_request("rid", req)
        cb = _callback(mocker, "perm:rid:deny", user_id=1)

        await on_permission_click(cb)

        assert req.result is False
        assert req.event.is_set()

    @pytest.mark.asyncio
    async def test_unknown_action_ignored(self, mocker, fresh_state):
        """Неизвестное действие не меняет state."""
        req = PendingRequest(initiator_user_id=1, initiator_username="u", tool_name="t")
        fresh_state.register_request("rid", req)
        cb = _callback(mocker, "perm:rid:wat", user_id=1)

        await on_permission_click(cb)

        assert not req.event.is_set()
