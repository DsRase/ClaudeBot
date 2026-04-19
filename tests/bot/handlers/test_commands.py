import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, Chat, User
from src.bot.handlers.commands import (
    start_command, help_command, getid_command, on_reset_perms,
    update_conf_command, change_model, change_model_callback, cancel_model_callback,
)
from src.bot.permissions.state import get_permission_state
from src.config import BotMessages


class TestBotHandlers:
    """Тестовый класс для проверки хендлеров бота"""

    @pytest.fixture
    def message(self):
        """Фикстура для мока сообщения"""
        message = MagicMock(spec=Message)
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 123456
        message.from_user = MagicMock(spec=User)
        message.from_user.id = 789012
        message.answer = AsyncMock()
        return message

    @pytest.mark.asyncio
    async def test_start_command(self, message, mocker):
        """Тест команды /start"""
        mock_get_random = mocker.patch(
            'src.bot.handlers.commands.get_random_message',
            return_value="Привет! Я бот-помощник"
        )

        await start_command(message)

        mock_get_random.assert_called_once_with(BotMessages.START_MESSAGE)

        message.answer.assert_called_once_with("Привет! Я бот-помощник")

    @pytest.mark.asyncio
    async def test_help_command(self, message, mocker):
        """Тест команды /help"""
        mock_get_random = mocker.patch(
            'src.bot.handlers.commands.get_random_message',
            return_value="Я умею: /start, /help, /getid"
        )

        await help_command(message)

        mock_get_random.assert_called_once_with(BotMessages.HELP_MESSAGE)
        message.answer.assert_called_once_with("Я умею: /start, /help, /getid")

    @pytest.mark.asyncio
    async def test_getid_command(self, message):
        """Тест команды /getid"""

        await getid_command(message)

        expected_text = f"Твой ID: {message.from_user.id}"
        message.answer.assert_called_once_with(expected_text)

class TestUpdateConf:
    """Сценарии команды /update_conf."""

    @pytest.mark.asyncio
    async def test_reloads_settings_and_replies(self, mocker):
        """Команда вызывает reload_settings и отвечает инфой о новом конфиге."""
        mock_reload = mocker.patch(
            "src.bot.handlers.commands.reload_settings",
            return_value=mocker.MagicMock(default_model="gpt-5.4", access_user_ids=[1, 2, 3]),
        )
        mocker.patch(
            "src.bot.permissions.admin.get_settings",
        ).return_value.configure_mock(admin_user_ids=[111])

        msg = mocker.MagicMock()
        msg.from_user.id = 111
        msg.answer = mocker.AsyncMock()

        await update_conf_command(msg)

        mock_reload.assert_called_once(), "reload_settings должен быть вызван"
        reply_text = msg.answer.await_args_list[-1].args[0]
        assert "gpt-5.4" in reply_text, f"ответ не содержит новую модель: {reply_text!r}"
        assert "3" in reply_text, f"ответ не содержит кол-во юзеров: {reply_text!r}"

    @pytest.mark.asyncio
    async def test_non_admin_cannot_update_conf(self, mocker):
        """Не-админ не может вызвать /update_conf — reload_settings не зовётся."""
        mock_reload = mocker.patch("src.bot.handlers.commands.reload_settings")
        mocker.patch(
            "src.bot.permissions.admin.get_settings",
        ).return_value.configure_mock(admin_user_ids=[999])

        msg = mocker.MagicMock()
        msg.from_user.id = 111
        msg.answer = mocker.AsyncMock()

        await update_conf_command(msg)

        mock_reload.assert_not_called(), "reload_settings не должен вызываться для не-админа"


