from src.storage.redis.redis_client import get_redis


class TestGetRedis:
    """Сценарии получения Redis клиента."""

    def test_returns_instance(self, monkeypatch, tmp_path):
        """Проверяет, что get_redis возвращает объект клиента."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")

        get_redis.cache_clear()
        client = get_redis()
        assert client is not None, "get_redis вернул None вместо объекта клиента"

    def test_is_singleton(self, monkeypatch, tmp_path):
        """Проверяет, что повторный вызов get_redis возвращает тот же объект."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")

        get_redis.cache_clear()
        assert get_redis() is get_redis(), "get_redis вернул разные объекты при повторном вызове"
