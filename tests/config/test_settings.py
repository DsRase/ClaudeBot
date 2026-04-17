import pytest
from pydantic import ValidationError

from src.config import Settings

def test_loads_required_fields(monkeypatch, tmp_path):
    """Проверяет, что обязательные поля корректно загружаются из переменных окружения."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TELEGRAM_TOKEN", "test_token")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")

    settings = Settings()

    assert settings.telegram_token == "test_token"
    assert settings.anthropic_api_key == "test_key"


def test_defaults(monkeypatch, tmp_path):
    """Проверяет, что опциональные поля имеют корректные дефолтные значения."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")

    settings = Settings()

    assert settings.premium_user_ids == []
    assert settings.premium_model == "claude-opus-4-6"
    assert settings.default_model == "claude-sonnet-4-6"


def test_premium_user_ids_parsed_as_list(monkeypatch, tmp_path):
    """Проверяет, что PREMIUM_USER_IDS из строки парсится в список int."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TELEGRAM_TOKEN", "t")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("PREMIUM_USER_IDS", "[111,222,333]")

    settings = Settings()

    assert settings.premium_user_ids == [111, 222, 333]


def test_missing_required_field_raises(monkeypatch, tmp_path):
    """Проверяет, что отсутствие обязательных полей вызывает ValidationError."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings()