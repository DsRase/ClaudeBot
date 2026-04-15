from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    telegram_token: str
    anthropic_api_key: str

    premium_user_ids: list[int] = []
    premium_model: str = "claude-opus-4-6"
    default_model: str = "claude-sonnet-4-6"

    model_config = {
        "env_file": ".env",
    }

@lru_cache
def get_settings() -> Settings:
    return Settings()
