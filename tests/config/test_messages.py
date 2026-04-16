from src.config.messages import BotMessages


def test_not_premium_message_is_non_empty_string():
    assert isinstance(BotMessages.NOT_PREMIUM, str)
    assert BotMessages.NOT_PREMIUM
