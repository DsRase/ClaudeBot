import pytest
from pydantic import ValidationError

from src.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _isolate(monkeypatch, tmp_path):
    """Каждый тест работает в чистой tmp_path и с чистым кэшем настроек."""
    monkeypatch.chdir(tmp_path)
    # вычищаем env, который мог протечь из process env / реального .env
    for var in (
        "ACCESS_USER_IDS", "DEFAULT_MODEL", "AVAILABLE_MODELS",
        "MAX_TOKENS", "REDIS_URL", "SQLITE_PATH",
        "CONTEXT_MAX_STORED", "CONTEXT_DEFAULT_LIMIT",
        "PERMISSION_REQUEST_TIMEOUT", "AGENT_MAX_ITERATIONS",
        "SEARCH_DEFAULT_MAX_RESULTS",
        "FETCH_MAX_CONTENT_CHARS", "FETCH_REQUEST_TIMEOUT", "FETCH_USER_AGENT",
        "LLM_BASE_URL",
    ):
        monkeypatch.delenv(var, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestSettings:
    """Сценарии загрузки конфига (env для секретов, yaml для остального)."""

    def test_secrets_loaded_from_env(self, monkeypatch):
        """Секреты тянутся из env: TELEGRAM_TOKEN, LLM_API_KEY, LLM_BASE_URL."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "test_token")
        monkeypatch.setenv("LLM_API_KEY", "test_key")
        monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")

        settings = Settings()

        assert settings.telegram_token == "test_token"
        assert settings.llm_api_key == "test_key"
        assert settings.llm_base_url == "https://example.com/v1"

    def test_defaults_when_no_yaml(self, monkeypatch):
        """Без config.yaml настраиваемые поля берут дефолты из класса."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        settings = Settings()

        assert settings.access_user_ids == [], "дефолтный access_user_ids не пустой"
        assert settings.default_model == "claude-opus-4.6", "дефолтная default_model изменилась"
        assert settings.available_models == ["claude-opus-4.6"]
        assert settings.sqlite_path == "data/bot.db"
        assert settings.llm_base_url == "https://api.stepanovikov.uno/v1"

    def test_yaml_overrides_defaults(self, monkeypatch, tmp_path):
        """Поля из config.yaml переопределяют дефолты класса."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")
        (tmp_path / "config.yaml").write_text(
            "access_user_ids: [111, 222]\n"
            "default_model: gpt-5.4\n"
            "available_models:\n"
            "  - gpt-5.4\n"
            "  - claude-opus-4.6\n"
            "sqlite_path: custom/path.db\n",
            encoding="utf-8",
        )

        settings = Settings()

        assert settings.access_user_ids == [111, 222], "access_user_ids не подхватился из yaml"
        assert settings.default_model == "gpt-5.4"
        assert settings.available_models == ["gpt-5.4", "claude-opus-4.6"]
        assert settings.sqlite_path == "custom/path.db"

    def test_env_wins_over_yaml(self, monkeypatch, tmp_path):
        """Если поле есть и в env и в yaml — env побеждает."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")
        monkeypatch.setenv("LLM_BASE_URL", "https://from-env.example/v1")
        (tmp_path / "config.yaml").write_text(
            "llm_base_url: https://from-yaml.example/v1\n",
            encoding="utf-8",
        )

        settings = Settings()

        assert settings.llm_base_url == "https://from-env.example/v1", \
            "env должен переопределить yaml"

    def test_missing_required_field_raises(self, monkeypatch):
        """Без TELEGRAM_TOKEN и LLM_API_KEY — ValidationError."""
        monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)

        with pytest.raises(ValidationError):
            Settings()
