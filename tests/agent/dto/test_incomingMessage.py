from src.agent.dto import IncomingMessage


class TestIncomingMessage:
    """Конструктор IncomingMessage."""

    def test_required_fields_only(self):
        """Минимальный набор обязательных полей."""
        msg = IncomingMessage(text="hi", user_id=1, chat_id=2, platform_msg_id=3, ts=1000)
        assert msg.text == "hi"
        assert msg.user_id == 1
        assert msg.chat_id == 2
        assert msg.platform_msg_id == 3
        assert msg.ts == 1000

    def test_optional_fields_default_to_none(self):
        """username/fname/lname/reply_* по умолчанию None."""
        msg = IncomingMessage(text="hi", user_id=1, chat_id=2, platform_msg_id=3, ts=1000)
        assert msg.username is None
        assert msg.fname is None
        assert msg.lname is None
        assert msg.reply_to_msg_id is None
        assert msg.reply_to_username is None

    def test_full_payload(self):
        """Все поля сохраняются как переданы."""
        msg = IncomingMessage(
            text="hi",
            user_id=1,
            chat_id=2,
            platform_msg_id=3,
            ts=1000,
            username="vasya",
            fname="Вася",
            lname="Пупкин",
            reply_to_msg_id=99,
            reply_to_username="petya",
        )
        assert msg.username == "vasya"
        assert msg.fname == "Вася"
        assert msg.lname == "Пупкин"
        assert msg.reply_to_msg_id == 99
        assert msg.reply_to_username == "petya"
