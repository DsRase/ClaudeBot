import asyncio

from aiogram.types import Message


async def add_think_load(message: Message, interval: float = 0.4) -> None:
    """Анимирует индикатор загрузки в конце текста сообщения.

    Запускается как `asyncio.create_task(...)` и останавливается через `task.cancel()`.
    """
    syms = ["|", "/", "—", "\\"]
    base_text = message.text or ""
    i = 0
    try:
        while True:
            try:
                await message.edit_text(f"{base_text} {syms[i % len(syms)]}")
            except Exception:
                return
            i += 1
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        return
