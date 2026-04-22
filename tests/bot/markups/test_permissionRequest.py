from src.bot.markups import build_permission_keyboard


class TestBuildPermissionKeyboard:
    """Inline-клавиатура запроса разрешения тулы."""

    def test_has_three_buttons_in_one_row(self):
        """Клавиатура — один ряд из трёх кнопок (allow / allow_session / deny)."""
        kb = build_permission_keyboard("req123")
        assert len(kb.inline_keyboard) == 1, "ожидался один ряд"
        assert len(kb.inline_keyboard[0]) == 3, "ожидалось 3 кнопки в ряду"

    def test_callback_data_uses_request_id(self):
        """Все три callback_data содержат переданный request_id."""
        kb = build_permission_keyboard("req123")
        for btn in kb.inline_keyboard[0]:
            assert btn.callback_data.startswith("perm:req123:"), \
                f"callback_data не содержит request_id: {btn.callback_data!r}"

    def test_actions_set(self):
        """Действия в callback_data: allow, allow_session, deny."""
        kb = build_permission_keyboard("x")
        actions = [btn.callback_data.split(":")[2] for btn in kb.inline_keyboard[0]]
        assert set(actions) == {"allow", "allow_session", "deny"}, \
            f"набор действий не совпадает: {actions}"
