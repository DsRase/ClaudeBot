from typing import Protocol


class ThinkingIndicator(Protocol):
    """Порт индикатора «бот думает» на время долгого LLM-вызова.

    Используется как async context manager: __aenter__ поднимает индикатор,
    __aexit__ его снимает (что бы это ни значило для конкретного интерфейса —
    удалить think-msg, погасить typing-индикатор, и т.п.).
    """

    async def __aenter__(self) -> "ThinkingIndicator": ...

    async def __aexit__(self, exc_type, exc, tb) -> None: ...
