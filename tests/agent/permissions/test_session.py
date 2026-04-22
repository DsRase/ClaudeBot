from src.agent.permissions.session import reset_session_permissions
from src.agent.permissions.state import get_permission_state


class TestResetSessionPermissions:
    """Сценарии reset_session_permissions."""

    def test_returns_cleared_count(self):
        """Возвращает количество сброшенных тул."""
        get_permission_state.cache_clear()
        state = get_permission_state()
        state.grant_for_session(42, "search")
        state.grant_for_session(42, "fetch")

        assert reset_session_permissions(42) == 2

    def test_zero_when_nothing_to_clear(self):
        """0 для юзера без разрешений."""
        get_permission_state.cache_clear()
        assert reset_session_permissions(999) == 0

    def test_state_is_cleared_after_reset(self):
        """После reset is_allowed_in_session=False."""
        get_permission_state.cache_clear()
        state = get_permission_state()
        state.grant_for_session(42, "search")

        reset_session_permissions(42)

        assert not state.is_allowed_in_session(42, "search")
