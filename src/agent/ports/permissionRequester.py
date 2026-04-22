from typing import Protocol


class PermissionRequester(Protocol):
    """Порт запроса разрешения у инициатора на вызов тулы агента.

    Каждый интерфейс реализует по-своему: Telegram — inline-клавиатура,
    Discord — reaction/button, web — модалка в UI.
    """

    async def request(self, tool_name: str, description: str) -> bool:
        """Запросить разрешение. Возвращает True/False (таймаут считается отказом)."""
        ...
