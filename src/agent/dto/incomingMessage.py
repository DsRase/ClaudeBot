from pydantic import BaseModel


class IncomingMessage(BaseModel):
    """Интерфейс-агностичное входящее сообщение.

    Адаптер любого интерфейса (Telegram, Discord, Web) собирает IncomingMessage
    из своего нативного события и передаёт в ChatService. Поля подобраны так,
    чтобы их можно было заполнить в любом разумном чат-интерфейсе.
    """
    text: str
    user_id: int
    chat_id: int
    platform_msg_id: int
    ts: int  # unix timestamp UTC
    username: str | None = None
    fname: str | None = None
    lname: str | None = None
    reply_to_msg_id: int | None = None
    reply_to_username: str | None = None
