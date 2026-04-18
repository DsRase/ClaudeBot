import pytest
from pydantic import ValidationError

from src.config import Settings


class TestSettings:
    """Сценарии загрузки конфига."""

    def test_loads_required_fields(self, monkeypatch, tmp_path):
        """Проверяет, что обязательные поля корректно загружаются из переменных окружения."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TELEGRAM_TOKEN", "test_token")
        monkeypatch.setenv("LLM_API_KEY", "test_key")

        settings = Settings()

        assert settings.telegram_token == "test_token", "telegram_token не подхватился из окружения"
        assert settings.llm_api_key == "test_key", "llm_api_key не подхватился из окружения"

    def test_defaults(self, monkeypatch, tmp_path):
        """Проверяет, что опциональные поля имеют корректные дефолтные значения."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        settings = Settings()

        assert settings.access_user_ids == [], "дефолтный access_user_ids не пустой"
        assert settings.default_model == "claude-opus-4.6", "дефолтная default_model изменилась"
        assert settings.llm_base_url == "https://api.stepanovikov.uno/v1", \
            "дефолтный llm_base_url изменился"

    def test_access_user_ids_parsed_as_list(self, monkeypatch, tmp_path):
        """Проверяет, что ACCESS_USER_IDS из строки парсится в список int."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")
        monkeypatch.setenv("ACCESS_USER_IDS", "[111,222,333]")

        settings = Settings()

        assert settings.access_user_ids == [111, 222, 333], \
            "ACCESS_USER_IDS распарсился в неожиданный список"

    def test_missing_required_field_raises(self, monkeypatch, tmp_path):
        """Проверяет, что отсутствие обязательных полей вызывает ValidationError."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)

        with pytest.raises(ValidationError):
            Settings()
