from src.storage.redis.redis_client import get_redis


def test_get_redis_returns_instance(monkeypatch, tmp_path):
    """Проверяет, что get_redis возвращает объект клиента."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")

    get_redis.cache_clear()
    client = get_redis()
    assert client is not None, "get_redis должен возвращать объект клиента"


def test_get_redis_is_singleton(monkeypatch, tmp_path):
    """Проверяет, что повторный вызов get_redis возвращает тот же объект."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")

    get_redis.cache_clear()
    assert get_redis() is get_redis(), "get_redis должен возвращать один и тот же объект"
