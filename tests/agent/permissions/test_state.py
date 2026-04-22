import asyncio

import pytest

from src.agent.permissions.state import (
    PendingRequest,
    PermissionState,
    get_permission_state,
)


class TestPendingRequest:
    """Конструктор PendingRequest."""

    def test_defaults(self):
        """event инициализируется, result=False, save_for_session=False."""
        req = PendingRequest(initiator_user_id=1, initiator_username="x", tool_name="search")
        assert isinstance(req.event, asyncio.Event)
        assert req.result is False
        assert req.save_for_session is False

    def test_username_can_be_none(self):
        """initiator_username может быть None."""
        req = PendingRequest(initiator_user_id=1, initiator_username=None, tool_name="t")
        assert req.initiator_username is None


class TestSessionPermissions:
    """Управление session-разрешениями в PermissionState."""

    def test_grant_then_is_allowed(self):
        """grant_for_session делает is_allowed_in_session=True."""
        s = PermissionState()
        s.grant_for_session(1, "search")
        assert s.is_allowed_in_session(1, "search")

    def test_unknown_user_returns_false(self):
        """Незнакомый user_id → False."""
        s = PermissionState()
        assert not s.is_allowed_in_session(999, "search")

    def test_unknown_tool_returns_false(self):
        """Знакомый user, но другой tool → False."""
        s = PermissionState()
        s.grant_for_session(1, "search")
        assert not s.is_allowed_in_session(1, "fetch")

    def test_grant_is_idempotent(self):
        """Повторный grant не плодит дубликаты (set)."""
        s = PermissionState()
        s.grant_for_session(1, "search")
        s.grant_for_session(1, "search")
        assert s.session_permissions[1] == {"search"}

    def test_clear_returns_count(self):
        """clear_session_permissions возвращает количество очищенных."""
        s = PermissionState()
        s.grant_for_session(1, "search")
        s.grant_for_session(1, "fetch")
        assert s.clear_session_permissions(1) == 2
        assert not s.is_allowed_in_session(1, "search")

    def test_clear_unknown_user_returns_zero(self):
        """Очистка незнакомого юзера возвращает 0."""
        s = PermissionState()
        assert s.clear_session_permissions(999) == 0


class TestPendingRequestRegistry:
    """Реестр pending-запросов в PermissionState."""

    def test_register_and_get(self):
        """register + get возвращает тот же объект."""
        s = PermissionState()
        req = PendingRequest(initiator_user_id=1, initiator_username=None, tool_name="t")
        s.register_request("rid", req)
        assert s.get_request("rid") is req

    def test_get_unknown_returns_none(self):
        """Неизвестный request_id → None."""
        s = PermissionState()
        assert s.get_request("nope") is None

    def test_pop_removes(self):
        """pop возвращает запрос и удаляет его из реестра."""
        s = PermissionState()
        req = PendingRequest(initiator_user_id=1, initiator_username=None, tool_name="t")
        s.register_request("rid", req)
        assert s.pop_request("rid") is req
        assert s.get_request("rid") is None

    def test_pop_unknown_returns_none(self):
        """pop неизвестного → None."""
        s = PermissionState()
        assert s.pop_request("nope") is None


class TestGetPermissionState:
    """Синглтон-фабрика get_permission_state."""

    def test_returns_singleton(self):
        """Повторный вызов возвращает тот же экземпляр."""
        get_permission_state.cache_clear()
        assert get_permission_state() is get_permission_state()

    def test_returns_permission_state_instance(self):
        """Возвращается именно PermissionState."""
        get_permission_state.cache_clear()
        assert isinstance(get_permission_state(), PermissionState)
