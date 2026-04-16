import pytest

from src.bot.handlers.chat import chat
from src.config.messages import BotMessages


@pytest.fixture
def message(mocker):
    msg = mocker.MagicMock()
    msg.text = "привет"
    msg.answer = mocker.AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_premium_user_gets_llm_answer(mocker, message):
    message.from_user.id = 111

    mock_settings = mocker.patch("src.bot.handlers.chat.get_settings")
    mock_settings.return_value.premium_user_ids = [111, 222]

    mock_ask = mocker.patch(
        "src.bot.handlers.chat.ask",
        new=mocker.AsyncMock(return_value="ответ от Claude"),
    )

    await chat(message)

    mock_ask.assert_awaited_once_with("привет", True)
    message.answer.assert_any_await("ответ от Claude")


@pytest.mark.asyncio
async def test_non_premium_user_gets_rejection(mocker, message):
    message.from_user.id = 999

    mock_settings = mocker.patch("src.bot.handlers.chat.get_settings")
    mock_settings.return_value.premium_user_ids = [111, 222]

    mock_ask = mocker.patch("src.bot.handlers.chat.ask", new=mocker.AsyncMock())

    await chat(message)

    mock_ask.assert_not_awaited()

    call_args = message.answer.await_args
    actual_text = call_args[0][0] if call_args[0] else None
    assert actual_text in BotMessages.NOT_PREMIUM, "Вернулся неочевидный текст для NOT_PREMIUM"
