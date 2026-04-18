import json

import pytest

from src.storage.redis.context import add_message, get_context
from src.storage.schemas import ChatMessage


@pytest.fixture
def message():
    # без user_id, тк он exclude=True и не выживает roundtrip через Redis
    return ChatMessage(role="user", id=10, ts=1000, text="привет")


class TestContextRepository:
    """Сценарии работы с историей чата в Redis."""

    @pytest.mark.asyncio
    async def test_add_message_calls_rpush_and_ltrim(self, mocker, monkeypatch, message):
        """Проверяет, что add_message записывает сообщение и обрезает список до лимита."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        mock_redis = mocker.AsyncMock()
        mocker.patch("src.storage.redis.context.get_redis", return_value=mock_redis)
        mocker.patch("src.storage.redis.context.get_settings").return_value.context_max_stored = 500

        await add_message(chat_id=42, message=message)

        expected_payload = json.dumps(message.model_dump(mode="python"), ensure_ascii=False)
        mock_redis.rpush.assert_awaited_once_with("context:42", expected_payload), \
            "rpush вызван с неверным ключом или сериализованным сообщением"
        mock_redis.ltrim.assert_awaited_once_with("context:42", -500, -1), \
            "ltrim вызван не с теми границами обрезки списка"

    @pytest.mark.asyncio
    async def test_get_context_returns_messages(self, mocker, monkeypatch, message):
        """Проверяет, что get_context возвращает десериализованный список сообщений."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        mock_redis = mocker.AsyncMock()
        mock_redis.lrange.return_value = [json.dumps(message.model_dump(mode="python"), ensure_ascii=False)]
        mocker.patch("src.storage.redis.context.get_redis", return_value=mock_redis)
        mocker.patch("src.storage.redis.context.get_settings").return_value.context_default_limit = 100

        result = await get_context(chat_id=42)

        mock_redis.lrange.assert_awaited_once_with("context:42", -100, -1), \
            "lrange запросил не последние 100 сообщений"
        assert len(result) == 1, f"ожидалось одно сообщение, получено: {len(result)}"
        assert result[0] == message, "десериализованное сообщение не совпадает с исходным"

    @pytest.mark.asyncio
    async def test_get_context_custom_limit(self, mocker, monkeypatch):
        """Проверяет, что get_context использует переданный limit вместо дефолтного."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        mock_redis = mocker.AsyncMock()
        mock_redis.lrange.return_value = []
        mocker.patch("src.storage.redis.context.get_redis", return_value=mock_redis)
        mocker.patch("src.storage.redis.context.get_settings").return_value.context_default_limit = 100

        await get_context(chat_id=42, limit=200)

        mock_redis.lrange.assert_awaited_once_with("context:42", -200, -1), \
            "lrange проигнорировал переданный limit=200"
