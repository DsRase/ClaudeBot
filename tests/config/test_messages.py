from src.config.messages import BotMessages
from src.utils.messager import get_random_message


def test_not_premium_message_is_non_empty_string():
    assert isinstance(get_random_message(BotMessages.NOT_PREMIUM), str), "Возвращается не строка"
    assert get_random_message(BotMessages.NOT_PREMIUM), "Ничего не возвращается"
