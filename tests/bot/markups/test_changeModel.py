import pytest
from src.bot.markups import build_back_btn, build_models_keyboard


class TestBuildBackBtn:
    """Кнопка отмены."""

    def test_returns_list_with_one_button(self):
        buttons = build_back_btn()
        assert len(buttons) == 1

    def test_callback_data_is_back(self):
        button = build_back_btn()[0]
        assert button.callback_data == "back"


class TestBuildModelsKeyboard:
    """Клавиатура смены модели."""

    @pytest.fixture
    def keyboard(self, mocker):
        mocker.patch(
            "src.bot.markups.changeModel.get_settings",
        ).return_value.configure_mock(
            available_models=["claude-opus-4.6", "claude-sonnet-4.6"]
        )
        return build_models_keyboard(user_id=111)

    def test_has_button_per_model_plus_back(self, keyboard):
        # 2 модели + 1 кнопка отмены
        assert len(keyboard.inline_keyboard) == 3

    def test_model_callback_data_format(self, keyboard):
        """callback_data каждой модели — 'model:<user_id>:<model>'."""
        model_rows = keyboard.inline_keyboard[:-1]  # последняя — back
        for row in model_rows:
            btn = row[0]
            parts = btn.callback_data.split(":")
            assert parts[0] == "model", f"неверный префикс: {btn.callback_data!r}"
            assert parts[1] == "111", f"user_id не тот: {btn.callback_data!r}"

    def test_model_button_text_matches_model_name(self, keyboard):
        """Текст кнопки совпадает с именем модели из callback_data."""
        model_rows = keyboard.inline_keyboard[:-1]
        for row in model_rows:
            btn = row[0]
            model_from_data = btn.callback_data.split(":", 2)[2]
            assert btn.text == model_from_data, (
                f"текст кнопки {btn.text!r} не совпадает с моделью {model_from_data!r}"
            )

    def test_back_button_is_last_row(self, keyboard):
        last_row = keyboard.inline_keyboard[-1]
        assert last_row[0].callback_data == "back"

    def test_user_id_embedded_in_all_model_buttons(self, mocker):
        """user_id корректно прокидывается для разных юзеров."""
        mocker.patch(
            "src.bot.markups.changeModel.get_settings",
        ).return_value.configure_mock(available_models=["claude-opus-4.6"])

        kb = build_models_keyboard(user_id=999)
        btn = kb.inline_keyboard[0][0]
        assert ":999:" in btn.callback_data, f"user_id 999 не в callback_data: {btn.callback_data!r}"
