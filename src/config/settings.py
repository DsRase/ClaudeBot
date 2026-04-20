from functools import lru_cache
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


CONFIG_YAML = Path("config.yaml")


class Settings(BaseSettings):
    """Конфиг бота. Секреты — из .env, всё остальное — из config.yaml."""
    # Секреты (только из .env)
    telegram_token: str
    llm_api_key: str
    llm_base_url: str = "https://api.stepanovikov.uno/v1"

    # Доступ
    access_user_ids: list[int] = []
    admin_user_ids: list[int] = []

    # LLM
    default_model: str = "claude-opus-4.7"
    available_models: list[str] = ["claude-opus-4.7"]
    adaptive_selector_model: str = "claude-opus-4.7"
    max_tokens: int = 1024

    # Хранилище
    sqlite_path: str = "data/bot.db"
    redis_url: str = "redis://localhost:6379"
    context_max_stored: int = 500
    context_default_limit: int = 50

    # Агент
    permission_request_timeout: int = 120
    agent_max_iterations: int = 10
    search_default_max_results: int = 5

    # Fetch (тула fetch_url)
    fetch_max_content_chars: int = 10_000
    fetch_request_timeout: int = 15
    fetch_user_agent: str = "Mozilla/5.0 (compatible; PipindrBot/1.0)"

    model_config = SettingsConfigDict(
        env_file=".env",
        yaml_file=str(CONFIG_YAML),
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Приоритет: явные kwargs > env > .env > config.yaml > file_secrets
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    """Получить объект конфига. Синглтон."""
    return Settings()


def reload_settings() -> Settings:
    """Сбросить кэш и перечитать конфиг (для будущей команды /update_conf)."""
    get_settings.cache_clear()
    return get_settings()
