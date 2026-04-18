import pytest

from src.bot.permissions.resetSessionPermissions import reset_session_permissions
from src.bot.permissions.state import get_permission_state


@pytest.fixture(autouse=True)
def fresh_state():
    state = get_permission_state()
    state.session_permissions.clear()
    yield
    state.session_permissions.clear()


class TestResetSessionPermissions:
    """Сценарии сброса session-разрешений юзера."""

    def test_clears_all_user_permissions(self):
        """Все session-разрешения юзера удаляются, возвращается их количество."""
        state = get_permission_state()
        state.grant_for_session(111, "search")
        state.grant_for_session(111, "fetch")

        cleared = reset_session_permissions(111)

        assert cleared == 2, f"должно быть удалено 2 разрешения, удалено {cleared}"
        assert not state.is_allowed_in_session(111, "search")
        assert not state.is_allowed_in_session(111, "fetch")

    def test_empty_returns_zero(self):
        """Если у юзера не было разрешений, возвращается 0 и ничего не падает."""
        assert reset_session_permissions(111) == 0

    def test_does_not_touch_other_users(self):
        """Сброс одному юзеру не затрагивает разрешения другого."""
        state = get_permission_state()
        state.grant_for_session(111, "search")
        state.grant_for_session(222, "search")

        reset_session_permissions(111)

        assert state.is_allowed_in_session(222, "search"), \
            "разрешения чужого юзера не должны быть затронуты"
