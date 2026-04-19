from src.storage.sqlite.users import (
    get_user_memory as _get,
    set_user_memory as _set,
    clear_user_memory as _clear,
)


async def get_user_memory_fn(user_id: int) -> str:
    memory = await _get(user_id)
    return memory if memory else "(память пуста)"


async def set_user_memory_fn(user_id: int, content: str) -> str:
    await _set(user_id, content)
    return f"Память обновлена ({len(content)} символов)."


async def clear_user_memory_fn(user_id: int) -> str:
    await _clear(user_id)
    return "Память очищена."
