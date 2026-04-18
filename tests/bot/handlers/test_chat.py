import pytest

from src.bot.handlers.chat import chat
from src.config import BotMessages
from src.storage.schemas import ChatMessage


BOT_USERNAME = "mega_pipindr_bot"
BOT_ID = 42


@pytest.fixture
def history():
    return [ChatMessage(role="user", id=10, ts=1000, text="привет", user_id=111)]


@pytest.fixture
def bot(mocker):
    b = mocker.MagicMock()
    b.me = mocker.AsyncMock(return_value=mocker.MagicMock(id=BOT_ID, username=BOT_USERNAME))
    return b


@pytest.fixture
def message(mocker):
    msg = mocker.MagicMock()
    msg.message_id = 555
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
    sent = mocker.MagicMock()
    sent.message_id = 777
    sent.delete = mocker.AsyncMock()
    msg.answer = mocker.AsyncMock(return_value=sent)
    msg.reply = mocker.AsyncMock(return_value=sent)
    return msg


class TestChatHandler:
    """Сценарии обработки входящего сообщения хендлером chat."""

    @pytest.mark.asyncio
    async def test_allowed_user_gets_llm_answer(self, mocker, message, bot, history):
        """Проверяет, что пользователь из access-списка в личке получает ответ от LLM."""
        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            access_user_ids=[111, 222],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.get_context", new=mocker.AsyncMock(return_value=history))
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock(return_value="ответ от LLM"))

        await chat(message, bot)

        mock_ask.assert_awaited_once_with(history, permission_requester=mocker.ANY, extra_tools=mocker.ANY), \
            "ask должен вызываться с историей и permission_requester"
        message.answer.assert_any_await("ответ от LLM", entities=mocker.ANY), \
            "ответ модели не был отправлен пользователю в личке через answer"

    @pytest.mark.asyncio
    async def test_unknown_user_gets_rejection(self, mocker, message, bot):
        """Проверяет, что пользователь не из access-списка получает отказ и LLM не вызывается."""
        message.from_user.id = 999

        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            access_user_ids=[111, 222],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock())

        await chat(message, bot)

        mock_ask.assert_not_awaited(), "ask не должен был вызываться, но был вызван"
        call_args = message.answer.await_args
        actual_text = call_args[0][0] if call_args[0] else None
        assert actual_text in BotMessages.NO_ACCESS, "вернулся текст не из списка NO_ACCESS"

    @pytest.mark.asyncio
    async def test_chat_scoped_tools_passed_to_ask(self, mocker, message, bot, history):
        """В ask должна передаваться chat-scoped тула read_full_history."""
        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            access_user_ids=[111],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.get_context", new=mocker.AsyncMock(return_value=history))
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock(return_value="ok"))

        await chat(message, bot)

        extra_tools = mock_ask.await_args.kwargs["extra_tools"]
        names = [t.name for t in extra_tools]
        assert "read_full_history" in names, f"read_full_history не попал в extra_tools: {names}"

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
            access_user_ids=[111],
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
            access_user_ids=[111],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.get_context", new=mocker.AsyncMock(return_value=history))
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock(return_value="ответ"))

        await chat(message, bot)

        mock_ask.assert_awaited_once(), "ask должен быть вызван при упоминании бота в группе"
        message.reply.assert_any_await("ответ", entities=mocker.ANY), \
            "ответ в группе должен быть отправлен через reply, а не answer"

    @pytest.mark.asyncio
    async def test_reply_to_username_captured(self, mocker, message, bot, history):
        """При ответе на чужое сообщение в Redis сохраняются @username адресата и id сообщения."""
        message.reply_to_message = mocker.MagicMock()
        message.reply_to_message.message_id = 222
        message.reply_to_message.from_user.username = "petya"

        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            access_user_ids=[111],
        )
        mock_add = mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.get_context", new=mocker.AsyncMock(return_value=history))
        mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock(return_value="ответ"))

        await chat(message, bot)

        saved_user_msg = mock_add.await_args_list[0].args[1]
        assert saved_user_msg.to_username == "petya", \
            f"to_username не сохранился, получено: {saved_user_msg.to_username!r}"
        assert saved_user_msg.reply_id == 222, \
            f"reply_id не сохранился, получено: {saved_user_msg.reply_id!r}"

    @pytest.mark.asyncio
    async def test_ask_failure_sends_error_and_deletes_think_msg(self, mocker, message, bot, history):
        """Если ask падает — юзеру летит сообщение из LLM_ERROR, а думалка удаляется."""
        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            access_user_ids=[111],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.get_context", new=mocker.AsyncMock(return_value=history))
        mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock(side_effect=RuntimeError("upstream 421")))

        think_msg = mocker.MagicMock()
        think_msg.message_id = 777
        think_msg.delete = mocker.AsyncMock()
        message.answer = mocker.AsyncMock(return_value=think_msg)

        await chat(message, bot)

        think_msg.delete.assert_awaited_once(), "думалка должна быть удалена даже при ошибке ask"
        sent_texts = [c.args[0] for c in message.answer.await_args_list if c.args]
        assert any(t in BotMessages.LLM_ERROR for t in sent_texts), \
            f"юзеру не отправлен текст из LLM_ERROR, отправлено: {sent_texts}"

    @pytest.mark.asyncio
    async def test_group_reply_to_bot_triggers_reply(self, mocker, message, bot, history):
        """Проверяет, что ответ на сообщение бота в группе приводит к срабатыванию хендлера."""
        message.chat.type = "group"
        message.text = "и что дальше?"
        message.reply_to_message = mocker.MagicMock()
        message.reply_to_message.from_user.id = BOT_ID
        message.reply_to_message.from_user.username = None

        mocker.patch("src.bot.handlers.chat.get_settings").return_value.configure_mock(
            access_user_ids=[111],
        )
        mocker.patch("src.bot.handlers.chat.add_message", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.get_context", new=mocker.AsyncMock(return_value=history))
        mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock(return_value="ответ"))

        await chat(message, bot)

        mock_ask.assert_awaited_once(), "ask должен быть вызван при ответе на сообщение бота"
        message.reply.assert_any_await("ответ", entities=mocker.ANY), \
            "ответ должен быть отправлен через reply"
