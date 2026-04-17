import pytest

from src.agent.agent import ask
from src.config.settings import Settings
from src.storage.schemas import ChatMessage


@pytest.fixture
def history():
    return [
        ChatMessage(role="user", user_id=1, content="привет", timestamp=1000),
    ]


@pytest.mark.asyncio
async def test_ask_returns_llm_response(mocker, monkeypatch, history):
    """Проверяет, что ask возвращает content из ответа модели."""
    monkeypatch.setenv("TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

    mock_llm = mocker.patch("src.agent.agent.ChatAnthropic").return_value
    mock_llm.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="ответ"))

    result = await ask(history)

    mock_llm.ainvoke.assert_awaited_once(), "ainvoke должен быть вызван ровно один раз"
    assert result == "ответ", "ask должен вернуть content из ответа модели"


@pytest.mark.asyncio
async def test_ask_uses_premium_model(mocker, monkeypatch, history):
    """Проверяет, что для премиум пользователя выбирается premium_model из настроек."""
    monkeypatch.setenv("TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

    mock_cls = mocker.patch("src.agent.agent.ChatAnthropic")
    mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

    await ask(history, is_premium=True)

    _, kwargs = mock_cls.call_args
    assert kwargs["model"] == Settings.model_fields["premium_model"].default, \
        "для премиум пользователя должна использоваться premium_model из настроек"


@pytest.mark.asyncio
async def test_ask_uses_default_model(mocker, monkeypatch, history):
    """Проверяет, что для обычного пользователя выбирается default_model из настроек."""
    monkeypatch.setenv("TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

    mock_cls = mocker.patch("src.agent.agent.ChatAnthropic")
    mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

    await ask(history, is_premium=False)

    _, kwargs = mock_cls.call_args
    assert kwargs["model"] == Settings.model_fields["default_model"].default, \
        "для обычного пользователя должна использоваться default_model из настроек"
