import asyncio

import pytest

from src.bot.utils.addThinkLoad import add_think_load


class TestAddThinkLoad:
    """Анимация индикатора загрузки в конце текста сообщения."""

    @pytest.mark.asyncio
    async def test_edits_message_at_least_once(self, mocker):
        """За короткое время вызывается edit_text хотя бы раз."""
        msg = mocker.MagicMock()
        msg.text = "base"
        msg.edit_text = mocker.AsyncMock()

        task = asyncio.create_task(add_think_load(msg, interval=0.01))
        await asyncio.sleep(0.03)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert msg.edit_text.await_count >= 1

    @pytest.mark.asyncio
    async def test_includes_base_text(self, mocker):
        """Каждый edit_text содержит базовый текст."""
        msg = mocker.MagicMock()
        msg.text = "base"
        msg.edit_text = mocker.AsyncMock()

        task = asyncio.create_task(add_think_load(msg, interval=0.01))
        await asyncio.sleep(0.02)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        for call in msg.edit_text.await_args_list:
            assert "base" in call.args[0]

    @pytest.mark.asyncio
    async def test_returns_on_edit_error(self, mocker):
        """Если edit_text падает — корутина выходит без исключения."""
        msg = mocker.MagicMock()
        msg.text = "base"
        msg.edit_text = mocker.AsyncMock(side_effect=RuntimeError("boom"))

        await asyncio.wait_for(add_think_load(msg, interval=0.01), timeout=0.5)

    @pytest.mark.asyncio
    async def test_handles_none_text(self, mocker):
        """Если у сообщения нет text — используется пустая строка."""
        msg = mocker.MagicMock()
        msg.text = None
        msg.edit_text = mocker.AsyncMock()

        task = asyncio.create_task(add_think_load(msg, interval=0.01))
        await asyncio.sleep(0.02)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert msg.edit_text.await_count >= 1
