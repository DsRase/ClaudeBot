import asyncio

import pytest

from src.bot.adapters.thinkingIndicator import TelegramThinkingIndicator


def _make_message(mocker, chat_type="private"):
    msg = mocker.MagicMock()
    msg.chat.type = chat_type
    msg.chat.id = 10
    think = mocker.MagicMock()
    think.delete = mocker.AsyncMock()
    msg.reply = mocker.AsyncMock(return_value=think)
    msg.answer = mocker.AsyncMock(return_value=think)
    return msg, think


@pytest.fixture(autouse=True)
def _stub_add_think_load(mocker):
    async def _noop(_msg):
        await asyncio.sleep(3600)

    mocker.patch("src.bot.adapters.thinkingIndicator.add_think_load", new=_noop)


class TestTelegramThinkingIndicator:
    """async context manager для индикатора 'думаю...'."""

    @pytest.mark.asyncio
    async def test_aenter_sends_thinking_message_in_private(self, mocker):
        """В личке think-msg отправляется через answer."""
        msg, _ = _make_message(mocker, chat_type="private")

        async with TelegramThinkingIndicator(msg):
            pass

        msg.answer.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_aenter_uses_reply_in_group(self, mocker):
        """В группе think-msg — через reply."""
        msg, _ = _make_message(mocker, chat_type="group")

        async with TelegramThinkingIndicator(msg):
            pass

        msg.reply.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_aexit_deletes_thinking_message(self, mocker):
        """На выходе think-msg удаляется."""
        msg, think = _make_message(mocker, chat_type="private")

        async with TelegramThinkingIndicator(msg):
            pass

        think.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_aexit_swallows_delete_failure(self, mocker):
        """Ошибка удаления think-msg не пробрасывается наружу."""
        msg, think = _make_message(mocker, chat_type="private")
        think.delete.side_effect = RuntimeError("boom")

        async with TelegramThinkingIndicator(msg):
            pass
