import pytest

from src.bot.handlers import chat as chat_module


def _tg_message(mocker, text="hi", chat_type="private", reply_to=None, bot_id=100):
    msg = mocker.MagicMock()
    msg.text = text
    msg.chat.type = chat_type
    msg.chat.id = 2
    msg.message_id = 10
    msg.from_user.id = 1
    msg.from_user.is_bot = False
    msg.from_user.username = "u"
    msg.from_user.first_name = "f"
    msg.from_user.last_name = "l"
    msg.date.timestamp = mocker.MagicMock(return_value=1000.0)
    msg.reply_to_message = reply_to
    return msg


def _bot(mocker, username="bot", user_id=100):
    bot = mocker.MagicMock()
    me = mocker.MagicMock()
    me.username = username
    me.id = user_id
    bot.me = mocker.AsyncMock(return_value=me)
    return bot


class TestIsTriggered:
    """_is_triggered: логика триггера в группах и личке."""

    @pytest.mark.asyncio
    async def test_private_always_triggers(self, mocker):
        """В личке любое сообщение триггерит."""
        msg = _tg_message(mocker, chat_type="private")
        assert await chat_module._is_triggered(msg, _bot(mocker)) is True

    @pytest.mark.asyncio
    async def test_group_without_mention_does_not_trigger(self, mocker):
        """В группе без @упоминания и без reply-to-bot — не триггер."""
        msg = _tg_message(mocker, text="random", chat_type="group")
        assert await chat_module._is_triggered(msg, _bot(mocker, username="bot")) is False

    @pytest.mark.asyncio
    async def test_group_mention_triggers(self, mocker):
        """В группе с @упоминанием бота — триггер."""
        msg = _tg_message(mocker, text="hey @bot привет", chat_type="group")
        assert await chat_module._is_triggered(msg, _bot(mocker, username="bot")) is True

    @pytest.mark.asyncio
    async def test_group_reply_to_bot_triggers(self, mocker):
        """В группе reply на сообщение бота — триггер."""
        reply = mocker.MagicMock()
        reply.from_user.id = 100
        msg = _tg_message(mocker, text="yo", chat_type="group", reply_to=reply)
        assert await chat_module._is_triggered(msg, _bot(mocker, user_id=100)) is True


class TestToIncoming:
    """_to_incoming: маппинг TG-сообщения в IncomingMessage."""

    def test_basic_fields(self, mocker):
        """Поля из aiogram.Message корректно перекладываются в IncomingMessage."""
        msg = _tg_message(mocker)

        incoming = chat_module._to_incoming(msg)

        assert incoming.text == "hi"
        assert incoming.user_id == 1
        assert incoming.chat_id == 2
        assert incoming.platform_msg_id == 10
        assert incoming.ts == 1000
        assert incoming.username == "u"

    def test_reply_fields_from_reply_message(self, mocker):
        """Если есть reply_to_message — reply_to_msg_id/reply_to_username заполняются."""
        reply = mocker.MagicMock()
        reply.message_id = 77
        reply.from_user.username = "other"
        msg = _tg_message(mocker, reply_to=reply)

        incoming = chat_module._to_incoming(msg)

        assert incoming.reply_to_msg_id == 77
        assert incoming.reply_to_username == "other"

    def test_no_reply_fields_are_none(self, mocker):
        """Без reply_to_message → reply_to_* is None."""
        msg = _tg_message(mocker)

        incoming = chat_module._to_incoming(msg)

        assert incoming.reply_to_msg_id is None
        assert incoming.reply_to_username is None


class TestChatHandler:
    """Главный @router.message() хендлер."""

    @pytest.mark.asyncio
    async def test_ignores_messages_without_text(self, mocker):
        """Сообщения без .text игнорируются (stickers/media/etc)."""
        respond = mocker.patch("src.bot.handlers.chat.respond", new=mocker.AsyncMock())
        record = mocker.patch("src.bot.handlers.chat.record_message", new=mocker.AsyncMock())
        msg = _tg_message(mocker)
        msg.text = None

        await chat_module.chat(msg, _bot(mocker))

        respond.assert_not_awaited()
        record.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ignores_bot_messages(self, mocker):
        """Сообщения от ботов игнорируются."""
        respond = mocker.patch("src.bot.handlers.chat.respond", new=mocker.AsyncMock())
        record = mocker.patch("src.bot.handlers.chat.record_message", new=mocker.AsyncMock())
        msg = _tg_message(mocker)
        msg.from_user.is_bot = True

        await chat_module.chat(msg, _bot(mocker))

        respond.assert_not_awaited()
        record.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_triggered_group_only_records(self, mocker):
        """В группе без триггера — только record_message, respond не зовётся."""
        respond = mocker.patch("src.bot.handlers.chat.respond", new=mocker.AsyncMock())
        record = mocker.patch("src.bot.handlers.chat.record_message", new=mocker.AsyncMock())
        msg = _tg_message(mocker, text="ничего", chat_type="group")

        await chat_module.chat(msg, _bot(mocker, username="bot"))

        record.assert_awaited_once()
        respond.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_triggered_calls_respond_with_adapters(self, mocker):
        """В личке (триггер по умолчанию) — зовётся respond с тремя адаптерами."""
        respond = mocker.patch("src.bot.handlers.chat.respond", new=mocker.AsyncMock())
        mocker.patch("src.bot.handlers.chat.record_message", new=mocker.AsyncMock())
        msg = _tg_message(mocker, chat_type="private")

        await chat_module.chat(msg, _bot(mocker))

        respond.assert_awaited_once()
        args = respond.await_args.args
        assert args[0].text == "hi"
        assert args[1] is not None and args[2] is not None and args[3] is not None
