from typing import Protocol


class ResponseChannel(Protocol):
    """Порт отправки финального ответа пользователю.

    Адаптер сам решает, как разбивать на чанки, форматировать и куда слать.
    ChatService лишь передаёт готовый текст и опциональный «тип ошибки».
    """

    async def send_response(self, text: str) -> int | None:
        """Отправить ответ пользователю. Возвращает platform_msg_id первого отправленного сообщения (или None)."""
        ...

    async def send_error(self, reason: str) -> None:
        """Сообщить пользователю об ошибке. `reason` — код ошибки, адаптер выбирает текст сам.

        Известные коды: "llm_failed", "no_access".
        """
        ...
