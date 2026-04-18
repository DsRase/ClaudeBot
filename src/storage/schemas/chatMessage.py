from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_serializer

_MSK = ZoneInfo("Europe/Moscow")


class ChatMessage(BaseModel):
    """Одно сообщение в истории чата. Дамп этой модели уходит в LLM как есть."""
    role: Literal["user", "assistant"]
    id: int  # telegram message_id
    ts: int  # unix timestamp UTC; в JSON-дампе превращается в "YYYY-MM-DD HH:MM" по МСК
    from_username: str | None = None
    fname: str | None = None
    lname: str | None = None
    to_username: str | None = None
    reply_id: int | None = None
    text: str
    user_id: int | None = Field(default=None, exclude=True)

    @field_serializer("ts", when_used="json")
    def _ser_ts(self, ts: int) -> str:
        return datetime.fromtimestamp(ts, tz=_MSK).strftime("%Y-%m-%d %H:%M")
