import json
from datetime import datetime, timezone

import pytest

from src.storage.schemas import ChatMessage


class TestChatMessage:
    """Сценарии создания и валидации DTO ChatMessage."""

    def test_create_user_message(self):
        """Проверяет, что сообщение пользователя создаётся с корректными полями."""
        msg = ChatMessage(role="user", id=10, ts=1000, text="привет", user_id=123)
        assert msg.role == "user", "role не совпадает с переданным"
        assert msg.id == 10, "id не совпадает с переданным"
        assert msg.user_id == 123, "user_id не совпадает с переданным"
        assert msg.text == "привет", "text не совпадает с переданным"
        assert msg.ts == 1000, "ts не совпадает с переданным"

    def test_create_assistant_message(self):
        """Проверяет, что у ассистента user_id равен None по умолчанию."""
        msg = ChatMessage(role="assistant", id=11, ts=2000, text="ответ", from_username="Пипиндр")
        assert msg.user_id is None, "у ассистента user_id оказался не None"
        assert msg.from_username == "Пипиндр", "from_username ассистента не сохранился"

    def test_serialization_roundtrip_python_mode(self):
        """В python-режиме ts остаётся int — это формат для Redis."""
        msg = ChatMessage(role="user", id=42, ts=9999, text="текст", user_id=42)
        dumped = msg.model_dump(mode="python")
        assert dumped["ts"] == 9999, "ts в python-режиме должен быть int"
        assert "user_id" not in dumped, "user_id не должен попадать в дамп"
        restored = ChatMessage.model_validate(dumped)
        assert restored.id == msg.id and restored.text == msg.text and restored.ts == msg.ts, \
            "поля после roundtrip не совпадают"

    def test_json_dump_formats_ts_to_msk(self):
        """В json-режиме ts превращается в строку YYYY-MM-DD HH:MM по МСК — это формат для LLM."""
        ts = int(datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc).timestamp())
        msg = ChatMessage(role="user", id=1, ts=ts, text="x")
        dumped = msg.model_dump(mode="json")
        assert dumped["ts"] == "2026-01-15 15:00", f"ts в json-режиме отформатировался не в МСК: {dumped['ts']!r}"

    def test_user_id_excluded_from_dump(self):
        """user_id не должен попадать в дамп ни в каком режиме."""
        msg = ChatMessage(role="user", id=1, ts=1, text="x", user_id=123)
        assert "user_id" not in msg.model_dump(mode="python"), "user_id просочился в python-дамп"
        assert "user_id" not in msg.model_dump(mode="json"), "user_id просочился в json-дамп"
        assert "user_id" not in json.loads(msg.model_dump_json()), "user_id просочился в json-строку"

    def test_invalid_role_raises(self):
        """Проверяет, что недопустимое значение role вызывает исключение."""
        with pytest.raises(Exception):
            ChatMessage(role="admin", id=1, ts=1, text="x")

    def test_optional_fields_default_none(self):
        """Проверяет, что from_username/fname/lname/to_username/reply_id по умолчанию None."""
        msg = ChatMessage(role="user", id=1, ts=1, text="x")
        assert msg.from_username is None, "from_username должен быть None по умолчанию"
        assert msg.fname is None, "fname должен быть None по умолчанию"
        assert msg.lname is None, "lname должен быть None по умолчанию"
        assert msg.to_username is None, "to_username должен быть None по умолчанию"
        assert msg.reply_id is None, "reply_id должен быть None по умолчанию"

    def test_user_fields_preserved(self):
        """Проверяет, что from_username/fname/lname сохраняются как переданы."""
        msg = ChatMessage(
            role="user", id=1, ts=1, text="x",
            from_username="vasya", fname="Вася", lname="Пупкин",
        )
        assert (msg.from_username, msg.fname, msg.lname) == ("vasya", "Вася", "Пупкин"), \
            "поля юзера сохранились некорректно"
