from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    telegram_token: str
    anthropic_api_key: str
    debug: bool = False

    model_config = {"env_file": ".env"}