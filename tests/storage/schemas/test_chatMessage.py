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
