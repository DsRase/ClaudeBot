from src.config import BotMessages
from src.utils.messager import get_random_message


class TestBotMessages:
    """Сценарии проверки констант для бота."""

    def test_no_access_message_is_non_empty_string(self):
        """Проверяет, что get_random_message возвращает непустую строку из NO_ACCESS."""
        msg = get_random_message(BotMessages.NO_ACCESS)
        assert isinstance(msg, str), "вернулось не строковое значение"
        assert msg, "вернулась пустая строка вместо текста"
