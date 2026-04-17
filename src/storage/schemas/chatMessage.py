from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Одно сообщение в истории чата."""
    role: Literal["user", "assistant"]
    user_id: int | None  # None для сообщений ассистента
    content: str
    timestamp: int  # Unix timestamp
