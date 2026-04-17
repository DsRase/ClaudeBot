from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Основной конфиг с .env и прочим."""
    telegram_token: str
    anthropic_api_key: str

    max_tokens: int = 1024

    premium_user_ids: list[int] = []
    base_user_ids: list[int] = []
    premium_model: str = "claude-opus-4-6"
    default_model: str = "claude-sonnet-4-6"

    redis_url: str = "redis://localhost:6379"
    context_max_stored: int = 500
    context_default_limit: int = 100

    model_config = {
        "env_file": ".env",
    }

@lru_cache
def get_settings() -> Settings:
    """Получить объект конфига. Синглтон."""
    return Settings()
