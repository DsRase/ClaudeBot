import pytest

from src.agent.agent import ask
from src.config.settings import Settings
from src.storage.schemas import ChatMessage


@pytest.fixture
def history():
    return [
        ChatMessage(role="user", user_id=1, content="привет", timestamp=1000),
    ]


class TestAsk:
    """Сценарии вызова функции ask."""

    @pytest.mark.asyncio
    async def test_returns_llm_response(self, mocker, monkeypatch, history):
        """Проверяет, что ask возвращает content из ответа модели."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

        mock_llm = mocker.patch("src.agent.agent.ChatAnthropic").return_value
        mock_llm.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="ответ"))

        result = await ask(history)

        mock_llm.ainvoke.assert_awaited_once(), "ainvoke должен быть вызван ровно один раз"
        assert result == "ответ", "ask вернул не тот content, что ожидался"

    @pytest.mark.asyncio
    async def test_uses_premium_model(self, mocker, monkeypatch, history):
        """Проверяет, что для премиум пользователя выбирается premium_model из настроек."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

        mock_cls = mocker.patch("src.agent.agent.ChatAnthropic")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history, is_premium=True)

        _, kwargs = mock_cls.call_args
        assert kwargs["model"] == Settings.model_fields["premium_model"].default, \
            "для премиум пользователя выбрана не premium_model"

    @pytest.mark.asyncio
    async def test_user_metadata_prefixed_in_llm_message(self, mocker, monkeypatch):
        """Проверяет, что метаданные юзера (@username, имя) попадают в сообщение, отправляемое LLM."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

        history = [ChatMessage(
            role="user", user_id=1, content="привет", timestamp=1,
            username="vasya", first_name="Вася", last_name="Пупкин",
        )]
        mock_cls = mocker.patch("src.agent.agent.ChatAnthropic")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        sent_messages = mock_cls.return_value.ainvoke.await_args[0][0]
        user_msg_content = sent_messages[-1].content
        assert "vasya" in user_msg_content and "Вася" in user_msg_content, \
            f"метаданные юзера не попали в сообщение для LLM: {user_msg_content!r}"
        assert "привет" in user_msg_content, \
            f"оригинальный контент потерян при префиксации: {user_msg_content!r}"

    @pytest.mark.asyncio
    async def test_reply_target_added_to_llm_message(self, mocker, monkeypatch):
        """Проверяет, что reply_to_username попадает в префикс сообщения для LLM."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

        history = [ChatMessage(
            role="user", user_id=1, content="ну ок", timestamp=1,
            username="vasya", first_name="Вася", reply_to_username="petya",
        )]
        mock_cls = mocker.patch("src.agent.agent.ChatAnthropic")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        sent = mock_cls.return_value.ainvoke.await_args[0][0][-1].content
        assert "ответил @petya" in sent, \
            f"reply_to_username не оказался в префиксе сообщения: {sent!r}"

    @pytest.mark.asyncio
    async def test_history_collapsed_into_single_human_message(self, mocker, monkeypatch):
        """Проверяет, что вся история сворачивается в один HumanMessage без отдельных AIMessage."""
        from langchain_core.messages import HumanMessage, SystemMessage
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

        history = [
            ChatMessage(role="user", user_id=1, content="один", timestamp=1, username="vasya"),
            ChatMessage(role="assistant", user_id=None, content="ответ1", timestamp=2),
            ChatMessage(role="user", user_id=2, content="два", timestamp=3, username="petya"),
        ]
        mock_cls = mocker.patch("src.agent.agent.ChatAnthropic")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        sent = mock_cls.return_value.ainvoke.await_args[0][0]
        assert len(sent) == 2, f"в LLM ушло {len(sent)} сообщений, ожидалось ровно 2 (system + human)"
        assert isinstance(sent[0], SystemMessage), "первое сообщение должно быть SystemMessage"
        assert isinstance(sent[1], HumanMessage), "второе сообщение должно быть HumanMessage"

    @pytest.mark.asyncio
    async def test_trigger_separated_from_history(self, mocker, monkeypatch):
        """Проверяет, что последнее сообщение явно отделено маркером 'Message to reply to NOW'."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

        history = [
            ChatMessage(role="user", user_id=1, content="старое", timestamp=1, username="vasya"),
            ChatMessage(role="user", user_id=2, content="новое", timestamp=3, username="petya"),
        ]
        mock_cls = mocker.patch("src.agent.agent.ChatAnthropic")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        content = mock_cls.return_value.ainvoke.await_args[0][0][1].content
        marker_pos = content.find("Message to reply to NOW")
        assert marker_pos != -1, "триггер не отделён маркером 'Message to reply to NOW'"
        assert content.find("новое") > marker_pos, "триггерное сообщение оказалось не в секции триггера"
        assert content.find("старое") < marker_pos, "контекстное сообщение попало в секцию триггера"

    @pytest.mark.asyncio
    async def test_assistant_reply_target_in_history(self, mocker, monkeypatch):
        """Проверяет, что ответ ассистента в истории отображается с указанием, кому он отвечал."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

        history = [
            ChatMessage(
                role="assistant", user_id=None, content="мой ответ",
                timestamp=1, reply_to_username="vasya",
            ),
            ChatMessage(role="user", user_id=2, content="новое", timestamp=2, username="petya"),
        ]
        mock_cls = mocker.patch("src.agent.agent.ChatAnthropic")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        content = mock_cls.return_value.ainvoke.await_args[0][0][1].content
        assert "Пипиндр ответил @vasya: мой ответ" in content, \
            f"строка ассистента не содержит указания адресата: {content!r}"

    @pytest.mark.asyncio
    async def test_uses_default_model(self, mocker, monkeypatch, history):
        """Проверяет, что для обычного пользователя выбирается default_model из настроек."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

        mock_cls = mocker.patch("src.agent.agent.ChatAnthropic")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history, is_premium=False)

        _, kwargs = mock_cls.call_args
        assert kwargs["model"] == Settings.model_fields["default_model"].default, \
            "для обычного пользователя выбрана не default_model"
