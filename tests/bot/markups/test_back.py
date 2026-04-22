from src.bot.markups import build_back_btn


class TestBuildBackBtn:
    """Кнопка отмены."""

    def test_returns_list_with_one_button(self):
        """Возвращает list из одной кнопки."""
        buttons = build_back_btn()
        assert len(buttons) == 1, f"ожидалась одна кнопка, получено: {len(buttons)}"

    def test_callback_data_is_back(self):
        """callback_data единственной кнопки == 'back'."""
        button = build_back_btn()[0]
        assert button.callback_data == "back", f"неверный callback_data: {button.callback_data!r}"

    def test_button_text_is_cancel(self):
        """Текст кнопки — 'Отмена'."""
        button = build_back_btn()[0]
        assert button.text == "Отмена", f"неверный текст кнопки: {button.text!r}"
