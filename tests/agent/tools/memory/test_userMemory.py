import pytest

from src.agent.tools.memory.userMemory import (
    clear_user_memory_fn,
    get_user_memory_fn,
    set_user_memory_fn,
)


class TestGetUserMemoryFn:
    """get_user_memory_fn."""

    @pytest.mark.asyncio
    async def test_returns_memory_when_present(self, mocker):
        """Если в БД есть память — возвращается она."""
        mocker.patch(
            "src.agent.tools.memory.userMemory._get",
            new=mocker.AsyncMock(return_value="data"),
        )

        assert await get_user_memory_fn(1) == "data"

    @pytest.mark.asyncio
    async def test_returns_placeholder_when_empty(self, mocker):
        """None/пустая строка → placeholder '(память пуста)'."""
        mocker.patch(
            "src.agent.tools.memory.userMemory._get",
            new=mocker.AsyncMock(return_value=None),
        )

        assert await get_user_memory_fn(1) == "(память пуста)"


class TestSetUserMemoryFn:
    """set_user_memory_fn."""

    @pytest.mark.asyncio
    async def test_writes_and_reports_length(self, mocker):
        """Пишет в БД и возвращает сообщение с длиной."""
        mock_set = mocker.patch(
            "src.agent.tools.memory.userMemory._set",
            new=mocker.AsyncMock(),
        )

        result = await set_user_memory_fn(1, "hello")

        mock_set.assert_awaited_once_with(1, "hello")
        assert "5" in result


class TestClearUserMemoryFn:
    """clear_user_memory_fn."""

    @pytest.mark.asyncio
    async def test_clears_and_confirms(self, mocker):
        """Чистит БД и отдаёт подтверждение."""
        mock_clear = mocker.patch(
            "src.agent.tools.memory.userMemory._clear",
            new=mocker.AsyncMock(),
        )

        result = await clear_user_memory_fn(1)

        mock_clear.assert_awaited_once_with(1)
        assert "очищена" in result
