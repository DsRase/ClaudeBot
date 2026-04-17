from src.config import BotMessages
from src.utils.messager import get_random_message


class TestBotMessages:
    """Сценарии проверки констант для бота."""

    def test_not_premium_message_is_non_empty_string(self):
        """Проверяет, что get_random_message возвращает непустую строку из NOT_PREMIUM."""
        msg = get_random_message(BotMessages.NOT_PREMIUM)
        assert isinstance(msg, str), "вернулось не строковое значение"
        assert msg, "вернулась пустая строка вместо текста"
