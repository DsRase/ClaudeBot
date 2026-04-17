import pytest

from src.bot.handlers.chat import chat
from src.config import BotMessages
from src.storage.schemas import ChatMessage


@pytest.fixture
def history():
    return [ChatMessage(role="user", user_id=111, content="привет", timestamp=1000)]


@pytest.fixture
def message(mocker):
    msg = mocker.MagicMock()
    msg.text = "привет"
    msg.chat.id = 999
    msg.from_user.id = 111
    msg.date.timestamp.return_value = 1000
    msg.answer = mocker.AsyncMock(return_value=mocker.AsyncMock(delete=mocker.AsyncMock()))
    return msg


class TestChatHandler:
    """Сценарии обработки входящего сообщения хендлером chat."""

    @pytest.mark.asyncio
    async def test_premium_user_gets_llm_answer(self, mocker, message, history):
        """Проверяет, что премиум пользователь получает ответ от LLM с is_premium=True."""
        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            premium_user_ids=[111, 222],
            base_user_ids=[],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.get_context", new=mocker.AsyncMock(return_value=history))
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock(return_value="ответ от Claude"))

        await chat(message)

        mock_ask.assert_awaited_once_with(history, True), "ask должен вызываться с историей и is_premium=True"
        message.answer.assert_any_await("ответ от Claude", entities=mocker.ANY), \
            "ответ модели не был отправлен пользователю"

    @pytest.mark.asyncio
    async def test_non_premium_user_gets_rejection(self, mocker, message):
        """Проверяет, что пользователь не из списков получает отказ и LLM не вызывается."""
        message.from_user.id = 999

        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            premium_user_ids=[111, 222],
            base_user_ids=[],
        )
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock())

        await chat(message)

        mock_ask.assert_not_awaited(), "ask не должен был вызываться, но был вызван"
        call_args = message.answer.await_args
        actual_text = call_args[0][0] if call_args[0] else None
        assert actual_text in BotMessages.NOT_PREMIUM, "вернулся текст не из списка NOT_PREMIUM"

    @pytest.mark.asyncio
    async def test_base_user_gets_llm_answer(self, mocker, message, history):
        """Проверяет, что базовый пользователь получает ответ от LLM с is_premium=False."""
        message.from_user.id = 333

        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            premium_user_ids=[111],
            base_user_ids=[333],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.get_context", new=mocker.AsyncMock(return_value=history))
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock(return_value="ответ"))

        await chat(message)

        mock_ask.assert_awaited_once_with(history, False), \
            "базовый пользователь получил вызов с неверным is_premium"
