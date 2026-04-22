import pytest

from src.bot.adapters.responseChannel import TelegramResponseChannel


def _make_message(mocker, chat_type="private"):
    msg = mocker.MagicMock()
    msg.chat.type = chat_type
    msg.chat.id = 10
    sent = mocker.MagicMock()
    sent.message_id = 555
    msg.reply = mocker.AsyncMock(return_value=sent)
    msg.answer = mocker.AsyncMock(return_value=sent)
    return msg, sent


@pytest.fixture(autouse=True)
def _stub_markdown(mocker):
    mocker.patch(
        "src.bot.adapters.responseChannel.telegramify_markdown.convert",
        return_value=("text", []),
    )
    mocker.patch(
        "src.bot.adapters.responseChannel.split_text_with_entities",
        return_value=[("text", [])],
    )


class TestSendResponse:
    """TelegramResponseChannel.send_response."""

    @pytest.mark.asyncio
    async def test_private_uses_answer(self, mocker):
        """В личке используется answer (не reply)."""
        msg, _ = _make_message(mocker, chat_type="private")
        ch = TelegramResponseChannel(msg)

        await ch.send_response("hello")

        msg.answer.assert_awaited_once()
        msg.reply.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_group_uses_reply_for_first_chunk(self, mocker):
        """В группе первый чанк — reply."""
        msg, _ = _make_message(mocker, chat_type="group")
        ch = TelegramResponseChannel(msg)

        await ch.send_response("hello")

        msg.reply.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_first_message_id(self, mocker):
        """Возвращает message_id первого отправленного чанка."""
        msg, sent = _make_message(mocker, chat_type="private")
        sent.message_id = 777
        ch = TelegramResponseChannel(msg)

        result = await ch.send_response("hi")

        assert result == 777

    @pytest.mark.asyncio
    async def test_multiple_chunks_use_answer_after_first(self, mocker):
        """В группе: первый — reply, последующие — answer."""
        mocker.patch(
            "src.bot.adapters.responseChannel.split_text_with_entities",
            return_value=[("a", []), ("b", []), ("c", [])],
        )
        msg, _ = _make_message(mocker, chat_type="group")
        ch = TelegramResponseChannel(msg)

        await ch.send_response("long")

        assert msg.reply.await_count == 1
        assert msg.answer.await_count == 2


class TestSendError:
    """TelegramResponseChannel.send_error."""

    @pytest.mark.asyncio
    async def test_known_reason_sends_message(self, mocker):
        """Известный код → юзеру отправляется текст из BotMessages."""
        msg, _ = _make_message(mocker, chat_type="private")
        ch = TelegramResponseChannel(msg)

        await ch.send_error("no_access")

        msg.answer.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unknown_reason_silent(self, mocker):
        """Неизвестный код → ничего не отправляется."""
        msg, _ = _make_message(mocker, chat_type="private")
        ch = TelegramResponseChannel(msg)

        await ch.send_error("wat")

        msg.answer.assert_not_awaited()
        msg.reply.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_group_uses_reply(self, mocker):
        """В группе ошибка — через reply."""
        msg, _ = _make_message(mocker, chat_type="group")
        ch = TelegramResponseChannel(msg)

        await ch.send_error("llm_failed")

        msg.reply.assert_awaited_once()
