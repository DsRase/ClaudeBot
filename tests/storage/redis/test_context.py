import pytest

from src.storage.redis.context import add_message, get_context
from src.storage.schemas import ChatMessage


@pytest.fixture
def message():
    return ChatMessage(role="user", user_id=1, content="привет", timestamp=1000)


@pytest.mark.asyncio
async def test_add_message_calls_rpush_and_ltrim(mocker, monkeypatch, message):
    """Проверяет, что add_message записывает сообщение и обрезает список до лимита."""
    monkeypatch.setenv("TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

    mock_redis = mocker.AsyncMock()
    mocker.patch("src.storage.redis.context.get_redis", return_value=mock_redis)
    mocker.patch("src.storage.redis.context.get_settings").return_value.context_max_stored = 500

    await add_message(chat_id=42, message=message)

    mock_redis.rpush.assert_awaited_once_with("context:42", message.model_dump_json()), \
        "rpush должен вызываться с правильным ключом и сериализованным сообщением"
    mock_redis.ltrim.assert_awaited_once_with("context:42", -500, -1), \
        "ltrim должен обрезать список до 500 последних сообщений"


@pytest.mark.asyncio
async def test_get_context_returns_messages(mocker, monkeypatch, message):
    """Проверяет, что get_context возвращает десериализованный список сообщений."""
    monkeypatch.setenv("TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

    mock_redis = mocker.AsyncMock()
    mock_redis.lrange.return_value = [message.model_dump_json()]
    mocker.patch("src.storage.redis.context.get_redis", return_value=mock_redis)
    mocker.patch("src.storage.redis.context.get_settings").return_value.context_default_limit = 100

    result = await get_context(chat_id=42)

    mock_redis.lrange.assert_awaited_once_with("context:42", -100, -1), \
        "lrange должен запрашивать последние 100 сообщений"
    assert len(result) == 1, "должно вернуться одно сообщение"
    assert result[0] == message, "сообщение должно совпадать с исходным"


@pytest.mark.asyncio
async def test_get_context_custom_limit(mocker, monkeypatch):
    """Проверяет, что get_context использует переданный limit вместо дефолтного."""
    monkeypatch.setenv("TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

    mock_redis = mocker.AsyncMock()
    mock_redis.lrange.return_value = []
    mocker.patch("src.storage.redis.context.get_redis", return_value=mock_redis)
    mocker.patch("src.storage.redis.context.get_settings").return_value.context_default_limit = 100

    await get_context(chat_id=42, limit=200)

    mock_redis.lrange.assert_awaited_once_with("context:42", -200, -1), \
        "lrange должен использовать переданный limit=200"
