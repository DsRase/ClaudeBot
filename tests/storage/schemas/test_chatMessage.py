import pytest

from src.storage.schemas import ChatMessage


class TestChatMessage:
    """Сценарии создания и валидации DTO ChatMessage."""

    def test_create_user_message(self):
        """Проверяет, что сообщение пользователя создаётся с корректными полями."""
        msg = ChatMessage(role="user", user_id=123, content="привет", timestamp=1000)
        assert msg.role == "user", "role не совпадает с переданным"
        assert msg.user_id == 123, "user_id не совпадает с переданным"
        assert msg.content == "привет", "content не совпадает с переданным"
        assert msg.timestamp == 1000, "timestamp не совпадает с переданным"

    def test_create_assistant_message(self):
        """Проверяет, что у ассистента user_id равен None."""
        msg = ChatMessage(role="assistant", user_id=None, content="ответ", timestamp=2000)
        assert msg.user_id is None, "у ассистента user_id оказался не None"

    def test_serialization_roundtrip(self):
        """Проверяет, что объект не теряет данные при сериализации и десериализации."""
        msg = ChatMessage(role="user", user_id=42, content="текст", timestamp=9999)
        restored = ChatMessage.model_validate_json(msg.model_dump_json())
        assert restored == msg, "объект после сериализации и десериализации не совпадает с исходным"

    def test_invalid_role_raises(self):
        """Проверяет, что недопустимое значение role вызывает исключение."""
        with pytest.raises(Exception):
            ChatMessage(role="admin", user_id=1, content="x", timestamp=1)

    def test_optional_user_fields_default_none(self):
        """Проверяет, что username/first_name/last_name/reply_to_username по умолчанию None."""
        msg = ChatMessage(role="user", user_id=1, content="x", timestamp=1)
        assert msg.username is None, "username должен быть None по умолчанию"
        assert msg.first_name is None, "first_name должен быть None по умолчанию"
        assert msg.last_name is None, "last_name должен быть None по умолчанию"
        assert msg.reply_to_username is None, "reply_to_username должен быть None по умолчанию"

    def test_user_fields_preserved(self):
        """Проверяет, что username/first_name/last_name сохраняются как переданы."""
        msg = ChatMessage(
            role="user", user_id=1, content="x", timestamp=1,
            username="vasya", first_name="Вася", last_name="Пупкин",
        )
        assert (msg.username, msg.first_name, msg.last_name) == ("vasya", "Вася", "Пупкин"), \
            "поля юзера сохранились некорректно"
