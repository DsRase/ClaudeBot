import pytest

from src.bot.handlers.chat import chat
from src.config import BotMessages
from src.storage.schemas import ChatMessage


BOT_USERNAME = "mega_pipindr_bot"
BOT_ID = 42


@pytest.fixture
def history():
    return [ChatMessage(role="user", user_id=111, content="привет", timestamp=1000)]


@pytest.fixture
def bot(mocker):
    b = mocker.MagicMock()
    b.me = mocker.AsyncMock(return_value=mocker.MagicMock(id=BOT_ID, username=BOT_USERNAME))
    return b


@pytest.fixture
def message(mocker):
    msg = mocker.MagicMock()
    msg.text = "привет"
    msg.chat.id = 999
    msg.chat.type = "private"
    msg.from_user.id = 111
    msg.from_user.is_bot = False
    msg.from_user.username = "vasya"
    msg.from_user.first_name = "Вася"
    msg.from_user.last_name = "Пупкин"
    msg.date.timestamp.return_value = 1000
    msg.reply_to_message = None
    msg.answer = mocker.AsyncMock(return_value=mocker.AsyncMock(delete=mocker.AsyncMock()))
    msg.reply = mocker.AsyncMock(return_value=mocker.AsyncMock(delete=mocker.AsyncMock()))
    return msg


class TestChatHandler:
    """Сценарии обработки входящего сообщения хендлером chat."""

    @pytest.mark.asyncio
    async def test_premium_user_gets_llm_answer(self, mocker, message, bot, history):
        """Проверяет, что премиум пользователь в личке получает ответ от LLM с is_premium=True."""
        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            premium_user_ids=[111, 222],
            base_user_ids=[],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.get_context", new=mocker.AsyncMock(return_value=history))
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock(return_value="ответ от Claude"))

        await chat(message, bot)

        mock_ask.assert_awaited_once_with(history, True), "ask должен вызываться с историей и is_premium=True"
        message.answer.assert_any_await("ответ от Claude", entities=mocker.ANY), \
            "ответ модели не был отправлен пользователю в личке через answer"

    @pytest.mark.asyncio
    async def test_non_premium_user_gets_rejection(self, mocker, message, bot):
        """Проверяет, что пользователь не из списков получает отказ и LLM не вызывается."""
        message.from_user.id = 999

        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            premium_user_ids=[111, 222],
            base_user_ids=[],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock())

        await chat(message, bot)

        mock_ask.assert_not_awaited(), "ask не должен был вызываться, но был вызван"
        call_args = message.answer.await_args
        actual_text = call_args[0][0] if call_args[0] else None
        assert actual_text in BotMessages.NOT_PREMIUM, "вернулся текст не из списка NOT_PREMIUM"

    @pytest.mark.asyncio
    async def test_base_user_gets_llm_answer(self, mocker, message, bot, history):
        """Проверяет, что базовый пользователь получает ответ от LLM с is_premium=False."""
        message.from_user.id = 333

        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            premium_user_ids=[111],
            base_user_ids=[333],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.get_context", new=mocker.AsyncMock(return_value=history))
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock(return_value="ответ"))

        await chat(message, bot)

        mock_ask.assert_awaited_once_with(history, False), \
            "базовый пользователь получил вызов с неверным is_premium"

    @pytest.mark.asyncio
    async def test_non_text_message_skipped(self, mocker, message, bot):
        """Проверяет, что не-текстовое сообщение полностью игнорируется (без сохранения и без LLM)."""
        message.text = None

        mock_add = mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock())

        await chat(message, bot)

        mock_add.assert_not_awaited(), "не-текстовое сообщение попало в Redis, а не должно было"
        mock_ask.assert_not_awaited(), "ask вызван для не-текстового сообщения"

    @pytest.mark.asyncio
    async def test_bot_message_skipped(self, mocker, message, bot):
        """Проверяет, что сообщение от бота полностью игнорируется."""
        message.from_user.is_bot = True

        mock_add = mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock())

        await chat(message, bot)

        mock_add.assert_not_awaited(), "сообщение от бота попало в Redis, а не должно было"
        mock_ask.assert_not_awaited(), "ask вызван для сообщения от бота"

    @pytest.mark.asyncio
    async def test_group_message_without_trigger_only_saved(self, mocker, message, bot):
        """Проверяет, что в группе без упоминания/реплая сообщение только сохраняется, без ответа."""
        message.chat.type = "group"
        message.text = "просто болтаем без бота"

        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            premium_user_ids=[111], base_user_ids=[],
        )
        mock_add = mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock())

        await chat(message, bot)

        mock_add.assert_awaited_once(), "сообщение из группы должно быть сохранено в Redis"
        mock_ask.assert_not_awaited(), "ask вызван без триггера в группе"
        message.reply.assert_not_awaited(), "был отправлен reply без триггера"
        message.answer.assert_not_awaited(), "был отправлен answer без триггера"

    @pytest.mark.asyncio
    async def test_group_mention_triggers_reply(self, mocker, message, bot, history):
        """Проверяет, что упоминание @username бота в группе приводит к ответу через reply."""
        message.chat.type = "group"
        message.text = f"@{BOT_USERNAME} как дела?"

        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            premium_user_ids=[111], base_user_ids=[],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.get_context", new=mocker.AsyncMock(return_value=history))
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock(return_value="ответ"))

        await chat(message, bot)

        mock_ask.assert_awaited_once(), "ask должен быть вызван при упоминании бота в группе"
        message.reply.assert_any_await("ответ", entities=mocker.ANY), \
            "ответ в группе должен быть отправлен через reply, а не answer"

    @pytest.mark.asyncio
    async def test_group_reply_to_bot_triggers_reply(self, mocker, message, bot, history):
        """Проверяет, что ответ на сообщение бота в группе приводит к срабатыванию хендлера."""
        message.chat.type = "group"
        message.text = "и что дальше?"
        message.reply_to_message = mocker.MagicMock()
        message.reply_to_message.from_user.id = BOT_ID
        message.reply_to_message.from_user.username = None

        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            premium_user_ids=[111], base_user_ids=[],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.get_context", new=mocker.AsyncMock(return_value=history))
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock(return_value="ответ"))

        await chat(message, bot)

        mock_ask.assert_awaited_once(), "ask должен быть вызван при ответе на сообщение бота"
        message.reply.assert_any_await("ответ", entities=mocker.ANY), \
            "ответ должен быть отправлен через reply"
