import pytest

from src.agent.agent import ask


@pytest.mark.asyncio
async def test_ask_returns_llm_response(mocker, monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

    mock_llm = mocker.patch("src.agent.agent.ChatAnthropic").return_value
    mock_llm.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="ответ"))

    result = await ask("привет")

    mock_llm.ainvoke.assert_awaited_once_with("привет")
    assert result == "ответ"
