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
    context_default_limit: int = 50

    permission_request_timeout: int = 120

    search_default_max_results: int = 5

    fetch_max_content_chars: int = 10_000
    fetch_request_timeout: int = 15
    fetch_user_agent: str = "Mozilla/5.0 (compatible; PipindrBot/1.0)"

    model_config = {
        "env_file": ".env",
    }

@lru_cache
def get_settings() -> Settings:
    """Получить объект конфига. Синглтон."""
    return Settings()
