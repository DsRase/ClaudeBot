from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Одно сообщение в истории чата."""
    role: Literal["user", "assistant"]
    user_id: int | None  # None для сообщений ассистента
    username: str | None = None  # @username Telegram юзера, может отсутствовать
    first_name: str | None = None  # имя юзера в Telegram
    last_name: str | None = None  # фамилия юзера в Telegram, может отсутствовать
    reply_to_username: str | None = None  # @username того, кому юзер ответил (если ответил)
    content: str
    timestamp: int  # Unix timestamp
