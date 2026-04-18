import pytest

from src.bot.handlers.permissions import on_permission_click
from src.bot.permissions.state import PendingRequest, get_permission_state


@pytest.fixture(autouse=True)
def fresh_state():
    state = get_permission_state()
    state.session_permissions.clear()
    state.pending_requests.clear()
    yield
    state.session_permissions.clear()
    state.pending_requests.clear()


def _make_callback(mocker, *, data: str, user_id: int = 111):
    cb = mocker.MagicMock()
    cb.data = data
    cb.from_user.id = user_id
    cb.answer = mocker.AsyncMock()
    cb.message = mocker.MagicMock()
    cb.message.html_text = "оригинал"
    cb.message.text = "оригинал"
    cb.message.edit_text = mocker.AsyncMock()
    return cb


class TestPermissionClick:
    """Сценарии клика по кнопке permission-запроса."""

    @pytest.mark.asyncio
    async def test_allow_sets_event_and_strikes_original(self, mocker):
        """Клик allow от инициатора: result=True, event сработал, сообщение зачёркнуто."""
        state = get_permission_state()
        request = PendingRequest(initiator_user_id=111, initiator_username="vasya", tool_name="search")
        state.register_request("rid", request)
        cb = _make_callback(mocker, data="perm:rid:allow", user_id=111)

        await on_permission_click(cb)

        assert request.event.is_set(), "event должен быть выставлен"
        assert request.result is True
        assert request.save_for_session is False
        edited = cb.message.edit_text.await_args.args[0]
        assert "<s>оригинал</s>" in edited and "Разрешено" in edited, \
            f"оригинал не зачёркнут или нет пометки: {edited!r}"

    @pytest.mark.asyncio
    async def test_allow_session_marks_save_for_session(self, mocker):
        """Клик allow_session: result=True, save_for_session=True."""
        state = get_permission_state()
        request = PendingRequest(initiator_user_id=111, initiator_username="vasya", tool_name="search")
        state.register_request("rid", request)
        cb = _make_callback(mocker, data="perm:rid:allow_session", user_id=111)

        await on_permission_click(cb)

        assert request.result is True
        assert request.save_for_session is True

    @pytest.mark.asyncio
    async def test_deny_sets_false(self, mocker):
        """Клик deny: result=False, event сработал."""
        state = get_permission_state()
        request = PendingRequest(initiator_user_id=111, initiator_username="vasya", tool_name="search")
        state.register_request("rid", request)
        cb = _make_callback(mocker, data="perm:rid:deny", user_id=111)

        await on_permission_click(cb)

        assert request.event.is_set()
        assert request.result is False

    @pytest.mark.asyncio
    async def test_non_initiator_gets_alert(self, mocker):
        """Клик не от инициатора: показывается alert, event не сработал."""
        state = get_permission_state()
        request = PendingRequest(initiator_user_id=111, initiator_username="vasya", tool_name="search")
        state.register_request("rid", request)
        cb = _make_callback(mocker, data="perm:rid:allow", user_id=222)

        await on_permission_click(cb)

        assert not request.event.is_set(), "чужой клик не должен выставлять event"
        cb.answer.assert_awaited_once()
        kwargs = cb.answer.await_args.kwargs
        assert kwargs.get("show_alert") is True, "не-инициатор должен получить alert (popup)"
        cb.message.edit_text.assert_not_awaited(), "не-инициатор не должен редактировать сообщение"

    @pytest.mark.asyncio
    async def test_unknown_request_id(self, mocker):
        """Клик по уже неактуальному запросу: popup, ничего не редактируется."""
        cb = _make_callback(mocker, data="perm:nope:allow", user_id=111)

        await on_permission_click(cb)

        cb.answer.assert_awaited_once()
        cb.message.edit_text.assert_not_awaited()
