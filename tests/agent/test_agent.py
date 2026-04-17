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