class TestResetPerms:
    """Сценарии команды /reset_perms."""

    @pytest.mark.asyncio
    async def test_reports_cleared_count(self, mocker):
        """Команда отвечает количеством сброшенных разрешений."""
        state = get_permission_state()
        state.grant_for_session(111, "search")
        state.grant_for_session(111, "fetch")
        msg = mocker.MagicMock()
        msg.from_user.id = 111
        msg.reply = mocker.AsyncMock()

        await on_reset_perms(msg)

        reply_text = msg.reply.await_args.args[0]
        assert "2" in reply_text, f"должно быть упомянуто число 2, ответ: {reply_text!r}"

    @pytest.mark.asyncio
    async def test_empty_reports_nothing_to_clear(self, mocker):
        """Если разрешений не было, отвечает понятным сообщением и не падает."""
        msg = mocker.MagicMock()
        msg.from_user.id = 111
        msg.reply = mocker.AsyncMock()

        await on_reset_perms(msg)

        msg.reply.assert_awaited_once()


class TestChangeModel:
    """Сценарии команды /change_model и её коллбэков."""

    @pytest.mark.asyncio
    async def test_shows_current_model_and_keyboard(self, mocker):
        """Команда отвечает текущей моделью пользователя и клавиатурой."""
        mocker.patch(
            "src.bot.handlers.commands.get_user_model",
            return_value="claude-opus-4.6",
        )
        mock_keyboard = mocker.MagicMock()
        mocker.patch(
            "src.bot.handlers.commands.build_models_keyboard",
            return_value=mock_keyboard,
        )

        msg = mocker.MagicMock()
        msg.from_user.id = 111
        msg.answer = mocker.AsyncMock()

        await change_model(msg)

        reply_text = msg.answer.await_args.args[0]
        assert "claude-opus-4.6" in reply_text, f"текущая модель не в ответе: {reply_text!r}"
        msg.answer.assert_awaited_once_with(reply_text, reply_markup=mock_keyboard)

    @pytest.mark.asyncio
    async def test_callback_changes_model_for_initiator(self, mocker):
        """Инициатор нажимает кнопку — модель меняется, сообщение редактируется."""
        mock_set = mocker.patch("src.bot.handlers.commands.set_user_model")

        cb = mocker.MagicMock()
        cb.data = "model:111:claude-sonnet-4.6"
        cb.from_user.id = 111
        cb.message.edit_text = mocker.AsyncMock()
        cb.answer = mocker.AsyncMock()

        await change_model_callback(cb)

        mock_set.assert_awaited_once_with(111, "claude-sonnet-4.6")
        edited_text = cb.message.edit_text.await_args.args[0]
        assert "claude-sonnet-4.6" in edited_text, f"новая модель не в ответе: {edited_text!r}"

    @pytest.mark.asyncio
    async def test_callback_rejects_non_initiator(self, mocker):
        """Чужой юзер нажимает кнопку — set_user_model не вызывается, alert отправляется."""
        mock_set = mocker.patch("src.bot.handlers.commands.set_user_model")

        cb = mocker.MagicMock()
        cb.data = "model:111:claude-sonnet-4.6"
        cb.from_user.id = 999  # не инициатор
        cb.answer = mocker.AsyncMock()

        await change_model_callback(cb)

        mock_set.assert_not_called()
        cb.answer.assert_awaited_once()
        _, kwargs = cb.answer.await_args
        assert kwargs.get("show_alert") is True, "alert должен быть показан"

    @pytest.mark.asyncio
    async def test_cancel_deletes_message(self, mocker):
        """Кнопка отмены удаляет сообщение."""
        cb = mocker.MagicMock()
        cb.message.delete = mocker.AsyncMock()

        await cancel_model_callback(cb)

        cb.message.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cancel_answers_on_delete_failure(self, mocker):
        """Если удалить не вышло — бот отвечает сообщением об ошибке и не падает."""
        cb = mocker.MagicMock()
        cb.message.delete = mocker.AsyncMock(side_effect=Exception("forbidden"))
        cb.message.answer = mocker.AsyncMock()

        await cancel_model_callback(cb)

        cb.message.answer.assert_awaited_once()

